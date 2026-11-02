# Regras normativas e invariantes JEIA_DXF_TECH 1.0

As palavras **DEVE**, **NÃO DEVE** e **PODE** são normativas. Regras abaixo não expressáveis integralmente em JSON Schema exigem verificação semântica futura. Um status autodeclarado `valid` não substitui essas verificações.

## ST — Estados, completude e decisões

- **ST-01:** cada registro com `validation` preserva evidências e diagnósticos. `verified` exige ao menos uma evidência verificável da propriedade e domínio em questão (um cabeçalho de unidade, sozinho, não verifica o raio de um círculo); `confirmed` exige uma decisão válida que o inclua no escopo. `conflicting` exige diagnóstico aberto e proíbe consumo dependente.
- **ST-02:** um `Quantity.value` desconhecido, rejeitado, não aplicável ou sem suporte é `null`, nunca zero. Para `conflicting`, a grandeza canônica é nula; valores divergentes permanecem nas observações de fonte. `extracted`/`interpreted` podem conter números sem liberar consumidores.
- **ST-03:** uma decisão vincula SHA-256, `analysisRevision`, IDs afetados e caminhos das propriedades das quais depende. Mudança desses dados invalida suas dependências. `supersedesDecisionId` conserva histórico; proíbe ciclos. Um ator sintético não confirma dados de produção.
- **ST-04:** cobertura incompleta (limite, timeout, Xref, entidade não suportada, truncamento ou falha de extração) exige diagnóstico e elegibilidade conservadora. Não há limite silencioso de 500 cotas ou 200 instâncias. Um limite técnico futuro pode interromper processamento, mas deve declarar o que ficou pendente.
- **ST-05:** o estágio não evolui por simples contagem de motores. `reviewed` pode continuar bloqueado. Uma limitação aceita não torna conhecida uma profundidade ou unidade fisicamente ausente.

## ID — Identidade, propriedade e referências

- **ID-01:** IDs são opacos e globalmente únicos. Uma implementação futura pode usar UUID determinístico ou digest com prefixo, mas a entrada deve representar `document.sha256 + tipo de registro + chave de origem`; a codificação é canônica e não ambígua. Não se utiliza hash da geometria para identidade.
- **ID-02:** a entidade de origem é identificada por hash do arquivo, proprietário e handle. Se handle estiver ausente, usar proprietário e ordinal de leitura preservado, com `identityMethod=owner_and_ordinal` e diagnóstico da limitação. Não inventar handle.
- **ID-03:** a ocorrência se identifica por entidade de origem + espaço raiz + caminho ordenado de instâncias + índices row/column de cada MINSERT. Definição não é ocorrência. Dois INSERTs do mesmo bloco têm ocorrências distintas; posições coincidentes não comprovam equivalência física.
- **ID-04:** toda referência aponta para registro existente do tipo correto. O documento tem exatamente um Model em estágio `extracted` ou posterior. Layers, frames, styles, viewports, entidades e ocorrências devem formar uma estrutura consistente. Uma entidade tem um proprietário (espaço, definição de bloco ou outra entidade, como ATTRIB pertencente a INSERT); a cadeia de proprietários não admite ciclos. Sua ocorrência deve ser alcançável a partir desse proprietário e do caminho de instâncias. ATTRIB já posicionado pela instância não recebe novamente o transform da definição; ATTDEF de definição e ATTRIB efetivo não são a mesma anotação.
- **ID-05:** `entity.geometryIds` referencia observações daquela entidade; `occurrence.canonicalGeometryId`, se preenchido, referencia geometria daquela ocorrência. `view.partId`, `part.viewIds`, `part.featureIds` e `feature.partId` são recíprocos. Anotações/cotas dentro de blocos têm registro por ocorrência, não apenas por definição.
- **ID-06:** geometrias nativas FreeCAD não associadas conservam `sourceObjectKey`, com `entityId` e `occurrenceId` nulos. Não associar por ordem de importação. Containers e shapes filhos não podem ser contados como ocorrências físicas duplicadas.
- **ID-07:** todas as fontes de um pacote têm `inputSha256` igual ao documento. Resultados de outra requisição, geração ou revisão não são mesclados. Esta regra é um requisito do futuro consumidor DXF e não altera a implementação anterior de proteção CAD.

