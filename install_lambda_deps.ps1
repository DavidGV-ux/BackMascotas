# Script para instalar dependencias compatibles con Lambda
# Uso: .\install_lambda_deps.ps1

Write-Host "🔧 Instalando dependencias compatibles con Lambda..." -ForegroundColor Green

# Activar entorno virtual si existe
if (Test-Path "venv\Scripts\activate.ps1") {
    Write-Host "✅ Activando entorno virtual..." -ForegroundColor Yellow
    .\venv\Scripts\activate.ps1
} else {
    Write-Host "⚠️  Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\activate.ps1
    pip install --upgrade pip
}

Write-Host "`n📦 Instalando dependencias específicas para Lambda..." -ForegroundColor Cyan

# Desinstalar versiones existentes
Write-Host "  - Desinstalando cffi y cryptography..." -ForegroundColor Yellow
pip uninstall cffi cryptography -y 2>$null

# Instalar versiones compatibles con Lambda
Write-Host "  - Instalando cffi==1.17.1..." -ForegroundColor Yellow
pip install cffi==1.17.1 --no-cache-dir

Write-Host "  - Instalando cryptography==43.0.3..." -ForegroundColor Yellow
pip install cryptography==43.0.3 --no-cache-dir

Write-Host "  - Desinstalando Pillow..." -ForegroundColor Yellow
pip uninstall Pillow -y 2>$null

Write-Host "  - Instalando Pillow==11.0.0 (compatible con Lambda)..." -ForegroundColor Yellow
pip install Pillow==11.0.0 --no-cache-dir

# Instalar todas las demás dependencias
Write-Host "  - Instalando otras dependencias..." -ForegroundColor Yellow
pip install -r requirements.txt --no-cache-dir

Write-Host "`n✅ Verificando instalación..." -ForegroundColor Green

# Verificar que se instalaron correctamente
try {
    python -c "import cffi; import cryptography; from PIL import Image; print('✅ cffi, cryptography y Pillow instalados correctamente')"
} catch {
    Write-Host "❌ Error al verificar dependencias" -ForegroundColor Red
    exit 1
}

Write-Host "`n✨ Dependencias instaladas. Ahora puedes desplegar con:" -ForegroundColor Green
Write-Host "   zappa update dev" -ForegroundColor Cyan

