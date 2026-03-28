[Setup]
AppName=Reboot.py
AppVersion=1.0
AppPublisher=Project Reboot
DefaultDirName={autopf}\Reboot.py
DefaultGroupName=Reboot.py
OutputDir=Output
OutputBaseFilename=Reboot.py_Setup
SetupIconFile=ReleaseBuild\assets\icons\reboot.ico
UninstallDisplayIcon={app}\assets\icons\reboot.ico
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "ReleaseBuild\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Reboot.py"; Filename: "{app}\Reboot.py.exe"; IconFilename: "{app}\assets\icons\reboot.ico"
Name: "{autodesktop}\Reboot.py"; Filename: "{app}\Reboot.py.exe"; Tasks: desktopicon; IconFilename: "{app}\assets\icons\reboot.ico"

[Run]
Filename: "{app}\Reboot.py.exe"; Description: "{cm:LaunchProgram,Reboot.py}"; Flags: nowait postinstall skipifsilent
