# Safe geometry-only use of researched open-source headless DXF reader.
# Deliberately does NOT invoke PostProcessor or write any CNC instructions.
import importlib.util,json,sys,os
src=sys.argv[1]
spec=importlib.util.spec_from_file_location('jeia_dxf_experimental',os.path.join(os.path.dirname(__file__),'dxf2gcode_headless.py'))
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
p=m.DXFParser(filepath=src)
shapes=m.chain_entities(p.raw_entities)
result={'motor':'DXF parser experimental (pesquisa 31/10)','arquivo':os.path.basename(src),'entidades_geometricas':len(p.raw_entities),'contornos':len(shapes),'detalhes':[{'elementos':len(s.elements),'fechado':bool(s.is_closed),'area_estimada_mm2':round(s.area,3),'classificacao_experimental':'interno' if s.is_internal else 'externo'} for s in shapes[:200]],'alerta':'Classificação de furos/áreas não validada; não usar para fabricar nem liberar G-code. Apenas DXF ASCII suportado.'}
print(json.dumps(result,ensure_ascii=False))
