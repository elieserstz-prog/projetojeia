# Relatório técnico — FreeCAD Fase 2B

**Experimental — somente para testes. A integração DXF não está aprovada.**

## Escopo e preservação

Novo adaptador independente, na branch `desenvolvimento-dxf-fase-2b`, criada a partir do commit original `456495402676e7b4bee023377d5fea0ddfa8230f`. Código e materiais ficam em `dxf_fase_2b/`; ZIP e SHA-256 ficam na raiz da branch. Não há importação de módulos da CAD nem alterações em seus fontes, motores, abas ou fluxo STEP.

O schema é exatamente o da Fase 2A (`842311804e3ccc2efc253adf17cf7a16d2b6407d`), sem propriedades novas. Os quatro DXFs sintéticos foram copiados byte a byte dos exemplos daquela entrega; a Fase 2A não foi modificada. O ZIP desta fase não inclui código da CAD, dependências instaladas ou binários FreeCAD.

## Extração implementada

O controlador lê o DXF uma vez, calcula SHA-256 e entrega um snapshot dos mesmos bytes a um processo isolado. O worker usa explicitamente `Import.readDXF(..., ignore_errors=False)`; não alterna para importador legado, não chama downloader e não salva documentos CAD. O documento de importação é temporário; o código restaura o documento ativo anterior e fecha apenas o que criou.

O coletor também pode ser testado diretamente com documentos/shapes FreeCAD reais. Ele exporta:

- Shapes: validade, tipo, contagens, caixa envolvente e volume nativo quando há sólidos.
- Curvas: LINE, ARC, CIRCLE, ELLIPSE e BSPLINE, quando serializáveis sem aproximação.
- Arestas: índice nativo, orientação, parâmetros inicial/final, comprimento e endpoints.
- Faces: índice, tipo/sumário da superfície, área, domínio paramétrico, centro de massa, orientação, wires e índices de arestas.
- Coordenadas: placements original/exportado e composição global que evita aplicar duas vezes o placement do objeto. Se a transformação global não puder ser determinada, preserva BREP local e marca a geometria como sem suporte, sem fabricar coordenadas WCS.
- Origem disponível: Name, Label, TypeId e propriedades DXF específicas quando o FreeCAD as fornecer. Não deduz handle, layer ou bloco pelo nome/posição.
- BREP original e global completos como texto, permitindo preservar superfícies/curvas não representadas analiticamente pelo schema. Exportações acima do limite são omitidas com diagnóstico, sem truncamento falso.

Como o contrato 1.0 não tem payload de superfície/face, detalhes de face/topologia e BREP ficam em `evidence.value`, vinculados ao resumo geométrico do objeto. Não foi modificado o schema para fazer caber uma extensão. BSPLINE preserva sua curva de suporte; o intervalo da aresta recortada e sua orientação são registrados separadamente na evidência/BREP. Não tratar a curva inteira como aresta recortada ignorando esses campos.

Os IDs das observações derivam do hash do arquivo e da chave nativa `Objeto.EdgeN`/`Objeto.Shape`. Isso identifica observações desta importação; não comprova correspondência com entidade DXF ou estabilidade dos índices entre versões/configurações do FreeCAD. `entityId`/`occurrenceId` permanecem nulos quando esse vínculo não existe. Não há associação fabricada com entidades da Fase 2A nem reconciliação entre motores.

Shapes pais e filhos são preservados com indicação de agregação; não são somados como quantidade física. Referências de origem/datum do próprio FreeCAD são marcadas como referências de construção, sem promover seus envelopes a peça real. Curvas sem suporte, inconsistências entre curva e aresta localizada, ausência de transformação, objetos sem Shape e limites são diagnosticados.

## Resultado dos testes

| Grupo | Executado | Passou | Falhou | Significado |
|---|---:|---:|---:|---|
| Unidade/contrato/controlador | 33 | 33 | 0 | Inclui simulações explicitamente nomeadas; não comprova importação FreeCAD |
| Kernel FreeCAD/Part real | 12 | 12 | 0 | Serialização, topologia, BREP e coordenadas em fixtures de memória |
| DXF via FreeCADCmd | 1 | 0 | 1 | Processo falha com SIGSEGV |
| DXF via API Python compatível | 4 | 0 | 4 | `Import.readDXF` falha; nenhuma geometria desses DXFs foi declarada extraída |

Não houve testes marcados skipped/expected-failure para transformar falha nativa em aprovação. O probe retorna código 1 e `integrationApproved=false`. Os testes unitários retornam 0; esses resultados são mantidos separados.

### Testes unitários

