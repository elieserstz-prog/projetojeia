# Plano de testes e critérios de aprovação

Este arquivo especifica testes futuros. Não instala bibliotecas, não implementa adaptadores nem altera a CAD. Testes contra o contrato devem exigir saídas corretas e bloqueios explícitos; manter uma limitação do leitor antigo só é aceitável se seu resultado não contaminar o modelo operacional novo.

## 1. Níveis e evidências futuras

| Nível | O que testar | Evidência necessária |
|---|---|---|
| Estrutura | Meta-schema, JSON, campos, tipos, enums e formatos | Positivos aceitos; contraprovas rejeitadas no caminho esperado |
| Semântica | IDs, propriedade, referências, estados, matrizes e elegibilidade | Regra violada identificada com escopo e consumidores |
| Adaptadores | Dados extraídos de cada motor sem perda silenciosa | Versão/opções, fixture DXF real, hash e resultado individual preservados |
| Reconciliação | Mesmo domínio/unidade/frame e conflitos | Métricas, perfil numérico e decisão rastreável |
| Interpretação | Classes, peças, vistas e hipóteses físicas | Referência revisada tecnicamente e pendências explícitas |
| Operacional | Características/intenção de processo -> JEIA | Quantidades físicas corretas, sem repetição de tempos/operações |
| Compatibilidade | Nove abas, STEP e proteção contra respostas obsoletas | Comparação com comportamento de referência, sem regressão funcional |
| Destino | Instalação Windows controlada, futura e separada de produção | Execução integrada dos fluxos relevantes antes de distribuir |

Uma passagem em nível de estrutura não aprova os demais. Comparação com referência deve registrar passado/falho/não executado/bloqueado e versão exata das fontes. Teste com motor simulado não substitui motor real.

## 2. Matriz das 30 verificações da auditoria

Os identificadores abaixo rastreiam os 30 comportamentos observados na auditoria original. São requisitos para fixtures de regressão do contrato/consumidor futuro, não uma ordem de modificar todos os leitores antigos.

| ID | Cenário | Resultado exigido na integração futura |
|---|---|---|
| JS01 | Model e Paper com entidades distantes | Espaços separados; sem somar envelopes de apresentação |
| JS02 | 10 polegadas no Model | 254 mm, fator aplicado uma vez |
| JS03 | INSUNITS=7 | 1 km = 1000000 mm ou bloqueio explícito por precisão/suporte; nunca fator 1 |
| JS04 | Extrusion e elevação de círculo | Preservar OCS, z e normal; não achatar |
| JS05 | Moldura envolvendo peça | Não converter peça em bolso por aninhamento da folha |
| JS06 | Componente em layer 0 dentro de INSERT | Preservar layer original e herança efetiva |
| JS07 | Escala não uniforme + rotação | Composição matricial na ordem correta |
| JS08 | Círculo/arco sob escala não uniforme | Elipse/trecho elíptico exato, ou unsupported com bloqueio explícito |
| JS09 | Bulge sob escala não uniforme | Curva composta analítica coerente; não inventar arco circular |
| JS10 | Arco espelhado | Extremos, varredura e orientação corretos |
| JS11 | Cota dentro de bloco | Preservar definição e cada ocorrência, com associações |
| JS12 | Cota no Paper | Origem/layout preservados; não misturar com medida física do Model |
| JS13 | Vistas habilitadas e desabilitadas | Somente vistas autorizadas para aquele escopo contribuem |
| JS14 | Mesmo furo em projeções repetidas | Uma feature confirmada, sem quantidade/tempo duplicado |
| JS15 | Arco discretizado para prévia | Manter geometria analítica; tesselação não substitui fonte dimensional |
| EZ01 | Paper com cotas/linhas | Conteúdo extraído por espaço ou ausência declarada; listar nome do layout não basta |
| EZ02 | INSERT com geometria e cota internas | Inventário recursivo com domínio explícito; gráficos de cotas não contaminam envelope da peça |
| EZ03 | Polegadas e DIMLFAC | Separar valor geométrico, apresentação e unidade; sem conversão duplicada |
| EZ04 | Moldura em layer congelada | Preservar visibilidade e classificação; não usar no bruto automaticamente |
| EZ05 | 501 cotas | Todas preservadas ou truncamento diagnosticado; não fingir cobertura com 500 |
| EZ06 | LINE/ARC/CIRCLE/LWPOLYLINE/POLYLINE | Entidades analíticas exportadas, não somente contagens |
| EZ07 | Círculo OCS corretamente medido pela biblioteca | Preservar sua transformação e origem no contrato, além do envelope |
| BR01 | JSON ezdxf no painel | Observações estruturadas preservadas e rastreáveis até o consumidor |
| BR02 | Exportação JSON ezdxf | Sem perda de campos/precisão ou alteração de significado |
| BR03 | JSON FreeCAD no painel | Preservar observações e ambiguidades de identidade |
| BR04 | Exportação JSON FreeCAD | Sem perda; diferenciar relatório visível de dado operacional efetivamente consumido |
| EX01 | Área experimental de círculo r=15 | Área analítica correta em fonte confiável ou impedir uso da estimativa defeituosa do probe |
| EX02 | Bulge omitido em alguns vértices | Associação por vértice correta; probe não validado não alimenta a feature |
| EX03 | Probe mistura Model/Paper | Resultado limitado explicitamente; não contaminar modelo canônico |
| EX04 | Probe ignora POLYLINE clássica | Suporte por adaptador confiável ou unsupported explícito; não ausência silenciosa |

