import struct
import unittest
import zlib
from pathlib import Path

from os_icons import FALLBACK_KEY, LOGO_REGISTRY, logo_asset_path, logo_metadata


SUPPORTED_FAMILIES = (
    "Windows 11", "Ubuntu Desktop", "Fedora Workstation", "Arch Linux", "Linux Mint", "openSUSE Leap",
    "Pop!_OS", "Debian", "ChromeOS Flex", "Zorin OS", "elementary OS", "Manjaro", "Kali Linux", "Tails",
    "MX Linux", "Rocky Linux", "AlmaLinux", "NixOS", "EndeavourOS", "CachyOS",
)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_alpha(path: Path, x: int, y: int) -> int:
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
    if (width, height, bit_depth, color_type, interlace) != (32, 32, 8, 6, 0):
        raise AssertionError(f"unexpected RGBA PNG format: {path}")
    if not (0 <= x < width and 0 <= y < height):
        raise AssertionError("sample outside image")
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
    return rows[y][x * 4 + 3]


class OsIconTests(unittest.TestCase):
    def test_every_supported_family_has_a_transparent_png_asset(self):
        for family in SUPPORTED_FAMILIES:
            metadata = logo_metadata(family)
            self.assertIn(metadata["key"], LOGO_REGISTRY)
            self.assertTrue(metadata["asset"].endswith(".png"))
            path = logo_asset_path(family)
            self.assertTrue(path.is_file(), path)
            self.assertEqual(_png_alpha(path, 31, 0), 0)
            self.assertEqual(_png_alpha(path, 14, 16), 255)

    def test_unknown_family_uses_transparent_fallback(self):
        self.assertEqual(logo_metadata("A future operating system")["key"], FALLBACK_KEY)
        fallback = logo_asset_path("A future operating system")
        self.assertEqual(fallback.name, "generic-os.png")
        self.assertTrue(fallback.is_file())
        self.assertEqual(_png_alpha(fallback, 31, 0), 0)

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
