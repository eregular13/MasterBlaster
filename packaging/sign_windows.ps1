# Optional Authenticode signing for PyInstaller output.
# Set MB_CODESIGN_CERT_THUMBPRINT or CODESIGN_CERT_THUMBPRINT to enable.

param(
    [Parameter(Mandatory = $true)]
    [string]$ArtifactPath
)

$thumbprint = $env:MB_CODESIGN_CERT_THUMBPRINT
if (-not $thumbprint) {
    $thumbprint = $env:CODESIGN_CERT_THUMBPRINT
}

if (-not $thumbprint) {
    Write-Host "SKIP: No signing thumbprint configured — artifact remains unsigned."
    exit 0
}

$signtool = "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
if (-not (Test-Path $signtool)) {
    Write-Host "SKIP: signtool.exe not found — artifact remains unsigned."
    exit 0
}

$exe = Join-Path $ArtifactPath "MasterBlaster.exe"
if (-not (Test-Path $exe)) {
    Write-Error "MasterBlaster.exe not found at $exe"
    exit 1
}

& $signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /sha1 $thumbprint $exe
Write-Host "Signed $exe"
exit $LASTEXITCODE