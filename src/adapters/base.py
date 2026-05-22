from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    @abstractmethod
    async def send_message(self, user_id: str, text: str) -> None:
        ...

    @abstractmethod
    async def handle_command(self, user_id: str, command: str, args: str = "") -> str:
        ...
