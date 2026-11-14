import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_admin_system_and_permissions(client: AsyncClient):
    import uuid
    suffix = uuid.uuid4().hex[:8]

    # 1. Login with the seeded Admin user (admin / 123456)
    res_admin_login = await client.post("/api/v1/auth/login", json={
        "username_or_email": "admin",
        "password": "123456"
    })
    assert res_admin_login.status_code == 200
    assert res_admin_login.json()["user"]["role"] == "ADMIN"
    admin_token = res_admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Register a new user -> must ALWAYS have role USER
    user_payload = {
        "username": f"user_{suffix}",
        "email": f"user_{suffix}@example.com",
        "password": "Password123!",
        "full_name": f"Regular User {suffix}"
    }
    res_user_reg = await client.post("/api/v1/auth/register", json=user_payload)
    assert res_user_reg.status_code == 201
    assert res_user_reg.json()["role"] == "USER"
    user_id = res_user_reg.json()["id"]

    res_user_login = await client.post("/api/v1/auth/login", json={
        "username_or_email": user_payload["username"],
        "password": user_payload["password"]
    })
    assert res_user_login.status_code == 200
    user_token = res_user_login.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 3. Unauthenticated requests -> 401 Unauthorized
    res_unauth_list = await client.get("/api/v1/users/admin/list")
    assert res_unauth_list.status_code == 401
    res_unauth_stats = await client.get("/api/v1/users/admin/stats")
    assert res_unauth_stats.status_code == 401

    # 4. Regular user trying to access admin user list -> 403 Forbidden
    res_forbidden_list = await client.get("/api/v1/users/admin/list", headers=user_headers)
    assert res_forbidden_list.status_code == 403

    # 5. Regular user trying to access admin stats -> 403 Forbidden
    res_forbidden_stats = await client.get("/api/v1/users/admin/stats", headers=user_headers)
    assert res_forbidden_stats.status_code == 403

    # 6. Regular user trying to update role -> 403 Forbidden
    res_forbidden_patch = await client.patch(
        f"/api/v1/users/{user_id}/role",
        json={"role": "ADMIN"},
        headers=user_headers
    )
    assert res_forbidden_patch.status_code == 403

    # 7. Admin user accessing default user list -> 200 OK, views ALL roles (both ADMIN and USER, with ADMIN prioritized first)
    res_admin_list = await client.get("/api/v1/users/admin/list", headers=admin_headers)
    assert res_admin_list.status_code == 200
    users_data = res_admin_list.json()
    assert isinstance(users_data, list)
    assert len(users_data) >= 2
    roles_in_default_list = {u["role"] for u in users_data}
    assert "ADMIN" in roles_in_default_list
    assert "USER" in roles_in_default_list
    assert users_data[0]["role"] == "ADMIN"
    for u in users_data:
        assert "role" in u
        assert u["role"] in ["ADMIN", "USER"]

    # 8. Admin user filtering by role
    res_filtered = await client.get("/api/v1/users/admin/list?role=ADMIN", headers=admin_headers)
    assert res_filtered.status_code == 200
    for u in res_filtered.json():
        assert u["role"] == "ADMIN"

    # 9. Admin user accessing stats
    res_stats = await client.get("/api/v1/users/admin/stats", headers=admin_headers)
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert "total_users" in stats
    assert "admin_count" in stats
    assert "user_count" in stats
    assert stats["admin_count"] >= 1

    # 10. Admin updates regular user to ADMIN -> 200 OK
    res_promote = await client.patch(
        f"/api/v1/users/{user_id}/role",
        json={"role": "ADMIN"},
        headers=admin_headers
    )
    assert res_promote.status_code == 200
    assert res_promote.json()["role"] == "ADMIN"

    # 11. Edge case: Update role with invalid value -> 422 Unprocessable Entity
    res_invalid_role = await client.patch(
        f"/api/v1/users/{user_id}/role",
        json={"role": "SUPER_ADMIN"},
        headers=admin_headers
    )
    assert res_invalid_role.status_code == 422

    # 12. Edge case: Update role of non-existent user -> 404 Not Found
    res_not_found = await client.patch(
        "/api/v1/users/non-existent-user-uuid/role",
        json={"role": "USER"},
        headers=admin_headers
    )
    assert res_not_found.status_code == 404

    # 13. Edge case: Search with special characters (%, _, ', @)
    res_special_search = await client.get(
        "/api/v1/users/admin/list?q=%25%27_@",
        headers=admin_headers
    )
    assert res_special_search.status_code == 200
    assert isinstance(res_special_search.json(), list)

    # 14. Edge case: Search with query too long (> 100 chars) -> 422
    long_query = "a" * 150
    res_too_long = await client.get(
        f"/api/v1/users/admin/list?q={long_query}",
        headers=admin_headers
    )
    assert res_too_long.status_code == 422

    # 15. Edge case: Invalid role filter query -> 422
    res_invalid_filter = await client.get(
        "/api/v1/users/admin/list?role=GUEST",
        headers=admin_headers
    )
    assert res_invalid_filter.status_code == 422

    # 16. Admin demotes user back to USER
    res_demote = await client.patch(
        f"/api/v1/users/{user_id}/role",
        json={"role": "USER"},
        headers=admin_headers
    )
    assert res_demote.status_code == 200
    assert res_demote.json()["role"] == "USER"

    # 17. Admin locks user account
    res_lock = await client.patch(
        f"/api/v1/users/{user_id}/lock",
        json={"is_locked": True},
        headers=admin_headers
    )
    assert res_lock.status_code == 200
    assert res_lock.json()["is_locked"] is True

    # 18. Locked user attempts to login -> 403 Forbidden
    res_locked_login = await client.post("/api/v1/auth/login", json={
        "username_or_email": user_payload["username"],
        "password": user_payload["password"]
    })
    assert res_locked_login.status_code == 403

    # 19. Locked user attempts to use old token -> 403 Forbidden
    res_locked_me = await client.get("/api/v1/auth/me", headers=user_headers)
    assert res_locked_me.status_code == 403

    # 20. Admin cannot lock themselves -> 400 Bad Request
    admin_id = res_admin_login.json()["user"]["id"]
    res_self_lock = await client.patch(
        f"/api/v1/users/{admin_id}/lock",
        json={"is_locked": True},
        headers=admin_headers
    )
    assert res_self_lock.status_code == 400

    # 21. Admin unlocks user account
    res_unlock = await client.patch(
        f"/api/v1/users/{user_id}/lock",
        json={"is_locked": False},
        headers=admin_headers
    )
    assert res_unlock.status_code == 200
    assert res_unlock.json()["is_locked"] is False

    # 22. User can login again successfully
    res_login_again = await client.post("/api/v1/auth/login", json={
        "username_or_email": user_payload["username"],
        "password": user_payload["password"]
    })
    assert res_login_again.status_code == 200

    # 23. Regular user forbidden from crawler config
    res_user_crawler = await client.get("/api/v1/users/admin/crawler-config", headers=user_headers)
    assert res_user_crawler.status_code == 403

    # 24. Admin gets crawler config
    res_admin_crawler = await client.get("/api/v1/users/admin/crawler-config", headers=admin_headers)
    assert res_admin_crawler.status_code == 200
    cfg = res_admin_crawler.json()
    assert "interval_minutes" in cfg
    assert "is_enabled" in cfg
    assert "recent_logs" in cfg

    # 25. Edge case: Selecting a regular USER as notify_user_id -> 400 Bad Request (chỉ cho phép Quản lý ADMIN)
    res_non_admin_notify = await client.post(
        "/api/v1/users/admin/crawler-config",
        json={
            "interval_minutes": 5,
            "is_enabled": True,
            "notify_user_id": user_id,
            "notify_mode": "ALWAYS"
        },
        headers=admin_headers
    )
    assert res_non_admin_notify.status_code == 400

    # 26. Admin updates crawler interval to 5 minutes with an ADMIN notify_user_id -> 200 OK
    res_update_crawler = await client.post(
        "/api/v1/users/admin/crawler-config",
        json={
            "interval_minutes": 5,
            "is_enabled": True,
            "notify_user_id": admin_id,
            "notify_mode": "ALWAYS"
        },
        headers=admin_headers
    )
    assert res_update_crawler.status_code == 200
    updated_cfg = res_update_crawler.json()
    assert updated_cfg["interval_minutes"] == 5
    assert updated_cfg["is_enabled"] is True
    assert updated_cfg["notify_user_id"] == admin_id
    assert updated_cfg["notify_mode"] == "ALWAYS"
    assert updated_cfg["sender_username"] == "admin"

    # 27. Edge case: Invalid notify_mode -> 422 Unprocessable Entity
    res_invalid_mode = await client.post(
        "/api/v1/users/admin/crawler-config",
        json={
            "interval_minutes": 10,
            "is_enabled": True,
            "notify_user_id": admin_id,
            "notify_mode": "SOMETIMES"
        },
        headers=admin_headers
    )
    assert res_invalid_mode.status_code == 422

    # 28. Regular user forbidden from crawler cleanup endpoint -> 403 Forbidden
    res_forbidden_cleanup = await client.post("/api/v1/users/admin/crawler-cleanup", headers=user_headers)
    assert res_forbidden_cleanup.status_code == 403

    # 29. Public endpoint reflects 5 minutes
    res_public_crawler = await client.get("/api/v1/prices/config")
    assert res_public_crawler.status_code == 200
    assert res_public_crawler.json()["interval_minutes"] == 5

    # 30. Delete user tests:
    # 30a. Regular user cannot delete user -> 403 Forbidden
    res_forbidden_del = await client.delete(f"/api/v1/users/{user_id}", headers=user_headers)
    assert res_forbidden_del.status_code == 403

    # 30b. Admin cannot delete themselves -> 400 Bad Request
    res_self_del = await client.delete(f"/api/v1/users/{admin_id}", headers=admin_headers)
    assert res_self_del.status_code == 400

    # 30c. Admin deleting non-existent user -> 404 Not Found
    res_not_found_del = await client.delete("/api/v1/users/non-existent-user-uuid", headers=admin_headers)
    assert res_not_found_del.status_code == 404

    # 30d. Admin deletes regular user -> 200 OK and user is permanently removed
    res_del_ok = await client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)
    assert res_del_ok.status_code == 200
    assert res_del_ok.json()["success"] is True
    assert res_del_ok.json()["deleted_user"]["id"] == user_id

    res_check_deleted = await client.get(f"/api/v1/users/{user_id}", headers=admin_headers)
    assert res_check_deleted.status_code == 404



