# JEIA DXF Fase 2B — diagnóstico Windows experimental

**Revisão R01:** leia primeiro [RELATORIO_CORRECOES_R01.md](RELATORIO_CORRECOES_R01.md). Trata objetos sem `getGlobalPlacement()` sem inventar WCS e acrescenta 30 ensaios diferenciais de fechamento de POLYLINE. As configurações adicionais são exclusivamente temporárias e não alteram os quatro casos originais. Sem frame conhecido, a comparação global fica pendente; sem aresta no shape original, o caso 01 continua falhando. Semântica do caso 02 e unidade do caso 04 continuam pendentes.

Este pacote testa o **FreeCAD já instalado** e os quatro DXFs sintéticos da Fase 2B. Não integra resultados à JEIA. Não execute a JEIA CAD 04.1 durante o diagnóstico.

## Como executar no Windows

1. Salve `JEIA_DXF_TECH_FASE_2B_DIAGNOSTICO_WINDOWS_CORRECOES_R01.zip` em **Downloads**. Use **Extrair tudo** em uma pasta nova; não execute de dentro do ZIP. Mantenha as subpastas juntas e preserve a sessão anterior.
2. Abra a pasta extraída `JEIA_DXF_TECH_FASE_2B_DIAGNOSTICO_WINDOWS_CORRECOES_R01` e dê dois cliques em **INICIAR_DIAGNOSTICO.cmd**. Não execute como administrador. Leia na janela o que será executado.
3. Aguarde a indicação da pasta `resultados\sessao_...`. Abra **RESUMO.txt** e **relatorio.json** nessa pasta. Guarde também `bootstrap.json`, logs e subpastas dos casos. A execução pode levar até dez minutos se houver travamento.

O caminho absoluto dos resultados aparece na janela. Os arquivos não são colocados em `/workspace` no seu computador. Nenhum resultado é enviado pela rede automaticamente.

Se houver várias instalações, consulte `candidates` no `bootstrap.json` e selecione explicitamente o executável existente. Pelo Prompt de Comando, na pasta extraída:

```bat
INICIAR_DIAGNOSTICO.cmd -FreeCADCmd "C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe"
```

O caminho é um exemplo: use o de sua instalação. Para escolher outra pasta de resultados, acrescente `-OutputRoot "C:\Users\SEU_USUARIO\Downloads\Resultados_JEIA_DXF"`.

## Se o Windows bloquear o PowerShell

O pacote **não altera a política de execução**, não a contorna por `ExecutionPolicy Bypass` e não exige a instalação de Python ou PowerShell. Se o `.cmd` informar bloqueio de script:

1. Abra somente o **FreeCAD existente**.
2. Em **Macro → Macros**, selecione a pasta extraída e execute **Executar_Diagnostico.FCMacro**. Essa macro usa o Python já embutido no FreeCAD para iniciar os mesmos testes em processos `FreeCADCmd` separados. Não lê nem altera os documentos abertos na interface.
3. Consulte `resultados\sessao_macro_...` na pasta do pacote.

Se houver mais de um FreeCAD, edite apenas a variável `FREECAD_CMD` na macro fornecida e informe o caminho existente. Não edite arquivos da instalação do FreeCAD nem da JEIA. Caso a macro também seja bloqueada pela sua política de segurança, encaminhe a mensagem; o pacote não faz mudanças para liberar a execução.

## O que será executado e gravado

- Busca somente de `FreeCADCmd.exe`: PATH, pastas FreeCAD em Program Files/Programs e metadados de desinstalação do FreeCAD no Registro, apenas para leitura. Instalações portáteis fora desses locais exigem caminho explícito. Não usa o comando de desinstalação.
- Uma chamada `FreeCADCmd --version`, com timeout de 30 segundos e configuração isolada. Se falhar, os quatro DXFs ficam `not_run` e o erro é exportado.
- Um controlador em outro `FreeCADCmd`, um controle sintético do kernel e quatro trabalhadores separados para importar os quatro DXFs. Cada importação usa `Import.readDXF(..., ignore_errors=False)`, o mesmo ponto de entrada da Fase 2B aprovada. Não há tentativa automática de outro importador, download ou instalação.
- Depois dos quatro casos, um trabalhador adicional compara o original e cinco variantes sintéticas em cinco perfis de investigação (30 ensaios). Grava contagens antes/depois do adaptador, estatísticas e resultados incrementais em `polyline_probe/`. Não repara nem substitui os DXFs aprovados. As preferências desse trabalhador só afetam seu perfil temporário.
- Perfis novos por processo: `--user-cfg`, `--system-cfg`, `--log-file`; variáveis de dados, configuração e temporários redirecionadas **somente nos processos filhos**. Nenhuma variável persistente é alterada. O controlador e os trabalhadores verificam os caminhos efetivos antes de importar. Se o isolamento não for reconhecido pela versão instalada, o teste para e registra a falha.
- Documentos temporários criados e fechados nos processos filhos. Não salva projeto FCStd, não abre arquivos da JEIA e não modifica os DXFs fornecidos. Em timeout, encerra apenas o processo iniciado pelo diagnóstico e seus descendentes.
- JSON, resumo, logs, arquivos de requisição/resposta e BREP na nova pasta da sessão. Os arquivos `user.cfg`/`system.cfg` produzidos são exclusivamente dessa sessão. Nada é apagado automaticamente fora dela. Para remover os resultados, exclua somente a pasta da sessão quando não precisar mais dela.