## UN — Unidades e representação numérica

- **UN-01:** o frame define a unidade das coordenadas; `document.units` resolve unidades de desenho em mm. Não trocar unidade de um frame sem converter seus números. Grandezas canônicas de comprimento usam mm; ângulos canônicos usam rad. Raw tags, textos e medidas originais são preservados.
- **UN-02:** `$INSUNITS=0` não significa mm. Valores desconhecidos ou contraditórios exigem resolução explícita. `$MEASUREMENT`, `$LUNITS`, nomes de arquivo, tamanho da folha e nomes de layers não definem sozinhos unidade física.
- **UN-03:** conversões industriais de referência (mm por unidade):

| INSUNITS | Unidade | mm/unidade |
|---|---|---|
| 1 | polegada | 25.4 |
| 2 | pé internacional | 304.8 |
| 3 | milha internacional | 1609344 |
| 4 | milímetro | 1 |
| 5 | centímetro | 10 |
| 6 | metro | 1000 |
| 7 | quilômetro | 1000000 |
| 8 | micropolegada (microinch) | 0.0000254 |
| 9 | milésimo de polegada (mil) | 0.0254 |
| 10 | jarda internacional | 914.4 |
| 11 | ångström | 0.0000001 |
| 12 | nanômetro | 0.000001 |
| 13 | micrômetro | 0.001 |
| 14 | decímetro | 100 |
| 15 | decâmetro | 10000 |
| 16 | hectômetro | 100000 |
| 17 | gigâmetro | 1000000000000 |
| 21 | pé US Survey | 1200000 / 3937 |
| 22 | polegada US Survey | 100000 / 3937 |
| 23 | jarda US Survey | 3600000 / 3937 |
| 24 | milha US Survey | 6336000000 / 3937 |

Os códigos 18–20 preservam significado astronômico (AU, ano-luz e parsec), mas conversão operacional está fora do perfil industrial inicial: registrar `unsupported`, sem fator 1 de fallback. Códigos não reconhecidos também permanecem sem resolução. Reconhecer um código não comprova precisão suficiente para as coordenadas específicas.

- **UN-04:** unidades declaradas em blocos são preservadas como metadados. Uma conversão automática de unidades do CAD de origem pode já ter sido incorporada aos fatores 41–43 do INSERT. O mapeamento usa os fatores efetivamente gravados; NÃO aplica uma segunda conversão só por existir `declaredInsunits`. Uma conversão adicional exige evidência do sistema de origem e um transform separado rastreável.
- **UN-05:** nenhuma etapa de cálculo arredonda para exibição. Documentar perfil numérico e erros de comparação; coordenadas de grande magnitude e perda de precisão abrem diagnóstico. Tolerância numérica de software NÃO é tolerância de fabricação.

## TR — Matrizes e OCS/WCS

- **TR-01:** matrizes são afins 4×4, armazenadas por linhas e aplicadas a vetores-coluna: `p_dest=M*p_origem`; a última linha é `[0,0,0,1]`. Para A→B→C, `M_A_C=M_B_C*M_A_B`. Não copiar a disposição interna de uma biblioteca que use vetores-linha sem conversão explícita.
- **TR-02:** normal de extrusão `N` é normalizada, com componentes finitos e norma não nula. OCS usa o Arbitrary Axis Algorithm: se `abs(Nx)<1/64` e `abs(Ny)<1/64`, `Ax=normalize(Wy × N)`; senão `Ax=normalize(Wz × N)`; `Ay=N × Ax`. A matriz OCS→WCS usa colunas `Ax, Ay, N`. Centro/elevacão continuam dados da entidade; não são adicionados como uma segunda origem arbitrária ao OCS.
- **TR-03:** saber o tipo DXF precede escolher o frame: endpoints LINE são WCS; centro de ARC/CIRCLE e vértices de LWPOLYLINE são OCS segundo suas definições DXF; POLYLINE 2D e 3D não são intercambiáveis. Preservar os códigos 30/38 e 210/220/230. Não projetar Z para zero.
- **TR-04:** `matrix=null` representa mapeamento não determinado e impede consumidores que dele dependem. Transform singular, normal inválida, escala zero ou cadeia inconsistente abre diagnóstico. Cada `componentTransformIds` é ordenado do primeiro aplicado ao último; sua composição deve reproduzir a matriz final. Cadeias não admitem ciclos.
- **TR-05:** `Occurrence.transformToSpaceId` mapeia coordenadas da geometria de origem para o frame de referência do próprio espaço. No Model, esse é WCS do Model. No Paper, são coordenadas do layout. Nunca equivale por si só a Paper→Model. Conversão para frame em mm é um transform rastreável separado ou componente explícito, aplicado uma única vez.