O plano não exige substituir ezdxf, FreeCAD ou o probe experimental. Se uma limitação do motor não puder ser corrigida no escopo autorizado, o adaptador conserva os dados disponíveis e bloqueia o uso que não pode demonstrar.

## 3. Casos adicionais obrigatórios

| Grupo | Variações |
|---|---|
| Identidade | Dois blocos iguais em posições diferentes; mesma posição; handles iguais em arquivos diferentes; handle ausente; ATTRIB anexado a INSERT; documento revisado |
| Arrays | MINSERT com 2×3 células, espaçamentos negativos, espaçamento zero e células coincidentes; sem deduplicação física automática |
| Hierarquia | Blocos aninhados, base não nula, BYBLOCK/BYLAYER, recursão, Xref ausente e limite de recursos |
| Geometria | Bulges positivos/negativos/maiores que semicircunferência; última aresta fechada; elipse, spline racional/periódica, curva composta, normal inválida e escala singular |
| Apresentação | Folha/carimbo na mesma layer da peça; nomes enganosos; sem moldura; carimbo explodido; texto de gravação ambíguo |
| Vistas | Translação/reordenação/rotação da disposição, detalhes 1:2 e 2:1, corte, vista auxiliar, vista excluída e duas peças no arquivo |
| Layouts | Vários Paper Spaces, viewports com escalas diferentes, twist, recorte não retangular e perspectiva |
| Unidades | INSUNITS=0, 1, 4, 7, unidades US Survey e códigos desconhecidos; conflito de cabeçalho/decisão; coordenadas grandes |
| Cotas | Sem grupo 42; valor calculado; override nominal divergente; unidades alternativas; tolerância unilateral/bilateral/limites; GDT e datums; texto não interpretado |
| Deduplicação | Mesmo furo em duas vistas; furos diferentes de mesmo diâmetro; coincidência de projeção; furo passante vs cego; padrão repetido; relação same/different contraditória |
| Operações | Pré-furo, furação e alargamento legítimos; duplicata com ID diferente; quantidade por features; setups/face pendentes |
| Segurança de consumo | Hash/geração/requisição diferentes, decisão de revisão antiga, amostra sintética marcada eligible, versão de contrato desconhecida |

## 4. Oráculos e tolerâncias

- Fixtures analíticas têm resultados matemáticos conhecidos: endpoints, centros, normais, semieixos, comprimentos e transformações. Contagens e identidade são exatas.
- Para fixtures industriais, a referência deve ser revisada por profissional responsável e preservar cotas/documentação de origem; não usar somente screenshot, caixa envolvente ou a saída de um motor como verdade absoluta.
- O perfil ilustrativo é `lengthAbsMm=1e-6`, `lengthRel=1e-9`, `angleAbsRad=1e-9`, aplicável apenas a fixtures analíticas adequadas. Perfis de BREP/curvas aproximadas devem ser definidos conforme métodos e erro conhecido antes do teste.
- Para comparação escalar, usar RC-03. Não ampliar tolerância depois de observar falha para obter passagem. Comparação geométrica exige testes de estrutura/parametrização/pontos, além de envelope.
- Métodos aproximados devem declarar erro; erro desconhecido não passa como exatidão dimensional. Parâmetros de teste não viram tolerâncias de fabricação.

## 5. Critérios de aprovação da especificação (esta Fase 1)

1. Schema, dicionário e regras são consistentes e definem obrigatoriedade, nulidade e estados sem defaults físicos implícitos.
2. Os quatro exemplos positivos são estruturalmente válidos; contraprova estrutural é rejeitada. Contraprovas semânticas deixam clara a insuficiência do schema sozinho.
3. Exemplos mostram identidade por ocorrência, separação Model/Paper, escala de bloco vs viewport vs vista, OCS não achatado, conflito preservado e bloqueio proporcional.
4. Não há contradição entre regras e valores dos exemplos; cálculos ilustrativos são conferidos documentalmente.
5. Dependências e consumidores bloqueados são explícitos; nenhum exemplo autoriza fabricação.
6. Entrega contém somente documentação/schema/exemplos e preserva o repositório e as instalações existentes.
7. O usuário revisa e aprova a especificação antes de qualquer código de adaptação ou integração.

## 6. Critérios futuros para aprovar adaptadores e integração

- **Fidelidade:** preservar entidades analíticas, bruto e transformações nos casos suportados; identificar todos os trechos incompletos.
- **Referências:** zero IDs duplicados, referências órfãs, cadeias cíclicas ou misturas de arquivo/revisão nos casos aceitos.
- **Unidades:** zero conversões silenciosas e zero aplicações duplicadas de fatores nas fixtures aprovadas.
- **Reconciliação:** todo conflito/ausência fica visível, com escopo e bloqueio pertinente; ausência dupla não é concordância.
- **Interpretação:** nenhum caso ambíguo do corpus é excluído/promovido automaticamente sem evidência exigida. Medir cobertura de automação separadamente de segurança; baixa cobertura não deve ser mascarada por decisões forçadas.
- **Características e operações:** quantidades e chaves de intenção coincidem com os oráculos; preservar etapas legítimas de um mesmo furo.
- **Compatibilidade:** nove abas, motores, fluxo STEP e proteção de identidade continuam operando com os resultados de referência. Testes simulados não bastam para comprovar motor e integração Windows.
- **Recursos:** limites de memória/tempo/entidades serão definidos antes dos testes com corpus representativo; estouro produz diagnóstico e bloqueio, nunca truncamento silencioso.

Nenhum código de teste operacional desta matriz foi implementado nesta entrega. A preparação de fixtures DXF reais, runners, adaptadores e validação Windows pertence a autorização posterior.
