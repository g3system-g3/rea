; Instalador da Calculadora (Inno Setup 6)
; Gerado automaticamente pelo GitHub Actions. Para gerar na mão:
;   iscc instalador.iss   (depois de criar dist\Calculadora.exe com o PyInstaller)

#define AppName "Calculadora G3"
#define AppVersion "1.1.0"
#define AppExe "Calculadora.exe"

[Setup]
AppId={{8C1B6F3E-4C7A-4E2B-9B7E-3A5D2C9F1E10}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=G3
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
; instala só para o usuário atual, sem pedir senha de administrador
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=Instalar-Calculadora
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir a calculadora agora"; Flags: nowait postinstall skipifsilent
