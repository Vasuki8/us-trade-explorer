"""Bounded, allowlisted Census acquisition. Candidate output is never a public release."""
import argparse
import hashlib
import http.client
import json
import os
import re
import socket
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

class SourceError(Exception):
    """Safe-to-display diagnostic with no request URL, body or credentials."""

class RetryableSourceError(SourceError):
    pass

def validate_period(period):
    if not isinstance(period,str) or not re.fullmatch(r'20\d{2}-(0[1-9]|1[0-2])',period):
        raise SourceError('Period must be YYYY-MM in the supported century')

def fetch_bytes(url):
    parsed=urlsplit(url)
    if parsed.scheme!='https' or parsed.netloc!=HOST or parsed.path not in PATHS.values() or parsed.fragment:
        raise SourceError('Source is not allowlisted')
    connection=http.client.HTTPSConnection(HOST,timeout=5)
    deadline=time.monotonic()+RESPONSE_SECONDS
    expired=threading.Event()
    watchdog=None
    response=None
    try:
        connection.connect()
        transport=connection.sock
        remaining=deadline-time.monotonic()
        if remaining<=0:raise RetryableSourceError('Source request timed out')
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
        connection.request('GET',parsed.path+'?'+parsed.query,headers={'Accept':'application/json','Accept-Encoding':'identity','User-Agent':'US-Trade-Explorer/0.1'})
        response=connection.getresponse()
        if response.status in (429,500,502,503,504):raise RetryableSourceError('Source temporarily unavailable')
        if response.status!=200:raise SourceError('Source rejected request; check credentials, period and contract')
        if response.getheader('Content-Encoding','identity')!='identity':raise SourceError('Unsupported response encoding')
        content_type=response.getheader('Content-Type','').split(';')[0].strip().lower()
        if content_type not in ('application/json','text/json'):raise SourceError('Source did not return JSON')
        size=response.getheader('Content-Length')
        if size is not None and (not size.isdigit() or int(size)>MAX_BYTES):raise SourceError('Response exceeds size limit')
        chunks=[];length=0
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise RetryableSourceError('Source request timed out')
            transport.settimeout(remaining)
            chunk=response.read1(min(65536,MAX_BYTES+1-length))
            if not chunk:break
            chunks.append(chunk);length+=len(chunk)
            if length>MAX_BYTES:raise SourceError('Response exceeds size limit')
        if expired.is_set() or time.monotonic()>=deadline:raise RetryableSourceError('Source request timed out')
        return b''.join(chunks)
    except SourceError:
        raise
    except (OSError,http.client.HTTPException,socket.timeout):
        raise RetryableSourceError('Source connection failed') from None
    finally:
        if watchdog is not None:
            watchdog.cancel()
            watchdog.join()
        if response is not None:response.close()
        connection.close()

def parse_rows(data,flow,period):
    validate_period(period)
    if flow not in PATHS:raise SourceError('Unsupported flow')
    prefix='I' if flow=='imports' else 'E';value_field='GEN_VAL_MO' if flow=='imports' else 'ALL_VAL_MO'
    required={f'{prefix}_COMMODITY',f'{prefix}_COMMODITY_SDESC','CTY_CODE','CTY_NAME',value_field,'time','COMM_LVL'}
    dimensions={'DISTRICT':'00',**({'CTY_SUBCODE':'0','RP':'00'} if flow=='imports' else {'DF':'-'} )}
    allowed=required|dimensions.keys()
    if not isinstance(data,list) or not 2<=len(data)<=MAX_ROWS+1 or not isinstance(data[0],list):raise SourceError('Empty or oversized source table')
    header=data[0]
    if not all(isinstance(h,str) for h in header) or len(header)!=len(set(header)) or not required<=set(header) or not set(header)<=allowed:raise SourceError('Source schema changed')
    rows=[];seen=set()
    for raw in data[1:]:
        if not isinstance(raw,list) or len(raw)!=len(header) or not all(isinstance(v,str) for v in raw):raise SourceError('Malformed source row')
        row=dict(zip(header,raw));code=row[f'{prefix}_COMMODITY'];country=row['CTY_CODE'];value=row[value_field]
        if not re.fullmatch(r'\d{2}',code) or not re.fullmatch(r'\d{4}',country) or row['time']!=period or row['COMM_LVL']!='HS2':raise SourceError('Source dimension mismatch')
        if any(name in row and row[name]!=expected for name,expected in dimensions.items()):raise SourceError('Unexpected source aggregation')
        if not re.fullmatch(r'(0|[1-9]\d{0,23})',value):raise SourceError('Unknown value or suppression marker; review contract')
        for name in (f'{prefix}_COMMODITY_SDESC','CTY_NAME'):
            if not 0<len(row[name])<=250 or any(ord(c)<32 for c in row[name]):raise SourceError('Invalid source description')
        key=(code,country)
        if key in seen:raise SourceError('Duplicate source dimensions')
        seen.add(key)
        rows.append({'product':code,'description':row[f'{prefix}_COMMODITY_SDESC'],'partnerCode':country,'partnerName':row['CTY_NAME'],'flow':flow,'period':period,'value':value,'status':'reported_zero' if value=='0' else 'reported'})
    return rows

