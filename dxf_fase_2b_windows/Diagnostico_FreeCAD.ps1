# Windows PowerShell 5.1; no external Python, installation or policy change.
[CmdletBinding()]
param(
    [string]$FreeCADCmd = '',
    [string]$OutputRoot = '',
    [ValidateRange(10,120)][int]$VersionTimeoutSeconds = 30,
    [ValidateRange(480,1200)][int]$DiagnosticTimeoutSeconds = 600
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PackageRoot = $PSScriptRoot

function Write-JsonFile([string]$Path, $Value) {
    [IO.File]::WriteAllText($Path, ($Value | ConvertTo-Json -Depth 30), (New-Object Text.UTF8Encoding($false)))
}

function New-IsolatedProfile([string]$Root) {
    $values = @{
        FREECAD_USER_HOME='home'; FREECAD_USER_DATA='data'; FREECAD_USER_TEMP='temp';
        APPDATA='roaming'; LOCALAPPDATA='local'; TEMP='temp'; TMP='temp';
        XDG_CONFIG_HOME='config'; XDG_DATA_HOME='data'; XDG_CACHE_HOME='cache'
    }
    $result = @{}
    foreach ($key in $values.Keys) {
        $dir = Join-Path $Root $values[$key]
        [void][IO.Directory]::CreateDirectory($dir)
        $result[$key] = $dir
    }
    $result['PYTHONDONTWRITEBYTECODE'] = '1'
    return $result
}

function Get-ProfileArguments([string]$Root) {
    return @('--user-cfg', (Join-Path $Root 'user.cfg'), '--system-cfg', (Join-Path $Root 'system.cfg'),
             '--log-file', (Join-Path $Root 'FreeCAD.log'))
}

function Invoke-DiagnosticProcess([string]$Executable, [string[]]$Arguments,
                                   [hashtable]$Environment, [int]$TimeoutSeconds, [string]$Prefix) {
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName = $Executable
    # All arguments are fixed option strings or Windows file paths. Quotes and
    # terminal backslashes are rejected instead of building a shell expression.
    $quoted = foreach ($arg in $Arguments) {
        if ($arg.Contains('"') -or $arg.EndsWith('\')) { throw 'Invalid argument path' }
        '"' + $arg + '"'
    }
    $info.Arguments = $quoted -join ' '
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.WorkingDirectory = $Session
    foreach ($key in $Environment.Keys) { $info.EnvironmentVariables[$key] = $Environment[$key] }
    $proc = New-Object Diagnostics.Process
    $proc.StartInfo = $info
    $timer = [Diagnostics.Stopwatch]::StartNew()
    if (-not $proc.Start()) { throw 'Unable to start FreeCADCmd' }
    $stdout = $proc.StandardOutput.ReadToEndAsync()
    $stderr = $proc.StandardError.ReadToEndAsync()
    $timedOut = -not $proc.WaitForExit($TimeoutSeconds * 1000)
    if ($timedOut) {
        # Only the process launched here and its children; no process-name kill.
        $taskkill = Join-Path $env:SystemRoot 'System32\taskkill.exe'
        & $taskkill /PID $proc.Id /T /F | Out-Null
        if (-not $proc.WaitForExit(10000)) { $proc.Kill() }
    }
    $proc.WaitForExit()
    [IO.File]::WriteAllText($Prefix + '.stdout.txt', $stdout.GetAwaiter().GetResult(), (New-Object Text.UTF8Encoding($false)))
    [IO.File]::WriteAllText($Prefix + '.stderr.txt', $stderr.GetAwaiter().GetResult(), (New-Object Text.UTF8Encoding($false)))
    $code = $proc.ExitCode
    $proc.Dispose()
    return @{exitCode=$code; timedOut=$timedOut; seconds=$timer.Elapsed.TotalSeconds;
             stdout=([IO.Path]::GetFileName($Prefix) + '.stdout.txt');
             stderr=([IO.Path]::GetFileName($Prefix) + '.stderr.txt')}
}

function Find-FreeCADCmd {
    $paths = New-Object 'System.Collections.Generic.List[string]'
    foreach ($app in @(Get-Command FreeCADCmd.exe -CommandType Application -All -ErrorAction SilentlyContinue)) {
        $paths.Add($app.Source)
    }
    $roots = New-Object 'System.Collections.Generic.List[string]'
    foreach ($base in @($env:ProgramFiles, ${env:ProgramFiles(x86)}, (Join-Path $env:LOCALAPPDATA 'Programs'))) {
        if ($base -and (Test-Path -LiteralPath $base -PathType Container)) {
            foreach ($dir in @(Get-ChildItem -LiteralPath $base -Directory -Filter 'FreeCAD*' -ErrorAction SilentlyContinue)) {
                $roots.Add($dir.FullName)
            }
        }
    }
    # Read only FreeCAD uninstall metadata; never execute registry commands.
    foreach ($key in @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
                        'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
                        'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*')) {
        foreach ($entry in @(Get-ItemProperty -Path $key -ErrorAction SilentlyContinue)) {
            if (($entry.PSObject.Properties.Name -contains 'DisplayName') -and $entry.DisplayName -like '*FreeCAD*') {
                if (($entry.PSObject.Properties.Name -contains 'InstallLocation') -and $entry.InstallLocation) {
                    $roots.Add([string]$entry.InstallLocation)
                }
            }
        }
    }
    foreach ($root in $roots) {
        foreach ($relative in @('bin\FreeCADCmd.exe', 'FreeCADCmd.exe')) {
            $path = Join-Path $root $relative
            if (Test-Path -LiteralPath $path -PathType Leaf) { $paths.Add((Get-Item -LiteralPath $path).FullName) }
        }
    }
    return @($paths | Sort-Object -Unique)
}

Write-Host 'JEIA DXF Fase 2B - DIAGNOSTICO EXPERIMENTAL' -ForegroundColor Cyan
Write-Host 'Serao iniciados SOMENTE processos do FreeCADCmd instalado, com perfis temporarios.'
Write-Host 'Serao lidos quatro exemplos DXF sinteticos. Resultados serao gravados em uma pasta nova.'
Write-Host 'Nao ha instalacao, alteracao de politica, acesso a rede ou execucao do aplicativo JEIA.'
Write-Host 'Em caso de timeout, somente os processos deste diagnostico serao encerrados.'

if (-not $OutputRoot) { $OutputRoot = Join-Path $PackageRoot 'resultados' }
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
[void][IO.Directory]::CreateDirectory($OutputRoot)
$Session = Join-Path $OutputRoot ('sessao_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [Guid]::NewGuid().ToString('N').Substring(0,8))
[void][IO.Directory]::CreateDirectory($Session)
$bootstrap = @{format='JEIA_DXF_WINDOWS_BOOTSTRAP'; version='1.0'; integrationApproved=$false;
               windowsValidationApproved=$false; session=$Session; status='failed';
               powershellVersion=$PSVersionTable.PSVersion.ToString(); os=[Environment]::OSVersion.ToString()}
$exitCode = 1
try {
    if ($env:OS -ne 'Windows_NT') { throw 'This launcher requires Windows' }
    if ($FreeCADCmd) {
        $exe = (Get-Item -LiteralPath $FreeCADCmd -ErrorAction Stop).FullName
        if ([IO.Path]::GetFileName($exe) -ine 'FreeCADCmd.exe') { throw 'Select the existing FreeCADCmd.exe' }
        $bootstrap['candidates'] = @($exe)
    } else {
        $found = @(Find-FreeCADCmd)
        $bootstrap['candidates'] = $found
        if ($found.Count -eq 0) { throw 'FreeCADCmd not found. Run with -FreeCADCmd and the existing full path. Nothing will be installed.' }
        if ($found.Count -gt 1) { throw 'Multiple FreeCADCmd installations found. See bootstrap.json and select one with -FreeCADCmd.' }
        $exe = $found[0]
    }
    $bootstrap['freecadCmd'] = $exe
    $bootstrap['executableSha256'] = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
    Write-Host ('FreeCADCmd: ' + $exe)
    $startupProfile = Join-Path $Session 'startup_profile'
    $childEnv = New-IsolatedProfile $startupProfile
    $versionArgs = @(Get-ProfileArguments $startupProfile) + @('--version')
    $bootstrap['versionProbe'] = Invoke-DiagnosticProcess $exe $versionArgs $childEnv $VersionTimeoutSeconds (Join-Path $Session 'version')
    if ($bootstrap['versionProbe'].timedOut -or $bootstrap['versionProbe'].exitCode -ne 0) {
        throw 'FreeCADCmd --version failed or timed out. DXF tests were not started. See version logs.'
    }
    $config = @{session=$Session; freecadCmd=$exe}
    $configPath = Join-Path $Session 'session.json'
    Write-JsonFile $configPath $config
    $childEnv['JEIA_DIAG_SESSION'] = $configPath
    $driverProfile = Join-Path $Session 'driver_profile'
    $driverEnv = New-IsolatedProfile $driverProfile
    $driverEnv['JEIA_DIAG_SESSION'] = $configPath
    $driverArgs = @(Get-ProfileArguments $driverProfile) + @((Join-Path $PackageRoot 'diagnostic\run_driver.FCMacro'))
    $bootstrap['driver'] = Invoke-DiagnosticProcess $exe $driverArgs $driverEnv $DiagnosticTimeoutSeconds (Join-Path $Session 'driver')
    if ($bootstrap['driver'].timedOut -or $bootstrap['driver'].exitCode -ne 0) { throw 'Diagnostic process failed or timed out; inspect logs.' }
    $reportPath = Join-Path $Session 'relatorio.json'
    if (-not (Test-Path -LiteralPath $reportPath)) { throw 'FreeCADCmd returned without writing the diagnostic JSON' }
    $report = Get-Content -LiteralPath $reportPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $bootstrap['status'] = 'completed'
    $bootstrap['technicalOutcome'] = $report.technicalOutcome
    $exitCode = if ($report.technicalOutcome -eq 'failed') { 1 } else { 0 }
} catch {
    $bootstrap['error'] = $_.Exception.Message
    Write-Host $bootstrap['error'] -ForegroundColor Yellow
    if (-not (Test-Path -LiteralPath (Join-Path $Session 'relatorio.json'))) {
        $cases = foreach ($file in @(Get-ChildItem -LiteralPath (Join-Path $PackageRoot 'examples') -Filter '*.dxf' -File)) {
            @{file=$file.Name; status='not_run'; reason=$bootstrap['error']}
        }
        Write-JsonFile (Join-Path $Session 'relatorio.json') @{
            format='JEIA_DXF_WINDOWS_DIAGNOSTIC'; version='1.0'; experimental=$true;
            integrationApproved=$false; windowsValidationApproved=$false; technicalOutcome='failed';
            error=$bootstrap['error']; cases=@($cases)
        }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $Session 'RESUMO.txt'))) {
        [IO.File]::WriteAllText((Join-Path $Session 'RESUMO.txt'),
            ('FALHA DE INICIALIZACAO: ' + $bootstrap['error'] + [Environment]::NewLine +
             'Testes DXF nao aprovados. JEIA nao foi executado. Integracao nao autorizada.'),
            (New-Object Text.UTF8Encoding($false)))
    }
} finally {
    Write-JsonFile (Join-Path $Session 'bootstrap.json') $bootstrap
    Write-Host ('Resultados: ' + $Session) -ForegroundColor Cyan
    Write-Host 'Leia RESUMO.txt e relatorio.json. Envie a pasta da sessao para analise.'
    Write-Host 'Este pacote nao aprova nem integra funcionalidades ao JEIA.'
}
exit $exitCode
