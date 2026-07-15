#define MyAppName "Agente de Impressao"
#define MyAppVersion "DEV_VERSION"
#define MyAppPublisher "AGSolutions"
#define MyAppExeName "Agente_Impressao.exe"

[Setup]
; Identificador único do seu App
AppId={{8A8C34B6-1234-4567-8901-234567890ABC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
; Instala no %LocalAppData% para NÃO pedir senha de Administrador
DefaultDirName={localappdata}\{#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=Instalador_Agente_Impressao
Compression=lzma
SolidCompression=yes
SetupIconFile=compiler:SetupClassicIcon.ico
; Diz ao instalador para fechar o app se estiver aberto na hora da atualização
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Pega TUDO o que o PyInstaller gerou na pasta dist e joga no instalador
Source: "dist\Agente_Impressao\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\Agente_Impressao\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Quando atualizado via código (silencioso), forçamos o aplicativo a abrir sozinho no final
Filename: "{app}\{#MyAppExeName}"; Flags: nowait; Check: WizardSilent
; Opção manual para quando o cliente clica para instalar na mão
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent