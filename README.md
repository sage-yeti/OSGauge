# OSGauge

A small desktop application that scans the current computer and compares it with the published requirements for Windows 11, Ubuntu Desktop, Fedora Workstation, Arch Linux, Linux Mint, openSUSE Leap, Pop!_OS, Debian, ChromeOS Flex, Zorin OS, elementary OS, Manjaro, Kali Linux, Tails, MX Linux, Rocky Linux, AlmaLinux, NixOS, EndeavourOS, CachyOS, Void Linux, antiX, Q4OS Trinity, Bodhi Linux, SparkyLinux MinimalGUI, Slax, Alpine Linux, and Tiny Core Linux.

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
- Supports English, Italian, Spanish, German, and French GUI/report text; System follows the detected locale and falls back to English
- Remembers theme, selected OS, and safe window placement per user
- Includes an About panel and keyboard shortcuts (F5/Ctrl+R scan, Ctrl+S JSON report)
- Keeps OS definitions in an editable JSON file
- Scans hardware once, then ranks every supported OS by compatibility score
- Shows pass, review, or fail status and supports side-by-side OS comparison
- Exports and imports privacy-conscious `.osrprofile` machine profiles for offline analysis on another computer
- Uses only Python's standard library

## Download and run

Download the latest release for your platform:

- Windows GUI: `OSGauge-Windows-x64.exe` (double-click to run; no console window opens)
- Linux GUI: `OSGauge-Linux-x64` (make it executable with `chmod +x`, then run it)
- Linux portable AppImage: `OSGauge-Linux-x86_64.AppImage` (x86-64; make it executable with `chmod +x`, then run it)
- Windows CLI: `OSGauge-CLI-Windows-x64.exe`
- Linux CLI: `OSGauge-CLI-Linux-x64`

The packaged versions include the requirements database and do not require Python to be installed.

To run the Linux AppImage, download it, make it executable, and launch it:

```text
chmod +x OSGauge-Linux-x86_64.AppImage
./OSGauge-Linux-x86_64.AppImage
```

