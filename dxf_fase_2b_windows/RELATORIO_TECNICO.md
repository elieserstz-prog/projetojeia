# Diagnóstico Windows da Fase 2B — entrega experimental

> Relatório histórico da entrega inicial. Para a revisão atual, consulte `RELATORIO_CORRECOES_R01.md` e `validation/correcao_windows/`.

Data: 2026-11-02. Branch de entrega: `diagnostico-windows-dxf-fase-2b`. Base: Fase 2B `a6aeed691cf4276a2e0f4c50bc723909e8712d8c`, cujo histórico preserva o original `456495402676e7b4bee023377d5fea0ddfa8230f`. Nenhuma implementação foi integrada à JEIA.

## Escopo e arquivos

Todas as adições estão em `dxf_fase_2b_windows/`, mais o ZIP e seu SHA-256 na raiz da branch. Nenhum arquivo existente da Fase 2B foi modificado.

| Arquivo/pasta | Responsabilidade |
|---|---|
| `INICIAR_DIAGNOSTICO.cmd` | Entrada Windows visível, sem elevação nem mudança de política |
| `Diagnostico_FreeCAD.ps1` | Detecção somente para leitura, escolha explícita em caso de múltiplos executáveis, processo/versionamento, timeout e relatório de falhas de inicialização |
| `Executar_Diagnostico.FCMacro`, `diagnostic/bootstrap.py` | Alternativa com Python já embutido no FreeCAD quando PowerShell estiver bloqueado; não manipula documentos GUI |
| `diagnostic/run_driver.FCMacro`, `run_worker.FCMacro` | Entradas de execução explícitas para FreeCADCmd |
| `diagnostic/driver.py` | Integridade dos ativos, controle nativo, quatro processos independentes, validação da resposta, comparação e relatórios |
| `diagnostic/native_worker.py` | `Import.readDXF`, inventário completo de objetos observados, coletor aprovado, pontos médios das arestas, reabertura BREP e registro de importação parcial rejeitada |
| `diagnostic/core.py` | Perfis isolados, subprocessos sem shell, comparação analítica, identidade de respostas e resumo |
| `approved_adapter/jeia_dxf_freecad/` | Cópia byte a byte do adaptador e schema aprovados; não executa seu runner antigo |
| `examples/` | Os quatro DXFs aprovados, sem alteração |
| `expected.json`, `APPROVED_FILES.json` | Oráculos geométricos independentes e rastreabilidade SHA-256 |
| `tests/` | Regressões automatizadas e controle geométrico nativo opcional para desenvolvedor |
| `validation/` | Evidências Linux identificadas como tal; não são resultados do Windows |

O novo harness reutiliza o **coletor** e o **contrato** aprovados sem mudanças. Faz a importação por `Import.readDXF` em documentos próprios e acrescenta um envelope de diagnóstico. Não modifica o runner aprovado para acrescentar flags. Isso evita modificar a entrega anterior e permite isolar cada processo, observar objetos sem Shape e registrar o estado parcial de uma importação que falhou.

## Execução e isolamento

O launcher informa previamente as ações, procura executáveis existentes e cria uma sessão única. Não instala nem baixa módulos. Todas as preferências, logs, dados e temporários do diagnóstico são redirecionados nos processos filhos. Os arquivos reais de configuração não são copiados nem abertos para escrita. `ConfigGet(UserParameter/SystemParameter/UserAppData/UserHomePath)` deve apontar para a sessão antes da importação. Versões que não reconheçam o isolamento são recusadas. Não há fallback para executar o worker sem isolamento.

O diagnóstico usa o Python embutido em FreeCADCmd. A alternativa por macro usa o Python do FreeCAD GUI somente como lançador; os testes continuam no FreeCADCmd. O pacote não pede privilégios administrativos, não altera Registro, PATH, associações, política PowerShell ou instalação. Escritas esperadas limitam-se ao pacote/resultados escolhidos pelo operador. O runtime FreeCAD instalado pode carregar seus módulos habituais de sistema, mas os complementos do perfil pessoal não são carregados do diretório habitual pelo pacote.

