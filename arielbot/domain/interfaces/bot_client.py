from abc import ABC, abstractmethod


class BotClient(ABC):
    @abstractmethod
    async def send_group_msg(self, group_id: int, bot_id: int,
                              text: str = "", image: bytes = None,
                              cover: str = None) -> None:
        ...