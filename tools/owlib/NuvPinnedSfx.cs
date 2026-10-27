// GPL-3.0. Local DataTool extension for the audited non-speech ultimate asset.
using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using DataTool.Flag;
using TankLib;

namespace DataTool.ToolLogic.Extract;

[Tool("extract-nuv-audio", Description = "Extract pinned local voice/SFX resources as original WEM", CustomFlags = typeof(ExtractFlags))]
public class NuvPinnedSfx : ITool {
    public void Parse(ICLIFlags toolFlags) {
        var flags = (ExtractFlags)toolFlags;
        flags.EnsureOutputDirectory();
        var resources = flags.Positionals.Skip(3).ToArray();
        if (resources.Length is < 1 or > 10) throw new ArgumentException("Specify 1–10 audited audio resource GUIDs");
        flags.RawSound = true;
        foreach (var name in resources) {
            if (!Regex.IsMatch(name, @"\A[0-9A-Fa-f]{12}\.(?:03[Ff]|0[Bb]2)\z"))
                throw new ArgumentException("Only a literal .03F SFX or .0B2 speech GUID is accepted");
            var index = ulong.Parse(name[..12], NumberStyles.HexNumber, CultureInfo.InvariantCulture);
            var type = ushort.Parse(name[13..], NumberStyles.HexNumber, CultureInfo.InvariantCulture);
            var guid = new teResourceGUID(index).WithType(type);
            SaveLogic.Combo.SaveSoundFile(flags, flags.OutputPath, guid);
            Console.WriteLine($"[NUV] Extracted original local audio {guid}");
        }
    }
}
