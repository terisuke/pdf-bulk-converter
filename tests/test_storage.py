from app.services.storage import _max_number_in_path, get_next_image_number


def test_max_number_in_path(tmp_path):
    (tmp_path / "0000001.jpeg").write_text("a")
    (tmp_path / "0000005.jpg").write_text("a")
    (tmp_path / "not_number.jpeg").write_text("a")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "0000003.jpeg").write_text("a")
    assert _max_number_in_path(str(tmp_path)) == 5


def test_get_next_image_number_local(tmp_path, monkeypatch):
    (tmp_path / "0000007.jpeg").write_text("a")
    monkeypatch.setattr(
        "app.services.storage.settings.workspace_path", str(tmp_path), raising=False
    )
    monkeypatch.setattr("app.services.storage.settings.gcp_region", "local", raising=False)
    assert get_next_image_number() == 8
