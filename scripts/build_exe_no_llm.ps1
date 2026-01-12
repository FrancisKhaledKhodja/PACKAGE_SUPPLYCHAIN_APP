$ErrorActionPreference = 'Stop'

$Version = '1.6.2'
$ExeName = "SUPPLYCHAIN_APP_v$Version"

# Build single EXE (without LLM/RAG libs)
$UvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (-not $UvCmd) {
  Write-Error "uv n'est pas disponible dans le PATH. Installez uv puis relancez ce script."
}

try {
  uv run python -c "import PyInstaller" | Out-Null
} catch {
  Write-Error "PyInstaller n'est pas installé dans l'environnement uv. Exécutez: uv sync --extra build"
}

uv run python -m PyInstaller --clean --noconfirm --onefile --noconsole --name $ExeName `
  --paths "src" `
  --add-data "web;web" `
  --collect-submodules "package_pudo" `
  --collect-submodules "fastexcel" `
  --collect-all "fastexcel" `
  --collect-submodules "supplychain_app.blueprints.treatments" `
  --collect-submodules "supplychain_app.blueprints.assistant" `
  --hidden-import "supplychain_app.blueprints.assistant.routes" `
  --hidden-import "fastexcel" `
  --exclude-module "chromadb" `
  --exclude-module "chroma_hnswlib" `
  --exclude-module "sentence_transformers" `
  --exclude-module "transformers" `
  --exclude-module "torch" `
  --exclude-module "torchvision" `
  --exclude-module "torchaudio" `
  --exclude-module "onnxruntime" `
  --exclude-module "sklearn" `
  --exclude-module "pytorch_lightning" `
  --exclude-module "langchain" `
  --exclude-module "langchain_core" `
  --exclude-module "langchain_community" `
  --exclude-module "langchain_text_splitters" `
  src\run_exe.py
