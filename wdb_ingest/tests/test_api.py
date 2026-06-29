"""HTTP-level checks — the gate is enforced server-side, not just in the UI."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_http_gate_forbids_contributor_signoff(client, to_pending):
    sub = to_pending()
    # a contributor-role request for the curator sign-off is refused server-side (403)
    r = client.post(f"/submissions/{sub.id}/curator-approve", headers={"X-WDB-Role": "contributor"})
    assert r.status_code == 403
    # the curator may → QUEUED
    r = client.post(f"/submissions/{sub.id}/curator-approve", headers={"X-WDB-Role": "curator"})
    assert r.status_code == 200
    assert r.json()["state"] == "QUEUED"


def test_build_requires_curator(client, to_pending):
    sub = to_pending()
    client.post(f"/submissions/{sub.id}/curator-approve", headers={"X-WDB-Role": "curator"})
    assert client.post("/build", headers={"X-WDB-Role": "contributor"}).status_code == 403
    r = client.post("/build", headers={"X-WDB-Role": "curator"})
    assert r.status_code == 200
    assert r.json()["status"] == "AWAITING_BUILD"


def test_submit_over_http_stamps_contributor(client):
    r = client.post(
        "/submit",
        params={"filename": "x.md", "format": "doc", "initiative": "ssf_research", "size_label": "1 KB"},
        content=b"# x",
        headers={"X-WDB-User": "amina"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["state"] in ("SUBMITTED", "DRAFTED")
    assert body["provenance"]["contributor"] == "amina"
    assert body["targetPlacement"] == "ssf_research/x.md"


def test_role_scoped_listing(client, to_pending):
    to_pending(filename="a.md")  # amina's
    curator_view = client.get("/submissions", headers={"X-WDB-Role": "curator"})
    assert curator_view.status_code == 200
    assert len(curator_view.json()) >= 1
    # another contributor sees none of amina's
    bob_view = client.get("/submissions", headers={"X-WDB-Role": "contributor", "X-WDB-User": "bob"})
    assert bob_view.json() == []
