"""Build-time registration in Nightreign's SBI and WWEI game catalogs.

Wwise's Event objects alone do not populate these game-side lookups. Original
catalog bytes stay in place; changed arrays are appended and pointers updated.
"""
from dataclasses import dataclass
import re
import struct

from .build import digest,event_hash

SBI = "sound/soundbanksinfo.mobnkinfo"
EIB = "sound/eventinfo.eib"
MAX_BYTES = 4*1024*1024


def _read(data,fmt,offset):
    if offset < 0 or offset+struct.calcsize(fmt)>len(data):
        raise ValueError("Sound catalog points outside its data")
    return struct.unpack_from(fmt,data,offset)


def _bounded(data):
    if not 56<=len(data)<=MAX_BYTES:
        raise ValueError("Sound catalog exceeds its size bounds")


@dataclass(frozen=True)
class BankRecord:
    section: int
    record_offset: int
    bank_id: int
    entries: tuple[tuple[int,int],...]


class SoundBankIndex:
    def __init__(self,data: bytes):
        _bounded(data)
        if _read(data,"<4sIQQ",0)!=(b"SBI\0",0x10000,24,2):
            raise ValueError("Unsupported soundbank index format")
        self.records=[]
        for section in range(2):
            count,table = _read(data,"<QQ",24+section*32+16)
            if not 0<count<=10000 or table<88 or table+count*16>len(data):
                raise ValueError("Invalid soundbank index table")
            previous=-1
            for i in range(count):
                at=table+i*16
                bank,n,offset=_read(data,"<IIQ",at)
                valid_array = (n==0 and offset==0) or (offset>=88 and offset%8==0 and offset+n*8<=len(data))
                if bank<=previous or n>100000 or not valid_array:
                    raise ValueError("Invalid soundbank index record")
                previous=bank
                entries=tuple(_read(data,"<II",offset+j*8) for j in range(n))
                if any(flag not in (0,1) for _,flag in entries) or any(a[0]>=b[0] for a,b in zip(entries,entries[1:])):
                    raise ValueError("Soundbank events must have unique sorted IDs and known flags")
                self.records.append(BankRecord(section,at,bank,entries))

    def bank(self,bid):
        rows=[r for r in self.records if r.bank_id==bid]
        if len(rows)!=1:
            raise ValueError("Expected one unambiguous bank in the game sound index")
        return rows[0]


class EventInfo:
    def __init__(self,data: bytes):
        _bounded(data)
        if (_read(data,"<4sIQQ",0)!=(b"WWEI",0x80000,2,0)
                or _read(data,"<QQ",24)!=(len(data),2)):
            raise ValueError("Unsupported game event catalog format or size")
        self.tables=[]
        for i in range(2):
            header,=_read(data,"<Q",40+i*8)
            n,flag,keys,values=_read(data,"<IIQQ",header)
            if (header<56 or header%8 or flag!=i or not 0<n<=100000
                    or keys<56 or keys%8 or keys+n*8>len(data)
                    or values<56 or values+n>len(data)):
                raise ValueError("Invalid game event catalog table")
            entries=[(_read(data,"<Q",keys+j*8)[0],data[values+j]) for j in range(n)]
            if any(a[0]>=b[0] for a,b in zip(entries,entries[1:])):
                raise ValueError("Game event keys must be unique and sorted")
            self.tables.append(dict(entries))


def _requests(requests):
    if not isinstance(requests,list) or not 1<=len(requests)<=32:
        raise ValueError("Expected 1 to 32 new Play event registrations")
    seen=set()
    for request in requests:
        bid=request["bank_id"]
        if isinstance(bid,bool) or not isinstance(bid,int) or not 0<bid<=0xFFFFFFFF:
            raise ValueError("Invalid registered bank ID")
        names=[request.get(key) for key in ("event_name","template_name")]
        if any(not isinstance(n,str) or not re.fullmatch(r"Play_c\d{9}",n) for n in names):
            raise ValueError("Only character Play events may be registered")
        name,template=names
        eid=event_hash(name)
        if eid in seen or name==template:
            raise ValueError("Duplicate or existing event registration")
        seen.add(eid)
        # Existing WWEI keys can contain extra bits. Only the canonical cSound
        # key is constructed; every unrelated 64-bit key is kept verbatim.
        sid=int(name[6:]);template_sid=int(template[6:])
        yield bid,eid,event_hash(template),(1<<35)|sid,(1<<35)|template_sid


