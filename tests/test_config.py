from google_auth_pc.config import Config
from google_auth_pc import paths

def test_defaults_and_persistence(tmp_path):
    cfg = Config(tmp_path / "config.json")
    assert cfg.get("theme_mode") == "system"
    assert cfg.get("autostart") is True
    assert cfg.get("first_run_done") is False
    cfg.set("theme_mode", "dark")
    cfg.save()
    assert Config(tmp_path / "config.json").get("theme_mode") == "dark"

def test_unknown_file_loads_defaults(tmp_path):
    cfg = Config(tmp_path / "yok.json")
    assert cfg.get("geometry") == ""

def test_data_dir_uses_appdata(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    d = paths.data_dir()
    assert d.name == "GoogleAuthPC" and d.exists()
