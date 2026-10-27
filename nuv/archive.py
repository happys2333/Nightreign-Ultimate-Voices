"""Selective, read-only Nightreign BHD5/BDT extraction (Elden Ring layout).

Format reference: SoulsFormatsNEXT BHD5, MIT, Joseph Anderson et al.
Only requested files are read from the multi-gigabyte data archives.
"""
from dataclasses import dataclass
from pathlib import Path
import struct

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

MAX_HEADER = 32 * 1024 * 1024
MAX_RESOURCE = 512 * 1024 * 1024


def path_hash(path: str) -> int:
    value = 0
    path = "/" + path.strip().replace("\\", "/").lower().lstrip("/")
    for character in path:
        value = (value * 133 + ord(character)) & 0xFFFFFFFFFFFFFFFF
    return value


def _unpack(data: bytes, fmt: str, offset: int):
    if offset < 0 or offset + struct.calcsize(fmt) > len(data):
        raise ValueError("Archive header points outside its data")
    return struct.unpack_from(fmt, data, offset)


def decrypt_header(data: bytes, public_key: bytes) -> bytes:
    key = serialization.load_pem_public_key(public_key).public_numbers()
    block_size = (key.n.bit_length() + 7) // 8
    if not data or len(data) % block_size:
        raise ValueError("Invalid RSA archive header block length")
    output = bytearray()
    for offset in range(0, len(data), block_size):
        block = int.from_bytes(data[offset:offset + block_size], "big")
        if block >= key.n:
            raise ValueError("RSA archive block exceeds public modulus")
        output.extend(pow(block, key.e, key.n).to_bytes(block_size - 1, "big"))
    return bytes(output)


@dataclass(frozen=True)
class Entry:
    offset: int
    padded: int
    size: int
    key: bytes | None
    ranges: tuple[tuple[int, int], ...]


class Archive:
    def __init__(self, header: Path, public_key: bytes | None = None):
        self.header = Path(header)
        self.data_path = self.header.with_suffix(".bdt")
        if self.header.stat().st_size > MAX_HEADER:
            raise ValueError("Archive header exceeds size limit")
        data = self.header.read_bytes()
        if data[:4] != b"BHD5":
            if public_key is None:
                raise ValueError(f"RSA public key required for {self.header.name}")
            data = decrypt_header(data, public_key)
        magic, endian, _, reserved, version = _unpack(data, "<4sbBHI", 0)
        if magic != b"BHD5" or endian != -1 or reserved != 0 or version != 1:
            raise ValueError("Unsupported BHD5 layout")
        is64 = len(data) > 40 and _unpack(data, "<I", 20)[0] == 0 and _unpack(data, "<I", 28)[0] == 0
        count, table = _unpack(data, "<qq" if is64 else "<ii", 16)
        if not 0 < count <= 1_000_000:
            raise ValueError("Invalid BHD5 bucket count")
        self.entries: dict[int, Entry] = {}
        file_size = self.data_path.stat().st_size
        for index in range(count):
            if is64:
                number, flag, offset = _unpack(data, "<iiq", table + index * 16)
                if flag != 1:
                    raise ValueError("Unsupported BHD5 bucket flag")
            else:
                number, offset = _unpack(data, "<ii", table + index * 8)
            if not 0 <= number <= 1_000_000:
                raise ValueError("Invalid BHD5 file count")
            for entry_index in range(number):
                hashed, padded, size, start, _, key_offset = _unpack(data, "<Qiiqqq", offset + entry_index * 40)
                if not 0 <= size <= padded or start < 0 or start + padded > file_size:
                    raise ValueError("Invalid BDT resource bounds")
                key, ranges = None, []
                if key_offset:
                    key, range_count = _unpack(data, "<16sI", key_offset)
                    if range_count > 100_000:
                        raise ValueError("Invalid AES range count")
                    previous = -1
                    for range_index in range(range_count):
                        begin, end = _unpack(data, "<qq", key_offset + 20 + range_index * 16)
                        if begin == -1 and end == -1:
                            continue
                        if begin < 0 or end < begin or end > padded or (end - begin) % 16 or begin < previous:
                            raise ValueError("Invalid AES encrypted range")
                        ranges.append((begin, end))
                        previous = end
                if hashed in self.entries:
                    raise ValueError("Duplicate archive path hash")
                self.entries[hashed] = Entry(start, padded, size, key, tuple(ranges))

    def read(self, name: str) -> bytes:
        try:
            entry = self.entries[path_hash(name)]
        except KeyError:
            raise FileNotFoundError(f"{name} is absent from {self.header.name}") from None
        if entry.padded > MAX_RESOURCE:
            raise ValueError("Requested archive resource exceeds size limit")
        with self.data_path.open("rb") as stream:
            stream.seek(entry.offset)
            data = bytearray(stream.read(entry.padded))
        if len(data) != entry.padded:
            raise ValueError("Truncated BDT resource")
        if entry.key:
            for begin, end in entry.ranges:
                decryptor = Cipher(algorithms.AES(entry.key), modes.ECB()).decryptor()
                data[begin:end] = decryptor.update(data[begin:end]) + decryptor.finalize()
        return bytes(data[:entry.size or entry.padded])