## BL — Blocos, instâncias e arrays

- **BL-01:** para um bloco com base `b`, ponto de inserção `i` em OCS do INSERT, extrusão que define `A`, rotação local `Rz(theta)` e escala diagonal `S`, o mapeamento local ao frame do pai é `A * T(i) * Rz(theta) * S * T(-b)`. A transformação OCS própria da entidade do bloco precede essa cadeia quando aplicável. Instâncias aninhadas são compostas até o espaço raiz; escalas e rotações NÃO comutam.
- **BL-02:** em MINSERT, para célula `(r,c)`, `delta=(c*columnSpacing, r*rowSpacing, 0)` e `i_cell=i + Rz(theta)*delta`, no OCS do INSERT. `BlockInstance.insertPoint` conserva o ponto i do INSERT/array original, antes do deslocamento da célula, mesmo quando row/column são diferentes de zero. A grade é rotacionada, mas NÃO escalada por `S`. Depois usa-se BL-01 com `i_cell`. Preservar todos os índices brutos; se espaçamento zero produzir células coincidentes, diagnosticar ambiguidade de duplicação em vez de inferir quantidade física ou ocultar registros.
- **BL-03:** normalização de camada aplica a herança DXF de layer 0 por caminho de INSERT; tipos BYBLOCK/BYLAYER são resolvidos separadamente. Preservar tanto a layer da definição quanto a `effectiveLayerId` da ocorrência, além da visibilidade efetiva. Não confundir invisibilidade/frozen com prova de elemento descartável.
- **BL-04:** definições recursivas, Xrefs não resolvidas ou suporte parcial não são explodidos com limite silencioso. Preservar INSERT e caminho conhecido; emitir diagnóstico de cobertura. Resolução/obtenção automática de arquivo externo não faz parte desta especificação.

## GEO — Geometria analítica

- **GEO-01:** círculo permanece círculo sob similaridade. Sob escala não uniforme em seu plano, a imagem é elipse; não manter raio circular fictício. Arcos passam a trechos elípticos quando necessário. Transform inválido não autoriza descarte da entidade.
- **GEO-02:** `normal` e `xAxis` de ARC são expressos no frame da geometria; são unitários/perpendiculares. `yAxis=normal × xAxis`; `p(t)=center+radius*(cos(t)*xAxis+sin(t)*yAxis)`. `0<abs(sweepRad)<=2π`; volta completa deve preferir CIRCLE. Sob espelhamento, conferir extremos e ponto intermediário para preservar orientação e trecho, sem corrigir apenas o raio pelo valor absoluto.
- **GEO-03:** POLYLINE 2D em OCS tem `vertices.point=[x,y,0]` e `elevation` aplicada exatamente uma vez na normal local antes de OCS→espaço. `bulge_i=tan(theta_i/4)` pertence ao segmento que SAI do vértice i. O último bulge só participa se `closed=true`. Em POLYLINE3D, os pontos preservam z e bulge deve ser zero; elevação separada é zero. Larguras são não negativas, não podem ser descartadas sem diagnóstico quando relevantes.
- **GEO-04:** uma polilinha transformada cujos trechos deixem de ser representáveis por bulges circulares usa `COMPOSITE_CURVE`: segmentos analíticos LINE/ARC/ELLIPSE ou BSPLINE referenciados por geometria, com orientação explícita. Preservar a POLYLINE bruta e sua derivação. Segmentos da composição têm o mesmo frame, endpoints coerentes e nenhum ciclo. `closed=true` exige fechamento dentro do perfil numérico, não união entre peças distintas.
- **GEO-05:** BSPLINE usa nós distintos estritamente crescentes e multiplicidades paralelas (mesmo tamanho), no padrão OpenCascade. Para N controles e grau p, exige N>=p+1; pesos racionais positivos em número N, ou weights=null para não racional. Não periódica: soma das multiplicidades=N+p+1; multiplicidades internas <=p e das extremidades <=p+1. Periódica: multiplicidades <=p, primeira=última e soma das multiplicidades menos a primeira=N. Nenhuma redução de grau/tesselação silenciosa. `closed` não implica periodicidade e exige conferência geométrica do fechamento. ELLIPSE tem semieixos finitos, não nulos e perpendiculares, com norma do majorAxis >= minorAxis; seu intervalo paramétrico é explícito e tem 0<abs(sweepRad)<=2π.
- **GEO-06:** BREP_SUMMARY serve para comparação de caixa, volume e contagens, não substitui entidades analíticas. Volume só é comparado se unidade, fechamento, domínio geométrico e convenção de união estiverem explicitados. Volume zero de contorno DXF 2D não comprova falha; presença de cilindro não comprova furo usinável. Geometria `approximate` preserva seu erro/limitação em `approximationError`; erro desconhecido bloqueia uso dimensional aprovado.

