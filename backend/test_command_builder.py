"""
测试命令构建器功能
"""
from app.worker.utils import build_test_command


def test_basic_command():
    """测试基础命令（无参数）"""
    result = build_test_command({})
    print("基础命令:")
    print(result)
    print()
    assert "pip install" in result
    assert "pytest" in result
    assert "--junitxml=report.xml" in result


def test_marker_only():
    """测试仅带 marker 参数"""
    result = build_test_command({"marker": "smoke"})
    print("带 marker 的命令:")
    print(result)
    print()
    assert '-m \\"smoke\\"' in result


def test_keyword_only():
    """测试仅带 keyword 参数"""
    result = build_test_command({"keyword": "login"})
    print("带 keyword 的命令:")
    print(result)
    print()
    assert '-k \\"login\\"' in result


def test_both_params():
    """测试同时带 marker 和 keyword"""
    result = build_test_command({"marker": "smoke", "keyword": "login"})
    print("带 marker 和 keyword 的命令:")
    print(result)
    print()
    assert '-m \\"smoke\\"' in result
    assert '-k \\"login\\"' in result


def test_special_chars():
    """测试特殊字符转义"""
    result = build_test_command({"marker": 'test"with"quotes'})
    print("带特殊字符的命令:")
    print(result)
    print()
    assert 'test\\"with\\"quotes' in result


if __name__ == "__main__":
    print("=" * 60)
    print("测试命令构建器")
    print("=" * 60)
    print()
    
    test_basic_command()
    test_marker_only()
    test_keyword_only()
    test_both_params()
    test_special_chars()
    
    print("=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
