"""Bounded, allowlisted Census acquisition. Candidate output is never a public release."""
import argparse
import hashlib
import http.client
import json
import os
import re
import socket
import ssl
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

HOST = 'api.census.gov'
MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 100_000
RESPONSE_SECONDS = 30
PATHS = {flow:f'/data/timeseries/intltrade/{flow}/hs' for flow in ('imports','exports')}
DIAGNOSTIC_CATEGORIES = frozenset({
    'validation_failed', 'connect_timeout', 'headers_timeout', 'body_timeout',
    'dns_error', 'tls_error', 'connection_error', 'protocol_error',
    'rate_limited', 'upstream_unavailable', 'http_rejected', 'no_results',
})

class SourceError(Exception):
    """Safe-to-display diagnostic with no request URL, body or credentials."""

    def __init__(self, message, *, category='validation_failed', http_status=None):
        super().__init__(message)
        self.category = category if category in DIAGNOSTIC_CATEGORIES else 'validation_failed'
        self.http_status = http_status if type(http_status) is int and 100 <= http_status <= 599 else None

class RetryableSourceError(SourceError):
    pass

def validate_period(period):
    if not isinstance(period,str) or not re.fullmatch(r'20\d{2}-(0[1-9]|1[0-2])',period):
        raise SourceError('Period must be YYYY-MM in the supported century')

def validate_scope(product, partner):
    for value, pattern in ((product, r'(?:[0-9]{2}|\*)'), (partner, r'(?:[0-9]{4}|-|\*)')):
        if not isinstance(value, str) or not re.fullmatch(pattern, value):
            raise SourceError('Scope must be an HS2 code and a Census partner code, or explicit * wildcards')

def aggregate_dimensions(flow):
    # Census International Trade API User Guide, p. 7: '-' means total.
    return {'DISTRICT': '-', **({'CTY_SUBCODE': '-', 'RP': '-'} if flow == 'imports' else {'DF': '-'})}

def fetch_bytes(url):
    parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.netloc!=HOST or parsed.path not in PATHS.values() or parsed.fragment:
        raise SourceError('Source is not allowlisted')
    connection=http.client.HTTPSConnection(HOST,timeout=5)
    deadline=time.monotonic()+RESPONSE_SECONDS
    expired=threading.Event()
    watchdog=None
    response=None
    phase='connect'
    try:
        connection.connect()
        transport=connection.sock
        remaining=deadline-time.monotonic()
        if remaining<=0:raise RetryableSourceError('Source request timed out',category='connect_timeout')
        # Keep the socket reference: getresponse() may detach it for Connection: close.
        # Shutdown interrupts header/body reads even if a peer keeps dripping bytes.
        def abort_response():
            expired.set()
            try:transport.shutdown(socket.SHUT_RDWR)
            except OSError:pass
        watchdog=threading.Timer(remaining,abort_response)
        watchdog.daemon=True
        watchdog.start()
        transport.settimeout(remaining)
        phase='headers'
        connection.request('GET',parsed.path+'?'+parsed.query,headers={'Accept':'application/json','Accept-Encoding':'identity','User-Agent':'US-Trade-Explorer/0.1'})
        response=connection.getresponse()
        if response.status==429:raise RetryableSourceError('Source rate limited the request',category='rate_limited',http_status=429)
        if response.status in (500,502,503,504):raise RetryableSourceError('Source temporarily unavailable',category='upstream_unavailable',http_status=response.status)
        if response.status==204:raise SourceError('No records for this selection; no zero or candidate was created',category='no_results',http_status=204)
        if response.status!=200:raise SourceError('Source rejected request; check credentials, period and contract',category='http_rejected',http_status=response.status)
        if response.getheader('Content-Encoding','identity')!='identity':raise SourceError('Unsupported response encoding')
        content_type=response.getheader('Content-Type','').split(';')[0].strip().lower()
        if content_type not in ('application/json','text/json'):raise SourceError('Source did not return JSON')
        size=response.getheader('Content-Length')
        if size is not None and (not size.isdigit() or int(size)>MAX_BYTES):raise SourceError('Response exceeds size limit')
        phase='body'
        chunks=[];length=0
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise RetryableSourceError('Source request timed out',category='body_timeout')
            transport.settimeout(remaining)
            chunk=response.read1(min(65536,MAX_BYTES+1-length))
            if not chunk:break
            chunks.append(chunk);length+=len(chunk)
            if length>MAX_BYTES:raise SourceError('Response exceeds size limit')
        if expired.is_set() or time.monotonic()>=deadline:raise RetryableSourceError('Source request timed out',category='body_timeout')
        return b''.join(chunks)
    except SourceError:
        raise
    except (OSError,http.client.HTTPException) as error:
        if expired.is_set() or isinstance(error,TimeoutError):category=phase+'_timeout'
        elif isinstance(error,socket.gaierror):category='dns_error'
        elif isinstance(error,ssl.SSLError):category='tls_error'
        elif isinstance(error,http.client.HTTPException):category='protocol_error'
        else:category='connection_error'
        raise RetryableSourceError('Source transport failed',category=category) from None
    finally:
        if watchdog is not None:
            watchdog.cancel()
            watchdog.join()
        if response is not None:response.close()
        connection.close()