## VP / VI — Layouts, viewports e escala das vistas

- **VP-01:** viewports pertencem a um Paper Space e referenciam o Model. Não criam novas ocorrências físicas Model. A geometria própria do Paper continua identificada como Paper. Limites de viewport, recorte e anotações não se transformam automaticamente em contorno da peça.
- **VP-02:** em ortográfica, `modelToPaperTransformId` inclui a orientação da câmera, view target, twist, centro no papel e fator `paperHeight/modelViewHeight`, com unidades explicitadas. `viewCenter` é coordenada DCS; `viewTarget` e `viewDirection` são WCS; `paperCenter` é do frame Paper. Não usar coordenadas DCS como WCS. Uma matriz afim 4×4 pode reter profundidade da vista no terceiro componente para compor frames; esse componente não significa geometria física no papel nem recuperação de profundidade a partir do desenho 2D. Recorte controla visibilidade e não apaga a geometria de origem.
- **VP-03:** perspectiva preserva câmera, `projectionMatrix` e bruto quando disponíveis. `modelToPaperTransformId` afim deve ficar nulo se não representar o caso. Uma projeção perspectiva não permite recuperar dimensões físicas com uma escala escalar; consumidor dimensional é bloqueado sem outra evidência.
- **VI-01:** `drawingPerPart=s` significa comprimento REPRESENTADO / comprimento FÍSICO, ambos após conversão a mm. Vista 1:2 tem `s=0.5`; para levar desenho à peça aplica-se `1/s=2`, além da orientação/origem apropriadas. Modelo 1:1 só fica verificado por regra/documentação consistente, não por mera presença no Model.
- **VI-02:** `spaceToViewTransformId` define origem/orientação/unidades da representação da vista; NÃO inclui a correção física `1/s`. `viewToPartTransformId` inclui essa correção uma única vez. A cadeia completa deve reproduzir medidas físicas confirmadas. Escala de viewport é independente e não deve ser multiplicada novamente quando a origem da observação for a geometria Model.
- **VI-03:** cotas nominais não são redimensionadas só porque uma vista foi impressa 1:2. Interpretar fator geométrico, DIMLFAC/DIMSCALE, unidades alternativas e override conforme tipo/estilo. Divergência entre texto de escala, cotas e medidas é conflito, não média.
- **VI-04:** cada vista tem associação explícita à peça, escala própria e estado. Múltiplas peças no arquivo são permitidas. Vista sem associação segura não alimenta a peça de maior envelope por proximidade.

## QT / DI — Grandezas, cotas, tolerâncias e anotações

