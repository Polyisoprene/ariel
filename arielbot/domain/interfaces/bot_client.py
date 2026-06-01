from abc import ABC, abstractmethod
from typing import Optional


class BotClient(ABC):
    @abstractmethod
    async def send_group_msg(self, group_id: int, bot_id: int,
                              text: str = "", image: Optional[bytes] = None,
                              cover: Optional[str] = None) -> None:
        ...