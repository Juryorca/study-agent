"""Smoke tests for course CRUD endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_course(client: AsyncClient):
    res = await client.post("/api/courses", json={"name": "测试课程", "category": "计算机", "description": "一门测试课"})
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "测试课程"
    assert data["category"] == "计算机"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_courses(client: AsyncClient):
    # Create one first
    await client.post("/api/courses", json={"name": "课程A"})
    await client.post("/api/courses", json={"name": "课程B"})
    res = await client.get("/api/courses")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert len(data["courses"]) >= 2


@pytest.mark.asyncio
async def test_get_course_not_found(client: AsyncClient):
    res = await client.get("/api/courses/nonexistent-id")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_delete_course(client: AsyncClient):
    res = await client.post("/api/courses", json={"name": "待删除"})
    cid = res.json()["id"]
    res2 = await client.delete(f"/api/courses/{cid}")
    assert res2.status_code == 200
    # Verify deleted
    res3 = await client.get(f"/api/courses/{cid}")
    assert res3.status_code == 404


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    res = await client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_knowledge_list_empty(client: AsyncClient):
    res = await client.get("/api/knowledge?course_id=nonexistent")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["knowledge_points"] == []


@pytest.mark.asyncio
async def test_agent_sessions_empty(client: AsyncClient):
    res = await client.get("/api/agent/sessions?course_id=nonexistent")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_exams_list_empty(client: AsyncClient):
    res = await client.get("/api/exams?course_id=nonexistent")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
