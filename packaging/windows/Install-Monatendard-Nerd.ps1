[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$FontDirectory
)

$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($FontDirectory)) {
    $FontDirectory = Join-Path $PSScriptRoot 'fonts'
}
$fontDirectoryPath = (Resolve-Path -LiteralPath $FontDirectory).Path
$fontFiles = @(Get-ChildItem -LiteralPath $fontDirectoryPath -Filter 'MonatendardNFM-*.ttf' -File)
if ($fontFiles.Count -eq 0) {
    throw "설치할 Monatendard Nerd Font Mono TTF가 없습니다: $fontDirectoryPath"
}

$userFontDirectory = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$fontRegistry = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
New-Item -ItemType Directory -Force -Path $userFontDirectory | Out-Null
New-Item -Force -Path $fontRegistry | Out-Null

if (-not $WhatIfPreference) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class MonatendardNerdFontApi {
    [DllImport("gdi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern int AddFontResourceEx(string fileName, uint flags, IntPtr reserved);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern IntPtr SendMessageTimeout(
        IntPtr hWnd, uint Msg, UIntPtr wParam, IntPtr lParam,
        uint flags, uint timeout, out UIntPtr result);
}
'@
}

foreach ($font in $fontFiles) {
    $destination = Join-Path $userFontDirectory $font.Name
    $style = [System.IO.Path]::GetFileNameWithoutExtension($font.Name).Substring(
        'MonatendardNFM-'.Length
    )
    $registryName = "Monatendard Nerd Font Mono $style (TrueType)"
    if ($PSCmdlet.ShouldProcess($destination, '현재 사용자용 Nerd 글꼴 설치')) {
        Copy-Item -LiteralPath $font.FullName -Destination $destination -Force
        New-ItemProperty `
            -Path $fontRegistry `
            -Name $registryName `
            -Value $destination `
            -PropertyType String `
            -Force | Out-Null
        $loaded = [MonatendardNerdFontApi]::AddFontResourceEx(
            $destination, 0, [IntPtr]::Zero
        )
        if ($loaded -eq 0) {
            throw "Windows 세션에 Nerd 글꼴을 등록하지 못했습니다: $destination"
        }
    }
}

if (-not $WhatIfPreference) {
    $result = [UIntPtr]::Zero
    [void][MonatendardNerdFontApi]::SendMessageTimeout(
        [IntPtr]0xffff, 0x001D, [UIntPtr]::Zero, [IntPtr]::Zero,
        0x0002, 5000, [ref]$result
    )
}

Write-Host "Monatendard Nerd Font Mono $($fontFiles.Count)개 파일 설치를 완료했습니다."
Write-Host '편집기와 터미널을 다시 시작해 주세요.'