def parse_rows(data,flow,period,*,expected_summary=None):
    validate_period(period)
    if flow not in PATHS:raise SourceError('Unsupported flow')
    prefix='I' if flow=='imports' else 'E';value_field='GEN_VAL_MO' if flow=='imports' else 'ALL_VAL_MO'
    dimensions=aggregate_dimensions(flow)
    required={f'{prefix}_COMMODITY',f'{prefix}_COMMODITY_SDESC','CTY_CODE','CTY_NAME',value_field,'COMM_LVL'}|dimensions.keys()
    if expected_summary is not None:required=required|{'SUMMARY_LVL'}
    allowed=required|{'time','YEAR','MONTH'}
    if not isinstance(data,list) or not 2<=len(data)<=MAX_ROWS+1 or not isinstance(data[0],list):raise SourceError('Empty or oversized source table')
    header=data[0]
    if not all(isinstance(h,str) for h in header):raise SourceError('Source schema changed: invalid column names')
    names=set(header)
    if len(header)!=len(names) or not required<=names or not names<=allowed:
        # Only our fixed contract names and numeric counts may enter diagnostics.
        # Never echo an unexpected source column: it could reflect a credential.
        missing=','.join(sorted(required-names)) or 'none'
        raise SourceError(f'Source schema changed: missing known columns={missing}; duplicate columns={len(header)-len(names)}; unknown columns={len(names-allowed)}')
    if ('YEAR' in header)!=('MONTH' in header) or not ('time' in header or {'YEAR','MONTH'}<=set(header)):raise SourceError('Source period fields are missing or incomplete')
    rows=[];seen=set()
    for raw in data[1:]:
        if not isinstance(raw,list) or len(raw)!=len(header) or not all(isinstance(v,str) for v in raw):raise SourceError('Malformed source row')
        row=dict(zip(header,raw));code=row[f'{prefix}_COMMODITY'];country=row['CTY_CODE'];value=row[value_field]
        if not re.fullmatch(r'[0-9]{2}',code) or not re.fullmatch(r'(?:[0-9]{4}|-)',country) or row['COMM_LVL']!='HS2':raise SourceError('Source dimension mismatch')
        if ('time' in row and row['time']!=period) or ('YEAR' in row and (row['YEAR']!=period[:4] or row['MONTH']!=period[5:])):raise SourceError('Source period mismatch')
        if any(row[name]!=expected for name,expected in dimensions.items()):raise SourceError('Unexpected source aggregation')
        if expected_summary is not None and row['SUMMARY_LVL']!=expected_summary:raise SourceError('Unexpected source summary level')
        if not re.fullmatch(r'(0|[1-9]\d{0,23})',value):raise SourceError('Unknown value or suppression marker; review contract')
        for name in (f'{prefix}_COMMODITY_SDESC','CTY_NAME'):
            if not 0<len(row[name])<=250 or any(ord(c)<32 for c in row[name]):raise SourceError('Invalid source description')
        key=(code,country)
        if key in seen:raise SourceError('Duplicate source dimensions')
        seen.add(key)
        rows.append({'product':code,'description':row[f'{prefix}_COMMODITY_SDESC'],'partnerCode':country,'partnerName':row['CTY_NAME'],'flow':flow,'period':period,'value':value,'status':'reported_zero' if value=='0' else 'reported'})
    return rows

