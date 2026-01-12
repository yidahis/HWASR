import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
from ..models.schemas import TaskStatus

logger = logging.getLogger(__name__)


class TaskManager:
    """任务状态管理器"""

    def __init__(self):
        self.tasks: Dict[str, TaskStatus] = {}
        self.lock = asyncio.Lock()

    async def create_task(self, task_id: str) -> TaskStatus:
        """创建新任务"""
        async with self.lock:
            task = TaskStatus(
                task_id=task_id,
                status="pending",
                progress=0.0,
                message="任务已创建"
            )
            self.tasks[task_id] = task
            return task

    async def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        result_id: Optional[str] = None
    ) -> bool:
        """更新任务状态"""
        async with self.lock:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]

            if status is not None:
                task.status = status
            if progress is not None:
                task.progress = progress
            if message is not None:
                task.message = message
            if result_id is not None:
                task.result_id = result_id

            return True

    async def get_task(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        async with self.lock:
            return self.tasks.get(task_id)

    async def cleanup_task(self, task_id: str):
        """清理已完成或失败的任务"""
        async with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status in ["completed", "failed"]:
                    del self.tasks[task_id]


# 全局任务管理器实例
task_manager = TaskManager()
