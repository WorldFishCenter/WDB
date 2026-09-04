"""One knowledge-base root, and an upload that cannot land outside it.

`wdb_ingest/config.py` used to re-derive both roots instead of importing :mod:`wdb_paths` — with
a different empty-string behaviour and an extra override no reader knew about. And
`config.INITIATIVES` carried a comment about a real past bug (a bogus initiative folder getting
minted) while having zero uses: `initiative` and `filename` both arrived unvalidated on the path
that calls ``mkdir(parents=True)``.
"""

import pytest

import wdb_paths
from wdb_ingest import config, service
from wdb_ingest.models import SubmissionInput
from wdb_ingest.service import InvalidPlacement


# --- one derivation ------------------------------------------------------- #

def test_the_service_uses_wdb_paths_roots():
    """Read side and write side cannot disagree about which KB this is."""
    assert config.KB_ROOT == wdb_paths.KB_ROOT
    assert config.WDB_ROOT == wdb_paths.REPO_ROOT
    assert config.GRAPH_JSON == wdb_paths.GRAPH_JSON


def test_config_does_not_derive_roots_itself():
    """No `Path(__file__).parent.parent` climbing — the idiom wdb_paths exists to replace.

    Checked over the parsed module, not its text: the docstring *describes* the old idiom.
    """
    import ast

    tree = ast.parse((wdb_paths.REPO_ROOT / "wdb_ingest" / "config.py").read_text())
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id == "__file__"]


def test_an_empty_env_override_falls_back_instead_of_becoming_the_cwd(monkeypatch):
    """``WDB_KB=""`` used to resolve to ``Path("")`` — the current working directory — here."""
    import importlib

    monkeypatch.setenv("WDB_KB", "")
    reloaded = importlib.reload(wdb_paths)
    try:
        assert reloaded.KB_ROOT == reloaded.REPO_ROOT / "knowledge_base"
        assert str(reloaded.KB_ROOT) != ""
    finally:
        monkeypatch.delenv("WDB_KB", raising=False)
        importlib.reload(wdb_paths)


def test_the_passage_index_location_is_single_sourced():
    from mode_b.index import DEFAULT_INDEX_DIR

    assert DEFAULT_INDEX_DIR == str(wdb_paths.INDEX_DIR)


# --- an upload cannot escape the knowledge base --------------------------- #

@pytest.mark.parametrize("initiative", ["civ-kb", "not_an_initiative", "", "../peskas"])
def test_an_unknown_initiative_is_refused(initiative):
    """The exact bug config.INITIATIVES' comment memorialises."""
    with pytest.raises(InvalidPlacement):
        service.validate_placement(initiative, "notes.md")


@pytest.mark.parametrize("filename", ["../../etc/passwd", "sub/dir/x.csv", "", ".", ".."])
def test_a_path_bearing_filename_is_refused(filename):
    with pytest.raises(InvalidPlacement):
        service.validate_placement("peskas", filename)


def test_a_real_placement_passes():
    for initiative in config.INITIATIVES:
        service.validate_placement(initiative, "kenya_validated_trips.csv")


def test_submit_refuses_before_touching_the_filesystem(store, tmp_env):
    """Validation runs first, so a refused upload leaves nothing staged."""
    inp = SubmissionInput(filename="../escape.md", format="doc", sizeLabel="1 KB",
                          initiative="peskas")
    with pytest.raises(InvalidPlacement):
        service.submit(store, inp, b"x", contributor="ana", background=False)

    assert not any(config.STAGING_DIR.glob("**/*")) if config.STAGING_DIR.exists() else True
    assert store.list_submissions() == []


def test_submit_over_http_refuses_with_400(client):
    r = client.post(
        "/submit",
        params={"filename": "notes.md", "format": "doc", "initiative": "civ-kb"},
        content=b"# notes",
        headers={"X-WDB-Role": "contributor", "X-WDB-User": "ana"},
    )
    assert r.status_code == 400
    assert "civ-kb" in r.json()["error"]


# --- the index follows the knowledge base it indexes ---------------------- #

def test_the_index_is_kb_rooted_not_package_rooted(monkeypatch):
    """Pointing WDB_KB at another KB must move the passage index with it.

    The index used to live at ``mode_b/.index`` — inside the installed package — so a second
    knowledge base silently reused the first one's index: Mode B retrieved KB-A's passages and
    joined them against KB-B's ``graph.json``.
    """
    import importlib

    monkeypatch.setenv("WDB_KB", "/tmp/some-other-kb")
    reloaded = importlib.reload(wdb_paths)
    try:
        assert reloaded.INDEX_DIR == reloaded.KB_ROOT / ".index"
        assert "mode_b" not in reloaded.INDEX_DIR.parts
    finally:
        monkeypatch.delenv("WDB_KB", raising=False)
        importlib.reload(wdb_paths)


def test_the_index_location_is_overridable_on_its_own(monkeypatch):
    import importlib

    monkeypatch.setenv("WDB_INDEX", "/tmp/an-explicit-index")
    reloaded = importlib.reload(wdb_paths)
    try:
        assert str(reloaded.INDEX_DIR) == "/tmp/an-explicit-index"
    finally:
        monkeypatch.delenv("WDB_INDEX", raising=False)
        importlib.reload(wdb_paths)
