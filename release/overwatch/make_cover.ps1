$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$destination = Join-Path $PSScriptRoot 'media'
New-Item -ItemType Directory -Path $destination -Force | Out-Null
$bitmap = New-Object System.Drawing.Bitmap 1920,1080
$canvas = [System.Drawing.Graphics]::FromImage($bitmap)
$canvas.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$canvas.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$canvas.Clear([System.Drawing.ColorTranslator]::FromHtml('#101923'))
$gold = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml('#F4BE69'))
$white = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml('#F0F1EF'))
$muted = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml('#A8B7C9'))
$blue = New-Object System.Drawing.SolidBrush ([System.Drawing.ColorTranslator]::FromHtml('#213447'))
function Draw-Line([string]$text,[int]$size,[int]$x,[int]$y,$brush) {
    $font = New-Object System.Drawing.Font 'Microsoft YaHei UI',$size,([System.Drawing.FontStyle]::Bold),([System.Drawing.GraphicsUnit]::Pixel)
    $canvas.DrawString($text,$font,$brush,$x,$y)
    $font.Dispose()
}
$canvas.FillRectangle($gold,100,92,90,8)
Draw-Line 'NIGHTREIGN  /  黑夜君临' 32 100 124 $muted
Draw-Line 'OVERWATCH' 116 90 236 $white
Draw-Line 'ULTIMATE VOICES' 92 94 367 $white
Draw-Line '守望中文大招播报' 57 98 505 $gold
$canvas.FillRectangle($blue,100,646,1300,3)
Draw-Line '10 NIGHTFARERS   ·   LOCAL AUDIO' 35 100 694 $white
Draw-Line '十名角色  ·  本地播放  ·  保留技能音效' 29 100 756 $muted
Draw-Line 'NATIVE  /  MMV ADD-ON' 29 100 906 $gold
Draw-Line 'v0.1.0 BETA' 27 100 961 $muted
for($i=0;$i -lt 29;$i++) {
    $height = 50 + [int](210 * [Math]::Abs([Math]::Sin($i * 0.53)) * (1 - [Math]::Abs($i-14)/20))
    $canvas.FillRectangle($gold,1500+$i*9,540-$height/2,4,$height)
}
$canvas.Dispose()
$bitmap.Save((Join-Path $destination 'cover.png'),[System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()
$gold.Dispose(); $white.Dispose(); $muted.Dispose(); $blue.Dispose()
