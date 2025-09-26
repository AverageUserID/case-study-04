from app import app

def client():
    app.testing = True
    return app.test_client()

def test_requires_json():
    c = client()
    r = c.post("/v1/survey", data="hi", headers={"Content-Type": "text/plain"})
    assert r.status_code == 400

def test_validation_error():
    c = client()
    bad = {"name":"", "email":"bad", "age":9, "consent":False, "rating":9}
    r = c.post("/v1/survey", json=bad)
    assert r.status_code == 422
    assert r.json["error"] == "validation_error"

def test_happy_path():
    c = client()
    good = {"name":"Ava","email":"ava@example.com","age":22,"consent":True,"rating":4}
    r = c.post("/v1/survey", json=good)
    assert r.status_code == 201
    assert r.json["status"] == "ok"
