import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pipeline.census import parse_rows, fetch_candidate, SourceError, fetch_bytes, validate_period
from pipeline.store import ReleaseStore

HEADER = ['I_COMMODITY','I_COMMODITY_SDESC','CTY_CODE','CTY_NAME','GEN_VAL_MO','time','COMM_LVL','CTY_SUBCODE','DISTRICT','RP']
DATA = [HEADER, ['09','Coffee, tea','1220','Canada','123456','2026-07','HS2','0','00','00']]

class CensusTests(unittest.TestCase):
    def test_redirect_oversize_and_non_json_bodies_are_rejected_before_read(self):
        for status,headers in [(302,{'Location':'https://evil.test'}),(200,{'Content-Type':'application/json','Content-Length':str(11*1024*1024)}),(200,{'Content-Type':'text/html'})]:
            response=MagicMock();response.status=status;response.getheader.side_effect=lambda key,default=None:headers.get(key,default)
            connection=MagicMock();connection.getresponse.return_value=response
            with patch('pipeline.census.http.client.HTTPSConnection',return_value=connection),self.assertRaises(SourceError):fetch_bytes('https://api.census.gov/data/timeseries/intltrade/imports/hs?key=test')
            response.read1.assert_not_called()
    def test_streamed_body_limit_does_not_trust_missing_content_length(self):
        response=MagicMock();response.status=200;response.getheader.side_effect=lambda key,default=None:{'Content-Type':'application/json'}.get(key,default);response.read1.return_value=b'x'*65536
        connection=MagicMock();connection.getresponse.return_value=response
        with patch('pipeline.census.http.client.HTTPSConnection',return_value=connection),self.assertRaises(SourceError):fetch_bytes('https://api.census.gov/data/timeseries/intltrade/imports/hs')
        self.assertLessEqual(response.read1.call_count,162)
    def test_validates_rows_and_rejects_duplicates_unknown_markers_or_dimensions(self):
        self.assertEqual(parse_rows(DATA,'imports','2026-07')[0]['value'],'123456')
        for index,value in [(0,'0901'),(4,'NaN'),(4,'-1'),(5,'2026-06'),(7,'1'),(8,'12')]:
            bad=json.loads(json.dumps(DATA));bad[1][index]=value
            with self.subTest(index=index,value=value), self.assertRaises(SourceError):parse_rows(bad,'imports','2026-07')
        with self.assertRaises(SourceError):parse_rows(DATA+[DATA[1]],'imports','2026-07')
        with self.assertRaises(SourceError):parse_rows([HEADER],'imports','2026-07')
    def test_periods_cannot_inject_query_parameters(self):
        for period in ['2026-13','2026-07&key=evil','2026-7','1999-01']:
            with self.assertRaises(SourceError):validate_period(period)
    def test_fetch_is_fixed_to_census_and_redirects_never_followed(self):
        with self.assertRaises(SourceError):fetch_bytes('https://evil.test/?key=secret')
        with self.assertRaises(SourceError):fetch_bytes('http://api.census.gov/data/timeseries/intltrade/imports/hs')
    def test_fetch_error_is_sanitized_and_three_attempts_are_bounded(self):
        def fail(*args,**kwargs):raise OSError('https://source/?key=canary-private-secret')
        with patch('pipeline.census.fetch_bytes',side_effect=fail) as mocked,patch('pipeline.census.time.sleep'):
            with self.assertRaises(SourceError) as err:fetch_candidate('imports','2026-07','canary-private-secret')
        self.assertNotIn('canary',str(err.exception));self.assertEqual(mocked.call_count,3)
    def test_candidate_contains_no_request_secret_or_invented_release_date(self):
        with patch('pipeline.census.fetch_bytes',return_value=json.dumps(DATA).encode()):
            candidate=fetch_candidate('imports','2026-07','canary-private-secret')
        self.assertNotIn('canary',json.dumps(candidate));self.assertIsNone(candidate['officialReleaseDate'])
        self.assertEqual(candidate['state'],'candidate')
    def test_reflected_key_never_enters_evidence(self):
        bad=json.loads(json.dumps(DATA));bad[1][1]='canary-private-secret'
        with patch('pipeline.census.fetch_bytes',return_value=json.dumps(bad).encode()),self.assertRaises(SourceError):fetch_candidate('imports','2026-07','canary-private-secret')

class StoreTests(unittest.TestCase):
    def setUp(self):
        scratch=Path('.local/tests').resolve();scratch.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.tmp.cleanup);self.store=ReleaseStore(Path(self.tmp.name))
    @staticmethod
    def validate(data):
        if data.get('reconciled') is not True:raise ValueError('Failed reconciliation')
    def test_identical_processing_is_idempotent_and_failed_validation_preserves_active(self):
        payload={'reconciled':True,'value':'123'}
        first=self.store.publish(payload,self.validate)
        self.assertEqual(self.store.publish(payload,self.validate),first)
        self.assertEqual(len(list((Path(self.tmp.name)/'objects').glob('*.json'))),1)
        with self.assertRaises(ValueError):self.store.publish({'reconciled':False},self.validate)
        self.assertEqual(self.store.active(),payload)
    def test_interrupted_pointer_switch_preserves_last_good_and_rollback_checks_hash(self):
        first=self.store.publish({'reconciled':True,'value':'123'},self.validate)
        with patch('pipeline.store.os.replace',side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):self.store.publish({'reconciled':True,'value':'456'},self.validate)
        self.assertEqual(self.store.active()['value'],'123')
        second=self.store.publish({'reconciled':True,'value':'456'},self.validate)
        self.store.rollback(first,self.validate);self.assertEqual(self.store.active()['value'],'123')
        (Path(self.tmp.name)/'objects'/f'{second}.json').write_text('{}')
        with self.assertRaises(ValueError):self.store.rollback(second,self.validate)
        self.assertEqual(self.store.active()['value'],'123')

if __name__=='__main__':unittest.main()
