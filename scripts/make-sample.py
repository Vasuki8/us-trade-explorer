"""Deterministic synthetic UI fixture. Never describes actual trade."""
import json
from pathlib import Path

products = [('09', 'Coffee, tea & spices'), ('84', 'Machinery & mechanical appliances'), ('85', 'Electrical machinery & equipment'), ('87', 'Vehicles & transport equipment')]
partners = [('world','World','0000','aggregate'), ('canada','Canada','1220','country'), ('mexico','Mexico','2010','country'), ('china','China','5700','country'), ('india','India','5330','country'), ('germany','Germany','4280','country')]
periods = [f'{2024+(6+i)//12}-{(6+i)%12+1:02}' for i in range(25)]
r = dict(schemaVersion=1,id='sample-2026-07-v1',mode='sample',source='synthetic',scope='Illustrative sample: 4 HS2 chapters and 5 countries. These are invented figures, not official US trade statistics.',officialReleaseDate=None,officialRevisionDate=None,ingestedAt='2026-10-01T00:00:00Z',revisionDetectedAt=None,basis='census-monthly-goods-nsa-usd-v1',products=[dict(code=c,name=n,edition='HS2022') for c,n in products],partners=[dict(id=i,name=n,code=c,kind=k) for i,n,c,k in partners],periods=periods,observations=[])
for pi,(product,_) in enumerate(products):
    for flow in ['imports','exports']:
        for mi,period in enumerate(periods):
            values = []
            for ci,(partner,*_) in enumerate(partners[1:]):
                base = [240,5600,4200,3900][pi] * [12,10,16,4,7][ci] * 100000
                value = base * (100 + mi * (ci+1) + [0,3,-2,5,-1,1][mi%6]) // 100
                if flow == 'exports': value = value * (30+ci*9) // 100
                values.append(value)
                # One deliberately unavailable value exercises meaningful missing-data UI.
                missing = product=='09' and partner=='india' and period=='2025-07' and flow=='exports'
                r['observations'].append(dict(product=product,partner=partner,flow=flow,period=period,value=None if missing else str(value),status='not_available' if missing else 'reported'))
            r['observations'].append(dict(product=product,partner='world',flow=flow,period=period,value=str(sum(values)*2),status='reported'))
Path('tests/fixtures').mkdir(parents=True,exist_ok=True)
Path('tests/fixtures/sample-release.json').write_text(json.dumps(r,separators=(',',':'))+'\n',encoding='utf-8')
