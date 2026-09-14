# OS Readiness Checker

A small desktop application that scans the current computer and compares it with the published requirements for Windows 11, Ubuntu Desktop, Fedora Workstation, Arch Linux, Linux Mint, openSUSE Leap, and Pop!_OS.

## Features

- Automatically detects processor, memory, storage, architecture and display information
- Checks Windows-specific UEFI, Secure Boot and TPM information when available
- Explains each pass, failure and item that needs manual review
- Exports a portable JSON readiness report
- Keeps OS definitions in an editable JSON file
- Uses only Python's standard library

## Run from source

Install Python 3.10 or newer, then double-click **Launch OS Readiness Checker.bat**, or run:

```text
python app.py
```

Choose an operating system from the menu. The app scans the computer automatically and labels every item as Pass, Fail, or Unknown. A JSON report can be saved with **Save report**.

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

## License

MIT
