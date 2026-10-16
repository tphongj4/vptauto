Unicode true
!include "FileFunc.nsh"
Name "VPT Auto Manager"
OutFile "${STAGE}/VPTAuto.exe"
Icon "${APP_ICON}"
RequestExecutionLevel user
SilentInstall silent
AutoCloseWindow true
ManifestDPIAware true
Section
  IfFileExists "$EXEDIR\runtime\pythonw.exe" found missing
  missing:
    MessageBox MB_ICONSTOP "Khong tim thay runtime. Hay cai dat lai VPT Auto Manager."
    SetErrorLevel 1
    Quit
  found:
    ${GetParameters} $R0
    ClearErrors
    ExecWait '"$EXEDIR\runtime\pythonw.exe" "$EXEDIR\app\main.py" $R0' $0
    IfErrors failed done
  failed:
    MessageBox MB_ICONSTOP "Khong mo duoc ung dung. Hay cai dat lai VPT Auto Manager."
    SetErrorLevel 1
    Quit
  done:
    IntCmp $0 0 success failed failed
  success:
    SetErrorLevel $0
SectionEnd
