"""
异步任务管理器 - 用于将耗时的拍照/OCR/LLM 操作放到后台执行，避免 HTTP 请求超时。

使用方式:
1. 提交任务: task_manager.submit(task_func, *args, **kwargs) -> task_id
2. 轮询状态: task_manager.get_status(task_id) -> TaskStatus
3. 获取结果: task_manager.get_result(task_id) -> dict

前端工作流:
1. POST /experiments/{id}/run-test → 返回 {"task_id": "xxx", "status": "pending"}
2. GET /tasks/{task_id} → 轮询直到 status 为 completed/failed
3. 获取最终结果
"""

import asyncio
import logging
import time
import uuid
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskInfo:
    task_id: str
    status: TaskState = TaskState.PENDING
    progress: float = 0.0          # 0.0 ~ 1.0
    message: str = ""
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


class TaskManager:
    """
    基于线程池的异步任务管理器。

    将耗时操作（如拍照 + OCR + LLM）提交到后台线程执行，
    通过 task_id 查询执行进度和结果。
    """

    def __init__(self, max_workers: int = 4, ttl_seconds: float = 3600):
        self._tasks: Dict[str, TaskInfo] = {}
        self._lock = threading.Lock()
        self._max_workers = max_workers
        self._ttl_seconds = ttl_seconds

    def submit(self, func: Callable, *args, task_id: str = None, **kwargs) -> str:
        """
        提交一个同步函数到后台线程执行。

        Args:
            func: 要执行的函数（同步）
            *args: 函数参数
            task_id: 可选的任务 ID，不传则自动生成
            **kwargs: 函数关键字参数

        Returns:
            task_id
        """
        if task_id is None:
            task_id = uuid.uuid4().hex[:12]

        info = TaskInfo(task_id=task_id)
        with self._lock:
            self._tasks[task_id] = info

        def _run():
            info.status = TaskState.RUNNING
            info.started_at = time.time()
            try:
                result = func(*args, **kwargs)
                info.result = result
                info.status = TaskState.COMPLETED
                info.progress = 1.0
            except Exception as e:
                logger.exception(f"Task {task_id} failed: {e}")
                info.error = str(e)
                info.status = TaskState.FAILED
            finally:
                info.completed_at = time.time()

        thread = threading.Thread(target=_run, name=f"task-{task_id}", daemon=True)
        thread.start()
        logger.info(f"Task {task_id} submitted: {func.__name__}")
        return task_id

    def get_status(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务状态"""
        with self._lock:
            return self._tasks.get(task_id)

    def update_progress(self, task_id: str, progress: float, message: str = ""):
        """更新任务进度（可在任务函数内部调用）"""
        with self._lock:
            info = self._tasks.get(task_id)
            if info:
                info.progress = max(0.0, min(1.0, progress))
                if message:
                    info.message = message

    def cleanup(self):
        """清理已过期（TTL）的已完成/失败任务"""
        now = time.time()
        with self._lock:
            expired = [
                tid for tid, info in self._tasks.items()
                if info.completed_at and (now - info.completed_at) > self._ttl_seconds
            ]
            for tid in expired:
                del self._tasks[tid]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired tasks")


# 全局单例
task_manager = TaskManager()
