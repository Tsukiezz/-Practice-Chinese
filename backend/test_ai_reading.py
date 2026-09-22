"""Automated tests for AI Reading & Pronunciation Assessment."""
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient

from main import app, hash_password
from database import database
from ai_reading import (
    init_reading_tables,
    load_reading_topics,
    normalize_pinyin_to_tone_number,
    evaluate_pronunciation_offline,
)


@pytest.fixture(scope="module")
def client():
    with database() as conn:
        init_reading_tables(conn)
    return TestClient(app)


@pytest.fixture(scope="module")
def student_auth(client):
    email = "test_student_reading@example.test"
    password = "ReadingPassword123@"
    # Ensure test user exists
    with database() as conn:
        row = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if not row:
            salt = "11" * 16
            pwd_hash = hash_password(password, salt)
            conn.execute(
                "INSERT INTO users(name, email, password_hash, salt, role, is_active, created_at) VALUES(?,?,?,?,?,?,?)",
                ("Reading Tester", email, pwd_hash, salt, "student", 1, 1000000),
            )
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


def test_reading_topics(client):
    """Verify list of 22 topics is returned."""
    res = client.get("/api/reading/topics")
    assert res.status_code == 200
    topics = res.json()
    assert len(topics) >= 20
    topic_ids = [t["id"] for t in topics]
    assert "family" in topic_ids
    assert "food" in topic_ids
    assert "home" in topic_ids
    assert "school" in topic_ids
    assert "work" in topic_ids
    assert "travel" in topic_ids


def test_reading_vocabulary_hsk(client):
    """Verify vocabulary can be filtered by HSK 1 through HSK 6."""
    for hsk in (1, 2, 3, 4, 5, 6):
        res = client.get(f"/api/reading/vocabulary?hsk={hsk}&limit=10")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] > 0
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["hsk"] == hsk
            assert "hanzi" in item
            assert "pinyin" in item
            assert "meaning" in item


def test_reading_vocabulary_topic(client):
    """Verify vocabulary can be filtered by topic."""
    res = client.get("/api/reading/vocabulary?topic=family&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    assert len(data["items"]) > 0


def test_pinyin_normalization():
    """Verify pinyin with diacritics is accurately converted to tone numbers."""
    assert normalize_pinyin_to_tone_number("nǐ hǎo") == "ni3 hao3"
    assert normalize_pinyin_to_tone_number("mā ma") == "ma1 ma5"
    assert normalize_pinyin_to_tone_number("xué xí") == "xue2 xi2"


def test_offline_pronunciation_evaluator():
    """Verify rule-based pronunciation evaluation and error detection."""
    # 1. Exact match
    res_exact = evaluate_pronunciation_offline("你好", "nǐ hǎo", "你好")
    assert res_exact["accuracy_percent"] == 100.0
    assert res_exact["rating"] == "Xuất sắc"
    assert len(res_exact["errors"]) == 0

    # 2. Empty speech
    res_empty = evaluate_pronunciation_offline("你好", "nǐ hǎo", "")
    assert res_empty["accuracy_percent"] == 0.0
    assert res_empty["rating"] == "Chưa đạt"
    assert len(res_empty["errors"]) > 0

    # 3. Partial or different pronunciation
    res_diff = evaluate_pronunciation_offline("学习", "xuéxí", "xue1 xi1")
    assert 10.0 <= res_diff["accuracy_percent"] <= 95.0
    assert len(res_diff["corrections"]) > 0


def test_reading_evaluate_endpoint(client, student_auth):
    """Test full reading evaluation API with user authentication & history persistence."""
    payload = {
        "target_hanzi": "学习",
        "target_pinyin": "xuéxí",
        "target_meaning": "Học tập",
        "spoken_text": "学习",
        "save_history": True,
    }
    res = client.post("/api/reading/evaluate", json=payload, headers=student_auth)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["target_hanzi"] == "学习"
    assert 0.0 <= data["accuracy_percent"] <= 100.0
    assert data["rating"] in ("Xuất sắc", "Tốt", "Cần cải thiện", "Chưa đạt", "Đạt")
    assert "tone_score" in data
    assert "phoneme_score" in data
    assert "errors" in data
    assert "corrections" in data
    assert data["history_id"] is not None

    # Check that item appears in reading history
    history_res = client.get("/api/me/reading/history", headers=student_auth)
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert history_data["total"] >= 1
    found = any(item["id"] == data["history_id"] for item in history_data["items"])
    assert found
