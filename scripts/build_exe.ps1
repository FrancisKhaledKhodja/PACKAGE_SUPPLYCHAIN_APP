$ErrorActionPreference = 'Stop'

# Build single EXE
$Version = '1.6.2'
$ExeName = "SUPPLYCHAIN_APP_v$Version"

py -m PyInstaller --clean --noconfirm --onefile --name $ExeName `
  --paths "src" `
  --add-data "web;web" `
  --collect-submodules "supplychain_app.blueprints.assistant" `
  --hidden-import "supplychain_app.blueprints.assistant.routes" `
  src\run_exe.py
