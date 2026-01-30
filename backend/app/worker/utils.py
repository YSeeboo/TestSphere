"""
Worker utilities for building test execution commands.
"""


def build_test_command(params: dict) -> str:
    """
    构建 Docker 容器内部的测试执行命令。
    
    Args:
        params: 参数字典，支持以下键:
            - marker (str, optional): pytest marker 标记，如 "smoke"
            - keyword (str, optional): pytest 关键字过滤，如 "login"
    
    Returns:
        str: 完整的 bash 命令字符串
    
    Example:
        >>> build_test_command({"marker": "smoke", "keyword": "login"})
        'bash -c "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt && pytest -m \\"smoke\\" -k \\"login\\" --junitxml=report.xml"'
    """
    # 基础依赖安装命令
    install_cmd = "pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt"
    
    # 基础 pytest 命令
    pytest_cmd = "pytest"
    
    # 拼接 marker 参数
    marker = params.get("marker") or params.get("marker_expression")
    if marker:
        # 转义内部引号
        escaped_marker = marker.replace('"', '\\"')
        pytest_cmd += f' -m \\"{escaped_marker}\\"'
    
    # 拼接 keyword 参数
    keyword = params.get("keyword") or params.get("keyword_expression")
    if keyword:
        # 转义内部引号
        escaped_keyword = keyword.replace('"', '\\"')
        pytest_cmd += f' -k \\"{escaped_keyword}\\"'
    
    # 总是追加 JUnit XML 报告输出
    pytest_cmd += " --junitxml=report.xml"
    
    # 组合完整命令
    full_command = f'bash -c "{install_cmd} && {pytest_cmd}"'
    
    return full_command
