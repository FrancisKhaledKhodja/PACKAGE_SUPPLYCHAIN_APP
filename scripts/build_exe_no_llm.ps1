$ErrorActionPreference = 'Stop'

$Version = '1.5.0'
$ExeName = "SUPPLYCHAIN_APP_v$Version"

# Build single EXE (without LLM/RAG libs)
py -m PyInstaller --clean --noconfirm --onefile --name $ExeName `
  --paths "src" `
  --add-data "web;web" `
  --collect-submodules "supplychain_app.blueprints.assistant" `
  --hidden-import "supplychain_app.blueprints.assistant.routes" `
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
