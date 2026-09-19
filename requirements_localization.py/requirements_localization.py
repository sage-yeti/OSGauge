"""Presentation-layer localization for bundled requirements notes.

The requirements database remains canonical and language-neutral. Unknown or
future profile notes intentionally fall back to their original text.
"""
from __future__ import annotations

SUPPORTED_NOTE_LANGUAGES = ("en", "it", "es", "de", "fr", "zh-CN", "ru", "tr", "pt-BR", "el")
BUNDLED_NOTES = {
    "Windows 11": [
        "Microsoft also requires a CPU model on its approved processor list.",
        "DirectX 12 graphics with a WDDM 2.0 driver is required.",
        "Internet access and a Microsoft account may be required during setup."
    ],
    "Ubuntu Desktop 26.04 LTS": [
        "A USB port or DVD drive is needed for typical installer media.",
        "Trying the live USB first is the best way to confirm device and driver compatibility."
    ],
    "Fedora Workstation 44": [
        "Fedora publishes 4 GB RAM and 40 GB storage as recommendations; double these may provide a better experience.",
        "Trying the live USB first is the best way to confirm device and driver compatibility."
    ],
    "Arch Linux": [
        "Arch's installation guide states a minimum of 512 MiB RAM and says a basic installation should take less than 2 GiB of disk space.",
        "The guide does not specify a CPU speed or core-count minimum; those checks are represented as no threshold.",
        "More memory is needed to boot the live installation environment, and internet access is assumed during installation."
    ],
    "Linux Mint": [
        "Linux Mint lists 2 GB RAM and 20 GB disk space as minimums; 4 GB RAM and 100 GB disk are recommended for comfortable use.",
        "The FAQ does not specify a CPU speed or core-count minimum; those checks are represented as no threshold.",
        "The current Linux Mint download page provides 64-bit images."
    ],
    "openSUSE Leap 15.6": [
        "openSUSE lists 1 GB RAM, 10 GB for a minimal install, and 16 GB for a graphical desktop; 4 GB RAM is strongly recommended.",
        "The guide does not specify a CPU speed or core-count minimum; those checks are represented as no threshold.",
        "At least 40 GB is recommended for the root partition when using Btrfs snapshots."
    ],
    "Pop!_OS": [
        "System76 lists 4 GB RAM and 20 GB storage as requirements, with 8 GB RAM recommended.",
        "The supported CPU families are 64-bit x86 and ARM; no CPU speed or core-count minimum is stated.",
        "Installation media requires a USB flash drive."
    ],
    "Debian 13 (trixie)": [
        "Debian lists these as minimum recommended values for a desktop installation on amd64: a 1 GHz Pentium 4-class processor, 1 GB RAM, and 10 GB disk space.",
        "The official guide also lists lower values for installations without a desktop environment; this profile uses the desktop values.",
        "The amd64 installation guide does not specify a display or firmware requirement."
    ],
    "ChromeOS Flex": [
        "Google requires an Intel or AMD x86-64 compatible device, at least 4 GB RAM, and at least 16 GB internal storage.",
        "The device must be bootable from USB and provide full administrator access in its BIOS; the current hardware schema does not check those conditions.",
        "Google does not specify a CPU speed or core-count minimum."
    ],
    "Zorin OS 18.1": [
        "Zorin lists a 1 GHz dual-core 64-bit processor, 2 GB RAM, 15 GB storage for Core, and an 800 × 600 display as minimum requirements.",
        "Zorin OS Education and Pro require more storage (35 GB and 45 GB respectively); this profile uses the Core minimum."
    ],
    "elementary OS 8.1": [
        "elementary describes these as recommendations rather than strict minimums: a recent dual-core 64-bit processor, 4 GB RAM, 32 GB free SSD space, and a 1024 × 768 display.",
        "The official installation guide does not specify a CPU speed threshold."
    ],
    "Manjaro": [
        "Manjaro lists these as recommended system requirements: a dual-core processor, 4 GB memory, and 30 GB disk space.",
        "The page also recommends HD graphics and a monitor plus broadband internet; the current schema does not turn those descriptions into extra hardware checks.",
        "The desktop profile targets Manjaro's x86 workstation images."
    ],
    "Kali Linux": [
        "This profile targets Kali's default Xfce desktop and kali-linux-default metapackage.",
        "Kali documents 2 GB RAM and 20 GB disk space for that desktop installation; CPU speed and core minimums are not specified.",
        "Kali installer media requires USB/DVD boot support and Secure Boot disabled."
    ],
    "Tails": [
        "Tails is a live operating system intended to run from USB/DVD, not a conventional hard-disk desktop installation.",
        "Tails documents 3 GB RAM for smooth operation, a 64-bit x86-64 processor, and an 8 GB minimum USB stick.",
        "The storage check is a proxy for the documented USB capacity because the current schema cannot inspect removable media."
    ],
    "MX Linux": [
        "This profile uses the MX Linux desktop installation minimums from the official user manual: a modern i686-or-newer Intel/AMD processor, 1 GB RAM, and 6 GB free disk space.",
        "The manual recommends 2 GB RAM and 20 GB free space for general use; those are not strict compatibility minimums."
    ],
    "Rocky Linux 10": [
        "Rocky's minimum hardware guidance targets a minimal/server installation; graphical environments need more resources.",
        "Rocky documents 1 GHz 64-bit CPU, 2 GB RAM minimum for text-mode installation, and 10 GB disk space."
    ],
    "AlmaLinux 9": [
        "AlmaLinux's installation guide lists 1.5 GB RAM and 10 GB disk as system requirements; CPU speed is not specified.",
        "The project supports several architectures; this checker can meaningfully compare only architectures reported by its generic detector."
    ],
    "NixOS": [
        "NixOS does not publish a single conventional desktop minimum for its configurable installations, so RAM and storage thresholds are intentionally omitted.",
        "The official manual covers both graphical and manual installations and supports x86-64 and ARM graphical images."
    ],
    "EndeavourOS": [
        "This profile targets the standard x86-64 desktop installer. EndeavourOS lists 2.5 GB RAM, a dual-core 64-bit processor, and 15 GB disk space as minimums.",
        "The installer supports legacy BIOS, while modern UEFI is recommended."
    ],
    "CachyOS": [
        "This profile targets the CachyOS desktop edition on physical x86-64 hardware.",
        "CachyOS documents 3 GB RAM and 30 GB storage as minimums; its x86-64-v3 CPU and GPU guidance is listed as recommended, not a generic minimum."
    ],
    "Void Linux": [
        "Void's official base-system table lists 520 MB RAM and 700 MB storage for x86_64-glibc, 520 MB RAM and 600 MB storage for x86_64-musl, and Pentium 4 SSE2 with 520 MB RAM and 700 MB storage for i686-glibc.",
        "Desktop-environment requirements vary; this profile uses the documented base-system thresholds and does not invent desktop values. Void does not publish a CPU clock or core-count minimum."
    ],
    "antiX 26": [
        "antiX 26 is available in full and core editions for 32-bit and 64-bit Intel/AMD-compatible systems.",
        "The official project describes 512 MB RAM as the recommended minimum, 256 MB with preconfigured swap as a lower starting point, and 7 GB of hard-disk space. No CPU clock or core-count threshold is published."
    ],
    "Q4OS 6.9 Andromeda Trinity": [
        "Q4OS 6.9 Andromeda is the current stable LTS line; the official downloads page lists Trinity minimal hardware at 500 MHz CPU, 512 MB RAM, and 6 GB disk.",
        "Current Trinity x64 media is represented; older 32-bit media is a separate legacy line. The LTS support statement runs at least through August 2030."
    ],
    "Bodhi Linux 7.0.0": [
        "Bodhi lists a 500 MHz processor, 512 MB RAM, and 5 GB drive as minimums; its recommended 64-bit target is 1.0 GHz, 768 MB RAM, and 10 GB.",
        "The official download page identifies 7.0.0 as current; 32-bit legacy media is separate. The installer runs best above 512 MB, so the minimum is intentionally conservative."
    ],
    "SparkyLinux 8.4 MinimalGUI": [
        "SparkyLinux 8.4 stable provides a MinimalGUI Openbox edition for amd64 and i686-pae.",
        "The official lightweight requirements specify 256 MB RAM for Openbox-class desktops and 10 GB for the home editions; no CPU clock/core threshold is published. The Calamares installer needs more memory, while Advanced Installer is available below 1 GB."
    ],
    "Slax 12.2.0": [
        "Slax is a live system designed to boot from CD or USB; its official introduction lists 128 MB RAM for the desktop and 512 MB for running a web browser.",
        "No permanent-install storage threshold or CPU clock/core minimum is published, so those fields remain unasserted."
    ],
    "Alpine Linux 3.24": [
        "Alpine documents 128 MB as the x86_64 installation-memory minimum and at least 1 GB for a default installation; x86 and GUI values differ and are described in the official requirements matrix.",
        "The profile represents the base installation and does not assert desktop-environment requirements. The current stable 3.24 branch supports the listed canonical architectures."
    ],
    "Tiny Core Linux 17.1 TinyCore": [
        "TinyCore is the GUI-capable variant selected for this profile; Core is CLI-only and CorePlus is the installer-oriented variant.",
        "The official FAQ gives an absolute minimum of 46 MB RAM and an i486DX-class CPU, with 128 MB plus swap recommended. Storage depends on extensions and persistence, so no fixed threshold is asserted."
    ]
}

