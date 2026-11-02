# Correções isoladas do diagnóstico Windows — R01

Data: 02/11/2026, referência de calendário America/Sao_Paulo. Branch: `correcao-diagnostico-windows-fase-2b`. Base preservada: diagnóstico `bf78d6d6e2642a6f28a346ae981408486aaf05da`. Escopo: somente diagnóstico experimental; nenhuma integração à JEIA.

## Evidência Windows e limites da análise

O usuário informou que a sessão `sessao_macro_e668d16bfe48`, Windows/FreeCAD 1.1.4, iniciou FreeCADCmd/controlador, aprovou 24 verificações BREP, encontrou apenas dois dos três segmentos da polilinha do caso 01, manteve pendências legítimas em 02/04 e encontrou `AttributeError` em `getGlobalPlacement()` no caso 03.

Os arquivos completos dessa sessão não foram encontrados no ambiente nem nas branches remotas disponíveis. Não foram recebidos como anexo nesta solicitação. Esses dados são registrados como **relato do usuário**, sem afirmar releitura de JSON/BREP Windows. Evidência: `validation/correcao_windows/USER_WINDOWS_SUMMARY.json`. A correção deve ser executada novamente no Windows para confirmar seu comportamento no FreeCAD 1.1.4 instalado.

## 1. Objetos sem getGlobalPlacement

**Causa comprovada no diagnóstico:** o inventário anterior executava `obj.getGlobalPlacement()` sem a proteção que já existia no coletor aprovado. O trecho AST original foi executado com um objeto sem esse método e reproduziu o mesmo `AttributeError`. Evidência: `BEFORE_FIX.json`.

**Correção:** `inspect_objects()` verifica se o método existe e é chamável e captura erros de resolução da transformação. Mantém contagens e extremos **locais**, registra `coordinateFrameStatus=unresolved` e a causa, e continua observando os demais objetos. Não substitui a transformação por identidade, `obj.Placement` ou `Shape.Placement`. Somente emite pontos médios globais após aplicar com sucesso a mesma composição usada pelo coletor aprovado.

O adaptador aprovado permanece byte a byte idêntico. Ele já preservava `localBrep` quando não resolvia o frame. O auditor novo também reabre esse BREP local, mas registra `physicalCoordinatesApproved=false`: validade topológica não valida coordenadas globais.

Quando faltam frames, `assessment.py` apresenta a comparação global como **pending**, preserva integralmente a comparação parcial em `knownFrameComparison` e mantém `provisionalResultsAccepted=false`. Não promove o caso a aprovado. Conflitos nativos, BREP inválido e limites de recursos continuam falhando. Sem frames ausentes, uma aresta de fechamento faltante continua sendo **failed**.

## 2. Perda da aresta de fechamento

| Etapa | Resultado verificado |
|---|---|
| DXF aprovado, leitura direta dos grupos | `POLYLINE` handle `33`, flag 70=1; três VERTEX com flag 70=0; pontos (0,40), (10,40), (10,50) |
| ezdxf 1.4.4 já disponível | Polilinha fechada; três LINE virtuais, incluindo (10,50)–(0,40) |
| FreeCAD 1.0.0 Linux, antes do adaptador | Original completo com sete arestas totais em vez de oito; polilinha isolada com duas arestas em vez de três; fechamento ausente |
| Coletor aprovado, após importação | Mesmas contagens do shape nativo; observações geométricas do documento não mudaram |
| Variante equivalente, VERTEX sem o grupo opcional 70 | FreeCAD preservou as três arestas |
| Variante LWPOLYLINE fechada | FreeCAD preservou as três arestas |

O segmento faltante mede `sqrt(200)` unidades de desenho, com unidade declarada mm. Não é apenas uma diferença na contagem de objetos ou uma aresta repetida de contêiner.

**Mecanismo encontrado no fonte oficial FreeCAD 1.1.4:**

1. `dxf.h`: `eInteger1 = 70`.
2. `CDxfRead::SetupValueAttribute()` guarda o endereço da variável de destino.
3. `CDxfRead::ReadPolyLine()` registra `SetupValueAttribute(eInteger1, flags)` para ler as flags da POLYLINE.
4. O mesmo mapa de atributos continua ativo durante `ProcessAllEntityAttributes()` dos VERTEX. Cada grupo 70=0 de VERTEX sobrescreve a variável `flags`, antes igual a 1.
5. `OnReadPolyline(vertices, flags)` recebe o valor sobrescrito. `BuildWireFromPolyline()` testa `(flags & 1)`; sem o bit, não acrescenta a aresta final.

