# Especificação técnica JEIA_DXF_TECH 1.0

## 1. Objetivo e limites

Representar informação técnica DXF sem confundir geometria documental, interpretação da peça e aprovação pelo operador. Preservar observações independentes dos motores e permitir um modelo operacional rastreável. A existência de um campo ou a concordância entre motores não aprova fabricação.

O contrato não altera formatos/eventos STEP nem define G-code. `validation.cncReleased` é obrigatoriamente `false`. `operations` contém intenções de planejamento, sem instruções de execução.

## 2. Estrutura e presença

O objeto raiz tem 33 campos obrigatórios. `contract` é `JEIA_DXF_TECH`; `version` é a string `1.0`. `context`, `document` e `validation` são objetos. As coleções restantes são arrays, inclusive quando vazios. `sources` tem no mínimo um item. Vazio significa ausência de registros serializados, nunca comprovação de inspeção completa; cobertura incompleta exige diagnóstico.

| Grupo | Informação |
|---|---|
| `context`, `document`, `sources` | Requisição, revisão, arquivo, hash, unidades, origem, versões, opções e capacidades |
| `frames`, `transforms` | Sistemas de coordenadas e mapeamentos explícitos |
| `spaces`, `viewports`, `layers` | Model/Paper, apresentações, recortes e propriedades das camadas |
| `blockDefinitions`, `blockInstances` | Conteúdo reutilizável e cada instância/célula do desenho |
| `entities`, `occurrences`, `geometries` | Entidade de origem, ocorrência posicionada e observações geométricas dos motores |
| `dimensionStyles`, `dimensions`, `tolerances`, `annotations` | Estilos/overrides, medidas, textos, tolerâncias e suas associações |
| `parts`, `views` | Peças candidatas, projeções, escala independente e referência dimensional |
| `evidence`, `classifications` | Evidências, hipóteses de classificação e inclusão reversível |
| `observations`, `featureRelations`, `features` | Observações por vista e características físicas candidatas |
| `setups`, `operations` | Referências de montagem e intenções de processo, sem execução |
| `numericProfiles`, `reconciliations`, `decisions`, `diagnostics` | Perfis numéricos, conflitos, decisões vinculadas à revisão e impedimentos |
| `validation` | Estágio, validação estrutural/semântica e elegibilidade por consumidor/escopo |

O dicionário lista todas as propriedades de todas as definições. No 1.0, campos desconhecidos são rejeitados nos objetos tipados. Somente mapas declarados permitem chaves abertas: atributos brutos, cabeçalho, opções do motor, dados de evidência e grandezas nomeadas. Esses mapas não são atalhos para acionar cálculos sem semântica definida.

O campo `Entity.rawRecordDigest` é opcional. `Geometry.approximationError` é opcional nas representações exatas e obrigatório em `approximate` (pode ser nulo quando o erro não foi quantificado). Os demais campos das entidades são obrigatórios; valores não disponíveis são representados por `null` apenas onde o schema permite. Uma propriedade opcional ausente não se transforma em zero ou `false`.

## 3. Identidade e formato

Strings de ID seguem `Id`, são opacas e não dependem da posição geométrica. O hash SHA-256 é hexadecimal minúsculo com 64 caracteres. Datas usam RFC 3339 com offset explícito; consumidores devem validar `format: date-time` efetivamente, pois alguns validadores não ativam formatos por padrão.

Números JSON devem ser finitos. NaN/Infinity não pertencem ao formato. Grandezas extremamente grandes, mal condicionadas ou com precisão insuficiente exigem diagnóstico; não autorizar normalização numérica inexata sem medir seu erro. `rawGroups` preserva ordem, repetições e texto dos códigos DXF, inclusive campos que a versão atual não interpreta.

IDs de registros raiz são globalmente únicos no pacote. Registros aninhados com identidade, como viewports e observações de reconciliação, também participam do registro de identidade; `Target.kind` restringe a coleção referenciada. Listas de IDs não permitem repetição.

## 4. Estados de conhecimento

| Estado | Significado | Efeito permitido |
|---|---|---|
| `unknown` | Informação não determinada | Preservar ausência e registrar dependências |
| `extracted` | Lido da origem, sem comprovação de significado físico | Exibir dado com proveniência |
| `interpreted` | Hipótese técnica produzida por regra/associação | Exibir como candidato |
| `verified` | Propriedade conferida por regra verificável/evidência numérica | Usar apenas nos consumidores cujos outros requisitos estejam atendidos |
| `confirmed` | Decisão explícita vinculada ao escopo/revisão | Usar dentro do alcance da decisão e da elegibilidade |
| `conflicting` | Observações incompatíveis ainda não resolvidas | Impedir consumidores dependentes |
| `rejected` | Hipótese rejeitada, mantendo sua origem | Não consumir como verdadeira |
| `unsupported` | Informação existente, mas sem suporte confiável | Preservar o bruto e impedir inferências dependentes |
| `not_applicable` | Campo não se aplica, com motivo | Não apresentar como informação faltante |

O estado vem acompanhado de `evidenceIds`, `diagnosticIds` e `reason`. Regras ST detalham suas condições. `confirmed` não é um booleano geral de aprovação industrial.

