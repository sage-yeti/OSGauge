import json
import struct
import unittest
import zlib
from pathlib import Path

from os_icons import FALLBACK_KEY, LOGO_REGISTRY, logo_asset_path, logo_metadata


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _supported_families() -> tuple[str, ...]:
    requirements = json.loads(Path(__file__).with_name("requirements.json").read_text(encoding="utf-8"))
    return tuple(entry["os_family"] for entry in requirements["_lifecycle"].values())


def _png_rgba(path: Path) -> tuple[tuple[int, int, int, int, int], list[bytearray]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise AssertionError(f"not a PNG: {path}")
    offset = len(PNG_SIGNATURE)
    width = height = bit_depth = color_type = interlace = None
    compressed = bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    header = (width, height, bit_depth, color_type, interlace)
    if header != (32, 32, 8, 6, 0):
        raise AssertionError(f"unexpected RGBA PNG format: {path}")

    raw = zlib.decompress(bytes(compressed))
    stride = width * 4
    rows = []
    previous = bytearray(stride)
    cursor = 0
    for _row in range(height):
        filter_type = raw[cursor]
        cursor += 1
        current = bytearray(raw[cursor:cursor + stride])
        cursor += stride
        for index in range(stride):
            left = current[index - 4] if index >= 4 else 0
            up = previous[index]
            up_left = previous[index - 4] if index >= 4 else 0
            if filter_type == 1:
                current[index] = (current[index] + left) & 255
            elif filter_type == 2:
                current[index] = (current[index] + up) & 255
            elif filter_type == 3:
                current[index] = (current[index] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                estimate = left + up - up_left
                distance_left = abs(estimate - left)
                distance_up = abs(estimate - up)
                distance_up_left = abs(estimate - up_left)
                predictor = left if distance_left <= distance_up and distance_left <= distance_up_left else up if distance_up <= distance_up_left else up_left
                current[index] = (current[index] + predictor) & 255
            elif filter_type != 0:
                raise AssertionError(f"unsupported PNG filter {filter_type}")
        rows.append(current)
        previous = current
    return header, rows


def _alpha(rows: list[bytearray], x: int, y: int) -> int:
    return rows[y][x * 4 + 3]


class OsIconTests(unittest.TestCase):
    def test_every_supported_family_has_a_dedicated_transparent_png_asset(self):
        families = _supported_families()
        self.assertEqual(len(families), 28)
        keys = set()
        for family in families:
            metadata = logo_metadata(family)
            self.assertIn(metadata["key"], LOGO_REGISTRY)
            self.assertNotEqual(metadata["key"], FALLBACK_KEY)
            self.assertNotIn(metadata["key"], keys)
            keys.add(metadata["key"])
            self.assertTrue(metadata["asset"].endswith(".png"))
            path = logo_asset_path(family)
            self.assertTrue(path.is_file(), path)
            header, rows = _png_rgba(path)
            self.assertEqual(header, (32, 32, 8, 6, 0))
            self.assertEqual(_alpha(rows, 0, 0), 0)
            self.assertEqual(_alpha(rows, 31, 0), 0)
            self.assertEqual(_alpha(rows, 0, 31), 0)
            self.assertEqual(_alpha(rows, 31, 31), 0)
            self.assertTrue(any(row[index] > 0 for row in rows for index in range(3, len(row), 4)))
        self.assertEqual(len(keys), 28)

    def test_unknown_family_uses_transparent_fallback(self):
        self.assertEqual(logo_metadata("A future operating system")["key"], FALLBACK_KEY)
        fallback = logo_asset_path("A future operating system")
        self.assertEqual(fallback.name, "generic-os.png")
        self.assertTrue(fallback.is_file())
        header, rows = _png_rgba(fallback)
        self.assertEqual(header, (32, 32, 8, 6, 0))
        self.assertEqual(_alpha(rows, 31, 0), 0)
        self.assertTrue(any(row[index] > 0 for row in rows for index in range(3, len(row), 4)))

    def test_mapping_uses_family_not_translated_display_name(self):
        self.assertEqual(logo_metadata("Ubuntu Desktop 26.04 LTS", {"os_family": "Ubuntu Desktop"})["key"], "ubuntu-desktop")
        self.assertEqual(logo_metadata("Ubuntu Desktop 26.04 LTS", {"os_family": "Ubuntu Desktop"})["key"], logo_metadata("Ubuntu Desktop")["key"])

    def test_paths_are_resource_relative_and_portable(self):
        path = logo_asset_path("Windows 11")
        self.assertEqual(path.name, "windows-11.png")
        self.assertIn("assets", path.parts)
        self.assertIn("os_logos", path.parts)


if __name__ == "__main__":
    unittest.main()
