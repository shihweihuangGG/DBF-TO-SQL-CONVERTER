# ================================================================
# DBF-SQL-Converter Build & Package Script
# This script automates the build, sign, and compress process
# ================================================================

param(
    [string]$version = "1.7.2",
    [switch]$noSign = $false,
    [switch]$noZip = $false
)

$ErrorActionPreference = "Stop"
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "🔨 Building DBF-SQL-Converter v$version..." -ForegroundColor Cyan

# Step 1: Clean old builds
Write-Host "  ✓ Cleaning old build artifacts..." -ForegroundColor Yellow
Remove-Item -Recurse -Force "$scriptPath\dist\DBF_to_SQL_v$version" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$scriptPath\build\DBF_to_SQL_v$version" -ErrorAction SilentlyContinue

# Step 2: PyInstaller build
Write-Host "  ✓ Running PyInstaller..." -ForegroundColor Yellow
$buildCmd = "python -m PyInstaller --noconsole --onedir --collect-all dbfread " +
    "--hidden-import=dbfread --hidden-import=dbfread.dbf --hidden-import=dbfread.field_parser " +
    "--hidden-import=dbfread.ifiles --hidden-import=dbfread.exceptions " +
    "--name `"DBF_to_SQL_v$version`" DbfToSqlConverter.py -y"
Invoke-Expression $buildCmd | Out-Null

if (-not (Test-Path "$scriptPath\dist\DBF_to_SQL_v$version\DBF_to_SQL_v$version.exe")) {
    Write-Host "  ❌ Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Executable created successfully" -ForegroundColor Green

# Step 3: Code signing (optional)
if (-not $noSign) {
    Write-Host "  ✓ Signing executable..." -ForegroundColor Yellow
    $certPath = "$scriptPath\dbf_converter.pfx"
    $certPassword = "DBFConverter2026"
    
    if (Test-Path $certPath) {
        $signtoolPath = "C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe"
        if (Test-Path $signtoolPath) {
            & $signtoolPath sign /f $certPath /p $certPassword /t "http://timestamp.digicert.com" `
                "$scriptPath\dist\DBF_to_SQL_v$version\DBF_to_SQL_v$version.exe" 2>&1 | Out-Null
            Write-Host "  ✓ Signed successfully" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ signtool.exe not found, skipping signature" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠ Certificate not found, skipping signature" -ForegroundColor Yellow
    }
}

# Step 4: Create ZIP archive (optional)
if (-not $noZip) {
    Write-Host "  ✓ Creating ZIP archive..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2  # Wait for file handles to release
    $zipPath = "$scriptPath\dist\DBF_to_SQL_v$version.zip"
    
    try {
        Compress-Archive -Path "$scriptPath\dist\DBF_to_SQL_v$version" -DestinationPath $zipPath -Force
        $zipSize = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
        Write-Host "  ✓ Created: DBF_to_SQL_v$version.zip ($($zipSize) MB)" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠ Failed to create ZIP (file may be locked): $_" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ Build complete!" -ForegroundColor Green
Write-Host "   📁 Executable: dist\DBF_to_SQL_v$version\" -ForegroundColor Cyan
Write-Host "   📦 ZIP Archive: dist\DBF_to_SQL_v$version.zip" -ForegroundColor Cyan
