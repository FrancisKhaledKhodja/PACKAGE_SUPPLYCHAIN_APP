$ErrorActionPreference = 'Stop'

# Build single EXE
py -m PyInstaller --clean --noconfirm --onefile --name SupplyChainApp `
  --paths "src" `
  --add-data "web;web" `
  --collect-submodules "supplychain_app.blueprints.assistant" `
  --hidden-import "supplychain_app.blueprints.assistant.routes" `
  src\run_exe.py
