from pathlib import Path
import urllib.request,zipfile,io,pandas as pd,hashlib,json
B=Path(__file__).resolve().parent/'fontes_publicas';meta=[]
for y in range(2021,2025):
 url=f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{y}.zip';data=urllib.request.urlopen(url,timeout=60).read()
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  name=f'dfp_cia_aberta_DRE_ind_{y}.csv';a=pd.read_csv(z.open(name),sep=';',encoding='latin1',dtype={'CD_CONTA':str});a=a[a.CD_CVM.isin([19879,26441])&a.CD_CONTA.eq('3.11')&a.ORDEM_EXERC.eq('ÚLTIMO')];a.to_csv(B/f'lucro_individual_{y}.csv',index=False)
 meta.append(dict(ano=y,url=url,sha256=hashlib.sha256(data).hexdigest()));print(y,len(a),flush=True)
(B/'catalogo_lucro.json').write_text(json.dumps(meta,indent=2))