Referências: [`dxf.cpp`](https://github.com/FreeCAD/FreeCAD/blob/1.1.4/src/Mod/Import/App/dxf/dxf.cpp), funções `SetupValueAttribute`, `ProcessAllEntityAttributes` e `ReadPolyLine`; [`dxf.h`](https://github.com/FreeCAD/FreeCAD/blob/1.1.4/src/Mod/Import/App/dxf/dxf.h); [`ImpExpDxf.cpp`](https://github.com/FreeCAD/FreeCAD/blob/1.1.4/src/Mod/Import/App/dxf/ImpExpDxf.cpp), `BuildWireFromPolyline` e `OnReadPolyline`. URLs, tamanhos e hashes dos fontes consultados estão em `FREECAD_1_1_4_SOURCE_REFERENCE.json`. Consulta de fonte não equivale à execução desse binário 1.1.4.

**Conclusão:** o defeito de fechamento está no leitor de POLYLINE do importador, antes do adaptador, e é compatível com o comportamento informado no Windows. O desenho original contém o fechamento correto. O adaptador não removeu a aresta. A aprovação dos BREP não detecta esse erro: um wire aberto com duas arestas pode ser um BREP válido.

## 3. Configurações e ensaio diferencial

O novo diagnóstico adiciona um trabalhador isolado, após os quatro casos, para gerar **30 ensaios**: original completo e cinco variantes, sob perfil padrão isolado e quatro valores solicitados de `DxfImportMode`, com layers desativados nesses quatro perfis de investigação. As preferências são escritas **somente no perfil temporário desse trabalhador**. Os testes originais não mudam de configuração. Não são lidas nem modificadas as preferências habituais do Windows.

As variantes são: POLYLINE com VERTEX 70=0, mesma POLYLINE omitindo esse campo opcional, LWPOLYLINE fechada, POLYLINE com primeiro ponto explicitamente repetido e controle aberto. Todas preservam os três pontos definidores; apenas o controle aberto espera duas arestas. O original completo espera oito.

Neste Linux, o perfil padrão não conseguiu importar por erro de importação Python. Desativar a preservação de layers permitiu executar o leitor nativo; **isso não restaurou o fechamento**. Nos quatro valores de modo solicitados, o original completo manteve sete arestas e a POLYLINE isolada com VERTEX 70=0 manteve duas; retirar somente o campo opcional produziu três. Assim, o problema de inicialização/layers deste Linux e a perda de fechamento são problemas distintos.

O FreeCAD 1.0.0 retornou estatísticas `None` e objetos `Compound` nesses perfis. Não afirmamos que quatro valores solicitados correspondem a quatro modos efetivamente distintos nesse binário antigo. O fonte 1.1.4 define os modos 0–3; sua aplicação efetiva no Windows deve ser conferida pelas estatísticas e objetos do novo relatório. As configurações não alteram a passagem problemática das flags no leitor 1.1.4 inspecionado.

A variante com ponto final repetido gera, no ezdxf, quatro segmentos virtuais, um de comprimento zero. O relatório preserva os quatro e identifica explicitamente o degenerado; existem três segmentos não degenerados, comparáveis às três arestas nativas. Essa variante é controle de investigação, não uma recomendação de reparo.

**Nenhuma variante substitui o DXF aprovado. Nenhuma aresta é acrescentada pelo adaptador. O importador FreeCAD instalado não foi corrigido nem substituído.** Caso 01 continua falhando se sua geometria original vier incompleta.

## 4. Alterações e testes

| Arquivo | Alteração |
|---|---|
| `diagnostic/native_worker.py` | Inventário tolerante a método ausente, fatos locais separados e auditoria de BREP local; encaminha ensaio diferencial |
| `diagnostic/assessment.py` | Pendência explícita de frame, com comparação parcial preservada e não aceita |
| `diagnostic/polyline_probe.py` | Leitura limitada ao fixture sintético, variantes controladas, observações antes/depois do coletor e resultados incrementais |
| `diagnostic/driver.py` | Usa a avaliação de frames e executa a investigação extra sem alterar os quatro casos originais |
| `Executar_Diagnostico.FCMacro` | Carrega a cópia R01 em namespace próprio, sem reutilizar módulos da entrega anterior que possam estar em cache no FreeCAD GUI |
| `tests/test_windows_fixes.py` | 17 regressões novas para os dois problemas, preservação de pendências e carregamento da revisão correta |
| `tests/native_missing_placement.py` | Controle com shape Part real, sem método global; confirma retenção local sem coordenadas inventadas |
| `tests/ezdxf_polyline_reference.py` | Referência independente com ezdxf existente, incluindo controles e segmento degenerado |
| `README.md`, `LEIA_PRIMEIRO.txt`, este relatório, `build_package.py` | Instruções R01, escopo, evidências e ZIP com nome novo |

Resultados:

- **69 testes unitários passaram:** os 52 anteriores mais 17 regressões específicas. Incluem ausência/método não chamável/erro de placement, continuidade de outros objetos, falta de Placement, shape nulo, pontos globais apenas quando comprovados, fechamento ausente mantendo falha, pendências 02/04 preservadas e execução da macro R01 mesmo com o bootstrap anterior em cache. Saída em `validation/correcao_windows/UNIT_TESTS.txt`.
- **Controle nativo Part real passou:** objeto wrapper sem `getGlobalPlacement`, uma aresta local e BREP local reaberto; nenhum ponto global emitido. O contrato só contém geometria `UNSUPPORTED` para esse frame desconhecido; original permaneceu intacto.
- **8 referências reais do kernel e 16 round-trips BREP passaram**, com os dois controles negativos anteriores preservados.
- **Referência ezdxf passou:** original fechado com três segmentos; cinco variantes conferidas sem instalar biblioteca.
- **Controlador Linux completo executou:** isolamento e controle do kernel passaram; os quatro casos no perfil padrão mantiveram os erros de importação Python já documentados neste Linux; a investigação extra concluiu 30 ensaios. Foram 16 controles geométricos completos, oito diferenças esperadas de fechamento e seis falhas do perfil padrão. As falhas observadas são evidências, não aprovação da importação.
- **Escopo conferido:** CAD original, entrega aprovada Fase 2B, cópia aprovada do adaptador, schema, oráculos e quatro DXFs preservados; `validation/correcao_windows/SCOPE.json`.

O teste da ausência do método usa objetos controlados e um shape Part real; não é reprodução dos objetos específicos do caso 03 Windows, cujos dados brutos não estão disponíveis. A análise de 1.1.4 é de fonte público e relato do usuário; os testes nativos novos foram executados em Linux/FreeCAD 1.0.0. Windows e PowerShell não foram executados neste ambiente.

## 5. Uso e critérios para o novo teste Windows

Baixe o ZIP **CORRECOES_R01**, extraia em uma pasta nova e execute o mesmo `INICIAR_DIAGNOSTICO.cmd` ou `Executar_Diagnostico.FCMacro`. Não sobreponha a pasta da sessão anterior. O launcher informa as ações antes de iniciar. Além do relatório principal, haverá `polyline_probe/response.json` e `polyline_probe/trials/`, com JSON incremental por ensaio e DXFs sintéticos gerados apenas na sessão.

Esperado: caso 03 não abortar por falta do método; registrar inventário e BREP locais como pendentes quando não houver frame global comprovado. Caso 01 continuar reprovando geometria incompleta, com a matriz permitindo confirmar o mecanismo no binário Windows. Casos 02 e 04 mantêm suas pendências legítimas. Um controle BREP positivo não pode sobrepor essas pendências ou a falta de aresta.

`integrationApproved` e `windowsValidationApproved` continuam falsos na nova execução automática. A evidência da sessão anterior não é apagada ou desqualificada, mas a R01 precisa de teste próprio. Não houve instalação de dependências, geração de instalador, alteração da CAD 04.1, nove abas, motores originais, STEP, instalação Windows ou `main`. A correção anterior de respostas CAD não foi incorporada. Aguardar revisão dos resultados e autorização expressa antes de qualquer integração.