The existing standalone Linux GUI and CLI artifacts remain available separately. The AppImage is GUI-focused; use the separate Linux CLI artifact for command-line scans. Python is not required for either packaged Linux GUI format.

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
os-readiness-checker --profile machine-profile.osrprofile --all --json
os-readiness-checker --export-profile machine-profile.osrprofile --check ubuntu
os-readiness-checker --check ubuntu --lang it
```

Exit code `0` means no requested target failed, `1` means at least one mandatory check failed, and `2` means invalid arguments or an operational error. Review/unknown results are reported normally and are not operational errors.

To build the native package for the current platform:

```text
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean os_readiness_checker.spec
```

GitHub Actions builds separate native Windows and Linux binaries and publishes them as release assets for version tags.
The Linux workflow also builds and validates the x86-64 AppImage as a downloadable workflow artifact. It includes the packaged requirements database and all supported localization resources; settings and requirements caches remain in the normal per-user Linux locations outside the AppImage.

The app scans the computer once and opens a compatibility overview for every supported OS. Each result has an authoritative Pass, Review, or Fail status plus a supplementary 0–100 hardware compatibility score; ranking is based only on those detected hardware checks. Select an OS for its individual details, or use **Compare OSes** for a side-by-side view without another scan. Select an individual check to see a concise explanation and safe next steps. Use **Save report**, **Save HTML**, or **Copy results** to share the results.

Use **Compare machines** to compare the current loaded machine with an imported `.osrprofile`, or to compare two imported profiles. The view compares available hardware fields and can assess both machines against a selected OS using the existing compatibility, suitability, and installation-readiness engines. Imported data reflects its capture time; the selected-OS candidate assessment is not a universal ranking of the two computers.

The **Upgrade plan** summarizes required hardware, configuration, storage, and review items for the selected OS. Suitability-based headroom notes are clearly optional, and lifecycle warnings remain separate. Planning is read-only: the application never changes firmware, disks, hardware, or operating-system settings. From the CLI, add `--upgrade-plan` to a single `--check` or `--profile` analysis.

The requirements database has its own schema/data version. Use **Check requirements updates** to fetch a newer validated copy from this repository; failures are non-fatal and the bundled database always remains available. Validated data is cached per user in `%LOCALAPPDATA%\\OS Readiness Checker` on Windows or `~/.cache/OS Readiness Checker` on Linux. The GUI offers **System**, **Light**, and **Dark** themes; System follows the Windows preference or a detectable Linux desktop preference and otherwise falls back to light.

Profiles may include release and lifecycle information. The overview uses each OS family's current/default profile; rolling distributions are labeled as rolling, and lifecycle/EOL status is separate from hardware compatibility. When multiple releases are available, a specific profile can be selected with the CLI form `--check family@release` (for example, `--check ubuntu@26.04-lts`).

Results keep four concepts separate: Compatibility checks official hardware requirements; Suitability estimates application-defined hardware headroom; Lifecycle reports release support/EOL; Installation readiness checks the machine's current boot, firmware, storage, and security configuration. Installation readiness is advisory and read-only—it never changes firmware, disks, or boot settings.

Machine profiles are human-readable JSON files with the `.osrprofile` extension. They contain only detected hardware/configuration fields needed for analysis (never usernames, hostnames, serial numbers, network data, keys, or personal files). Imported profiles are re-evaluated with the current requirements database and application logic; installation readiness describes the configuration captured when the profile was created.

The GUI language can be set to **System**, **English**, **Italiano**, **Español**, **Deutsch**, or **Français** and is remembered in the existing settings. System recognizes common `es-*`, `de-*`, and `fr-*` locales and otherwise falls back to English. CLI flags and JSON/profile formats remain language-neutral; use `--lang en`, `it`, `es`, `de`, or `fr` only for human-readable CLI output.

Architecture-aware analysis recognizes x86-64, x86, ARM64/AArch64, and ARM32 aliases. OS compatibility follows each profile's published architecture support, and imported ARM64 profiles can be analyzed on another machine. Distributed binaries remain the existing Windows and Linux x86-64 builds; ARM64 analysis support does not imply a native ARM64 checker binary.

The optional **Recommend an OS** view ranks compatible systems against selected priorities such as beginner friendliness, older hardware, gaming, development, privacy, stability, long-term support, rolling software, and a Windows-like desktop. Compatibility remains authoritative; preference characteristics are application-defined guidance, not official vendor rankings or a universal “best OS.” Recommendations can use an imported machine profile. The CLI supports `--recommend` with repeatable `--prefer key=0|1|2` values.

### Flatpak (Linux)

The repository includes a Flatpak manifest (`packaging/flatpak/io.github.sage_yeti.OSReadinessChecker.yml`) using application ID `io.github.sageyeti.OSReadinessChecker`. Developers with `flatpak-builder` can build it with `flatpak-builder --force-clean build-dir packaging/flatpak/io.github.sage_yeti.OSReadinessChecker.yml`, then export a bundle with `flatpak build-bundle repo OSGauge-Linux-x86_64.flatpak io.github.sageyeti.OSReadinessChecker`. The Flatpak requests only display/IPC and read-only graphics access; sandboxing can make host disk, GPU, firmware, and boot details unavailable, which are reported as Unknown/Review. Importing a complete machine profile captured outside the sandbox remains reliable. AppImage is still supported and generally provides more direct host hardware visibility. No native ARM64 Flatpak artifact is currently distributed.

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
- [Void Linux installation requirements](https://docs.voidlinux.org/installation/)
- [antiX 26 release and requirements](https://antixlinux.com/about/)
- [Q4OS downloads and Trinity requirements](https://q4os.org/downloads1.html)
- [Bodhi Linux installation requirements](https://www.bodhilinux.com/w/installation-instructions/)
- [SparkyLinux stable downloads](https://sparkylinux.org/download/stable/)
- [Slax introduction and hardware requirements](https://www.slax.org/introduction.php)
- [Alpine Linux requirements](https://wiki.alpinelinux.org/wiki/Requirements)
- [Tiny Core Linux FAQ](https://www.tinycorelinux.net/faq.html)

## License

MIT
