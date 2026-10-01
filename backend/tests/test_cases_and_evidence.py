def test_case_lifecycle(client):
    resp = client.post("/api/cases", json={"name": "Test Case", "business_name": "Acme Ltd"})
    assert resp.status_code == 200
    case = resp.json()
    assert case["name"] == "Test Case"
    assert case["status"] == "open"
    case_id = case["id"]

    resp = client.get("/api/cases")
    assert resp.status_code == 200
    assert any(c["id"] == case_id for c in resp.json())

    resp = client.get(f"/api/cases/{case_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == case_id

    resp = client.get("/api/cases/does-not-exist")
    assert resp.status_code == 404


def test_evidence_upload_list_delete(client):
    case = client.post("/api/cases", json={"name": "Evidence Case"}).json()
    case_id = case["id"]

    resp = client.get(f"/api/cases/{case_id}/evidence/categories")
    assert resp.status_code == 200
    assert "sanction_letter" in resp.json()

    files = {"file": ("sanction.txt", b"terms: 25% margin on stock", "text/plain")}
    resp = client.post(
        f"/api/cases/{case_id}/evidence",
        files=files,
        data={"category": "sanction_letter"},
    )
    assert resp.status_code == 200
    evidence = resp.json()
    assert evidence["original_filename"] == "sanction.txt"
    assert evidence["category"] == "sanction_letter"
    assert evidence["size_bytes"] == len(b"terms: 25% margin on stock")
    evidence_id = evidence["id"]

    resp = client.get(f"/api/cases/{case_id}/evidence")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.delete(f"/api/cases/{case_id}/evidence/{evidence_id}")
    assert resp.status_code == 200

    resp = client.get(f"/api/cases/{case_id}/evidence")
    assert resp.json() == []


def test_evidence_rejects_unknown_case(client):
    files = {"file": ("x.txt", b"data", "text/plain")}
    resp = client.post("/api/cases/does-not-exist/evidence", files=files)
    assert resp.status_code == 404


def test_investigate_with_no_evidence_is_honest(client):
    case = client.post("/api/cases", json={"name": "Investigation Case"}).json()
    case_id = case["id"]

    resp = client.post(f"/api/cases/{case_id}/investigate")
    assert resp.status_code == 200
    investigation = resp.json()
    assert investigation["status"] == "no_evidence"
    assert investigation["evidence_count_considered"] == 0
    assert "No evidence" in investigation["summary"]
    assert investigation["details"] is None

    resp = client.get(f"/api/cases/{case_id}/investigations")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
