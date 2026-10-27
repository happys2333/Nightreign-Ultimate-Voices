import struct
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class ArchiveTests(unittest.TestCase):
    def test_selective_extract_decrypts_ranges_and_trims_padding(self):
        from nuv.archive import Archive, path_hash
        clear = b"a native soundbank" + bytes(14)
        key = bytes(range(16))
        encryptor = Cipher(algorithms.AES(key), modes.ECB()).encryptor()
        payload = encryptor.update(clear) + encryptor.finalize()
        header = bytearray(136)
        struct.pack_into("<4sbbbbIIIII", header, 0, b"BHD5", -1, 1, 0, 0, 1, 136, 1, 28, 0)
        struct.pack_into("<II", header, 28, 1, 36)
        struct.pack_into("<Qiiqqq", header, 36, path_hash("/cs_main.bnk"), 32, 18, 0, 0, 76)
        header[76:92] = key
        struct.pack_into("<Iqq", header, 92, 1, 0, 32)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sd.bhd").write_bytes(header)
            (root / "sd.bdt").write_bytes(payload)
            archive = Archive(root / "sd.bhd")
            self.assertEqual(archive.read("cs_main.bnk"), b"a native soundbank")
            with self.assertRaises(FileNotFoundError):
                archive.read("missing.bnk")

    def test_rejects_corrupt_offsets_before_reading_payload(self):
        from nuv.archive import Archive
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sd.bhd").write_bytes(b"BHD5" + bytes(24))
            (root / "sd.bdt").write_bytes(b"x")
            with self.assertRaises(ValueError):
                Archive(root / "sd.bhd")

    def test_hash_normalizes_game_paths(self):
        from nuv.archive import path_hash
        self.assertEqual(path_hash("CS_MAIN.BNK"), path_hash("/cs_main.bnk"))
        self.assertEqual(path_hash("sd\\cs_main.bnk"), path_hash("/sd/cs_main.bnk"))

    def test_zero_unpadded_size_in_data_archive_uses_stored_size(self):
        from nuv.archive import Archive, path_hash
        header = bytearray(76)
        struct.pack_into("<4sbbbbIIIII", header, 0, b"BHD5", -1, 1, 0, 0, 1, 76, 1, 28, 0)
        struct.pack_into("<II", header, 28, 1, 36)
        struct.pack_into("<Qiiqqq", header, 36, path_hash("/chr/player"), 4, 0, 0, 0, 0)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data.bhd").write_bytes(header)
            (root / "data.bdt").write_bytes(b"BND4")
            self.assertEqual(Archive(root / "data.bhd").read("/chr/player"), b"BND4")
