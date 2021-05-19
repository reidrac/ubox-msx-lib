#!/usr/bin/env python3

from argparse import ArgumentParser
from collections import defaultdict
from os import path
import json
import os
import subprocess
import struct
import sys
import tempfile
import traceback

__version__ = "1.0"

DEF_ROOM_WIDTH = 32
DEF_ROOM_HEIGHT = 24
DEF_BITS = 8

DEF_MAP_CONF = "map_conf.json"

"""
Format:

           2 bytes: map data length (0 for empty map; no more data included)
            1 byte: entities length (1 is just the terminator 0xff)
  map length bytes: map data (n-bit per tile) H x W x n (may be compressed)
           i bytes: entity data (0xff for end)

Expected layers: Map and Entities
"""


def apultra_compress(data):
    with tempfile.NamedTemporaryFile() as fd:
        fd.write(bytearray(data))
        fd.flush()

        ap_name = fd.name + ".ap"
        apultra_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "bin", "apultra")
        subprocess.call([apultra_path, "-v", fd.name, ap_name], stdout=sys.stderr)

    with open(ap_name, "rb") as fd:
        out = fd.read()
    os.unlink(ap_name)

    return [int(byte) for byte in out]


def find_name(data, name):
    for item in data:
        if item.get("name").lower() == name.lower():
            return item
    raise ValueError("%r not found" % name)


def find_id(data, id):
    for item in data:
        if item.get("id") == id:
            return item
    raise ValueError("id %r not found", id)


def get_property(obj, name, default):
    props = obj.get("properties", {})

    if isinstance(props, dict):
        return props.get(name, default)

    for p in props:
        if p["name"] == name:
            return p["value"]

    return default


