# app/tools/base_tool.py
from abc import ABC, abstractmethod
from typing import Any
import logging

logger = logging.getLogger(__name__)


class BaseTool(ABC):
   
    @property
    @abstractmethod
    def definition(self) -> dict[str, Any]: ...   # JSON schema sent to the LLM

    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @abstractmethod
    async def _run(self, **kwargs: Any) -> str: ...

    async def execute(self, **kwargs: Any) -> str:
        try:
            return await self._run(**kwargs)
        except Exception as exc:
            logger.exception("Tool %s failed", self.name)
            return f"Error: {self.name} failed ({type(exc).__name__})."