- **QT-01:** vocabulário inicial de QuantityMap: `diameter`, `radius`, `length`, `width`, `depth`, `x`, `y`, `z`, `pitch`, `pcdDiameter` usam mm em valores canônicos; `angle` usa rad; `area` mm2; `volume` mm3; `count` dimensionless com inteiro não negativo. Chave adicional preserva informação, mas não habilita consumidor sem semântica versionada/documentada. Feature não usa ausência de depth como passante.
- **DI-01:** `rawMeasurement`, `computedMeasurement` e `displayMeasurement` são grandezas diferentes. Texto bruto, texto apresentado, style e overrides são preservados. Não substituir o valor geométrico por texto nominal sem decisão de interpretação. Ausência do grupo 42 não impede que um motor calcule valor pelos pontos de definição; a origem dessa medição deve aparecer na evidência.
- **DI-02:** para medidas angulares, unidade da representação bruta deve ser explicitada pelo decodificador conforme tipo/campo/API DXF; não supor graus ou radianos por conveniência. Canonizar em rad sem perder a observação original. Em cotas ordenadas com saída vetorial de biblioteca, preservar vetor em evidência bruta e resolver o componente/eixo antes de preencher um Quantity escalar; não descartar os outros componentes sem registro.
- **DI-03:** tolerâncias assinadas representam desvios em relação ao nominal, com `lower<=upper`. Limites absolutos representam dimensões-limite e também são ordenados. Zonas geométricas preservam símbolo, datums e referência normativa; texto não interpretado mantém `interpretation=unparsed`, sem números fabricados. Tolerância geral só se associa ao domínio que o texto/norma realmente abrange.
- **DI-04:** anotações têm anchor e frame preservados quando disponíveis. Associação à geometria/vista usa referências DXF e evidências, não só proximidade. Texto gravado/usinável na peça e texto de carimbo podem usar a mesma entidade TEXT: ambiguidade exige revisão.

## CL — Separação de peça, moldura, carimbo e anotações

- **CL-01:** classificar ocorrências (e, quando necessário, conjuntos), preservando entidades e alternativas. Nome de layer e posição são indícios, não prova. A inclusão pode ser `included`, `excluded` ou `pending`; exclusão é reversível e nunca apaga o bruto.
- **CL-02:** exclusão automática exige ao menos duas famílias substantivas independentes dentre topologia, estrutura DXF, semântica textual, dimensional, consistência de projeção e template verificado; `layer_hint` e `position_hint` não atendem esse mínimo. Evidências correlatas com mesmo `independenceKey` contam uma vez. Contradição com vínculo dimensional/funcional da peça impõe `pending`, mesmo com alto score.
- **CL-03:** moldura candidata: estrutura de folha e fechamento envolvente + evidência adicional como marcas de dobra/formato ou template verificado. Carimbo: estrutura tabular/bloco com atributos + campos semânticos de revisão/desenho/responsabilidade. Peça: coerência topológica + associação dimensional/projeção funcional. Anotação: tipo/estilo/vínculo; tipo TEXT sozinho não comprova que não é geometria de gravação.
- **CL-04:** regiões desconectadas podem ser outras vistas, detalhes ou outras peças. Um contorno dentro da moldura não se torna bolso físico por aninhamento. Hachura, linhas ocultas e centro não geram usinagem sem interpretação. Uma layer congelada/invisível não exclui automaticamente matéria física.
- **CL-05:** `score` é ordenação de hipótese, não probabilidade calibrada ou autorização. Operador pode confirmar/excluir com motivo e escopo; conflitos físicos independentes permanecem abertos até resolução própria.

## RC — Reconciliação ezdxf / FreeCAD

- **RC-01:** preservar cada observação por fonte, versão, opções e hash. ezdxf é referência para estrutura documental; FreeCAD é evidência geométrica complementar. Nenhum motor tem autoridade absoluta sobre dimensão nominal, material ou função física.
- **RC-02:** primeiro associar por identidade preservada. Na ausência, produzir candidatos por tipo, domínio, transform, topologia e medidas; não parear pela ordem ou só pela caixa. Empates são `ambiguous`. Geometria de domínios diferentes é `not_comparable` (ex.: um objeto vs compound do desenho inteiro).
- **RC-03:** comparar no mesmo frame, unidades e escala física, após excluir duplicação de containers. Para comprimentos, `abs(a-b)<=max(lengthAbsMm,lengthRel*max(abs(a),abs(b)))`; para volume, usar parâmetros correspondentes; para ângulos, distância circular mínima modulo 2π respeitando orientação quando relevante. Contagens/IDs são exatos. Curvas exigem, além de caixa, parâmetros/intervalos e pontos de controle de referência do teste.
- **RC-04:** perfis numéricos são explícitos e rotulados `software_comparison_only`. O exemplo sugere abs=1e-6 mm, rel=1e-9, ângulo=1e-9 rad como perfil de fixtures analíticas, não promessa universal nem tolerância de fabricação. Importações aproximadas exigem perfil justificado; não ampliar limites só para fazer um caso passar.
- **RC-05:** `agree` só após comparação executada; duas ausências não concordam. `missing`, `differ`, `ambiguous` e `not_comparable` conservam todas as observações e diagnósticos. `differ` não seleciona observação canônica sem decisão de resolução; não usar maioria de motores nem média de medidas.
- **RC-06:** a decisão explicita o valor usado, a propriedade, evidências e motivo. Uma escolha do operador não torna falsa a observação rejeitada: ela continua registrada. Conflitos relacionados continuam bloqueando seus consumidores até resolução.