O FreeCAD carrega seus próprios módulos instalados na inicialização. O pacote não os altera. O teste usa um perfil limpo, portanto preferências e complementos particulares do perfil habitual não são reproduzidos. Uma falha neste perfil não demonstra, por si só, falha do motor usado anteriormente pela CAD 04.1.

## Como interpretar

| Arquivo | Referência verificada | Limite explícito |
|---|---|---|
| `01_geometrias_mm.dxf` | 8 arestas analíticas: linha, arco de 20° cruzando zero, círculo, 2 semicírculos de bulge e 3 segmentos de polilinha fechada | Arcos precisam preservar extremos, comprimento, centro, raio, plano e ponto médio; extras falham na multiplicidade |
| `02_peca_folha_carimbo_cotas.dxf` | Retângulo Model 100 × 60 mm e círculo R5 em (25,30) | Paper Space, carimbo, cotas, tolerâncias e viewport ficam pendentes de reconciliação; inventário e contrato registram o observado |
| `03_blocos_polegadas_ocs.dxf` | 2 elipses com semieixos 50,8/25,4 mm e círculo OCS R25,4 em plano XZ | Não aprova a associação entre shape, handle e ocorrência; não aplica novamente o fator 25,4 aos shapes |
| `04_unidade_ausente.dxf` | Presença estrutural de linha e BSpline; inventário do texto disponível | `$INSUNITS=0`: unidade física pendente, nunca assume milímetros |

Tolerância numérica de comparação: **0,00001 mm**, angular **0,0000001 rad**. São tolerâncias do teste sintético, não tolerâncias de fabricação. `expected.json` contém as referências completas e suas fórmulas são explicadas no relatório.

`passed` significa somente que uma verificação específica passou. `failed` indica falha ou diferença geométrica. `pending` indica informação que exige validação humana ou reconciliação futura. `not_run` significa não executado. O resultado geral pode permanecer `pending` mesmo com toda a geometria esperada presente. Os códigos de saída 0 dos lançadores significam diagnóstico concluído sem falha técnica, inclusive com pendências; não são aprovação de integração.

`windowsValidationApproved` e `integrationApproved` permanecem **false**. O contrato mantém CNC não liberado e matéria-prima/processo/orçamento bloqueados. Respostas parciais ou com erro são preservadas em `response.json` como rejeitadas; não são usadas na comparação. Não são somadas geometrias de contêineres com seus filhos, e observações coincidentes adicionais não são fundidas silenciosamente.

O contrato exportado é o do adaptador experimental aprovado, ainda com `schemaStatus=not_checked`. Não é instalado `jsonschema` no Windows. A checagem local do controlador cobre identidade, hashes, geração/revisão e bloqueio de consumidores; isso não equivale à validação integral do JSON Schema.

## O que enviar para análise

Envie a **pasta da sessão**, ou compacte-a pelo próprio Windows, incluindo JSON, resumo, logs e BREP. Ela contém caminhos locais e nomes de instalação necessários ao diagnóstico; revise antes de compartilhar. Não é necessário enviar a instalação JEIA nem arquivos industriais reais. A execução no seu Windows e a análise desses resultados ainda são necessárias antes de qualquer aprovação. Nenhuma integração será feita sem sua autorização.

## Conferência do download

Compare o resultado abaixo com o arquivo `.zip.sha256` publicado ao lado do ZIP:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath "$env:USERPROFILE\Downloads\JEIA_DXF_TECH_FASE_2B_DIAGNOSTICO_WINDOWS_CORRECOES_R01.zip"
```

O manifesto `MANIFESTO_SHA256.txt` dentro do pacote permite conferir os arquivos internos. `APPROVED_FILES.json` identifica o commit de origem e os hashes do adaptador e dos exemplos preservados.

## Validação realizada pelo desenvolvedor

Consulte `RELATORIO_CORRECOES_R01.md` e `validation/correcao_windows/`. `RELATORIO_TECNICO.md` e os demais resultados na pasta validation documentam a entrega inicial. A sessão Windows relatada pelo usuário está identificada como relato, pois seus arquivos completos não foram disponibilizados aqui. Os testes novos de lógica e os controles nativos em Linux não substituem a execução da R01 no Windows. PowerShell não está disponível neste ambiente e não foi instalado.
