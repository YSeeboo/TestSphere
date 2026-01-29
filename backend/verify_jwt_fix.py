#!/usr/bin/env python3
"""验证 JWT 密钥安全修复的脚本."""
import os
import sys
import subprocess
from pathlib import Path

# 颜色输出
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text: str):
    """打印分隔标题."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def print_success(text: str):
    """打印成功信息."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text: str):
    """打印错误信息."""
    print(f"{RED}✗ {text}{RESET}")


def print_warning(text: str):
    """打印警告信息."""
    print(f"{YELLOW}⚠ {text}{RESET}")


def test_1_env_file_exists():
    """测试 1: 检查 .env 文件是否存在."""
    print_header("测试 1: 检查 .env 文件")
    
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print_success(f".env 文件存在: {env_file}")
        return True
    else:
        print_error(f".env 文件不存在: {env_file}")
        print_warning("请运行: cp .env.example .env")
        return False


def test_2_secret_key_in_env():
    """测试 2: 检查 .env 文件中是否有 SECRET_KEY."""
    print_header("测试 2: 检查 SECRET_KEY 配置")
    
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print_error(".env 文件不存在，跳过此测试")
        return False
    
    content = env_file.read_text()
    lines = content.split('\n')
    
    secret_key = None
    for line in lines:
        if line.strip().startswith('SECRET_KEY='):
            secret_key = line.split('=', 1)[1].strip()
            break
    
    if secret_key:
        print_success(f"找到 SECRET_KEY 配置")
        print(f"  密钥长度: {len(secret_key)} 字符")
        print(f"  密钥预览: {secret_key[:8]}...{secret_key[-8:]}")
        
        # 检查长度
        if len(secret_key) >= 32:
            print_success("密钥长度符合要求 (≥32 字符)")
        else:
            print_error(f"密钥长度不足: {len(secret_key)} < 32")
            return False
        
        # 检查是否是不安全的密钥
        insecure_keys = [
            "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
            "your-secret-key-here",
            "secret",
            "changeme",
            "your-secret-key-must-be-at-least-32-characters-long-please-change-this",
        ]
        
        if secret_key in insecure_keys:
            print_error("检测到不安全的示例密钥！")
            print_warning("请运行以下命令生成新密钥:")
            print("  python -c \"import secrets; print(secrets.token_hex(32))\"")
            return False
        else:
            print_success("未使用已知的不安全密钥")
        
        return True
    else:
        print_error("未找到 SECRET_KEY 配置")
        return False


def test_3_config_no_default():
    """测试 3: 检查 config.py 是否移除了默认值."""
    print_header("测试 3: 检查配置文件")
    
    config_file = Path(__file__).parent / "app" / "core" / "config.py"
    if not config_file.exists():
        print_error(f"配置文件不存在: {config_file}")
        return False
    
    content = config_file.read_text()
    
    # 检查是否在 Field 的 default 参数中有硬编码的默认值
    # 注意：在 INSECURE_KEYS 黑名单中包含该密钥是正确的
    if 'default="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"' in content:
        print_error("配置文件在 default 参数中仍包含硬编码的不安全密钥！")
        return False
    else:
        print_success("配置文件已移除 default 参数中的硬编码密钥")
    
    # 检查是否使用了强制配置（...）
    if 'SECRET_KEY: str = Field(\n        ...' in content or 'SECRET_KEY: str = Field(...' in content:
        print_success("SECRET_KEY 已设置为强制配置（无默认值）")
    else:
        print_warning("未检测到强制配置语法，请手动确认")
    
    # 检查是否有验证器
    if 'validate_security_settings' in content or 'model_validator' in content:
        print_success("配置文件包含安全验证器")
    else:
        print_warning("未检测到安全验证器")
    
    return True


