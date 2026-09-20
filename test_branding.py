from pathlib import Path


ROOT = Path(__file__).resolve().parent


def read_file(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_osgauge_brand_is_exposed_in_runtime_surfaces():
    assert "OSGauge" in read_file("app.py")
    assert '"app.title": "OSGauge"' in read_file("locales/en.json")
    assert "OSGauge CLI" in read_file("cli.py")
    assert "0.5.2" in read_file("version.py")


def test_osgauge_artifacts_preserve_technical_identifiers():
    workflow = read_file(".github/workflows/build.yml")
    flatpak = read_file("packaging/flatpak/io.github.sage_yeti.OSReadinessChecker.yml")
    requirements_update = read_file("requirements_update.py")

    assert "OSGauge-Windows-x64.exe" in workflow
    assert "OSGauge-Linux-x86_64.AppImage" in workflow
    assert "OSGauge-Linux-x86_64.flatpak" in workflow
    assert "io.github.sageyeti.OSReadinessChecker" in flatpak
    assert 'os.environ.get("LOCALAPPDATA")' in requirements_update
    assert 'Path.home() / ".cache"' in requirements_update
    assert 'root / "OS Readiness Checker" / "requirements.json"' in requirements_update

def test_osgauge_brand_assets_are_packaged():
    branding = ROOT / "assets" / "branding"
    for name in ("OSGauge-original.png", "osgauge.png", "osgauge.ico", "osgauge-16.png", "osgauge-32.png", "osgauge-48.png", "osgauge-64.png", "osgauge-128.png", "osgauge-256.png"):
        assert (branding / name).is_file()
    assert "assets/branding/osgauge.png" in read_file("app.py")
    assert "osgauge.ico" in read_file("os_readiness_checker.spec")
    assert "osgauge.ico" in read_file("os_readiness_checker_cli.spec")
    assert "<svg" in read_file("packaging/linux/OS-Readiness-Checker.svg")
    assert "hicolor/${size}x${size}/apps" in read_file("packaging/linux/build_appimage.sh")
    assert "hicolor/${size}x${size}/apps/io.github.sageyeti.OSReadinessChecker.png" in read_file("packaging/flatpak/io.github.sage_yeti.OSReadinessChecker.yml")
