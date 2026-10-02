import pytest

from app.main import FRONTEND_DIST

pytestmark = pytest.mark.skipif(
    not (FRONTEND_DIST / "index.html").exists(), reason="frontend not built (run npm run build)"
)


def test_root_level_build_file_is_served_as_itself(client):
    res = client.get("/favicon.svg")
    assert res.status_code == 200
    assert "svg" in res.headers["content-type"]
    assert res.text.lstrip().startswith("<svg")


def test_unknown_paths_fall_back_to_the_spa(client):
    res = client.get("/cases/some-case-id")
    assert res.status_code == 200
    assert "<div id=\"root\">" in res.text


def test_path_traversal_cannot_escape_dist(client):
    res = client.get("/..%2F..%2Fbackend%2F.env.example")
    assert res.status_code == 200
    assert "GOOGLE_API_KEY" not in res.text
    assert "<div id=\"root\">" in res.text