def test_4_gitignore():
    """测试 4: 检查 .gitignore 是否排除 .env 文件."""
    print_header("测试 4: 检查 .gitignore")
    
    gitignore_paths = [
        Path(__file__).parent / ".gitignore",
        Path(__file__).parent.parent / ".gitignore",
    ]
    
    found = False
    for gitignore in gitignore_paths:
        if gitignore.exists():
            content = gitignore.read_text()
            if '.env' in content or '*.env' in content:
                print_success(f".env 已在 .gitignore 中排除: {gitignore}")
                found = True
                break
    
    if not found:
        print_error(".env 未在 .gitignore 中排除")
        print_warning("请将 .env 添加到 .gitignore 文件")
        return False
    
    return True


def test_5_import_config():
    """测试 5: 尝试导入配置（检查是否能正常加载）."""
    print_header("测试 5: 导入配置模块")
    
    # 添加项目路径
    backend_path = Path(__file__).parent
    sys.path.insert(0, str(backend_path))
    
    try:
        from app.core.config import settings
        print_success("配置模块导入成功")
        print(f"  APP_NAME: {settings.APP_NAME}")
        print(f"  DEBUG: {settings.DEBUG}")
        print(f"  SECRET_KEY 长度: {len(settings.SECRET_KEY)}")
        print(f"  SECRET_KEY 前8位: {settings.SECRET_KEY[:8]}...")
        return True
    except Exception as e:
        print_error(f"配置模块导入失败: {e}")
        return False


def test_6_reject_insecure_key():
    """测试 6: 验证系统会拒绝不安全的密钥."""
    print_header("测试 6: 验证安全检查机制")
    
    print("测试 6.1: 验证拒绝不安全的示例密钥")
    
    # 保存原始环境变量
    original_key = os.environ.get('SECRET_KEY')
    
    # 设置不安全的密钥
    test_key = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    os.environ['SECRET_KEY'] = test_key
    
    # 尝试导入配置
    try:
        # 清除已导入的模块
        if 'app.core.config' in sys.modules:
            del sys.modules['app.core.config']
        if 'app.core' in sys.modules:
            del sys.modules['app.core']
        
        from app.core.config import Settings
        settings = Settings()
        
        print_error("系统未能拒绝不安全的密钥！")
        result = False
    except ValueError as e:
        if "不安全的 SECRET_KEY" in str(e) or "INSECURE" in str(e).upper():
            print_success("系统正确拒绝了不安全的密钥")
            print(f"  错误消息: {str(e)[:80]}...")
            result = True
        else:
            print_warning(f"捕获到 ValueError，但错误消息可能不相关: {str(e)[:80]}...")
            result = False
    except Exception as e:
        print_warning(f"捕获到其他异常: {type(e).__name__}: {str(e)[:80]}...")
        result = False
    finally:
        # 恢复原始环境变量
        if original_key:
            os.environ['SECRET_KEY'] = original_key
        elif 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']
        
        # 清除模块缓存
        if 'app.core.config' in sys.modules:
            del sys.modules['app.core.config']
        if 'app.core' in sys.modules:
            del sys.modules['app.core']
    
    return result


def main():
    """运行所有测试."""
    print(f"\n{BLUE}{'*' * 70}{RESET}")
    print(f"{BLUE}{'JWT 密钥安全修复验证脚本'.center(70)}{RESET}")
    print(f"{BLUE}{'*' * 70}{RESET}")
    
    tests = [
        ("检查 .env 文件是否存在", test_1_env_file_exists),
        ("检查 SECRET_KEY 配置", test_2_secret_key_in_env),
        ("检查配置文件修改", test_3_config_no_default),
        ("检查 .gitignore", test_4_gitignore),
        ("导入配置模块", test_5_import_config),
        ("验证安全检查机制", test_6_reject_insecure_key),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"测试异常: {e}")
            results.append((name, False))
    
    # 打印总结
    print_header("测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")
    
    print(f"\n{BLUE}{'─' * 70}{RESET}")
    if passed == total:
        print_success(f"所有测试通过！({passed}/{total})")
        print_success("JWT 密钥安全修复验证成功！✨")
        return 0
    else:
        print_warning(f"部分测试失败：{passed}/{total} 通过")
        print_warning("请根据上述错误信息进行修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())