def fetch_candidate(flow,period,key,*,product='09',partner='1220',capture=None):
    validate_period(period)
    validate_scope(product,partner)
    if flow not in PATHS:raise SourceError('Unsupported flow')
    if not isinstance(key,str) or not key or len(key)>256 or any(c.isspace() for c in key):raise SourceError('CENSUS_API_KEY is missing or invalid')
    if capture is not None and not callable(capture):raise SourceError('Invalid source capture adapter')
    prefix='I' if flow=='imports' else 'E';value='GEN_VAL_MO' if flow=='imports' else 'ALL_VAL_MO'
    # Census recommends YEAR/MONTH and smaller queries to reduce timeouts.
    dimensions=aggregate_dimensions(flow)
    query={
        # Filter columns are returned by Census; requesting them again in get
        # duplicates the response header. Keep get and predicates disjoint.
        'get':','.join([f'{prefix}_COMMODITY_SDESC','CTY_NAME',value]),
        'YEAR':period[:4],'MONTH':period[5:],'COMM_LVL':'HS2',
        f'{prefix}_COMMODITY':product,'CTY_CODE':partner,**dimensions,
    }
    # The guide places world '-' in DET, alongside countries, rather than CGP.
    # Keep established country queries unchanged; world is a new explicit scope.
    if partner=='-':query['SUMMARY_LVL']='DET'
    # Credential-bearing URL never leaves this function and fetch_bytes.
    url='https://'+HOST+PATHS[flow]+'?'+urlencode({**query,'key':key})
    for attempt in range(3):
        try:
            raw=fetch_bytes(url)
            if len(raw)>MAX_BYTES or key.encode() in raw:raise SourceError('Response rejected by evidence safety check')
            try:data=json.loads(raw)
            except (ValueError,UnicodeError,RecursionError):raise SourceError('Invalid JSON response') from None
            rows=parse_rows(data,flow,period,expected_summary='DET' if partner=='-' else None)
            if any((product!='*' and row['product']!=product) or (partner!='*' and row['partnerCode']!=partner) for row in rows):raise SourceError('Source returned rows outside the requested scope')
            identity={'schemaVersion':2,'flow':flow,'period':period,'sourceQuery':query,'sourceHash':hashlib.sha256(raw).hexdigest()}
            candidate={
                **identity,
                'candidateId':hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                'state':'candidate','source':'https://'+HOST+PATHS[flow],
                'scope':{'commodityLevel':'HS2','product':product,'partner':partner,'coverage':'unverified'},
                'officialReleaseDate':None,'officialRevisionDate':None,
                'ingestedAt':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'rows':rows,'publicationBlockers':['Live dimensions and coverage not yet reconciled','Official publication evidence not yet attached'],
            }
            if key in json.dumps(candidate,ensure_ascii=False):raise SourceError('Response rejected by evidence safety check')
            # A trusted archival adapter receives only validated source bytes,
            # never the credential-bearing URL or a request object.
            if capture is not None:capture(raw)
            return candidate
        except (SourceError,OSError) as error:
            safe=error if isinstance(error,SourceError) else RetryableSourceError('Source transport failed',category='connection_error')
            # Fixed keys, allowlisted categories and bounded integers only. Never str(error).
            print(json.dumps({'event':'census_attempt_failed','attempt':attempt+1,'category':safe.category,'httpStatus':safe.http_status}),file=sys.stderr)
            if not isinstance(safe,RetryableSourceError):raise safe from None
            if attempt==2:raise SourceError('Source acquisition failed after three attempts',category=safe.category,http_status=safe.http_status) from None
            time.sleep(2**attempt)
    raise SourceError('Acquisition did not complete')

def main():
    parser=argparse.ArgumentParser(description='Fetch one monthly candidate; does not publish')
    parser.add_argument('--flow',choices=PATHS,required=True);parser.add_argument('--period',required=True);parser.add_argument('--output',type=Path,default=Path('pipeline/output'))
    parser.add_argument('--product',default='09',help='HS2 code; default 09. Quote * for all chapters.')
    parser.add_argument('--partner',default='1220',help='Census code; default 1220 (Canada). Quote * for all source partners.')
    args=parser.parse_args()
    try:
        candidate=fetch_candidate(args.flow,args.period,os.environ.get('CENSUS_API_KEY',''),product=args.product,partner=args.partner)
        args.output.mkdir(parents=True,exist_ok=True)
        path=args.output/f"candidate-{args.flow}-{args.period}-{candidate['candidateId']}.json"
        # Query-aware identity avoids collisions between narrow and broad requests.
        if not path.exists():
            temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(candidate,separators=(',',':')),encoding='utf-8');os.replace(temporary,path)
        print(f"Candidate validated: {len(candidate['rows'])} rows; requested coverage remains unverified. Publication remains blocked.")
    except SourceError as error:
        status=f', HTTP {error.http_status}' if error.http_status is not None else ''
        parser.exit(1,f'Acquisition failed [{error.category}{status}]: {error}\n')

if __name__=='__main__':main()
