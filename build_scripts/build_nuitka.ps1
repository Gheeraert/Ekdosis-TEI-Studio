<#
Recette de compilation Nuitka pour Ekdosis-TEI Studio (Windows).

Produit un exécutable autoporteur de l'UI Tkinter (launch_ets.py) dans
dist/ (dossier non suivi par git). Le module ets.web est inclus car
l'UI peut lancer le serveur Flask de publication en sous-processus.

Usage :
    powershell -ExecutionPolicy Bypass -File build_scripts/build_nuitka.ps1

Prérequis : environnement virtuel .venv à la racine du dépôt, un compilateur
C (MSVC via Build Tools, ou MinGW64 que Nuitka peut télécharger seul).
#>

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Environnement virtuel introuvable : $Python. Créez-le avec 'python -m venv .venv' puis installez requirements.txt."
}

Write-Output "Installation/mise à jour de Nuitka..."
& $Python -m pip install --upgrade nuitka | Out-Null

$DistDir = Join-Path $RepoRoot "dist"
$BuildDir = Join-Path $RepoRoot "build\nuitka"
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null

$VersionMatch = Select-String -Path (Join-Path $RepoRoot "pyproject.toml") -Pattern '^version\s*=\s*"([^"]+)"'
$Version = if ($VersionMatch) { $VersionMatch.Matches[0].Groups[1].Value } else { "0.0.0" }
$OutputName = "Ekdosis-TEI-Studio-$Version.exe"

Write-Output "Compilation avec Nuitka (version $Version)..."
& $Python -m nuitka `
    --standalone `
    --onefile `
    --enable-plugin=tk-inter `
    --windows-console-mode=disable `
    --company-name="Ekdosis-TEI Studio" `
    --product-name="Ekdosis-TEI Studio" `
    --file-version=$Version `
    --product-version=$Version `
    --include-package=ets `
    --include-package-data=ets.resources `
    --include-package-data=ets.web `
    --assume-yes-for-downloads `
    --output-dir=$BuildDir `
    --output-filename=$OutputName `
    launch_ets.py

$BuiltExe = Join-Path $BuildDir $OutputName
if (-not (Test-Path $BuiltExe)) {
    throw "Échec de la compilation : $BuiltExe introuvable."
}
Copy-Item $BuiltExe (Join-Path $DistDir $OutputName) -Force

$PandocSource = "C:\Program Files\Pandoc\pandoc.exe"
if (Test-Path $PandocSource) {
    Copy-Item $PandocSource (Join-Path $DistDir "pandoc.exe") -Force
    Write-Output "pandoc.exe copié à côté de l'exécutable (requis pour l'import de notices .docx)."
} else {
    Write-Warning "pandoc.exe introuvable à '$PandocSource' : copiez-le manuellement à côté de $OutputName avant diffusion."
}

Write-Output "Exécutable généré : $(Join-Path $DistDir $OutputName)"
