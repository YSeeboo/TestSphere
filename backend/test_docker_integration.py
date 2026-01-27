"""
测试 Docker 集成功能
用于验证 Docker SDK 是否正常工作
"""
import docker
from app.worker.utils import build_test_command


def test_docker_connection():
    """测试 Docker 连接"""
    print("=" * 60)
    print("测试 1: Docker 连接")
    print("=" * 60)
    
    try:
        client = docker.from_env()
        print("✅ Docker 连接成功")
        
        # 获取 Docker 版本信息
        version = client.version()
        print(f"Docker 版本: {version.get('Version', 'Unknown')}")
        print(f"API 版本: {version.get('ApiVersion', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ Docker 连接失败: {e}")
        return False


def test_simple_container():
    """测试简单容器运行"""
    print("\n" + "=" * 60)
    print("测试 2: 简单容器运行")
    print("=" * 60)
    
    try:
        client = docker.from_env()
        
        print("启动测试容器 (python:3.11-slim)...")
        container = client.containers.run(
            image="python:3.11-slim",
            command='bash -c "python --version && echo \'Hello from Docker!\'"',
            detach=True,
            remove=False
        )
        
        print(f"容器 ID: {container.short_id}")
        print("等待容器执行完成...")
        
        result = container.wait()
        exit_code = result.get('StatusCode', -1)
        
        print(f"退出码: {exit_code}")
        
        logs = container.logs().decode('utf-8')
        print("\n容器输出:")
        print("-" * 60)
        print(logs)
        print("-" * 60)
        
        container.remove()
        print("✅ 容器已清理")
        
        return exit_code == 0
        
    except Exception as e:
        print(f"❌ 容器运行失败: {e}")
        return False


def test_command_builder_integration():
    """测试命令构建器集成"""
    print("\n" + "=" * 60)
    print("测试 3: 命令构建器集成")
    print("=" * 60)
    
    test_cases = [
        {},
        {"marker": "smoke"},
        {"keyword": "test_login"},
        {"marker": "smoke", "keyword": "login"}
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {params}")
        try:
            cmd = build_test_command(params)
            print(f"✅ 命令构建成功")
            print(f"命令: {cmd[:100]}..." if len(cmd) > 100 else f"命令: {cmd}")
        except Exception as e:
            print(f"❌ 命令构建失败: {e}")
            return False
    
    return True


def test_volume_mount():
    """测试卷挂载功能"""
    print("\n" + "=" * 60)
    print("测试 4: 卷挂载功能")
    print("=" * 60)
    
    import tempfile
    import os
    
    try:
        # 创建临时目录和测试文件
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            with open(test_file, "w") as f:
                f.write("Hello from host!")
            
            print(f"临时目录: {tmpdir}")
            print(f"测试文件: {test_file}")
            
            client = docker.from_env()
            
            # 运行容器并读取挂载的文件
            container = client.containers.run(
                image="python:3.11-slim",
                command='bash -c "cat /app/test.txt && echo \' - read from container\'"',
                volumes={tmpdir: {'bind': '/app', 'mode': 'rw'}},
                working_dir="/app",
                detach=True,
                remove=False
            )
            
            result = container.wait()
            exit_code = result.get('StatusCode', -1)
            logs = container.logs().decode('utf-8')
            
            print(f"\n容器输出:")
            print("-" * 60)
            print(logs)
            print("-" * 60)
            
            container.remove()
            
            if exit_code == 0 and "Hello from host!" in logs:
                print("✅ 卷挂载测试成功")
                return True
            else:
                print("❌ 卷挂载测试失败")
                return False
                
    except Exception as e:
        print(f"❌ 卷挂载测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("Docker 集成测试套件")
    print("=" * 60)
    print()
    
    results = []
    
    # 测试 1: Docker 连接
    results.append(("Docker 连接", test_docker_connection()))
    
    # 如果连接失败，后续测试无法进行
    if not results[0][1]:
        print("\n⚠️  Docker 连接失败，请确保 Docker 守护进程正在运行")
        return
    
    # 测试 2: 简单容器运行
    results.append(("简单容器运行", test_simple_container()))
    
    # 测试 3: 命令构建器集成
    results.append(("命令构建器集成", test_command_builder_integration()))
    
    # 测试 4: 卷挂载功能
    results.append(("卷挂载功能", test_volume_mount()))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name:20s} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 60)
    if all_passed:
        print("🎉 所有测试通过！Docker 集成正常工作")
    else:
        print("⚠️  部分测试失败，请检查错误信息")
    print("=" * 60)


if __name__ == "__main__":
    main()
