#define MyAppName "JEIA TECH Industrial LAB"
#define MyAppVersion "20.6.8.3.12"
#define MyAppExeName "JEIA_MOTORES_TESTE.exe"
[Setup]
AppId={{BC1B596A-AF23-4DA3-A2F0-3F44C3EC2C80}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\JEIA TECH Industrial LAB
DefaultGroupName=JEIA TECH Industrial LAB
OutputDir=INSTALADOR_PRONTO
OutputBaseFilename=JEIA_TECH_Industrial_ATUALIZACAO_CAD_04_1
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no
[Files]
Source: "dist\JEIA_MOTORES_TESTE\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autodesktop}\JEIA TECH Industrial LAB"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\JEIA TECH Industrial LAB"; Filename: "{app}\{#MyAppExeName}"
[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir JEIA TECH Industrial LAB"; Flags: nowait postinstall skipifsilent
[Code]
procedure BackupBeforeUpgrade();
var
  FolderName, OriginalPath, ShellPath, BackupRoot: String;
begin
  OriginalPath := ExpandConstant('{app}\JEIA_original_preservado.html');
  ShellPath := ExpandConstant('{app}\jeia_shell.html');
  if not FileExists(OriginalPath) then Exit;
  FolderName := GetDateTimeString('yyyymmdd_hhnnss', '-', ':');
  BackupRoot := ExpandConstant('{commonappdata}\JEIA TECH Industrial\backups-installer\') + FolderName;
  if not ForceDirectories(BackupRoot) then
    RaiseException('Impossivel criar backup. Atualizacao cancelada.');
  if not CopyFile(OriginalPath, BackupRoot + '\JEIA_original_preservado.html', False) then
    RaiseException('Impossivel copiar HTML original. Atualizacao cancelada.');
  if FileExists(ShellPath) then
    if not CopyFile(ShellPath, BackupRoot + '\jeia_shell.html', False) then
      RaiseException('Impossivel copiar shell. Atualizacao cancelada.');
end;
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then BackupBeforeUpgrade();
end;
