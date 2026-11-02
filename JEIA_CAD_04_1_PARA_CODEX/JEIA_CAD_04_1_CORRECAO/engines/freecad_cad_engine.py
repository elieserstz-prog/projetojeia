# JEIA TECH Industrial — FreeCAD headless, somente leitura, JSON preliminar.
import sys, json, os, traceback
out=None
try:
 import FreeCAD as App
 import Part
 args=sys.argv[-3:]
 if len(args)!=3:raise ValueError('Parâmetros incompletos para FreeCADCmd')
 mode,path,out=args
 if mode not in ('step','dxf'):raise ValueError('Modo desconhecido')
 if not os.path.isfile(path):raise FileNotFoundError(path)
 d=App.newDocument('JEIA_AUDITORIA')
 if mode=='step':
  shape=Part.Shape();shape.read(path)
  if shape.isNull():raise ValueError('Forma STEP nula')
  shapes=[shape]
 else:
  try:
   import importDXF
   importDXF.insert(path,d.Name)
   d.recompute()
   shapes=[o.Shape for o in d.Objects if hasattr(o,'Shape') and not o.Shape.isNull()]
  except Exception as ee:raise RuntimeError('O importador DXF do FreeCADCmd não está disponível: '+str(ee))
 if not shapes:raise RuntimeError('Nenhuma forma geométrica encontrada')
 compound=Part.makeCompound(shapes)
 b=compound.BoundBox
 cylinders=[]
 for fi,face in enumerate(compound.Faces):
  surface=face.Surface
  if 'Cylinder' in type(surface).__name__:
   cylinders.append({'face':fi+1,'diametro_mm':round(float(surface.Radius)*2,5)})
  if len(cylinders)>=200:break
 result={'motor':'FreeCAD/Part', 'sucesso':True,'modo':mode,'arquivo':os.path.basename(path),'formato':'BREP CAD' if mode=='step' else 'importacao DXF experimental',
 'solidos':len(compound.Solids),'faces':len(compound.Faces),'arestas':len(compound.Edges),
 'valido':bool(compound.isValid()),'volume_mm3':round(float(compound.Volume),6) if mode=='step' else None,
 'bbox_mm':{'x':round(b.XLength,6),'y':round(b.YLength,6),'z':round(b.ZLength,6)},
 'cilindros_superficies':cylinders,
 'avisos':['A presença de superfície cilíndrica não comprova furo usinável.', 'Conferir posicionamento, unidades, cotas nominais, material e tolerâncias.', 'Não liberar código CNC ou orçamento sem validação.'], 'apto_para_cnc':False}
except Exception as exc:
 result={'sucesso':False,'erro':type(exc).__name__+': '+str(exc),'detalhe':traceback.format_exc()[-1200:]}
finally:
 try:
  if out:
   with open(out,'w',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
 except Exception:pass
 try:
  if 'd' in locals():App.closeDocument(d.Name)
 except Exception:pass
