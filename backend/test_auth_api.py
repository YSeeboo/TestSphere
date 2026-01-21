"""认证 API 测试脚本."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"


async def test_auth_flow() -> None:
    """测试完整的认证流程."""
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("🧪 开始测试认证模块")
        print("=" * 60)
        
        # 1. 测试健康检查
        print("\n1️⃣ 测试健康检查接口...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        assert response.status_code == 200
        
        # 2. 测试用户注册
        print("\n2️⃣ 测试用户注册...")
        register_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123"
        }
        response = await client.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 201:
            user_data = response.json()
            print(f"   用户创建成功: {user_data['username']} ({user_data['email']})")
        else:
            print(f"   响应: {response.json()}")
        
        # 3. 测试用户登录 (OAuth2 表单)
        print("\n3️⃣ 测试用户登录 (OAuth2)...")
        login_data = {
            "username": "test@example.com",  # OAuth2 使用 username 字段传递邮箱
            "password": "password123"
        }
        response = await client.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print(f"   登录成功！")
            print(f"   Access Token: {access_token[:50]}...")
        else:
            print(f"   响应: {response.json()}")
            return
        
        # 4. 测试获取当前用户信息
        print("\n4️⃣ 测试获取当前用户信息...")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(f"{BASE_URL}/users/me", headers=headers)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"   用户信息:")
            print(f"     - ID: {user_data['id']}")
            print(f"     - 用户名: {user_data['username']}")
            print(f"     - 邮箱: {user_data['email']}")
            print(f"     - 激活状态: {user_data['is_active']}")
            print(f"     - 超级管理员: {user_data['is_superuser']}")
        else:
            print(f"   响应: {response.json()}")
        
        # 5. 测试无 Token 访问保护接口
        print("\n5️⃣ 测试无 Token 访问保护接口...")
        response = await client.get(f"{BASE_URL}/users/me")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        assert response.status_code == 401
        
        # 6. 测试更新用户信息
        print("\n6️⃣ 测试更新用户信息...")
        update_data = {"username": "updated_testuser"}
        response = await client.put(
            f"{BASE_URL}/users/me",
            json=update_data,
            headers=headers
        )
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"   更新成功！新用户名: {user_data['username']}")
        else:
            print(f"   响应: {response.json()}")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_auth_flow())
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
