"""The game resolves TAE events through these catalogs before Wwise sees them."""
from copy import deepcopy
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from nuv.build import event_hash

SBI = "sound/soundbanksinfo.mobnkinfo"
EIB = "sound/eventinfo.eib"


def sound_key(sid, stop=False):
    return (1 << 35) | sid | ((1 << 39) if stop else 0)


def catalogs(template="Play_c000207103",bank_id=10):
    # Two SBI sections, including an untouched language-specific bank.
    data = bytearray(136)
    struct.pack_into("<4sIQQ",data,0,b"SBI\0",0x10000,24,2)
    struct.pack_into("<16sQQ",data,24,b"A"*16,2,88)
    struct.pack_into("<16sQQ",data,56,b"B"*16,1,120)
    for at,bid,entries in [(88,bank_id,[(event_hash(template),0),(event_hash(template.replace("Play_","Stop_",1)),0)]),
                           (104,bank_id+10,[(123,1)]),(120,30,[(456,0)])]:
        entries = sorted(entries)
        struct.pack_into("<IIQ",data,at,bid,len(entries),len(data))
        data.extend(b"".join(struct.pack("<II",*e) for e in entries))
    eib = bytearray(56)
    struct.pack_into("<4sIQQQQ",eib,0,b"WWEI",0x80000,2,0,0,2)
    for i in range(2):
        header = len(eib)
        entries = sorted([(sound_key(int(template.removeprefix("Play_c")),bool(i)),0),(sound_key(307110,bool(i)),1)])
        eib.extend(struct.pack("<IIQQ",len(entries),i,header+24,header+24+len(entries)*8))
        eib.extend(b"".join(struct.pack("<Q",k) for k,_ in entries))
        eib.extend(bytes(v for _,v in entries))
        eib.extend(bytes(-len(eib)%8))
        struct.pack_into("<Q",eib,40+i*8,header)
    struct.pack_into("<Q",eib,24,len(eib))
    return bytes(data),bytes(eib)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.sbi,self.eib = catalogs()
        self.requests = [{"bank_id":10,"event_name":"Play_c900207000", "template_name":"Play_c000207103"}]

    def test_new_tae_event_is_unregistered_even_when_its_wwise_event_exists(self):
        from nuv.registry import verify_routes
        # This is the missing boundary in the original isolated SDK tests.
        with self.assertRaisesRegex(ValueError,"unregistered"):
            verify_routes(self.sbi,self.eib,self.requests)

    def test_registers_play_routes_without_changing_existing_or_localized_entries(self):
        from nuv.registry import register_events,verify_routes,SoundBankIndex,EventInfo
        outputs,report = register_events(self.sbi,self.eib,self.requests)
        self.assertEqual(verify_routes(outputs[SBI],outputs[EIB],self.requests),1)
        old,new = SoundBankIndex(self.sbi),SoundBankIndex(outputs[SBI])
        target = next(r for r in new.records if r.bank_id==10)
        expected = sorted(old.records[0].entries+((event_hash("Play_c900207000"),0),))
        self.assertEqual(list(target.entries),expected)
        for before,after in zip(old.records[1:],new.records[1:]):
            self.assertEqual(before,after)
        source_info,output_info = EventInfo(self.eib),EventInfo(outputs[EIB])
        self.assertEqual(source_info.tables[1],output_info.tables[1])
        for key,value in source_info.tables[0].items():
            self.assertEqual(output_info.tables[0][key],value)
        self.assertNotIn(sound_key(900207000,True),output_info.tables[1])
        self.assertEqual(report["registered_events"],1)
        self.assertTrue(report["all_original_routes_preserved"])

    def test_refuses_missing_templates_unknown_banks_and_duplicate_requests(self):
        from nuv.registry import register_events
        for change in ({"bank_id":999},{"template_name":"Play_c000999999"},
                       {"event_name":"Stop_c900207000"},{"event_name":"Play_c000207103"}):
            req = {**self.requests[0],**change}
            with self.subTest(change=change),self.assertRaises(ValueError):
                register_events(self.sbi,self.eib,[req])
        with self.assertRaises(ValueError):
            register_events(self.sbi,self.eib,self.requests*2)

    def test_rejects_malformed_headers_sizes_and_out_of_bounds_tables(self):
        from nuv.registry import register_events
        corruptions = []
        for offset,fmt,value in [(4,"<I",0),(16,"<Q",999999),(48,"<Q",9999999),(96,"<Q",9999999)]:
            data = bytearray(self.sbi);struct.pack_into(fmt,data,offset,value)
            corruptions.append((bytes(data),self.eib))
        for offset,fmt,value in [(4,"<I",0),(24,"<Q",3),(40,"<Q",9999999),(56,"<I",999999)]:
            data = bytearray(self.eib);struct.pack_into(fmt,data,offset,value)
            corruptions.append((self.sbi,bytes(data)))
        for a,b in corruptions:
            with self.subTest(a=a[:8],b=b[:8]),self.assertRaises(ValueError):
                register_events(a,b,self.requests)

    def test_reads_effective_metadata_override_and_refuses_other_resources(self):
        from nuv.game import Resources
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);game=root/"game";game.mkdir()
            first,last=root/"first",root/"last"
            for folder,data in ((first,b"first"),(last,b"last")):
                path=folder/SBI;path.parent.mkdir(parents=True);path.write_bytes(data)
            with patch("nuv.game.effective_packages",return_value=[first,last]):
                resources=Resources(game,root/"profile.me3")
            value,origin=resources.read_sound_metadata(SBI)
            self.assertEqual(value,b"last")
            self.assertEqual(Path(origin),last/SBI)
            with self.assertRaises(ValueError):
                resources.read_sound_metadata("regulation.bin")

    def test_valid_empty_native_bank_record_is_preserved(self):
        from nuv.registry import register_events,SoundBankIndex
        data=bytearray(self.sbi)
        struct.pack_into("<IQ",data,108,0,0)
        outputs,_=register_events(bytes(data),self.eib,self.requests)
        self.assertEqual(SoundBankIndex(outputs[SBI]).bank(20).entries,())
