[CmdletBinding(SupportsShouldProcess)]
param()

$ErrorActionPreference = 'Stop'
$userFontDirectory = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$fontRegistry = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
$removed = 0

if (-not $WhatIfPreference) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class MonatendardNerdFontApi {
    [DllImport("gdi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern bool RemoveFontResourceEx(string fileName, uint flags, IntPtr reserved);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern IntPtr SendMessageTimeout(
        IntPtr hWnd, uint Msg, UIntPtr wParam, IntPtr lParam,
        uint flags, uint timeout, out UIntPtr result);
}
'@
}

if (Test-Path -LiteralPath $fontRegistry) {
    $properties = (Get-ItemProperty -LiteralPath $fontRegistry).PSObject.Properties
    foreach ($property in $properties) {
        $fileName = [System.IO.Path]::GetFileName([string]$property.Value)
        if ($property.Name -like 'PS*' -or $fileName -notlike 'MonatendardNFM-*.ttf') {
            continue
        }
        if ($PSCmdlet.ShouldProcess($property.Name, '현재 사용자 Nerd 글꼴 등록 제거')) {
            Remove-ItemProperty -LiteralPath $fontRegistry -Name $property.Name
        }
    }
}

if (Test-Path -LiteralPath $userFontDirectory) {
    $fontFiles = @(
        Get-ChildItem -LiteralPath $userFontDirectory -Filter 'MonatendardNFM-*.ttf' -File
    )
    foreach ($font in $fontFiles) {
        if ($PSCmdlet.ShouldProcess($font.FullName, '현재 사용자 Nerd 글꼴 파일 제거')) {
            [void][MonatendardNerdFontApi]::RemoveFontResourceEx(
                $font.FullName, 0, [IntPtr]::Zero
            )
            Remove-Item -LiteralPath $font.FullName -Force
            $removed++
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

Write-Host "Monatendard Nerd Font Mono 제거를 완료했습니다. 제거한 파일: $removed"
Write-Host '편집기와 터미널을 다시 시작해 주세요.'
