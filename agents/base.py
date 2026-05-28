from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
