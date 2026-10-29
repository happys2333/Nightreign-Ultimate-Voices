# Overwatch Ultimate Voices — MMVWeaponsMerge Add-on 0.1.0 Beta

Prebuilt add-on for the exact locally tested MMV animation base. No Python, SDK, compiler or Overwatch installation is needed. Voice assets, timings and patched game-resource bytes are identical to the existing tested package.

Requires Nightreign 1.3.3.0 and an existing working MMV/ME3 setup. The original, unpatched MMV chr/c0000.anibnd.dcx must hash to:

`0eafca3631ddbbf3b2ec67edb49068bdc4ebcf5e4d48b2b1720a0a1c2921be69`

This is the input hash, not the supplied patched file's hash. Do not apply it to a different animation base just because its name contains MMV.

Place the `UltimateVoices-MMV` folder beside your existing ME3 profile. Copy your original working profile and append the package block from ME3-PACKAGE.txt to the copy. Update the path if necessary. The example requires the existing MMV package ID to be MMVWeaponsMerge; change load_after to its actual ID if different. Start the profile copy, keeping its existing save/co-op/translation settings. Do not load another Ultimate Voices variant at the same time.

There is no standalone launcher for this variant: it depends on your existing MMV profile and other resources. It includes the patched animation bundle derived from the specified MMV input, not a complete MMV installation. No co-op DLL, other required MMV resources, translations, saves or personal profiles are bundled.

Mapping: Wylder/Anran, Guardian/Doomfist, Ironeye/Hanzo, Duchess/Zenyatta (friendly), Raider/Reinhardt, Recluse/Doctrine, Revenant/Ana (friendly recipient), Executor/Winston (shared activation roar), Scholar/Sombra, Undertaker/Shion. Other selected spoken clips use the enemy version. Guardian and Ironeye speak at accepted action start; Scholar at recovery around 3.3 seconds. Dedicated original shouts are isolated while skill effects remain.

The local tester reported no issues observed on 28 October 2026. Full branch, mixed-install distance and frame-time matrices remain incomplete. Each installed client uses its own audio; unmodified teammates receive no voice-file transmission. Restore the original profile or remove the package entry to disable the add-on. Do not overwrite the original MMV folder. See CREDITS.txt. No public upload has been performed.
