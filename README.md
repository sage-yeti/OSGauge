# OS Readiness Checker

A small desktop application that scans the current computer and compares it with the published requirements for Windows 11, Ubuntu Desktop, Fedora Workstation, Arch Linux, Linux Mint, openSUSE Leap, Pop!_OS, Debian, ChromeOS Flex, Zorin OS, elementary OS, Manjaro, Kali Linux, Tails, MX Linux, Rocky Linux, AlmaLinux, NixOS, EndeavourOS, and CachyOS.

## Features

- Automatically detects processor, GPU, memory, storage, boot-disk layout, filesystem and display information when available
- Checks Windows-specific UEFI, Secure Boot and TPM information when available
- Reports virtualization capability when the operating system exposes it
- Explains each pass, failure and item that needs manual review
- Exports portable JSON and self-contained offline HTML readiness reports
- Copies a compact compatibility summary for support chats and forums
- Checks for newer validated requirements data from this repository without updating the application
- Includes a cross-platform CLI for single-target or all-target scans
- Supports System, Light, and Dark GUI themes
- Remembers theme, selected OS, and safe window placement per user
- Includes an About panel and keyboard shortcuts (F5/Ctrl+R scan, Ctrl+S JSON report)
- Keeps OS definitions in an editable JSON file
- Scans hardware once, then ranks every supported OS by compatibility score
- Shows pass, review, or fail status and supports side-by-side OS comparison
- Uses only Python's standard library

## Download and run

Download the latest release for your platform:

- Windows GUI: `OS-Readiness-Checker-Windows-x64.exe` (double-click to run; no console window opens)
- Linux GUI: `OS-Readiness-Checker-Linux-x64` (make it executable with `chmod +x`, then run it)
- Windows CLI: `OS-Readiness-Checker-CLI-Windows-x64.exe`
- Linux CLI: `OS-Readiness-Checker-CLI-Linux-x64`

The packaged versions include the requirements database and do not require Python to be installed.

## Run from source or build

Developers who want to run or build from source need Python 3.10 or newer. To run from source, double-click **Launch OS Readiness Checker.bat** on Windows, or run:

```text
python app.py
```

The CLI uses the same hardware scan and compatibility engine:

```text
os-readiness-checker --list
os-readiness-checker --check "Windows 11" --verbose
os-readiness-checker --all --json --output readiness.json
```

Exit code `0` means no requested target failed, `1` means at least one mandatory check failed, and `2` means invalid arguments or an operational error. Review/unknown results are reported normally and are not operational errors.

To build the native package for the current platform:

```text
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean os_readiness_checker.spec
```

GitHub Actions builds separate native Windows and Linux binaries and publishes them as release assets for version tags.

The app scans the computer once and opens a compatibility overview for every supported OS. Each result has an authoritative Pass, Review, or Fail status plus a supplementary 0–100 hardware compatibility score; ranking is based only on those detected hardware checks. Select an OS for its individual details, or use **Compare OSes** for a side-by-side view without another scan. Select an individual check to see a concise explanation and safe next steps. Use **Save report**, **Save HTML**, or **Copy results** to share the results.

The requirements database has its own schema/data version. Use **Check requirements updates** to fetch a newer validated copy from this repository; failures are non-fatal and the bundled database always remains available. Validated data is cached per user in `%LOCALAPPDATA%\\OS Readiness Checker` on Windows or `~/.cache/OS Readiness Checker` on Linux. The GUI offers **System**, **Light**, and **Dark** themes; System follows the Windows preference or a detectable Linux desktop preference and otherwise falls back to light.

Each release includes `SHA256SUMS.txt` for verifying downloaded binaries. Screenshots are omitted because the available validation environment does not include a working Tk/Tcl runtime for reliable current-theme capture.

## Important limits

System requirements are not the same as a complete compatibility guarantee. Driver support, peripherals, and model-specific issues are best checked with the vendor's compatibility list or a Linux live USB.

Windows 11 additionally requires a processor model from Microsoft's approved list and DirectX 12 graphics with WDDM 2.0. This initial version reports those as review notes rather than making an unreliable guess. Secure Boot and TPM information can also be unavailable when Windows restricts access to it.

Requirements are kept in `requirements.json`, so another operating system can be added without changing the program code.

When an official requirement page does not publish a CPU speed or core-count minimum, that check is represented as no threshold and the vendor note is retained in the definition. Other published minimums, such as architecture, memory, storage, and display resolution, are checked by the same generic evaluator.

## Tests

```text
python -m unittest -v
```

## Requirement sources

- [Windows 11 system requirements](https://support.microsoft.com/en-us/windows/experience/compatibility/windows-11-system-requirements)
- [Ubuntu Desktop requirements](https://ubuntu.com/download/desktop)
- [Fedora Workstation download and requirements](https://fedoraproject.org/workstation/download/)
- [Arch Linux installation requirements](https://wiki.archlinux.org/title/Installation_guide)
- [Linux Mint system requirements](https://www.linuxmint.com/faq.php)
- [openSUSE Leap 15.6 minimum system requirements](https://doc.opensuse.org/documentation/leap/startup/html/book-startup/art-opensuse-installquick.html)
- [Pop!_OS installation requirements](https://support.system76.com/support/install-pop)
- [Debian 13 system requirements](https://www.debian.org/releases/stable/amd64/ch03s04.en.html)
- [ChromeOS Flex minimum device requirements](https://support.google.com/chromeosflex/answer/11552529?hl=en)
- [Zorin OS system requirements](https://help.zorin.com/docs/getting-started/system-requirements/)
- [elementary OS installation requirements](https://elementary.io/docs/installation)
- [Manjaro recommended system requirements](https://wiki.manjaro.org/index.php?title=About_Manjaro/en)

## License

MIT
