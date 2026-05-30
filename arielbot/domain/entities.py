from dataclasses import dataclass


@dataclass
class SubTarget:
    uid: str
    nickname: str
    live_status: int


@dataclass
class SubChannel:
    uid: str
    group_id: int
    bot_id: int
    live_active: bool
    dyn_active: bool


@dataclass
class BotStatus:
    bot_id: int
    group_id: int
    push_active: bool
    bot_active: bool


@dataclass
class BiliCookie:
    data: dict
    refresh_token: str


@dataclass
class DynamicCache:
    dyn_id: str
    uname: str
    content: bytes


@dataclass
class BiliUserInfo:
    uid: str
    name: str
    is_following: bool