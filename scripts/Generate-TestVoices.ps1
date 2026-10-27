param([string]$OutputDirectory = (Join-Path $PSScriptRoot '..\voices'))
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $chineseVoice = $synth.GetInstalledVoices() | Where-Object { $_.Enabled -and $_.VoiceInfo.Culture.Name -like 'zh-*' } | Select-Object -First 1
    if (-not $chineseVoice) { throw 'Windows 未安装中文语音。请在 Windows 语言设置中安装中文语音包，或直接提供自己的 WAV。' }
    $synth.SelectVoice($chineseVoice.VoiceInfo.Name)
    $synth.Rate = 1
    $synth.Volume = 80
    $format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(48000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
    $clips = [ordered]@{
        wylder = '追踪者，绝招发动！'
        guardian = '守护者，救赎之翼！'
        ironeye = '铁之眼，一箭贯穿！'
        duchess = '女爵，黑夜掩护！'
        raider = '无赖，风暴降临！'
        revenant = '复仇者，不死军势！'
        recluse = '隐士，灵魂鲜血之歌！'
        executor = '执行者，诅咒释放！'
        scholar = '学者，命运相连！'
        undertaker = '送葬者，终结时刻！'
    }
    $target = [System.IO.Path]::GetFullPath($OutputDirectory)
    [System.IO.Directory]::CreateDirectory($target) | Out-Null
    foreach ($id in $clips.Keys) {
        $path = Join-Path $target ($id + '.wav')
        if (Test-Path -LiteralPath $path) { Write-Output "保留现有音频: $path"; continue }
        $synth.SetOutputToWaveFile($path, $format)
        $synth.Speak($clips[$id])
        $synth.SetOutputToNull()
        Write-Output "已生成: $path"
    }
    Write-Output ('中文测试语音: ' + $chineseVoice.VoiceInfo.Name)
} finally { $synth.Dispose() }