Cada DXF possui requisição única, SHA-256 e geração própria. São verificados `requestId`, hash de documento e fontes, `selectionGeneration`, `analysisRevision`, `cncReleased=false` e consumidores bloqueados. O diagnóstico não se comunica com a CAD 04.1. Essas verificações são locais ao pacote e não constituem alteração da correção anterior de respostas CAD.

## Oráculos e comparação

Os valores foram calculados das definições dos DXFs sintéticos, sem usar a saída do importador FreeCAD como verdade. Comprimentos estão em mm somente onde a unidade DXF é declarada.

1. **Geometrias mm:** linha (0,0)–(10,0); círculo C=(40,0), R3; arco C=(20,0), R5, de 350° a 370°. Seu comprimento é `5*pi/9` e o ponto médio (25,0). Os dois bulges ±1 formam semicírculos R5, centros (5,20)/(15,20), pontos médios (5,15)/(15,25). A polilinha fechada liga (0,40), (10,40), (10,50) e retorna a (0,40). Esperam-se oito arestas analíticas, sem extras físicos silenciosamente ignorados. A inversão da orientação da mesma linha é permitida; trocar a metade de um círculo falha.
2. **Model/Paper:** cinco referências mínimas — quatro lados do retângulo 100×60 e círculo C=(25,30), R5. Gráficos de cota e Paper Space podem adicionar arestas; ficam registrados e não são tratados como outra operação de usinagem. A referência não aprova moldura, carimbo, cota, tolerância ou layout. A ausência de uma das referências Model é falha mesmo com semântica Paper pendente.
3. **Blocos/OCS/polegadas:** base do bloco (1,0), círculo C=(0,0), R1; INSERT em (10,20), escala (2,1), rotação 90°, duas colunas separadas por 5. Após descontar o ponto base e transformar, centros em polegadas (10,18) e (10,23); em mm (254,457,2) e (254,584,2). Semieixo maior paralelo a Y: 50,8 mm; menor paralelo a X: 25,4 mm. A extrusão OCS (0,1,0) do círculo em (2,3,4) resulta em WCS (-2,4,3) polegadas = (-50,8;101,6;76,2) mm, raio 25,4, normal Y. Escala dupla, conversão ausente, círculo no lugar de elipse, plano errado ou instância ausente falham. A identidade de handle/ocorrência continua pendente.
4. **Unidade ausente:** registra linha, BSpline e texto disponíveis, sem inferir calibração física. A comparação estrutural exige linha e BSpline; texto/Unicode e correspondência à spline original ficam explicitamente pendentes. Nunca aprova dimensões físicas com `$INSUNITS=0`.

O comparador não transforma círculos em furos nem agrupa operações. Contêineres e referências de construção explicitamente identificados pelo coletor não entram na soma de arestas físicas. Geometrias coincidentes de objetos distintos são preservadas; fixtures com contagem exata falham com extras. Essa regra de teste não substitui reconciliação entre vistas.

BREP original e global são exportados para arquivos de nome numérico e SHA-256, mantendo o texto original também no contrato. Cada BREP é reimportado pelo kernel, verificando validade, ausência de shape nulo, contagens de vértices/arestas/faces/sólidos; no global também são comparados comprimentos das arestas. Faces são registradas como observações, sem exigir sua criação onde o DXF contém somente curvas. Conflitos, perda de transformação global e limites de recursos causam falha, sem aprovação parcial silenciosa.

## Testes realizados