Para uma `Quantity`, `unknown`, `unsupported`, `not_applicable` e `rejected` exigem `value=null`. Dado bruto que conflita com outro deve permanecer em registros de observação separados; uma grandeza canônica em conflito não pode ocultar uma escolha unilateral.

## 5. Validação do pacote e elegibilidade

`schemaStatus` e `semanticStatus` admitem `not_checked`, `valid` ou `invalid`. São resultados, não poderes: uma implementação consumidora deve validar o pacote recebido em vez de confiar nos status autodeclarados.

Estágios: `draft` (extração pode estar incompleta), `extracted` (cobertura de leitura declarada), `reconciled` (comparações executadas ou ausências explícitas) e `reviewed` (decisões exigidas no escopo registradas). Uma revisão pode continuar bloqueada por dados físicos desconhecidos.

Cada entrada de `eligibility` vincula escopo e consumidor (`visualization`, `material`, `process`, `cost`):

- `eligible`: requisitos daquele uso atendidos, sem bloqueio aberto no escopo/dependências.
- `provisional`: somente apresentação de estimativa explicitamente incompleta; não pode ser contabilizada como resultado técnico aprovado.
- `blocked`: há dado necessário ausente, ambiguidade ou conflito impeditivo.
- `not_assessed`: sem avaliação para o uso.

Não existir entrada não significa elegibilidade. Defaults são impeditivos para matéria-prima, processo e custo. A visualização pode permanecer disponível para revisão mesmo quando cálculo estiver bloqueado. Dados sintéticos são sempre bloqueados para consumo operacional.

## 6. Representações geométricas

`GeometryPayload` é uma união discriminada por `type`: POINT, LINE, CIRCLE, ARC, ELLIPSE (inclusive trecho elíptico), POLYLINE, BSPLINE, COMPOSITE_CURVE, BREP_SUMMARY ou UNSUPPORTED.

- Dados geométricos estão nas unidades do `frameId`, nunca em unidade implícita.
- ARC usa normal e eixo X do plano, ângulo inicial e varredura assinada em radianos; CIRCLE representa volta completa.
- ELLIPSE usa vetores dos semieixos. Start/sweep parametrizam esses eixos; volta completa tem módulo `2π`.
- POLYLINE preserva vértices, bulge por segmento de saída, larguras, fechamento e elevacão. A convenção XY/OCS e a aplicação de elevação estão nas regras GEO-03, sem dupla aplicação.
- BSPLINE preserva grau, pontos de controle, nós distintos, multiplicidades e pesos racionais quando existentes.
- COMPOSITE_CURVE referencia segmentos analíticos orientados, permitindo preservar uma polilinha transformada com trechos elípticos.
- BREP_SUMMARY é somente resumo; não substitui arestas analíticas nem identifica furos por conter cilindros.
- UNSUPPORTED conserva o tipo e o motivo; dados brutos ficam na entidade e em evidências.

Não há payload de malha canônica no 1.0. Meshes, HATCH complexo, ACIS, entidades proxy e outras representações fora da união são preservados como tipos DXF/atributos brutos com estado `unsupported`, até extensão versionada. Uma visualização futura pode derivar tesselação sem promovê-la a geometria analítica.

Cada motor pode produzir sua própria `Geometry`; `canonicalGeometryId` só seleciona uma geometria com transformação e reconciliação suficientes. Caso contrário, permanece `null`. `appliedTransformIds` registra a ordem de derivação geométrica entre frames. Geometria agregada FreeCAD sem vínculo confiável com uma entidade mantém IDs de entidade/ocorrência nulos e `sourceObjectKey` identificável. `approximate` é separado de `analytic`; aproximação sem erro quantificado não pode sustentar cálculo dimensional aprovado.

## 7. Cobertura e falhas

Capacidades declaradas por um motor não provam que ele leu toda a entidade ou todo o documento. Limites de quantidade, timeout, blocos ausentes, Xrefs não resolvidas, falhas de decoding e trechos truncados exigem diagnósticos com escopo e consumidores afetados.

Não descartar uma entidade por falha de conversão. Preservar `dxfType`, proprietário, origem e grupos brutos; marcar geometria sem suporte. Não transformar uma falha do motor em relatório vazio de sucesso. Não somar shapes de containers e filhos como se fossem ocorrências independentes.

## 8. Evolução, transporte e isolamento

Schema Draft 2020-12, sem carregamento de schemas remotos para validar este pacote: todas as `$ref` internas resolvem em `$defs`. O URI `$schema` identifica o dialeto padrão e não exige rede durante o uso de um validador já configurado.

Alterações de significado ou remoção de campos exigem nova versão. Acrescentar propriedades também exige versão explicitamente reconhecida, pois 1.0 rejeita campos tipados desconhecidos. Uma implementação antiga não ignora uma versão nova silenciosamente.

O envelope de identidade usa requisição, geração e hash, mas não redefine a correção anterior nem mexe em seus eventos. A futura adaptação de transporte será objeto de implementação separada. Não adicionar propriedades DXF às estruturas STEP por conveniência. O consumidor operacional futuro deve atuar exclusivamente sobre dados desta versão validados no escopo.
