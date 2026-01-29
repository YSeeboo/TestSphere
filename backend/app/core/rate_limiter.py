"""简单的速率限制器实现."""

import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status


class RateLimiter:
    """
    简单的内存速率限制器.

    使用滑动窗口算法，基于 IP 地址限制请求频率。

    注意：这是一个基于内存的简单实现，适用于单实例部署。
    生产环境建议使用 Redis 作为存储后端以支持分布式部署。
    """

    def __init__(self):
        """初始化速率限制器."""
        # 存储格式: {(ip, endpoint): [(timestamp1, timestamp2, ...)]}
        self._requests: Dict[Tuple[str, str], list[float]] = defaultdict(list)

    def check_rate_limit(
        self,
        request: Request,
        max_requests: int = 5,
        window_seconds: int = 60,
    ) -> None:
        """
        检查请求是否超过速率限制.

        Args:
            request: FastAPI 请求对象
            max_requests: 时间窗口内允许的最大请求数
            window_seconds: 时间窗口大小（秒）

        Raises:
            HTTPException: 429 Too Many Requests 如果超过限制
        """
        # 获取客户端 IP
        client_ip = self._get_client_ip(request)

        # 获取端点路径
        endpoint = request.url.path

        # 创建键
        key = (client_ip, endpoint)

        # 当前时间
        current_time = time.time()

        # 清理过期的请求记录（超出时间窗口）
        cutoff_time = current_time - window_seconds
        self._requests[key] = [
            ts for ts in self._requests[key]
            if ts > cutoff_time
        ]

        # 检查是否超过限制
        if len(self._requests[key]) >= max_requests:
            # 计算重试时间
            oldest_request = self._requests[key][0]
            retry_after = int(oldest_request + window_seconds - current_time)

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"请求过于频繁，请在 {retry_after} 秒后重试",
                headers={"Retry-After": str(retry_after)},
            )

        # 记录本次请求
        self._requests[key].append(current_time)

    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端真实 IP 地址.

        优先从 X-Forwarded-For 或 X-Real-IP 头获取（反向代理场景）。

        Args:
            request: FastAPI 请求对象

        Returns:
            str: 客户端 IP 地址
        """
        # 尝试从头部获取真实 IP（考虑反向代理）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For 可能包含多个 IP，取第一个
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # 直接连接的情况
        if request.client:
            return request.client.host

        return "unknown"

    def cleanup(self, max_age_seconds: int = 3600) -> None:
        """
        清理旧的请求记录（可选的定期维护任务）.

        Args:
            max_age_seconds: 保留记录的最大时长（秒）
        """
        current_time = time.time()
        cutoff_time = current_time - max_age_seconds

        # 清理所有过期记录
        keys_to_delete = []
        for key, timestamps in self._requests.items():
            # 过滤掉过期的时间戳
            self._requests[key] = [ts for ts in timestamps if ts > cutoff_time]

            # 如果没有剩余记录，标记删除
            if not self._requests[key]:
                keys_to_delete.append(key)

        # 删除空记录
        for key in keys_to_delete:
            del self._requests[key]


# 全局速率限制器实例
rate_limiter = RateLimiter()
