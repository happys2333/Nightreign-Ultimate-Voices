"""Conservative offline editor for Nightreign's little-endian Wwise v135 banks.

Only chunk envelopes, HIRC envelopes, Event action lists and routing prefixes
are read. Original HIRC payloads and unknown chunks stay byte-for-byte intact.
The v135 layouts are cross-checked against bnnm/wwiser's parser/wparser.py.
"""

from dataclasses import dataclass
import hashlib
import math
import struct

from .audio import validate_pcm_wem


MAX_BANK_BYTES = 512 * 1024 * 1024
SUPPORTED_PATCH_VERSIONS = frozenset({135})


@dataclass(frozen=True)
class Chunk:
    tag: bytes
    payload: bytes


@dataclass(frozen=True)
class HircObject:
    kind: int
    id: int
    payload: bytes


def _u32(data, offset=0):
    if offset < 0 or offset + 4 > len(data):
        raise ValueError("truncated uint32 in soundbank")
    return struct.unpack_from("<I", data, offset)[0]


def _var(data, offset=0):
    value = 0
    start = offset
    for _ in range(5):
        if offset >= len(data):
            raise ValueError("truncated Event action count")
        byte = data[offset]
        offset += 1
        value = (value << 7) | (byte & 0x7F)
        if value > 0xFFFFFFFF:
            raise ValueError("Event action count overflows uint32")
        if not byte & 0x80:
            if offset - start > 1 and data[start] == 0x80:
                raise ValueError("noncanonical Event action count")
            return value, offset
    raise ValueError("invalid Event action count")


def _pack_var(value):
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.append(0x80 | (value & 0x7F))
        value >>= 7
    return bytes(reversed(out))


def _chunk_bytes(tag, payload):
    if len(payload) > 0xFFFFFFFF:
        raise ValueError("soundbank chunk exceeds uint32 size")
    return tag + struct.pack("<I", len(payload)) + payload


