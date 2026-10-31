# Nexus resource package revision

User direction: compare other Nightreign mods and adopt their straightforward distribution model. No support email is authorized.

References checked: Wylder sound effect pack (Nexus 716) previews one sd/hero01.bnk; Bloodborne Dash and Hybrid Combat SFX (Nexus 787) previews chr animation plus sd/cs_main.bnk, and documents ME3 installation and a separate MMV compatibility file. Their downloadable status does not establish why our original uploads were quarantined. Reproduction: Native 4826 and Toolkit 4828 remain quarantined, while MMV 4827 and Audio Sources 4829 are downloadable.

Design: add a Native-Resources packaging variant containing the same 24 verified game resources, two ME3 profiles, bilingual instructions, customization guide, credits/license and checksums. It has no CMD/BAT/PS1/Python/C#/EXE/DLL payload and does not replace any game code or change audio. Launch through installed ME3; profiles retain relative paths and documented save settings. Keep existing released artifacts and quarantined uploads intact. Code/build toolkit remains on GitHub for customization.

Implementation: add an explicit --resource-only packaging option valid only with Native; use dedicated installation templates; emit a distinctly named ZIP, metadata and receipt. Verify exact resource identity, archive whitelist, CRC, hashes and relocated ME3 parsing before upload. Publish this documented packaging revision once, then inspect actual Nexus status. Do not claim removal of scripts guarantees approval, conceal file types or repeatedly repackage to defeat scanning. If Nexus still quarantines the revision, preserve it and report the need for moderator review.

Public docs: recommend Native-Resources for normal users, preserve MMV guidance and custom-audio instructions, keep old launcher package identifiable, accurately report the platform's current state. Update GitHub main and release links. No game launch or gameplay retesting is necessary because game resource bytes are unchanged.
