"""Obtém occt-import-js 0.0.23 para uso local, com textos de licença.
Sem credenciais; URLs oficiais da distribuição npm publicada.
"""
from pathlib import Path
import urllib.request,ssl,hashlib,sys,os,time
BASE=Path(__file__).resolve().parent/'vendor'/'occt'
BASE.mkdir(parents=True,exist_ok=True)
FILES={'occt-import-js.js':50000,'occt-import-js.wasm':1000000,
       'license.occt-import-js.txt':1000,'license.occt.txt':1000,
       'occt-import-js-worker.js':100}
SOURCES=['https://cdn.jsdelivr.net/npm/occt-import-js@0.0.23/dist/',
         'https://unpkg.com/occt-import-js@0.0.23/dist/']
ctx=ssl.create_default_context()
for name,minimum in FILES.items():
    target=BASE/name
    if target.is_file() and target.stat().st_size>minimum:
        print('PRESENTE:',name,target.stat().st_size)
        continue
    errors=[]
    for source in SOURCES:
        try:
            u=source+name
            req=urllib.request.Request(u,headers={'User-Agent':'JEIA-Package-Builder/2.0'})
            with urllib.request.urlopen(req,timeout=65,context=ctx) as response:
                content=response.read(30*1024*1024)
            if len(content)<minimum:
                raise ValueError('Arquivo incompleto ('+str(len(content))+' bytes)')
            if name.endswith('.wasm') and content[:4]!=b'\0asm':
                raise ValueError('Arquivo WASM invalido')
            if name.endswith('.js') and b'function' not in content:
                raise ValueError('JavaScript invalido')
            target.write_bytes(content)
            print('OK',name,len(content),'SHA256',hashlib.sha256(content).hexdigest())
            break
        except Exception as exc:
            errors.append(source+' -> '+str(exc))
    else:
        print('FALHA: Não foi possível baixar '+name+'. Sem esse arquivo NÃO é seguro gerar o instalador.')
        for err in errors:print('   ',err)
        sys.exit(2)
print('OPENCASCADE LOCAL CONFERIDO; documentos de licença incluídos.')