def main():

    parser = ArgumentParser(description="Map importer",
                            epilog="Copyright (C) 2020 Juan J Martinez <jjm@usebox.net>",
                            )

    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__)
    parser.add_argument(
        "--room-width", dest="rw", default=DEF_ROOM_WIDTH, type=int,
        help="room width (default: %s)" % DEF_ROOM_WIDTH)
    parser.add_argument(
        "--room-height", dest="rh", default=DEF_ROOM_HEIGHT, type=int,
        help="room height (default: %s)" % DEF_ROOM_HEIGHT)
    parser.add_argument("--max-ents", dest="max_ents", default=0, type=int,
                        help="max entities per room (default: unlimited)")
    parser.add_argument("--max-bytes", dest="max_bytes", default=0, type=int,
                        help="max bytes per room (default: unlimited)")
    parser.add_argument("-b", dest="bin", action="store_true",
                        help="output binary data (default: C code)")
    parser.add_argument("-d", dest="dir", default=".", type=str,
                        help="directory to generate the bin files (default: .)")
    parser.add_argument("-c", dest="conf", default=DEF_MAP_CONF, type=str,
                        help="JSON configuration file (default: %s)" % DEF_MAP_CONF)
    parser.add_argument("--aplib", dest="aplib", action="store_true",
                        help="APLIB compressed")
    parser.add_argument("-r", dest="reverse", action="store_true",
                        help="Reverse map order")
    parser.add_argument("-q", dest="quiet", action="store_true",
                        help="Don't output stats on stderr")
    parser.add_argument("map_json", help="Map to import")
    parser.add_argument("id", help="variable name")

    args = parser.parse_args()

    with open(args.conf, "rt") as fd:
        conf = json.load(fd)

    et_names = [d["name"] for d in conf["entities"]]
    et_weigths = dict((d["name"], d["w"]) for d in conf["entities"])
    et_bytes = dict((d["name"], d["bytes"]) for d in conf["entities"])

    with open(args.map_json, "rt") as fd:
        data = json.load(fd)

    mh = data.get("height", 0)
    mw = data.get("width", 0)

    if mh < args.rh or mh % args.rh:
        parser.error("Map size height not multiple of the room size")
    if mw < args.rw or mw % args.rw:
        parser.error("Map size witdh not multiple of the room size")

    tilewidth = data["tilewidth"]
    tileheight = data["tileheight"]

    tile_layer = find_name(data["layers"], "Map")["data"]

    def_tileset = find_name(data["tilesets"], "default")
    firstgid = def_tileset.get("firstgid")

    out = []
    for y in range(0, mh, args.rh):
        for x in range(0, mw, args.rw):
            block = []
            for j in range(args.rh):
                for i in range(args.rw):
                    block.append(tile_layer[x + i + (y + j) * mw] - firstgid)

            # pack
            current = []
            for i in range(0, args.rh * args.rw, 8 // DEF_BITS):
                tiles = []
                for k in range(8 // DEF_BITS):
                    tiles.append(block[i + k])

                b = 0
                pos = 8
                for k in range(8 // DEF_BITS):
                    pos -= DEF_BITS
                    b |= (tiles[k] & ((2**DEF_BITS) - 1)) << pos

                current.append(b)

            out.append(current)

    # track empty maps
    empty = []
    for i, block in enumerate(out):
        if all([byte == 0xff for byte in block]):
            empty.append(i)

    if args.aplib:
        compressed = []
        for i, block in enumerate(out):
            if i in empty:
                compressed.append(None)
                continue
            compressed.append(apultra_compress(block))
        out = compressed

    # add the map header
    for i in range(len(out)):
        if out[i] is None:
            continue
        size = len(out[i])

        # ents size placeholder 0
        out[i] = [size & 0xff, size >> 8, 0] + out[i]

    entities_layer = find_name(data["layers"], "Entities")
    if len(entities_layer):
        map_ents = defaultdict(list)
        map_ents_w = defaultdict(int)
        map_ents_bytes = defaultdict(int)
        map_ents_names = set()

        def check_bytes(name):
            if name not in map_ents_names:
                # update the entity size in bytes count per map
                try:
                    map_ents_bytes[m] += et_bytes[name]
                    map_ents_names.add(name)
                except KeyError:
                    parser.error("max_bytes: no 'bytes' found for %r" % name)

        try:
            objs = entities_layer["objects"]
            objs.sort(key=lambda o: o["y"])
            objs.sort(key=lambda o: o["x"])
            objs.sort(key=lambda o: et_names.index(o["name"].lower()))
        except ValueError:
            parser.error("map has an unnamed object")

        for obj in objs:
            name = obj["name"].lower()
            m = ((obj["x"] // tilewidth) // args.rw) \
                + (((obj["y"] // tileheight) // args.rh) * (mw // args.rw))
            x = obj["x"] % (args.rw * tilewidth)
            y = obj["y"] % (args.rh * tileheight)

            if name == "blocked":
                if obj["width"] > obj["height"]:
                    if y == 0:
                        # up blocked
                        out[m][1] |= (1 << 4)
                    else:
                        # down blocked
                        out[m][1] |= (1 << 5)
                else:
                    if x == 0:
                        # left blocked
                        out[m][1] |= (1 << 6)
                    else:
                        # tight blocked
                        out[m][1] |= (1 << 7)
                continue

            t = et_names.index(name)

            # MSB is direction

            param = int(get_property(obj, "param", 0))
            if param == 1:
                t |= 128

            if args.max_ents:
                # update the entity count per map
                try:
                    map_ents_w[m] += et_weigths[name]
                except KeyError:
                    parser.error("max_ents: no 'w' found for %r" % name)

            if args.max_bytes:
                check_bytes(name)

            special = None

            # specials
            if get_property(obj, "fixed", None) is not None:
                if obj["width"] >= obj["height"]:
                    special = obj["width"] - tilewidth
                    if not param:
                        x += special
                    special //= tilewidth
                    # flag horizonal
                    special |= 128
                else:
                    special = obj["height"] - tileheight
                    if not param:
                        y += special
                    special //= tileheight

            if name == "elevator":
                try:
                    respawn = json.loads(get_property(obj, "respawn", "[]"))
                    if args.max_bytes:
                        for name in respawn:
                            check_bytes(name)
                    special = [et_names.index(et) for et in respawn]
                    assert(len(special) < 255)
                except Exception as ex:
                    parser.error("Error parsing respawn: %s" % ex)

                # terminator
                special.append(0xff)
                # size
                special = [len(special), ] + special

            map_ents[m].extend([t, x, y])
            if special is not None:
                if isinstance(special, (tuple, list)):
                    map_ents[m].extend(special)
                else:
                    map_ents[m].append(special)

        if args.max_ents:
            for i, weight in map_ents_w.items():
                if weight > args.max_ents:
                    parser.error("map %i has %d entities, max is %d" %
                                 (i, weight, args.max_ents))

        if args.max_bytes:
            for i, byts in map_ents_bytes.items():
                if byts > args.max_bytes:
                    parser.error("map %i entities are %d bytes, max is %d" %
                                 (i, byts, args.max_bytes))

        # append the entities to the map data
        for i in range(len(out)):
            if not out[i]:
                continue
            elif map_ents[i]:
                out[i].extend(map_ents[i])
                out[i][2] += len(map_ents[i])
            # terminator
            out[i].append(0xff)
            out[i][2] += 1

    if args.reverse:
        out.reverse()

    if args.bin:
        for i, block in enumerate(out):
            filename = path.join(args.dir, "%s%02d.bin" % (args.id, i))
            with open(filename, "wb") as fd:
                if i in empty:
                    fd.write(struct.pack("<B", 0))
                else:
                    fd.write(bytearray(block))

        if not args.quiet:
            screen_with_data = len(out) - len(empty)
            total_bytes = sum(len(b) if b else 0 for b in out)
            print("%s: %s (%d screens, %d bytes, %.2f bytes avg)" % (
                path.basename(sys.argv[0]), args.id,
                screen_with_data, total_bytes, total_bytes / screen_with_data),
                file=sys.stderr)
        return

    print("#ifndef _%s_H" % args.id.upper())
    print("#define _%s_H" % args.id.upper())
    print("/* compressed: %s */" % args.aplib)
    print("#define WMAPS %d\n" % (mw // args.rw))
    print("#define MAPS %d\n" % len(out))

    print("#ifdef LOCAL")

    # includes a map table for fast access
    data_out = ""
    for i, block in enumerate(out):
        if not isinstance(block, list):
            continue
        data_out_part = ""
        for part in range(0, len(block), args.rw // 2):
            if data_out_part:
                data_out_part += ",\n"
            data_out_part += ', '.join(
                ["0x%02x" % byte for byte in block[part: part + args.rw // 2]])
        data_out += "const unsigned char %s_%d[%d] = {\n" % (
            args.id, i, len(block))
        data_out += data_out_part + "\n};\n"

    data_out += "const unsigned char * const %s[%d] = { " % (args.id, len(out))
    data_out += ', '.join(
        ["%s_%d" % (args.id,
                    i) if i not in empty else "(unsigned char *)0" for i in range(len(out))])
    data_out += " };\n"
    print(data_out)

    print("#else")
    print("extern const unsigned char * const %s[%d];\n" % (args.id, len(out)))

    print("#endif // LOCAL")
    print("#endif // _%s_H" % args.id.upper())

    if not args.quiet:
        screen_with_data = len(out) - len(empty)
        total_bytes = sum(len(b) if b else 0 for b in out)
        print("%s: %s (%d screens, %d bytes, %.2f bytes avg)" % (
            path.basename(sys.argv[0]), args.id,
            screen_with_data, total_bytes, total_bytes / screen_with_data),
            file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print("FATAL: %s\n***" % ex, file=sys.stderr)
        traceback.print_exc(ex)
        sys.exit(1)