def verify_routes(sbi: bytes,eib: bytes,requests: list[dict]) -> int:
    index,info=SoundBankIndex(sbi),EventInfo(eib)
    checked=0
    for bid,eid,_,key,_ in _requests(requests):
        if eid not in dict(index.bank(bid).entries) or key not in info.tables[0]:
            raise ValueError("New TAE sound is unregistered in the game sound catalogs")
        checked+=1
    return checked


def register_events(sbi: bytes,eib: bytes,requests: list[dict]) -> tuple[dict,dict]:
    index,info=SoundBankIndex(sbi),EventInfo(eib)
    routes=list(_requests(requests))
    occupied={eid for r in index.records for eid,_ in r.entries}
    bank_changes={}
    play=dict(info.tables[0])
    for bid,eid,template,key,template_key in routes:
        record=index.bank(bid)
        flags=dict(record.entries)
        if template not in flags or template_key not in info.tables[0]:
            raise ValueError("Native event registration template is missing")
        if eid in occupied or key in play:
            raise ValueError("New sound event is already registered")
        bank_changes.setdefault(bid,list(record.entries)).append((eid,flags[template]))
        play[key]=info.tables[0][template_key]
        occupied.add(eid)
    out_sbi=bytearray(sbi)
    allowed_sbi=set()
    for bid,entries in bank_changes.items():
        record=index.bank(bid)
        out_sbi.extend(bytes(-len(out_sbi)%8))
        offset=len(out_sbi)
        out_sbi.extend(b"".join(struct.pack("<II",*e) for e in sorted(entries)))
        struct.pack_into("<IQ",out_sbi,record.record_offset+4,len(entries),offset)
        allowed_sbi.update(range(record.record_offset+4,record.record_offset+16))
    out_eib=bytearray(eib)
    out_eib.extend(bytes(-len(out_eib)%8))
    header=len(out_eib);entries=sorted(play.items())
    out_eib.extend(struct.pack("<IIQQ",len(entries),0,header+24,header+24+len(entries)*8))
    out_eib.extend(b"".join(struct.pack("<Q",key) for key,_ in entries))
    out_eib.extend(bytes(flag for _,flag in entries))
    out_eib.extend(bytes(-len(out_eib)%8))
    struct.pack_into("<Q",out_eib,24,len(out_eib))
    struct.pack_into("<Q",out_eib,40,header)
    if max(len(out_sbi),len(out_eib))>MAX_BYTES:
        raise ValueError("Patched sound catalogs exceed their size budget")
    a,b=bytes(out_sbi),bytes(out_eib)
    new_index,new_info=SoundBankIndex(a),EventInfo(b)
    for old,new in zip(index.records,new_index.records):
        expected=tuple(sorted(bank_changes.get(old.bank_id,old.entries)))
        if old.bank_id!=new.bank_id or expected!=new.entries:
            raise ValueError("Soundbank index preservation audit failed")
    if new_info.tables[0]!=play or new_info.tables[1]!=info.tables[1]:
        raise ValueError("Game event catalog preservation audit failed")
    if (any(x!=y and i not in allowed_sbi for i,(x,y) in enumerate(zip(sbi,a)))
            or any(x!=y and i not in {*range(24,32),*range(40,48)} for i,(x,y) in enumerate(zip(eib,b)))):
        raise ValueError("Sound catalog changed unrelated original bytes")
    verify_routes(a,b,requests)
    return {SBI:a,EIB:b},{"registered_events":len(routes),"all_original_routes_preserved":True,
        "game_side_routes_verified":True,"registrations":requests,
        "files":{name:{"source_sha256":digest(old),"output_sha256":digest(new),
                       "source_bytes":len(old),"output_bytes":len(new)}
                 for name,old,new in ((SBI,sbi,a),(EIB,eib,b))}}
