from abc import ABC, abstractmethod
from typing import Any, List, Optional


class BiliAuthAPI(ABC):
    @abstractmethod
    async def get_qrcode(self) -> Optional[str]:
        ...

    @abstractmethod
    async def poll_scan(self) -> Optional[dict]:
        ...


class BiliContentAPI(ABC):
    @abstractmethod
    async def get_follow_dynamics(self) -> Optional[list]:
        ...

    @abstractmethod
    async def get_dynamic_by_id(self, dyn_id: str) -> Optional[Any]:
        ...

    @abstractmethod
    async def get_room_info_by_uids(self, uids: List[str]) -> Optional[dict]:
        ...

    @abstractmethod
    async def get_user_info(self, uid: str) -> Optional[dict | str]:
        ...

    @abstractmethod
    async def follow_user(self, uid: str, act: int) -> Optional[bool]:
        ...