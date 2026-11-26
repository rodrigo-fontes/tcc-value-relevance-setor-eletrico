from pathlib import Path
import urllib.request,zipfile,io,pandas as pd,hashlib,json
B=Path(__file__).resolve().parent;S=B/'fontes_publicas';u=pd.read_csv(B/'analise/dados/universo_identificado.csv');meta=[]
for y in range(2019,2025):
 out=S/f'complementos_{y}.csv'
 url=f'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{y}.zip'
 if out.exists():continue
 data=urllib.request.urlopen(url,timeout=60).read();parts=[]
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  for kind in ['BPA','DRE','DFC_MI','BPP']:
   for scope in ['con','ind']:
    name=f'dfp_cia_aberta_{kind}_{scope}_{y}.csv'
    if name not in z.namelist():continue
    a=pd.read_csv(z.open(name),sep=';',encoding='latin1',dtype={'CD_CONTA':str});a=a[a.CD_CVM.isin(u.CD_CVM)&a.ORDEM_EXERC.eq('ÚLTIMO')];a['demonstracao']=kind;a['escopo']=scope;parts.append(a)
 pd.concat(parts).to_csv(out,index=False)
 meta.append(dict(ano=y,url=url,sha256=hashlib.sha256(data).hexdigest()));print(y,flush=True)
(S/'catalogo_complementos.json').write_text(json.dumps(meta,indent=2))
