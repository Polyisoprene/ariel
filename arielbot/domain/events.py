from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class DynamicDetected:
    dynamic: object
    dyn_id: str
    uname: str
    targets: List[Tuple[int, int]]
    rendered_image: bytes


@dataclass
class LiveStatusChanged:
    uid: str
    uname: str
    room_id: str
    title: str
    cover_url: str
    is_live: bool
    targets: List[Tuple[int, int]]


@dataclass
class BotConnected:
    bot_id: int


@dataclass
class BotDisconnected:
    bot_id: int


@dataclass
class BotShutdown:
    pass