$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
Set-Location -LiteralPath $PSScriptRoot
$env:UV_CACHE_DIR = Join-Path $PSScriptRoot '.uv-cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $PSScriptRoot '.uv-python'
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'Install uv from https://docs.astral.sh/uv/getting-started/installation/ first.' }
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    uv venv --python 3.12 .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed.' }
}
uv pip install --python $python 'torch==2.11.0' --index-url https://download.pytorch.org/whl/cu128
if ($LASTEXITCODE -ne 0) { throw 'CUDA PyTorch installation failed.' }
uv pip install --python $python -r requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $python -c "import torch; from transformers import Qwen3_5ForCausalLM; assert torch.cuda.is_available(), 'CUDA GPU unavailable'; print(torch.cuda.get_device_name())"
if ($LASTEXITCODE -ne 0) { throw 'GPU environment check failed.' }
& $python -m japanese_learning.download
if ($LASTEXITCODE -ne 0) { throw 'Model download failed. Rerun setup.cmd to resume.' }
Write-Host 'Setup complete. Run launch.cmd.'
