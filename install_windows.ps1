# SpikeAI Screenshot Diagnosis - Windows Installation Script
# Automatically installs all dependencies correctly

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "SpikeAI Screenshot Diagnosis - Automated Installation" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/6] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.10 or higher." -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Create virtual environment
Write-Host "[2/6] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "Virtual environment already exists. Skipping..." -ForegroundColor Yellow
} else {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
    Write-Host "Virtual environment created successfully." -ForegroundColor Green
}
Write-Host ""

# Activate virtual environment
Write-Host "[3/6] Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\activate.ps1"
Write-Host "Virtual environment activated." -ForegroundColor Green
Write-Host ""

# Install CORE dependencies (CV + LLM)
Write-Host "[4/6] Installing CORE dependencies (CV + LLM)..." -ForegroundColor Yellow
Write-Host "This includes: BeautifulSoup, OpenCV, NumPy, scikit-image, Groq, etc." -ForegroundColor Cyan
pip install beautifulsoup4 lxml numpy opencv-python pillow scikit-image aiohttp requests openpyxl groq python-dotenv pytest pytest-cov imagehash --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install core dependencies." -ForegroundColor Red
    exit 1
}
Write-Host "Core dependencies installed successfully." -ForegroundColor Green
Write-Host ""

# Ask about OCR installation
Write-Host "[5/6] OCR Installation (OPTIONAL)" -ForegroundColor Yellow
Write-Host "OCR is optional - the pipeline works 100% accurately without it." -ForegroundColor Cyan
Write-Host "OCR adds text extraction capability but requires PyTorch (~200MB)." -ForegroundColor Cyan
Write-Host ""
$installOCR = Read-Host "Install OCR? (y/n) [default: n]"

if ($installOCR -eq "y" -or $installOCR -eq "Y") {
    Write-Host "Installing OCR (PyTorch CPU + EasyOCR)..." -ForegroundColor Yellow
    Write-Host "This may take 2-3 minutes..." -ForegroundColor Cyan
    
    # Install PyTorch CPU version
    pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cpu --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install PyTorch." -ForegroundColor Red
        exit 1
    }
    
    # Install EasyOCR
    pip install easyocr --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install EasyOCR." -ForegroundColor Red
        exit 1
    }
    
    # Test OCR
    python -c "import torch; import easyocr; print('OCR: OK')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OCR installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "WARNING: OCR installation completed but verification failed." -ForegroundColor Yellow
        Write-Host "The pipeline will still work without OCR." -ForegroundColor Yellow
    }
} else {
    Write-Host "Skipping OCR installation. Pipeline will use CV + LLM only." -ForegroundColor Cyan
}
Write-Host ""

# Create .env file if it doesn't exist
Write-Host "[6/6] Checking .env configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host ".env file already exists. Skipping..." -ForegroundColor Yellow
} else {
    Write-Host "Creating .env file template..." -ForegroundColor Cyan
    @"
PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
DISABLE_LLM=false
ENABLE_VLM=true
"@ | Out-File -FilePath .env -Encoding utf8
    Write-Host ".env file created. Please edit it and add your GROQ_API_KEY." -ForegroundColor Yellow
    Write-Host "Get your free API key at: https://console.groq.com/" -ForegroundColor Cyan
}
Write-Host ""

# Installation complete
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file and add your GROQ_API_KEY" -ForegroundColor White
Write-Host "2. Run: python main.py" -ForegroundColor White
Write-Host ""
Write-Host "Documentation: See INSTALL.md for troubleshooting" -ForegroundColor Cyan
Write-Host ""