def fetch_candidate(flow,period,key):
    validate_period(period)
    if flow not in PATHS:raise SourceError('Unsupported flow')
    if not isinstance(key,str) or not key or len(key)>256 or any(c.isspace() for c in key):raise SourceError('CENSUS_API_KEY is missing or invalid')
    prefix='I' if flow=='imports' else 'E';value='GEN_VAL_MO' if flow=='imports' else 'ALL_VAL_MO'
    # Default source dimensions are retained and checked if returned. Verify totals against
    # current live metadata before promoting; never silently strip a finer-level dimension.
    params={'get':f'{prefix}_COMMODITY,{prefix}_COMMODITY_SDESC,CTY_CODE,CTY_NAME,{value},COMM_LVL','time':period,'COMM_LVL':'HS2','CTY_CODE':'*','key':key}
    url='https://'+HOST+PATHS[flow]+'?'+urlencode(params)
    for attempt in range(3):
        try:
            raw=fetch_bytes(url)
            if len(raw)>MAX_BYTES or key.encode() in raw:raise SourceError('Response rejected by evidence safety check')
            try:data=json.loads(raw)
            except (ValueError,UnicodeError):raise SourceError('Invalid JSON response') from None
            rows=parse_rows(data,flow,period)
            if key in json.dumps(rows,ensure_ascii=False):raise SourceError('Response rejected by evidence safety check')
            return {'schemaVersion':1,'state':'candidate','source':'https://'+HOST+PATHS[flow],'sourceHash':hashlib.sha256(raw).hexdigest(),'flow':flow,'period':period,'officialReleaseDate':None,'officialRevisionDate':None,'ingestedAt':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'rows':rows,'publicationBlockers':['Live dimensions and coverage not yet reconciled','Official publication evidence not yet attached']}
        except (RetryableSourceError,OSError):
            if attempt==2:raise SourceError('Source acquisition failed after three attempts') from None
            time.sleep(2**attempt)
    raise SourceError('Acquisition did not complete')

def main():
    parser=argparse.ArgumentParser(description='Fetch one monthly candidate; does not publish')
    parser.add_argument('--flow',choices=PATHS,required=True);parser.add_argument('--period',required=True);parser.add_argument('--output',type=Path,default=Path('pipeline/output'))
    args=parser.parse_args()
    try:
        candidate=fetch_candidate(args.flow,args.period,os.environ.get('CENSUS_API_KEY',''))
        args.output.mkdir(parents=True,exist_ok=True)
        path=args.output/f"candidate-{args.flow}-{args.period}-{candidate['sourceHash'][:16]}.json"
        # Same source response creates one evidence file; a changed response gets a new name.
        if not path.exists():
            temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(candidate,separators=(',',':')),encoding='utf-8');os.replace(temporary,path)
        print(f"Candidate validated: {len(candidate['rows'])} rows. Publication remains blocked.")
    except SourceError as error:
        parser.exit(1,f'Acquisition failed: {error}\n')

if __name__=='__main__':main()
