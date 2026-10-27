"""Find the user's Steam installation and read the game version without launch."""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import re

from .archive import Archive, path_hash
from .profile import effective_packages

ROOT = Path(__file__).resolve().parent.parent


def find_game(explicit: str | None = None) -> Path:
    if explicit:
        candidates = [Path(explicit).expanduser()]
    else:
        libraries = []
        if os.name == "nt":
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Valve\Steam") as key:
                    libraries.append(Path(winreg.QueryValueEx(key,"SteamPath")[0]))
            except OSError:
                pass
        steam_default = Path(os.environ.get("ProgramFiles(x86)","C:/Program Files (x86)")) / "Steam"
        if steam_default not in libraries:
            libraries.append(steam_default)
        for library in tuple(libraries):
            folders = library / "steamapps/libraryfolders.vdf"
            if folders.is_file():
                text = folders.read_text(encoding="utf-8-sig")
                for path in re.findall(r'"path"\s*"([^"]+)"',text):
                    candidate = Path(path.replace("\\\\","\\"))
                    if candidate not in libraries:
                        libraries.append(candidate)
        candidates = [library / "steamapps/common/ELDEN RING NIGHTREIGN/Game" for library in libraries]
    for candidate in candidates:
        if (candidate / "nightreign.exe").is_file() and (candidate / "sd/sd.bhd").is_file():
            return candidate.resolve()
    raise FileNotFoundError("Cannot find nightreign.exe and sd/sd.bhd; specify --game-dir pointing to the Game folder")


def game_version(game: Path) -> str:
    if os.name != "nt":
        raise ValueError("Game version inspection requires Windows")
    library = ctypes.WinDLL("version",use_last_error=True)
    library.GetFileVersionInfoSizeW.argtypes=[wintypes.LPCWSTR,ctypes.POINTER(wintypes.DWORD)]
    library.GetFileVersionInfoSizeW.restype=wintypes.DWORD
    library.GetFileVersionInfoW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p]
    library.GetFileVersionInfoW.restype=wintypes.BOOL
    library.VerQueryValueW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(wintypes.UINT)]
    library.VerQueryValueW.restype=wintypes.BOOL
    executable = str(game / "nightreign.exe")
    unused = wintypes.DWORD()
    size = library.GetFileVersionInfoSizeW(executable,ctypes.byref(unused))
    if not size:
        raise ValueError("Cannot read nightreign.exe file version")
    data = ctypes.create_string_buffer(size)
    if not library.GetFileVersionInfoW(executable,0,size,data):
        raise ValueError("Cannot read nightreign.exe version resource")
    pointer, length = ctypes.c_void_p(),wintypes.UINT()
    if not library.VerQueryValueW(data,"\\",ctypes.byref(pointer),ctypes.byref(length)) or length.value < 24:
        raise ValueError("Invalid nightreign.exe version resource")
    values = ctypes.cast(pointer,ctypes.POINTER(wintypes.DWORD))
    if values[0] != 0xFEEF04BD:
        raise ValueError("Invalid game version signature")
    high,low=values[2],values[3]
    return f"{high >> 16}.{high & 65535}.{low >> 16}.{low & 65535}"


class Resources:
    def __init__(self,game: Path,base_profile: Path | None):
        self.game=game
        self.packages=effective_packages(base_profile) if base_profile else []
        self.archives=[]
        key=(ROOT / "config/keys/sd.pem").read_bytes()
        for name in ("sd/sd_dlc01.bhd","sd/sd.bhd"):
            header=game/name
            if header.is_file():
                self.archives.append(Archive(header,key))

    def read_bank(self,name: str) -> tuple[bytes,str]:
        if not re.fullmatch(r"sd/hero(?:0[1-9]|10)\.bnk",name):
            raise ValueError("Only verified hero soundbanks may be overridden")
        for package in reversed(self.packages):
            target=package/name
            if target.is_file():
                return target.read_bytes(),str(target)
        loose=self.game/name
        if loose.is_file():
            return loose.read_bytes(),str(loose)
        for archive in self.archives:
            if path_hash(Path(name).name) in archive.entries:
                return archive.read(Path(name).name),str(archive.header)
        raise FileNotFoundError(f"Cannot locate native bank {name}")

    def read_animation_bundle(self) -> tuple[bytes,str]:
        name = "chr/c0000.anibnd.dcx"
        for package in reversed(self.packages):
            target = package/name
            if target.is_file():
                return target.read_bytes(), str(target)
        loose = self.game/name
        if loose.is_file():
            return loose.read_bytes(), str(loose)
        header = self.game/"Data3.bhd"
        if header.is_file():
            key = (ROOT/"config/keys/data3.pem").read_bytes()
            archive = Archive(header, key)
            return archive.read(name), str(header)
        raise FileNotFoundError("Cannot locate the effective player animation bundle chr/c0000.anibnd.dcx")