NOTE_TRANSLATIONS = {
    "Alpine Linux 3.24": {
        "Alpine documents 128 MB as the x86_64 installation-memory minimum and at least 1 GB for a default installation; x86 and GUI values differ and are described in the official requirements matrix.": {
            "en": "Alpine documents 128 MB as the x86_64 installation-memory minimum and at least 1 GB for a default installation; x86 and GUI values differ and are described in the official requirements matrix.",
            "it": "Alpine documenta 128 MB come minimo di memoria d'installazione per x86_64 e almeno 1 GB per un'installazione predefinita; i valori per x86 e per la GUI differiscono e sono descritti nella matrice ufficiale dei requisiti.",
            "es": "Alpine documenta 128 MB como mínimo de memoria de instalación para x86_64 y al menos 1 GB para una instalación predeterminada; los valores para x86 y GUI difieren y se describen en la matriz oficial de requisitos.",
            "de": "Alpine nennt 128 MB als Mindestarbeitsspeicher für die Installation auf x86_64 und mindestens 1 GB für eine Standardinstallation; die Werte für x86 und die grafische Oberfläche unterscheiden sich und sind in der offiziellen Anforderungsmatrix beschrieben.",
            "fr": "Alpine documente 128 Mo comme mémoire minimale d’installation pour x86_64 et au moins 1 Go pour une installation par défaut ; les valeurs x86 et graphiques diffèrent et sont décrites dans la matrice officielle des exigences.",
            "zh-CN": "Alpine 文档说明，x86_64 安装至少需要 128 MB 内存，默认安装至少需要 1 GB；x86 和图形界面的数值不同，官方要求矩阵对此有说明。",
            "ru": "Alpine указывает 128 МБ как минимальный объём памяти для установки на x86_64 и не менее 1 ГБ для установки по умолчанию; значения для x86 и графической среды отличаются и приведены в официальной таблице требований.",
            "tr": "Alpine, x86_64 kurulumu için en az 128 MB, varsayılan kurulum için en az 1 GB bellek belirtir; x86 ve grafik arayüz değerleri farklıdır ve resmî gereksinim tablosunda açıklanır.",
            "pt-BR": "A Alpine documenta 128 MB como memória mínima de instalação para x86_64 e pelo menos 1 GB para uma instalação padrão; os valores para x86 e para a interface gráfica diferem e estão descritos na matriz oficial de requisitos.",
            "el": "Το Alpine τεκμηριώνει 128 MB ως ελάχιστη μνήμη εγκατάστασης για x86_64 και τουλάχιστον 1 GB για προεπιλεγμένη εγκατάσταση· οι τιμές για x86 και γραφικό περιβάλλον διαφέρουν και περιγράφονται στον επίσημο πίνακα απαιτήσεων."
        },
        "The profile represents the base installation and does not assert desktop-environment requirements. The current stable 3.24 branch supports the listed canonical architectures.": {
            "en": "The profile represents the base installation and does not assert desktop-environment requirements. The current stable 3.24 branch supports the listed canonical architectures.",
            "it": "Il profilo rappresenta l'installazione base e non stabilisce requisiti per l'ambiente desktop. L'attuale ramo stabile 3.24 supporta le architetture canoniche elencate.",
            "es": "El perfil representa la instalación base y no establece requisitos para el entorno de escritorio. La rama estable 3.24 actual admite las arquitecturas canónicas indicadas.",
            "de": "Das Profil steht für die Basisinstallation und legt keine Anforderungen an eine Desktop-Umgebung fest. Der aktuelle stabile Zweig 3.24 unterstützt die aufgeführten kanonischen Architekturen.",
            "fr": "Le profil représente l’installation de base et ne fixe aucune exigence pour l’environnement de bureau. La branche stable 3.24 actuelle prend en charge les architectures canoniques indiquées.",
            "zh-CN": "该配置代表基础安装，不规定桌面环境要求。当前稳定的 3.24 分支支持所列出的标准架构。",
            "ru": "Профиль представляет базовую установку и не устанавливает требований к рабочему окружению. Текущая стабильная ветка 3.24 поддерживает перечисленные канонические архитектуры.",
            "tr": "Bu profil temel kurulumu temsil eder ve masaüstü ortamı gereksinimleri belirlemez. Güncel kararlı 3.24 dalı listelenen standart mimarileri destekler.",
            "pt-BR": "O perfil representa a instalação básica e não define requisitos de ambiente gráfico. A atual série estável 3.24 oferece suporte às arquiteturas canônicas listadas.",
            "el": "Το προφίλ αντιπροσωπεύει τη βασική εγκατάσταση και δεν ορίζει απαιτήσεις για περιβάλλον επιφάνειας εργασίας. Ο τρέχων σταθερός κλάδος 3.24 υποστηρίζει τις αναφερόμενες κανονικές αρχιτεκτονικές."
        }
    },
    "Ubuntu Desktop 26.04 LTS": {
        "Trying the live USB first is the best way to confirm device and driver compatibility.": {
            "en": "Trying the live USB first is the best way to confirm device and driver compatibility.",
            "it": "Provare prima la live USB è il modo migliore per confermare la compatibilità del dispositivo e dei driver.",
            "es": "Probar primero la USB en modo live es la mejor forma de confirmar la compatibilidad del dispositivo y los controladores.",
            "de": "Ein Test mit dem Live-USB ist der beste Weg, die Kompatibilität von Gerät und Treibern zu bestätigen.",
            "fr": "Essayer d’abord la clé USB en mode live est le meilleur moyen de confirmer la compatibilité du matériel et des pilotes.",
            "zh-CN": "先试用 Live USB 是确认设备和驱动兼容性的最佳方法。",
            "ru": "Сначала запустите систему с Live USB — это лучший способ проверить совместимость устройства и драйверов.",
            "tr": "Önce Live USB'yi denemek, aygıt ve sürücü uyumluluğunu doğrulamanın en iyi yoludur.",
            "pt-BR": "Testar primeiro o Live USB é a melhor forma de confirmar a compatibilidade do dispositivo e dos drivers.",
            "el": "Η δοκιμή πρώτα από Live USB είναι ο καλύτερος τρόπος επιβεβαίωσης της συμβατότητας συσκευής και οδηγών."
        }
    }
}

def localize_requirement_note(profile_name: str, note: str, language: str = "en") -> str:
    """Return a localized bundled note, or the original note for unknown data."""
    if profile_name not in BUNDLED_NOTES or note not in BUNDLED_NOTES[profile_name]:
        return note
    return NOTE_TRANSLATIONS.get(profile_name, {}).get(note, {}).get(language, note)

def bundled_note_translation_map(profile_name: str, note: str) -> dict[str, str]:
    """Expose one value for every supported language for coverage tests."""
    if profile_name not in BUNDLED_NOTES or note not in BUNDLED_NOTES[profile_name]:
        return {}
    return {language: localize_requirement_note(profile_name, note, language) for language in SUPPORTED_NOTE_LANGUAGES}

def missing_bundled_note_translations(requirements: dict, languages=SUPPORTED_NOTE_LANGUAGES) -> list[tuple[str, str, str]]:
    """Report missing keys without rejecting safe English values."""
    missing = []
    for profile_name, profile in requirements.items():
        for note in profile.get("notes", []):
            values = bundled_note_translation_map(profile_name, note)
            for language in languages:
                if language not in values or not values[language]:
                    missing.append((profile_name, note, language))
    return missing
