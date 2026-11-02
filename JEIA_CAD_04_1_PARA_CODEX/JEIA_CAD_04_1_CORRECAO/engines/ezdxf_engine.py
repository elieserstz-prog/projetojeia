"""JEIA: auditoria DXF sem edição do arquivo e sem liberar geometrias para CNC."""
import collections, hashlib, json, sys
from pathlib import Path
import ezdxf
from ezdxf import bbox

TYPES={0:'linear',1:'alinhada',2:'angular',3:'diametro',4:'raio',5:'angular_3p',6:'ordenada',8:'comprimento_arco'}

def scan(path):
    path=Path(path)
    doc=ezdxf.readfile(str(path))
    msp=doc.modelspace()
    es=list(msp)
    counts=collections.Counter(e.dxftype() for e in es)
    layers=collections.Counter(e.dxf.get('layer','0') for e in es)
    dimens=[]; warnings=[]
    for e in es:
        if e.dxftype()!='DIMENSION':continue
        if len(dimens)>=500:
            warnings.append('Limite de 500 cotas no relatório; arquivo não foi alterado.');break
        typ=e.dimtype
        value=None;error=None
        try:
            raw=e.get_measurement()
            value=float(raw) if isinstance(raw,(int,float)) else [round(float(v),6) for v in raw]
        except Exception as ex:error=str(ex)[:180]
        nom=e.dxf.get('text','')
        dimens.append({'tipo':TYPES.get(typ,str(typ)),'valor_geometrico_sem_escala':value,
                       'texto_cota':nom or '<automatico>', 'camada':e.dxf.get('layer','0'),
                       'dimstyle':e.dxf.get('dimstyle','Standard'),'erro':error,
                       'nota':'Diferenciar valor geométrico, texto nominal e tolerâncias; validar escala e unidades.'})
    envelope=None
    valid_geo=[e for e in es if e.dxftype() not in ('DIMENSION','TEXT','MTEXT','LEADER','MULTILEADER','VIEWPORT')]
    try:
        ext=bbox.extents(valid_geo,fast=True)
        if ext.has_data:
            envelope={'min':[round(v,5) for v in ext.extmin], 'max':[round(v,5) for v in ext.extmax],
                'dimensoes':[round(v,5) for v in ext.size]}
    except Exception as ex:warnings.append('Envelope não calculado: '+str(ex)[:150])
    if not dimens:warnings.append('Não foram encontradas cotas DIMENSION no Model. Verificar blocos, layouts ou textos desenhados.')
    warnings += ['Dimensões extraídas NÃO são cotas CAD liberadas para produção.',
                 'O envelope pode incluir moldura ou detalhes de outras vistas; não é a medida da matéria-prima.',
                 'Cotas com escalas, tolerâncias ou textos substitutos precisam de conferência visual.']
    return {'motor':'ezdxf','sucesso':True,'arquivo':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'versao_dxf':doc.dxfversion,'insunits':doc.header.get('$INSUNITS',0),
            'entidades_model':len(es),'tipos_model':dict(counts),'layers_model':dict(layers),
            'layouts':[l.name for l in doc.layouts], 'blocos_definidos':len(doc.blocks),
            'cotas_encontradas':len(dimens),'cotas':dimens,'envelope_geometria_model_nao_validado':envelope,
            'avisos':warnings,'apto_para_cnc':False,'apto_para_orcamento_automatico':False}

if __name__=='__main__':
    try:print(json.dumps(scan(sys.argv[1]),ensure_ascii=False))
    except Exception as ex:
        print(json.dumps({'erro':type(ex).__name__+': '+str(ex),'sucesso':False},ensure_ascii=False))
        sys.exit(1)
