using SoulsFormats;
using System.Buffers.Binary;
using System.Text.Json;

if (args[0] == "create")
{
    var binder = new BND4 { Version = "260102" };
    foreach (var (taeID, animationIDs) in new[] { (2901, new[] { 610000, 615000 }), (2902, new[] { 620000, 620005 }), (2908, new[] { 680000 }) })
    {
        var tae = new TAE { ID = taeID, Format = TAE.TAEFormat.SDT, Flags = new byte[8], EventBank = 0, SkeletonName = "skeleton", SibName = "fixture.sib", Animations = new() };
        foreach (int id in animationIDs)
        {
            var animation = new TAE.Animation(id, new TAE.Animation.AnimMiniHeader.Standard { AllowDelayLoad = true }, $"a{taeID - 2000}_{id}.hkt");
            var group = new TAE.EventGroup(128);
            animation.EventGroups.Add(group);
            var parameters = new byte[8];
            BinaryPrimitives.WriteInt32LittleEndian(parameters, 1);
            BinaryPrimitives.WriteInt32LittleEndian(parameters.AsSpan(4), args[2].StartsWith("collision") ? 900207000 : 207100 + id);
            animation.Events.Add(new TAE.Event(.2f, .3f, args[2] == "collision-134" ? 134 : 128, 0, parameters, false) { Group = group });
            tae.Animations.Add(animation);
        }
        if (args[2] == "duplicate-animation" && taeID == 2901)
            tae.Animations.Insert(0, tae.Animations[0]);
        binder.Files.Add(new BinderFile(Binder.FileFlags.Flag1, taeID, $"N:\\chr\\a{taeID - 2000}.tae", tae.Write()));
    }
    if (args[2] == "duplicate-tae")
        binder.Files.Add(new BinderFile(Binder.FileFlags.Flag1, 9999, "N:\\other.tae", binder.Files[0].Bytes));
    binder.Files.Add(new BinderFile(Binder.FileFlags.Flag1, 12, "N:\\unrelated.hkx", new byte[] { 7, 2, 3, 4 }));
    binder.Write(args[1]);
    return 0;
}

if (args[0] == "audit")
{
    if (args.Length > 4) Oodle.SearchPaths.Add(args[4]);
    var before = BND4.Read(args[1]);
    var after = BND4.Read(args[2]);
    using var plan = JsonDocument.Parse(File.ReadAllBytes(args[3]));
    var operations = plan.RootElement.GetProperty("operations").EnumerateArray().ToArray();
    void Check(bool condition, string message) { if (!condition) throw new Exception(message); }
    Check(before.Files.Count == after.Files.Count, "member count changed");
    int additionCount = 0;
    int changedMembers = 0;
    for (int i = 0; i < before.Files.Count; i++)
    {
        var a = before.Files[i]; var b = after.Files[i];
        Check(a.ID == b.ID && a.Name == b.Name && a.Flags == b.Flags && a.CompressionInfo.GetType() == b.CompressionInfo.GetType(), "member metadata changed");
        if (a.Bytes.SequenceEqual(b.Bytes)) continue;
        changedMembers++;
        Check(a.Name.EndsWith(".tae"), "non-TAE changed");
        var original = TAE.Read(a.Bytes); var changed = TAE.Read(b.Bytes);
        var selected = operations.Where(o => o.GetProperty("tae_id").GetInt32() == original.ID).ToArray();
        Check(selected.Length > 0, "unexpected changed TAE");
        foreach (var op in selected.Reverse())
        {
            var animation = changed.Animations.Single(x => x.ID == op.GetProperty("animation_id").GetInt32());
            var originalAnimation = original.Animations.Single(x => x.ID == animation.ID);
            var row = animation.Events[^1];
            var group = animation.EventGroups[^1];
            var bytes = row.GetParameterBytes(changed.BigEndian);
            Check(row.Type == 129 && row.Unk04 == 0 && bytes.Length == 32, "incorrect BySlot row type/size");
            Check(BinaryPrimitives.ReadInt32LittleEndian(bytes) == 1 && BinaryPrimitives.ReadInt32LittleEndian(bytes.AsSpan(4)) == op.GetProperty("sound_id").GetInt32(), "incorrect sound mapping");
            Check(bytes.AsSpan(8).SequenceEqual(Convert.FromHexString("FFFFFFFFFFFFFFFF000000010100000000000000FF000000")), "incorrect one-shot, slot, or sound ID offset settings");
            Check(row.StartTime == (float)op.GetProperty("start_seconds").GetDouble() && row.EndTime == (float)op.GetProperty("end_seconds").GetDouble(), "incorrect timing");
            Check(row.Group == group && group.GroupType == 128 && !originalAnimation.EventGroups.Contains(group), "incorrect event group");
            animation.Events.RemoveAt(animation.Events.Count - 1);
            animation.EventGroups.RemoveAt(animation.EventGroups.Count - 1);
            additionCount++;
        }
        foreach (var animation in changed.Animations.Where(x => selected.Any(o => o.GetProperty("animation_id").GetInt32() == x.ID)))
        {
            var oldAnimation = original.Animations.Single(x => x.ID == animation.ID);
            if (oldAnimation.Events.Count == 0) continue;
            byte[] oldBytes = oldAnimation.Events[0].GetParameterBytes(original.BigEndian);
            byte[] newBytes = animation.Events[0].GetParameterBytes(changed.BigEndian);
            if (oldBytes.SequenceEqual(newBytes)) continue;
            int common = Math.Min(oldBytes.Length, newBytes.Length);
            Check(Math.Abs(oldBytes.Length - newBytes.Length) == 8 && oldBytes.Take(common).SequenceEqual(newBytes.Take(common)) && oldBytes.Skip(common).All(x => x == 0) && newBytes.Skip(common).All(x => x == 0), "non-padding parameter difference");
            animation.Events[0].SetParameterBytes(changed.BigEndian, oldBytes);
        }
        Check(changed.Write().SequenceEqual(a.Bytes), "original TAE fields/events/groups changed");
    }
    Check(additionCount == operations.Length, "incorrect number of additions");
    Console.WriteLine(JsonSerializer.Serialize(new { addition_count = additionCount, changed_member_count = changedMembers, member_count = before.Files.Count, originals_restored_byte_identical = true }));
    return 0;
}
throw new Exception("Unknown fixture mode");