## FE / OP — Característica física e prevenção de duplicação

- **FE-01:** entidade -> ocorrência -> observação em vista -> característica física são níveis distintos. Não fundir observações por diâmetro, centro na folha, quantidade ou nome de layer iguais.
- **FE-02:** `same_feature` exige peça comum, transformação entre vistas resolvida e evidência suficiente de projeção/cotas/eixo/face, ou confirmação explícita do operador. `different_feature` preserva características diferentes mesmo que coincidam numericamente. `possible_same_feature` cria grupo ambíguo, sem somar quantidades como independentes nem colapsá-las como uma só.
- **FE-03:** uma observação não pertence a duas features confirmadas da mesma peça. Toda fusão confirmada entre múltiplas observações é sustentada por relações válidas conectando o conjunto; uma relação `different_feature` dentro desse conjunto é contradição. Membros diferentes de um padrão/array são features distintas, mesmo que tenham medidas iguais.
- **FE-04:** observações Model e de sua apresentação em viewport não representam duas características físicas. Geometria própria do Paper exige associação explícita antes de contribuir. Uma vista desabilitada não contribui com nova evidência operacional; dados brutos continuam preservados.
- **OP-01:** chave de intenção é `(partId, conjunto ordenado featureIds, stage, processVariant, passGroup, setupId)`. Duplicatas dessa chave são inválidas, mesmo com `Operation.id` diferente. Para operações gerais sem feature, o escopo é a própria peça; a mesma chave não se repete.
- **OP-02:** passagens, pré-furo, furação, mandrilamento e alargamento são etapas distintas legítimas. Não apagar operações só por atingirem a mesma feature. `passGroup` identifica agrupamento técnico justificado, não um campo livre usado para contornar deduplicação.
- **OP-03:** em operação de furos identificados, `quantity` deve corresponder à cardinalidade das features físicas distintas tratadas, não ao número de círculos/vistas. Operações gerais podem ter quantity=1 com conjunto vazio. Profundidade, face, orientação e setup pendentes bloqueiam uso técnico que delas dependa. Setups diferentes propostos não autorizam executar duas vezes o mesmo serviço; ambiguidade permanece visível.

## EL — Elegibilidade e exemplos sintéticos

- **EL-01:** status `eligible` exige referência semântica válida e nenhuma dependência impeditiva aberta. `requiredDecisionIds` deve apontar a decisões válidas e aplicáveis. Não existir entrada implica `not_assessed`, nunca liberação. `accepted_limitation` não limpa a natureza física de uma informação ausente.
- **EL-02:** informações incompletas podem permitir visualização/revisão. Matéria-prima depende de unidade, escala, peça e dimensão relevante; processo depende de identidade física e sequência pretendida; custo depende dos dados quantitativos necessários ao cálculo. Não somar estimativa provisória como orçamento aprovado.
- **EL-03:** `purpose=synthetic_example` exige diagnóstico `SYNTHETIC_DATA` e status `blocked` para material/process/cost, sem exceção por decisão de `synthetic_operator`. Os hashes dos exemplos são fictícios; produção deve calcular o SHA-256 dos bytes reais.
- **EL-04:** CNC nunca é liberado por esta versão do contrato. Não converter `verified`/`confirmed` em aprovação industrial global.
