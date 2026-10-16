Unicode true
!include "MUI2.nsh"
Name "VPT Auto Manager"
OutFile "${ARTIFACTS}/VPTAuto-Setup-${APP_VERSION}.exe"
InstallDir "$LOCALAPPDATA\Programs\VPTAuto"
RequestExecutionLevel user
SetCompressor /SOLID lzma
ManifestDPIAware true
Icon "${APP_ICON}"
UninstallIcon "${APP_ICON}"
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey "ProductName" "VPT Auto Manager"
VIAddVersionKey "FileDescription" "VPT Auto Manager Setup"
VIAddVersionKey "FileVersion" "${APP_VERSION}"
VIAddVersionKey "LegalCopyright" "VPT Auto Manager contributors"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\VPTAuto.exe"
!define MUI_FINISHPAGE_RUN_NOTCHECKED
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Vietnamese"

Section "VPT Auto Manager" SEC_MAIN
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File /r "${STAGE}/*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateShortcut "$DESKTOP\VPT Auto Manager.lnk" "$INSTDIR\VPTAuto.exe"
  CreateShortcut "$SMPROGRAMS\VPT Auto Manager.lnk" "$INSTDIR\VPTAuto.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VPTAuto" "DisplayName" "VPT Auto Manager"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VPTAuto" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VPTAuto" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VPTAuto" "DisplayIcon" "$INSTDIR\VPTAuto.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VPTAuto" "InstallLocation" "$INSTDIR"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VPTAuto" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VPTAuto" "NoRepair" 1
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  Delete "$DESKTOP\VPT Auto Manager.lnk"
  Delete "$SMPROGRAMS\VPT Auto Manager.lnk"
  Delete "$INSTDIR\VPTAuto.exe"
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\THIRD_PARTY_NOTICES.txt"
  RMDir /r "$INSTDIR\app"
  RMDir /r "$INSTDIR\runtime"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VPTAuto"
  ; Keep %LOCALAPPDATA%\VPTAuto\settings.json (user links and selections).
SectionEnd
