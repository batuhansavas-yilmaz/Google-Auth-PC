[Setup]
AppId={{8E3B1D8A-6F4C-4B7E-9C2D-5A1F0B7D3E21}
AppName=Google Auth PC
AppVersion=0.2.0
AppVerName=Google Auth PC 0.2.0
AppPublisher=Batuhan Savaş
DefaultDirName={autopf}\Google Auth PC
DefaultGroupName=Google Auth PC
DisableProgramGroupPage=no
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=dist\installer
OutputBaseFilename=GoogleAuthPC-Setup-0.2.0
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\GoogleAuthPC.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstü kısayolu oluştur"; GroupDescription: "Kısayollar:"; Flags: checkedonce

[Files]
Source: "dist\GoogleAuthPC.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Google Auth PC"; Filename: "{app}\GoogleAuthPC.exe"
Name: "{autodesktop}\Google Auth PC"; Filename: "{app}\GoogleAuthPC.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\GoogleAuthPC.exe"; Description: "Google Auth PC'yi çalıştır"; Flags: nowait postinstall skipifsilent
