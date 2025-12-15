$ErrorActionPreference = 'Stop'

# Build single EXE
py -m PyInstaller --clean --noconfirm --onefile --name SupplyChainApp `
  --add-data "web;web" `
  src\supplychain_app\run.py
