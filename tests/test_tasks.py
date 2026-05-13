def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_task(client, sample_task):
    resp = client.post("/api/v1/tasks/", json=sample_task)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == sample_task["title"]
    assert data["description"] == sample_task["description"]
    assert data["completed"] is False
    assert "id" in data
    assert "created_at" in data


def test_list_tasks_empty(client):
    resp = client.get("/api/v1/tasks/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tasks(client, sample_task):
    client.post("/api/v1/tasks/", json=sample_task)
    client.post("/api/v1/tasks/", json={"title": "Second task"})

    resp = client.get("/api/v1/tasks/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["title"] == "Test task"
    assert data[1]["title"] == "Second task"


def test_get_task(client, sample_task):
    create_resp = client.post("/api/v1/tasks/", json=sample_task)
    task_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == sample_task["title"]


def test_get_task_not_found(client):
    resp = client.get("/api/v1/tasks/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Task not found"


def test_update_task(client, sample_task):
    create_resp = client.post("/api/v1/tasks/", json=sample_task)
    task_id = create_resp.json()["id"]

    resp = client.put(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Updated", "completed": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated"
    assert data["completed"] is True
    assert data["description"] == sample_task["description"]


def test_update_task_not_found(client):
    resp = client.put("/api/v1/tasks/9999", json={"title": "Nope"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Task not found"


def test_delete_task(client, sample_task):
    create_resp = client.post("/api/v1/tasks/", json=sample_task)
    task_id = create_resp.json()["id"]

    resp = client.delete(f"/api/v1/tasks/{task_id}")
    assert resp.status_code == 204

    get_resp = client.get(f"/api/v1/tasks/{task_id}")
    assert get_resp.status_code == 404


def test_delete_task_not_found(client):
    resp = client.delete("/api/v1/tasks/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Task not found"


def test_create_task_missing_title(client):
    resp = client.post("/api/v1/tasks/", json={"description": "no title"})
    assert resp.status_code == 422


def test_create_task_extra_fields_ignored(client):
    resp = client.post(
        "/api/v1/tasks/",
        json={"title": "OK", "extra": "should be ignored"},
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "OK"