- **52 testes de regressão de lógica**, biblioteca padrão, incluindo subprocessos reais controlados para log/retorno/timeout; geometrias e fluxos Windows simulados são identificados como simulações. Comando: `python3 -m unittest discover -s dxf_fase_2b_windows/tests -v`. Saída integral em `validation/UNIT_TESTS.txt`.
- **8 referências geométricas no kernel FreeCAD 1.0.0 real**, construídas em memória: comparação aprovada; **16 BREP** original/global reabertos com sucesso. Dois controles negativos demonstram rejeição de BREP ausente e topologia alterada. Interpretador nativo compatível já existente: `/usr/bin/python3`, biblioteca `/usr/lib/freecad/lib`. Isso não é leitura DXF. Evidência: `validation/NATIVE_REFERENCE.json`.
- **FreeCADCmd 1.0.0 em Linux, com perfil isolado:** `--version` passou. O controlador e cinco trabalhadores iniciaram; isolamento efetivo confirmado; controle do kernel passou (12 arestas, 6 faces, volume 6000 mm³; dois BREP válidos). As **quatro importações DXF falharam**, retornando erro nativo de importação Python. As respostas preservam traceback e observações parciais rejeitadas. Resultado geral `failed`. Evidências: `validation/LINUX_SESSION/`.
- **Sintaxe Python/FCMacro e integridade de escopo:** analisadas sem instalação. Originais CAD e Fase 2B conferidos contra os commits preservados; `validation/SCOPE.json` e manifesto de ativos aprovados.
- **PowerShell/Windows:** não executados. Não há PowerShell nem Windows neste ambiente. Inspeção textual do launcher não equivale à análise sintática ou execução do PowerShell. Nenhum componente foi instalado para contornar isso.

Um detalhe comprovado no fluxo Linux: fornecer `.py` ao FreeCADCmd pode importar o módulo, sem executar `if __name__ == '__main__'`, retornando 0 sem JSON. As entradas `.FCMacro` do diagnóstico executaram o controlador e os workers efetivamente. Não alteramos a Fase 2B para corrigir seu runner; este é um harness separado. A verificação de existência de resposta impede tratar retorno 0 sem resultados como sucesso.

## Limitações e aprovação

Não há aprovação da importação DXF nem do funcionamento no Windows nesta entrega. O controle do kernel bem-sucedido não demonstra leitura DXF correta. A falha de importação neste Linux não demonstra falha da instalação Windows, e os perfis limpos podem diferir do perfil anteriormente usado pela JEIA. O pacote não tenta reparar FreeCAD/PySide, instalar dependências ou trocar o importador.

O contrato 1.0 e os dados de origem disponíveis têm as limitações já documentadas na Fase 2B: shapes não provam handles, origem em blocos, Model/Paper, vistas, tolerâncias ou interpretação industrial. O relatório mostra pendências; não inventa informações. A validação completa do JSON Schema não é executada pelo runtime Windows sem biblioteca adicional; o contrato permanece `schemaStatus=not_checked`.

Critérios para avaliar a próxima execução: FreeCADCmd identificado e inicializado; isolamento confirmado; controle do kernel aprovado; quatro casos efetivamente executados, sem crashes, erros, truncamento ou respostas incompatíveis; referências conhecidas presentes e BREP válidos; todas as pendências analisadas pelo operador. Mesmo atendidos esses critérios, a integração depende de análise dos resultados e autorização expressa do usuário. As flags de aprovação permanecem falsas.

CAD 04.1, nove abas, motores originais, fluxo STEP, instalação Windows e `main` permanecem preservados. A correção anterior de respostas CAD não é incorporada. O pacote ZIP inclui somente o diagnóstico, cópias do componente experimental aprovado, DXFs sintéticos, testes, documentação e evidências; não inclui instalação da JEIA ou binários FreeCAD.

## Referências técnicas

- FreeCAD 1.1.3, [`src/App/Application.cpp`](https://github.com/FreeCAD/FreeCAD/blob/1.1.3/src/App/Application.cpp): `parseProgramOptions` (`user-cfg`, `system-cfg`, `log-file`), `getCustomPaths` (`FREECAD_USER_HOME/DATA/TEMP`), `processFiles` (tratamento de `.py` e `.FCMacro`). Compatibilidade concreta adicional verificada no FreeCAD 1.0.0 instalado neste Linux; outras versões exigem execução do pacote.
- FreeCAD [`src/Main/MainCmd.cpp`](https://github.com/FreeCAD/FreeCAD/blob/1.1.3/src/Main/MainCmd.cpp): inicialização e execução do programa de console.
- Fase 2B aprovada experimentalmente: commit `a6aeed691cf4276a2e0f4c50bc723909e8712d8c`, arquivos preservados conforme `APPROVED_FILES.json`.