Python 3.12.14, `jsonschema` 4.26.0 já disponível. Cobrem identidade/hash/geração, dados ausentes, consumidores bloqueados, metadata, schema congelado, respostas simuladas incorretas, crash/timeout, limites, inexistência de executável, proibição de sobrescrever entrada/saída e detecção simulada de conflito de coordenadas/transformação ausente. Runtime do adaptador não depende de jsonschema; `schemaStatus` e `semanticStatus` permanecem `not_checked` nos pacotes, sem autodeclaração de validação operacional.

### Testes reais de geometria

Python 3.13.5 compatível com as bibliotecas FreeCAD 1.0.0 já instaladas. Doze casos isolados: linha, arco, círculo, elipse, B-spline, disco/face, caixa sólida, cilindro, placement simples, placement aninhado, limites parciais e documento vazio. O caso vazio comprova diagnóstico de ausência, não uma extração geométrica bem-sucedida.

Os casos com shapes preservam BREP e fazem round-trip com `Part.Shape.importBrepFromString`. Caixa: 12 arestas, seis faces e volume 6000 mm³; disco: área 25π mm²; cilindro: superfície cilíndrica preservada como metadado/topologia. Placements simples/aninhados foram conferidos. A preservação do objeto de origem é testada por placement, vértices, amostras das curvas, medidas e lista de objetos do documento. Texto BREP não é tratado como serialização canônica: o kernel pode reordenar tabelas internas de localização sem alterar geometria.

Esses documentos são criados em memória para teste do coletor e usam contexto `synthetic_example`. **Não são importações bem-sucedidas dos DXFs fornecidos.**

### Limitação de importação no ambiente

`/usr/bin/freecadcmd --version` já falha com SIGSEGV durante inicialização. O worker FreeCADCmd também falhou. A alternativa explícita com `/usr/bin/python3` e `/usr/lib/freecad/lib` carrega FreeCAD/Part e passa nos testes de kernel, porém `Import.readDXF` retorna `RuntimeError: <built-in function __import__> returned a result with an exception set` nos quatro DXFs.

Uma verificação separada do módulo Draft confirmou `ModuleNotFoundError: No module named 'PySide'`. Isso documenta uma dependência indisponível no ambiente; não estabelece que instalar um pacote isolado resolveria todos os problemas. Não foram instaladas dependências, criados aliases de Qt nem alteradas bibliotecas. A rota nativa deve ser revalidada em instalação FreeCAD completa/compatível, sob autorização posterior.

Os cinco pacotes DXF de falha continuam estruturalmente válidos, vazios de geometria, com diagnósticos impeditivos. Validade do JSON de falha NÃO significa aprovação do importador.

## Compatibilidade e limites restantes

- Compatibilidade estrutural com JEIA_DXF_TECH 1.0 verificada nos resultados de teste; validador semântico completo não implementado.
- Origem DXF, Model/Paper, blocos, layers e escala física não são reconstruídos a partir de shapes sem evidência. Os arrays correspondentes podem ficar vazios, com diagnóstico. Portanto, o pacote não deve ser apresentado como modelo semântico completo daquele DXF.
- Coordenadas observadas são mm internos do kernel. Conversão correta de unidades do DXF pelo importador não está demonstrada; não multiplicar novamente pelo fator do cabeçalho.
- Não há identificação de peça/moldura/carimbo, associação de vistas, furos físicos, operações ou cálculo de matéria-prima/orçamento.
- BREP preserva superfícies não representadas pelo payload analítico, mas o consumidor futuro deve interpretar domínio, orientação e trimming. Metadados de superfícies não substituem o BREP exato.
- Limites padrão: entrada 64 MiB, resposta 64 MiB, BREP por objeto 16 MiB (somando original/global), 20 mil arestas e 10 mil faces por objeto, timeout 120 s. Limites/omissões são diagnosticados; BREP truncado não é declarado completo.
- Falhas nativas fatais não podem ser capturadas por `try/except` dentro do mesmo processo; por isso existe controlador isolado. Sua proteção foi testada com simulações e falha real do FreeCADCmd.
- Windows não foi acessado ou modificado. Não houve teste Windows, geração de instalador/executável nem integração ao programa principal.

## Evidências e publicação

`RESULTADOS_UNITARIOS.txt` contém o log unitário. `validation/PROBE_RESULTADOS.json` separa cada caso/rota, código de saída e status. Os JSONs `validation/native_*.json` contêm os resultados reais do kernel; `validation/dxf_*.json` contêm as cinco falhas de importação com diagnósticos.

O ZIP e seu SHA-256 serão publicados diretamente na branch autorizada, sem depender de Release. O commit publicado e a verificação do link são informados no retorno da tarefa. O pacote não inclui arquivos da instalação atual.

**Conclusão: coletor de geometria e controlador desenvolvidos e testados; importação DXF integrada não aprovada neste ambiente. Qualquer integração ao JEIA permanece condicionada à autorização do usuário.**
