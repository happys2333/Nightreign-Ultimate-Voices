using SoulsFormats;
using System.Buffers.Binary;
using System.Security.Cryptography;
using System.Text.Json;

return Patcher.Run(args);

sealed class PatchException(string code, string message) : Exception(message)
{
    public string Code { get; } = code;
}

sealed record Operation(int TaeId, int AnimationId, int SoundId, float Start, float End);
sealed record Plan(string SourceHash, List<Operation> Operations);

static class Patcher
{
    const long MaxInputBytes = 256L * 1024 * 1024;
    const int MaxPlanBytes = 1024 * 1024;
    static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true, IncludeFields = true };

    static void Require(bool valid, string code, string message)
    {
        if (!valid) throw new PatchException(code, message);
    }

    public static int Run(string[] args)
    {
        try
        {
            Execute(args);
            return 0;
        }
        catch (PatchException ex)
        {
            Console.Error.WriteLine($"TAE_PATCH_ERROR {ex.Code}: {ex.Message}");
        }
        catch (Exception ex)
        {
            // Library diagnostics can contain large binary dumps or stack traces.
            Console.Error.WriteLine($"TAE_PATCH_ERROR PROCESSING: {ex.GetType().Name}; input could not be safely processed.");
        }
        return 2;
    }

    static Dictionary<string, string> Arguments(string[] args)
    {
        var result = new Dictionary<string, string>(StringComparer.Ordinal);
        var names = new[] { "--input", "--output", "--plan", "--game-dir", "--report" };
        Require(args.Length == names.Length * 2, "ARGUMENTS", "Expected --input FILE --output FILE --plan JSON --game-dir DIR --report FILE.");
        for (int i = 0; i < args.Length; i += 2)
        {
            Require(names.Contains(args[i]) && !string.IsNullOrWhiteSpace(args[i + 1]) && result.TryAdd(args[i], args[i + 1]), "ARGUMENTS", "Unknown, empty, or duplicate argument.");
        }
        return result;
    }

    static string SafePath(string path)
    {
        string windowsPath = path.Replace('/', '\\');
        Require(!windowsPath.StartsWith(@"\\", StringComparison.Ordinal), "PATH_UNSAFE", "UNC and device paths are not permitted; use a normal local-drive path.");
        var components = windowsPath.Split('\\');
        Require(!components.Any(c => c.Length > 0 && c != "." && c != ".." && (c.EndsWith('.') || c.EndsWith(' ') || c.Contains('~'))),
            "PATH_UNSAFE", "Trailing dots/spaces and short-name path aliases are not permitted.");
        string full = Path.GetFullPath(path);
        Require(!full[Path.GetPathRoot(full)!.Length..].Contains(':'), "PATH_UNSAFE", "Alternate data streams are not permitted.");
        string? current = full;
        while (current != null)
        {
            if (Path.Exists(current))
                Require((File.GetAttributes(current) & FileAttributes.ReparsePoint) == 0, "PATH_UNSAFE", "Symlinks and junctions are not permitted.");
            else
            {
                // Broken symbolic links may not satisfy Path.Exists.
                Require(new FileInfo(current).LinkTarget == null && new DirectoryInfo(current).LinkTarget == null, "PATH_UNSAFE", "Symlinks are not permitted.");
            }
            current = Path.GetDirectoryName(current);
        }
        return full;
    }

    static bool SamePath(string a, string b) => string.Equals(a, b, StringComparison.OrdinalIgnoreCase);
    static bool Within(string path, string root) => SamePath(path, root) || path.StartsWith(Path.TrimEndingDirectorySeparator(root) + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase);

    static void ValidateOutput(string output, string game, params string[] protectedPaths)
    {
        SafePath(output);
        Require(!Path.Exists(output), "PATH_UNSAFE", "Output and report paths must not already exist.");
        Require(!Within(output, game), "PATH_UNSAFE", "Writing inside the game directory is forbidden.");
        Require(!protectedPaths.Any(p => SamePath(output, p)), "PATH_UNSAFE", "Input, plan, output, and report paths must be distinct.");
        Require(Directory.Exists(Path.GetDirectoryName(output)), "PATH_UNSAFE", "Output parent directory must already exist.");
    }

    static byte[] ReadBounded(string path, long max, string code)
    {
        using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
        Require(stream.Length > 0 && stream.Length <= max, code, $"File size must be between 1 and {max} bytes.");
        byte[] bytes = new byte[(int)stream.Length];
        stream.ReadExactly(bytes);
        Require(stream.ReadByte() == -1, code, "File size changed while reading.");
        return bytes;
    }

    static void Keys(JsonElement element, params string[] required)
    {
        Require(element.ValueKind == JsonValueKind.Object, "PLAN_INVALID", "Expected a JSON object.");
        var keys = element.EnumerateObject().Select(p => p.Name).ToList();
        Require(keys.Count == required.Length && keys.Distinct(StringComparer.Ordinal).Count() == keys.Count && required.All(keys.Contains), "PLAN_INVALID", "Missing, unknown, or duplicate JSON field.");
    }

    static int PositiveInt(JsonElement element)
    {
        Require(element.TryGetInt32(out int value) && value > 0, "PLAN_INVALID", "IDs must be positive 32-bit integers.");
        return value;
    }

    static double Time(JsonElement element)
    {
        Require(element.TryGetDouble(out double value) && double.IsFinite(value) && value >= 0 && value <= 120, "PLAN_INVALID", "Times must be finite numbers between 0 and 120 seconds.");
        return value;
    }

    static Plan ReadPlan(string path)
    {
        try
        {
            using var document = JsonDocument.Parse(ReadBounded(path, MaxPlanBytes, "PLAN_INVALID"), new JsonDocumentOptions { MaxDepth = 8 });
            var root = document.RootElement;
            Keys(root, "schema_version", "source_sha256", "operations");
            Require(root.GetProperty("schema_version").TryGetInt32(out int schema) && schema == 1, "PLAN_INVALID", "Unsupported plan schema_version.");
            var hashElement = root.GetProperty("source_sha256");
            Require(hashElement.ValueKind == JsonValueKind.String, "PLAN_INVALID", "source_sha256 must be a hexadecimal string.");
            string hash = hashElement.GetString()!;
            Require(hash.Length == 64 && hash.All(char.IsAsciiHexDigit), "PLAN_INVALID", "source_sha256 must contain 64 hexadecimal characters.");
            var array = root.GetProperty("operations");
            Require(array.ValueKind == JsonValueKind.Array && array.GetArrayLength() is >= 1 and <= 64, "PLAN_INVALID", "Plan must contain between 1 and 64 operations.");
            var operations = new List<Operation>();
            var seen = new HashSet<(int, int, int)>();
            foreach (var row in array.EnumerateArray())
            {
                Keys(row, "tae_id", "animation_id", "sound_id", "start_seconds", "end_seconds");
                int tae = PositiveInt(row.GetProperty("tae_id"));
                int animation = PositiveInt(row.GetProperty("animation_id"));
                int sound = PositiveInt(row.GetProperty("sound_id"));
                double start = Time(row.GetProperty("start_seconds"));
                double end = Time(row.GetProperty("end_seconds"));
                Require(end > start && (float)end > (float)start, "PLAN_INVALID", "Event duration must remain positive at TAE float precision.");
                Require(seen.Add((tae, animation, sound)), "PLAN_INVALID", "Duplicate animation/sound operation.");
                operations.Add(new(tae, animation, sound, (float)start, (float)end));
            }
            return new(hash.ToLowerInvariant(), operations);
        }
        catch (JsonException) { throw new PatchException("PLAN_INVALID", "Malformed JSON plan."); }
        catch (InvalidOperationException) { throw new PatchException("PLAN_INVALID", "Incorrect JSON value type."); }
    }

    static string Sha(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
    static string Json(object value) => JsonSerializer.Serialize(value, JsonOptions);
    static object Compression(DCX.CompressionInfo compression) => new { type = compression.GetType().FullName, data = JsonSerializer.Serialize(compression, compression.GetType(), JsonOptions) };
    static string BinderHeader(BND4 b) => Json(new { b.Version, b.Format, b.Unk04, b.Unk05, b.BigEndian, b.BitBigEndian, b.Unicode, b.Extended, compression = Compression(b.Compression) });
    static string MemberHeader(BinderFile f) => Json(new { f.ID, f.Name, f.Flags, compression = Compression(f.CompressionInfo) });

    static string Snapshot(TAE t) => Json(new
    {
        t.ID, t.Format, t.BigEndian, t.EventBank, t.SkeletonName, t.SibName, flags = Convert.ToHexString(t.Flags),
        t.AnimCount2Value, t.IsOldDemonsSoulsFormat_0x10000, t.IsOldDemonsSoulsFormat_0x1000A, t.HasErrorAndNeedsResave,
        compression = Compression(t.Compression),
        animations = t.Animations.Select(a => new
        {
            a.ID, a.AnimFileName, header = JsonSerializer.Serialize(a.MiniHeader, a.MiniHeader.GetType(), JsonOptions),
            groups = a.EventGroups.Select(g => new { g.GroupType, g.GroupData }),
            events = a.Events.Select(e => new { e.Type, e.StartTime, e.EndTime, e.Unk04, group_index = a.EventGroups.IndexOf(e.Group), parameters_hex = Convert.ToHexString(e.GetParameterBytes(t.BigEndian)) })
        })
    });

    static int ReadInt(byte[] bytes, int offset, bool bigEndian) => bigEndian ? BinaryPrimitives.ReadInt32BigEndian(bytes.AsSpan(offset, 4)) : BinaryPrimitives.ReadInt32LittleEndian(bytes.AsSpan(offset, 4));
    static byte[] Parameters(int soundId, bool bigEndian)
    {
        byte[] bytes = new byte[8];
        if (bigEndian)
        {
            BinaryPrimitives.WriteInt32BigEndian(bytes, 1);
            BinaryPrimitives.WriteInt32BigEndian(bytes.AsSpan(4), soundId);
        }
        else
        {
            BinaryPrimitives.WriteInt32LittleEndian(bytes, 1);
            BinaryPrimitives.WriteInt32LittleEndian(bytes.AsSpan(4), soundId);
        }
        return bytes;
    }

    static void VerifyBinder(BND4 before, BND4 after, HashSet<int> changed)
    {
        Require(BinderHeader(before) == BinderHeader(after) && before.Files.Count == after.Files.Count, "AUDIT_FAILED", "Binder header or file count changed.");
        for (int i = 0; i < before.Files.Count; i++)
        {
            Require(MemberHeader(before.Files[i]) == MemberHeader(after.Files[i]), "AUDIT_FAILED", "Binder member metadata changed.");
            if (!changed.Contains(i))
                Require(before.Files[i].Bytes.SequenceEqual(after.Files[i].Bytes), "AUDIT_FAILED", "An unrelated binder member changed.");
        }
    }

    static void VerifyTae(TAE original, TAE changed, byte[] originalBytes, Operation[] operations, List<object>? paddingAdjustments = null)
    {
        foreach (var operation in operations.Reverse())
        {
            var animation = changed.Animations.Single(a => a.ID == operation.AnimationId);
            var ev = animation.Events.Last(); var group = animation.EventGroups.Last();
            byte[] parameters = ev.GetParameterBytes(changed.BigEndian);
            Require(ev.Type == 128 && ev.Unk04 == 0 && ev.StartTime == operation.Start && ev.EndTime == operation.End &&
                parameters.Length is >= 8 and <= 16 && parameters.AsSpan(0, 8).SequenceEqual(Parameters(operation.SoundId, changed.BigEndian)) && parameters.Skip(8).All(b => b == 0) &&
                ReferenceEquals(ev.Group, group) && group.GroupType == 128 && group.GroupData.Equals(default(TAE.EventGroup.EventGroupDataStruct)) && animation.Events.Count(e => ReferenceEquals(e.Group, group)) == 1,
                "AUDIT_FAILED", "Inserted event differs from the requested type, sound, time, parameters, or group.");
            animation.Events.RemoveAt(animation.Events.Count - 1);
            animation.EventGroups.RemoveAt(animation.EventGroups.Count - 1);
        }
        // The 24-byte added event header changes the first data block's 16-byte
        // alignment. SoulsFormats includes this zero padding in GetParameterBytes.
        // No other event may differ; restore only proven zero alignment padding
        // before comparing the complete original structure and binary encoding.
        foreach (var animation in changed.Animations)
        {
            if (!operations.Any(o => o.AnimationId == animation.ID) || animation.Events.Count == 0) continue;
            var oldAnimation = original.Animations.Single(a => a.ID == animation.ID);
            byte[] oldBytes = oldAnimation.Events[0].GetParameterBytes(original.BigEndian);
            byte[] newBytes = animation.Events[0].GetParameterBytes(changed.BigEndian);
            if (oldBytes.SequenceEqual(newBytes)) continue;
            int commonLength = Math.Min(oldBytes.Length, newBytes.Length);
            Require(Math.Abs(oldBytes.Length - newBytes.Length) == 8 && oldBytes.AsSpan(0, commonLength).SequenceEqual(newBytes.AsSpan(0, commonLength)) &&
                oldBytes.Skip(commonLength).All(b => b == 0) && newBytes.Skip(commonLength).All(b => b == 0),
                "AUDIT_FAILED", "Original first-event parameters changed beyond zero alignment padding.");
            paddingAdjustments?.Add(new { tae_id = original.ID, animation_id = animation.ID, event_index = 0, original_storage_bytes = oldBytes.Length, output_storage_bytes = newBytes.Length, trailing_zero_alignment_only = true });
            animation.Events[0].SetParameterBytes(changed.BigEndian, oldBytes);
        }
        Require(Snapshot(original) == Snapshot(changed), "AUDIT_FAILED", "Original TAE events, headers, flags, or groups changed.");
        Require(changed.Write().SequenceEqual(originalBytes), "AUDIT_FAILED", "Original TAE cannot be restored byte-identically after removing only the additions.");
    }

    static void Execute(string[] args)
    {
        var arguments = Arguments(args);
        string input = SafePath(arguments["--input"]), output = SafePath(arguments["--output"]), planPath = SafePath(arguments["--plan"]), game = SafePath(arguments["--game-dir"]), reportPath = SafePath(arguments["--report"]);
        Require(File.Exists(input) && File.Exists(planPath) && Directory.Exists(game), "PATH_UNSAFE", "Input, plan, and game directory must exist.");
        ValidateOutput(output, game, input, planPath, reportPath);
        ValidateOutput(reportPath, game, input, planPath, output);
        Plan plan = ReadPlan(planPath);
        byte[] sourceBytes = ReadBounded(input, MaxInputBytes, "SOURCE_SIZE");
        string sourceHash = Sha(sourceBytes);
        Require(sourceHash == plan.SourceHash, "SOURCE_HASH", "Input SHA-256 does not match the approved plan.");
        Oodle.SearchPaths.Add(game);
        BND4 source = BND4.Read(sourceBytes);
        // Reject unsupported or lossy source encodings before making any change.
        byte[] noOp = source.Write();
        Require(sourceBytes.SequenceEqual(noOp), "ROUNDTRIP_FAILED", "Original binder does not roundtrip byte-identically with this pinned library.");
        VerifyBinder(source, BND4.Read(noOp), new());
        var taes = source.Files.Select((file, index) => (file, index)).Where(x => x.file.Name?.EndsWith(".tae", StringComparison.OrdinalIgnoreCase) == true)
            .Select(x => (x.file, x.index, tae: TAE.Read(x.file.Bytes))).ToList();
        var soundIds = plan.Operations.Select(o => o.SoundId).ToHashSet();
        foreach (var item in taes)
        foreach (var animation in item.tae.Animations)
        foreach (var ev in animation.Events)
        {
            // 128..134 are the game's sound rows; SoundType/SoundID are their first two int32 values.
            if (ev.Type is < 128 or > 134) continue;
            byte[] parameters = ev.GetParameterBytes(item.tae.BigEndian);
            Require(parameters.Length < 8 || !soundIds.Contains(ReadInt(parameters, 4, item.tae.BigEndian)), "SOUND_COLLISION", "A requested SoundID already exists in a TAE sound row.");
        }
        var changedIndices = new HashSet<int>();
        var originals = new Dictionary<int, TAE>();
        var memberReports = new List<object>();
        var paddingAdjustments = new List<object>();
        // Validate every target before mutating the in-memory binder.
        foreach (var op in plan.Operations)
        {
            var matches = taes.Where(x => x.tae.ID == op.TaeId).ToList();
            Require(matches.Count == 1, "TAE_COUNT", $"Expected one TAE with ID {op.TaeId}; found {matches.Count}.");
            Require(matches[0].tae.Animations.Count(a => a.ID == op.AnimationId) == 1, "ANIMATION_COUNT", $"Expected one animation {op.AnimationId} in TAE {op.TaeId}.");
            changedIndices.Add(matches[0].index);
        }
        foreach (int index in changedIndices.Order())
        {
            var item = taes.Single(x => x.index == index);
            TAE original = TAE.Read(item.file.Bytes);
            Require(original.Write().SequenceEqual(item.file.Bytes), "ROUNDTRIP_FAILED", "A target TAE does not roundtrip byte-identically.");
            originals.Add(index, original);
            var operations = plan.Operations.Where(o => o.TaeId == item.tae.ID).ToArray();
            foreach (var op in operations)
            {
                var animation = item.tae.Animations.Single(a => a.ID == op.AnimationId);
                var group = new TAE.EventGroup(128);
                animation.EventGroups.Add(group);
                animation.Events.Add(new TAE.Event(op.Start, op.End, 128, 0, Parameters(op.SoundId, item.tae.BigEndian), item.tae.BigEndian) { Group = group });
            }
            byte[] changedBytes = item.tae.Write();
            VerifyTae(original, TAE.Read(changedBytes), item.file.Bytes, operations, paddingAdjustments);
            memberReports.Add(new { member_index = index, member_id = item.file.ID, member_name = item.file.Name, tae_id = item.tae.ID, source_sha256 = Sha(item.file.Bytes), output_sha256 = Sha(changedBytes), inserted_event_count = operations.Length });
            item.file.Bytes = changedBytes;
        }
        byte[] outputBytes = source.Write();
        BND4 result = BND4.Read(outputBytes);
        BND4 untouchedSource = BND4.Read(sourceBytes);
        VerifyBinder(untouchedSource, result, changedIndices);
        foreach (int index in changedIndices)
            VerifyTae(originals[index], TAE.Read(result.Files[index].Bytes), untouchedSource.Files[index].Bytes, plan.Operations.Where(o => o.TaeId == originals[index].ID).ToArray());
        var report = new
        {
            schema_version = 1, source_sha256 = sourceHash, output_sha256 = Sha(outputBytes), source_bytes = sourceBytes.Length, output_bytes = outputBytes.Length,
            binder_member_count = source.Files.Count, changed_member_count = changedIndices.Count, inserted_event_count = plan.Operations.Count,
            source_noop_roundtrip_byte_identical = true, all_original_events_headers_groups_unchanged = true, all_other_binder_members_unchanged = true,
            operations = plan.Operations.Select(o => new { tae_id = o.TaeId, animation_id = o.AnimationId, event_type = 128, sound_type = 1, sound_id = o.SoundId, start_seconds = o.Start, end_seconds = o.End, parameters_hex = Convert.ToHexString(Parameters(o.SoundId, false)).ToLowerInvariant() }),
            changed_members = memberReports, alignment_padding_adjustments = paddingAdjustments
        };
        Publish(output, outputBytes, reportPath, JsonSerializer.SerializeToUtf8Bytes(report, JsonOptions), game, input, planPath);
        Console.WriteLine($"TAE_PATCH_OK {plan.Operations.Count} events inserted; {changedIndices.Count}/{source.Files.Count} binder members changed.");
    }

    static void Publish(string output, byte[] outputBytes, string report, byte[] reportBytes, string game, string input, string plan)
    {
        ValidateOutput(output, game, input, plan, report);
        ValidateOutput(report, game, input, plan, output);
        string outputTemp = Path.Combine(Path.GetDirectoryName(output)!, $".nuv-tae-{Guid.NewGuid():N}.tmp");
        string reportTemp = Path.Combine(Path.GetDirectoryName(report)!, $".nuv-tae-{Guid.NewGuid():N}.tmp");
        bool reportPublished = false;
        try
        {
            WriteNew(outputTemp, outputBytes);
            WriteNew(reportTemp, reportBytes);
            // Repeat path checks after staging; the final moves never overwrite existing files.
            ValidateOutput(output, game, input, plan, report);
            ValidateOutput(report, game, input, plan, output);
            File.Move(reportTemp, report, false);
            reportPublished = true;
            File.Move(outputTemp, output, false);
        }
        catch
        {
            if (reportPublished) File.Delete(report);
            throw;
        }
        finally
        {
            if (File.Exists(outputTemp)) File.Delete(outputTemp);
            if (File.Exists(reportTemp)) File.Delete(reportTemp);
        }
    }

    static void WriteNew(string path, byte[] bytes)
    {
        using var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        stream.Write(bytes);
        stream.Flush(true);
    }
}