class Bank:
    @classmethod
    def parse(cls, data: bytes):
        if not isinstance(data, bytes) or not 8 <= len(data) <= MAX_BANK_BYTES:
            raise ValueError("invalid soundbank size")
        chunks = []
        known = {}
        cursor = 0
        while cursor < len(data):
            if len(data) - cursor < 8:
                raise ValueError("truncated soundbank chunk header")
            tag = data[cursor:cursor + 4]
            size = _u32(data, cursor + 4)
            end = cursor + 8 + size
            if end > len(data):
                raise ValueError("soundbank chunk exceeds file bounds")
            if tag in (b"BKHD", b"HIRC", b"DIDX", b"DATA"):
                if tag in known:
                    raise ValueError(f"duplicate {tag.decode()} chunk")
                known[tag] = len(chunks)
            chunks.append(Chunk(tag, data[cursor + 8:end]))
            cursor = end
        if b"BKHD" not in known or b"HIRC" not in known:
            raise ValueError("soundbank requires BKHD and HIRC")
        header = chunks[known[b"BKHD"]].payload
        if len(header) < 16:
            raise ValueError("truncated BKHD")
        bank = cls()
        bank.version = _u32(header)
        bank.bank_id = _u32(header, 4)
        bank.alignment = _u32(header, 12)
        bank._chunks = chunks
        bank._known = known
        bank._objects = []
        bank._media = {}
        bank._dirty = False
        hirc = chunks[known[b"HIRC"]].payload
        count = _u32(hirc)
        if count > (len(hirc) - 4) // 9:
            raise ValueError("HIRC object count exceeds chunk bounds")
        cursor = 4
        ids = set()
        for _ in range(count):
            if cursor + 9 > len(hirc):
                raise ValueError("truncated HIRC object header")
            kind = hirc[cursor]
            size = _u32(hirc, cursor + 1)
            end = cursor + 5 + size
            if size < 4 or end > len(hirc):
                raise ValueError("HIRC object exceeds chunk bounds")
            oid = _u32(hirc, cursor + 5)
            if oid in ids:
                raise ValueError(f"duplicate HIRC object ID {oid}")
            ids.add(oid)
            bank._objects.append(HircObject(kind, oid, hirc[cursor + 9:end]))
            cursor = end
        if cursor != len(hirc):
            raise ValueError("unparsed bytes after HIRC objects")
        bank._lookup = {item.id: item for item in bank._objects}
        if (b"DIDX" in known) != (b"DATA" in known):
            raise ValueError("DIDX and DATA must occur together")
        if b"DIDX" in known:
            index = chunks[known[b"DIDX"]].payload
            media = chunks[known[b"DATA"]].payload
            if len(index) % 12:
                raise ValueError("invalid DIDX record size")
            intervals = []
            for cursor in range(0, len(index), 12):
                mid, offset, size = struct.unpack_from("<III", index, cursor)
                if mid in bank._media:
                    raise ValueError(f"duplicate media ID {mid}")
                if offset + size > len(media):
                    raise ValueError("DIDX media exceeds DATA bounds")
                bank._media[mid] = (offset, size)
                if size:
                    intervals.append((offset, offset + size))
            intervals.sort()
            if any(left[1] > right[0] for left, right in zip(intervals, intervals[1:])):
                raise ValueError("overlapping DIDX media records")
        if 123 <= bank.version <= 154 or bank.version <= 122:
            for item in bank._objects:
                if item.kind == 4:
                    bank.event_actions(item.id)
        return bank

    @property
    def chunks(self):
        """Immutable chunk envelopes, suitable for source/output comparisons.

        Reparse ``to_bytes()`` to inspect a patched bank's final HIRC payload
        and BKHD alignment padding; those are materialized when serializing.
        """
        return tuple(self._chunks)

    @property
    def objects(self):
        return tuple(self._objects)

    @property
    def objects_by_id(self):
        return dict(self._lookup)

    @property
    def event_ids(self):
        return {item.id for item in self._objects if item.kind == 4}

    @property
    def media_ids(self):
        return set(self._media)

    def event_actions(self, event_id: int):
        item = self._lookup.get(event_id)
        if item is None or item.kind != 4:
            raise ValueError(f"Event {event_id} is absent from bank")
        if self.version <= 122:
            count, offset = _u32(item.payload), 4
        elif self.version <= 154:
            count, offset = _var(item.payload)
        else:
            raise ValueError("unsupported Event layout for bank version")
        if count > (len(item.payload) - offset) // 4 or offset + count * 4 != len(item.payload):
            raise ValueError(f"invalid action list in Event {event_id}")
        return tuple(_u32(item.payload, offset + i * 4) for i in range(count))

    def media_bytes(self, media_id: int):
        if media_id not in self._media:
            raise ValueError(f"media {media_id} is absent from bank")
        offset, size = self._media[media_id]
        return self._chunks[self._known[b"DATA"]].payload[offset:offset + size]

    def _routing_bus(self, event_id):
        objects = self._lookup
        buses = set()
        visited_events = set()

        def node_bus(oid):
            visited = set()
            while oid:
                if oid in visited:
                    raise ValueError("cycle in soundbank parent routing")
                visited.add(oid)
                node = objects.get(oid)
                if node is None or node.kind not in (2, 5, 6, 7, 9):
                    raise ValueError(f"cannot resolve output bus through object {oid}")
                payload = node.payload
                offset = 0
                if node.kind == 2:
                    plugin = _u32(payload)
                    offset = 14
                    if plugin & 0xF == 2:
                        offset += 4 + _u32(payload, offset)
                if offset + 2 > len(payload):
                    raise ValueError("truncated node FX routing prefix")
                count = payload[offset + 1]
                offset += 2 + (1 + count * 7 if count else 0) + 1
                bus, oid = _u32(payload, offset), _u32(payload, offset + 4)
                if bus:
                    buses.add(bus)
                    return
            raise ValueError("event has no resolvable output bus")

        def event_bus(eid):
            if eid in visited_events:
                raise ValueError("cycle in PlayEvent routing")
            visited_events.add(eid)
            for aid in self.event_actions(eid):
                action = objects.get(aid)
                if action is None or action.kind != 3 or len(action.payload) < 7:
                    continue
                action_type = struct.unpack_from("<H", action.payload)[0]
                target = _u32(action.payload, 2)
                if action_type == 0x0403:
                    node_bus(target)
                elif action_type == 0x2103:
                    event_bus(target)
            visited_events.remove(eid)

        event_bus(event_id)
        if len(buses) != 1:
            raise ValueError("event must resolve to one unambiguous output bus")
        return buses.pop()

    def add_voice(self, event_id: int, namespace: str, wem: bytes,
                  volume_db: float = 0.0):
        """Append one Play action to an existing Event; retain every prior action.

        Object/media IDs are deterministic per namespace. A collision or repeat
        fails before mutating the bank. New audio routes directly to the Event's
        existing bus in 2D and has no loops, states, randomization or RTPCs.
        """
        if self.version not in SUPPORTED_PATCH_VERSIONS:
            raise ValueError(f"unsupported bank version {self.version}; patching requires v135")
        if (not isinstance(namespace, str) or not namespace.strip()
                or len(namespace.encode("utf-8")) > 512
                or any(ord(char) < 32 for char in namespace)):
            raise ValueError("patch namespace must be a nonempty printable string")
        if (isinstance(volume_db, bool) or not isinstance(volume_db, (int, float))
                or not math.isfinite(volume_db) or not -60 <= volume_db <= 12):
            raise ValueError("volume must be finite and between -60 and 12 dB")
        validate_pcm_wem(wem)
        actions = self.event_actions(event_id)
        bus_id = self._routing_bus(event_id)
        ids = {}
        occupied = set(self._lookup) | self.media_ids
        for role in ("sound", "action", "media"):
            # Wwise's unnamed objects/media use 30-bit GUID-derived ShortIDs.
            # Named Events/buses retain their original full-width FNV IDs.
            value = int.from_bytes(hashlib.sha256(f"nuv/v1/{namespace}/{role}".encode("utf-8")).digest()[:4], "little") & 0x3FFFFFFF
            if not value or value in occupied or value in ids.values():
                raise ValueError(f"namespace already patched or deterministic {role} ID collision")
            ids[role] = value
        if self.alignment < 1 or self.alignment > 4096 or self.alignment & (self.alignment - 1):
            raise ValueError("unsupported bank media alignment")
        # Codec id=PCM (1), company=Audiokinetic (0), type=codec (1).
        source = struct.pack("<IBIIB", 0x00010001, 0, ids["media"], len(wem), 0)
        fx_and_routing = bytes(3) + struct.pack("<II", bus_id, 0) + b"\0"
        # AkPropBundle: Volume (0) and Loop (0x3A); explicit one-shot count=1.
        props = b"\x02\0\x3A" + struct.pack("<fI", volume_db, 1) + b"\0"
        # Position override=2D, aux override flags, reflections bus, advanced
        # settings (virtual queue=PlayFromBeginning), no states and no RTPCs.
        # Kill new duplicate instances; the single-instance limit is per game
        # object (global-limit bit stays clear), preserving simultaneous peers.
        tail = b"\x01\x14" + bytes(4) + b"\x11\0\x01\0\0\0" + bytes(4)
        sound = HircObject(2, ids["sound"], source + fx_and_routing + props + tail)
        play = struct.pack("<HIBBBB I", 0x0403, ids["sound"], 0, 0, 0, 4, self.bank_id)
        action = HircObject(3, ids["action"], play)
        event = HircObject(4, event_id, _pack_var(len(actions) + 1)
                           + b"".join(struct.pack("<I", value) for value in (*actions, ids["action"])))
        chunks = list(self._chunks)
        known = dict(self._known)
        if b"DATA" in known:
            old_data = chunks[known[b"DATA"]].payload
        else:
            insertion = known[b"HIRC"]
            chunks[insertion:insertion] = [Chunk(b"DIDX", b""), Chunk(b"DATA", b"")]
            known = {c.tag: i for i, c in enumerate(chunks) if c.tag in (b"BKHD", b"HIRC", b"DIDX", b"DATA")}
            old_data = b""
        padding = (-len(old_data)) % self.alignment
        data_offset = len(old_data) + padding
        # Calculate complete output and alignment growth before allocating DATA
        # or mutating the bank. HIRC/raw source data are still unchanged here.
        sizes = [(part.tag, len(part.payload)) for part in chunks]
        sizes[known[b"DATA"]] = (b"DATA", data_offset + len(wem))
        sizes[known[b"DIDX"]] = (b"DIDX", sizes[known[b"DIDX"]][1] + 12)
        old_event = self._lookup[event_id]
        hirc_growth = 18 + len(sound.payload) + len(action.payload) + len(event.payload) - len(old_event.payload)
        sizes[known[b"HIRC"]] = (b"HIRC", sizes[known[b"HIRC"]][1] + hirc_growth)
        # Account for prior patches whose HIRC is stored as objects until save.
        if self._dirty:
            sizes[known[b"HIRC"]] = (b"HIRC", 4 + sum(9 + len(item.payload) for item in self._objects) + hirc_growth)
        data_position = sum(size + 8 for _, size in sizes[:known[b"DATA"]]) + 8
        header_padding = (-data_position) % self.alignment
        if sum(size + 8 for _, size in sizes) + header_padding > MAX_BANK_BYTES:
            raise ValueError("patched soundbank exceeds byte budget")
        chunks[known[b"DATA"]] = Chunk(b"DATA", old_data + bytes(padding) + wem)
        media = dict(self._media)
        media[ids["media"]] = (data_offset, len(wem))
        chunks[known[b"DIDX"]] = Chunk(b"DIDX", b"".join(
            struct.pack("<III", mid, *media[mid]) for mid in sorted(media)))
        # Insert dependencies ahead of Events; leave original objects in order.
        objects = list(self._objects)
        event_index = next(i for i, item in enumerate(objects) if item.id == event_id)
        objects[event_index] = event
        objects[event_index:event_index] = [sound, action]
        self._chunks, self._known, self._objects, self._media = chunks, known, objects, media
        self._lookup = {item.id: item for item in objects}
        self._dirty = True
        return {"event_id": event_id, "sound_id": ids["sound"], "action_id": ids["action"],
                "media_id": ids["media"], "bus_id": bus_id,
                "original_action_ids": list(actions), "wem_bytes": len(wem)}

    def to_bytes(self):
        chunks = list(self._chunks)
        if self._dirty:
            hirc = struct.pack("<I", len(self._objects)) + b"".join(
                struct.pack("<BII", item.kind, len(item.payload) + 4, item.id) + item.payload
                for item in self._objects)
            chunks[self._known[b"HIRC"]] = Chunk(b"HIRC", hirc)
            # Wwise requires DATA's absolute address to honor BKHD alignment.
            position = 0
            for part in chunks:
                if part.tag == b"DATA":
                    padding = (-(position + 8)) % self.alignment
                    if padding:
                        index = self._known[b"BKHD"]
                        header = chunks[index]
                        chunks[index] = Chunk(header.tag, header.payload + bytes(padding))
                    break
                position += len(part.payload) + 8
        size = sum(len(part.payload) + 8 for part in chunks)
        if size > MAX_BANK_BYTES:
            raise ValueError("soundbank exceeds byte budget")
        return b"".join(_chunk_bytes(part.tag, part.payload) for part in chunks)
