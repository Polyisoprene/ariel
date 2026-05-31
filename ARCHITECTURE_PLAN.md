# arielBot 架构重构方案

> 生成时间: 2026-05-31
> 当前版本: 0.4.9
> 目标: Clean Architecture 四层架构 + 事件驱动 + 完全符合设计模式六大原则

---

## 一、目录结构

```
arielbot/
├── __init__.py                     # CLI 入口 (click group)
├── bot.py                          # NoneBot 初始化，加载插件
├── domain/                         # 领域层（不依赖任何外层）
│   ├── __init__.py
│   ├── entities.py                 # 实体 + 值对象
│   ├── events.py                   # 领域事件定义
│   └── interfaces/                 # 抽象接口 (ABC)
│       ├── __init__.py
│       ├── repository.py           # 仓储接口
│       ├── api.py                  # B站API接口
│       ├── renderer.py             # 渲染器接口
│       └── event_bus.py            # 事件总线接口
├── application/                    # 应用层（依赖 Domain 接口）
│   ├── __init__.py
│   ├── auth_service.py             # 登录服务
│   ├── subscription_service.py     # 订阅管理服务
│   ├── query_service.py            # 查询服务
│   ├── bot_status_service.py       # Bot状态服务
│   └── push/                       # 推送子系统
│       ├── __init__.py
│       ├── check_jobs.py           # 定时检查任务
│       └── handlers.py             # 事件处理器
├── presentation/                   # 表现层（依赖 Application 服务）
│   ├── __init__.py
│   ├── commands/                   # 命令注册
│   │   ├── __init__.py
│   │   ├── registry.py             # 命令注册器
│   │   ├── auth_commands.py
│   │   ├── sub_commands.py
│   │   └── query_commands.py
│   ├── scheduler/                  # 定时任务
│   │   └── __init__.py
│   └── middleware/                 # 权限/规则
│       └── __init__.py
├── infrastructure/                 # 基础设施层（实现 Domain 接口）
│   ├── __init__.py
│   ├── database.py                 # 数据库连接管理
│   ├── repositories/               # 仓储实现
│   │   ├── __init__.py
│   │   ├── sub_repository.py
│   │   ├── bot_repository.py
│   │   ├── cookie_repository.py
│   │   └── dyn_repository.py
│   ├── adapters/                   # 外部适配器
│   │   ├── __init__.py
│   │   ├── bili_api.py             # B站API实现
│   │   ├── bili_auth.py            # 登录 + Cookie管理
│   │   ├── bili_wbi.py             # WBI签名
│   │   ├── renderer.py             # Skia渲染器
│   │   └── bot_client.py           # NoneBot客户端封装
│   ├── event_bus.py                # 事件总线实现
│   └── container.py                # DI容器
├── plugins/Core/                   # 保留原有入口
│   └── __init__.py                 # 组装所有模块并启动
```

---

## 二、分层职责

### 2.1 Domain Layer（领域层）— 不依赖任何外层

#### domain/entities.py

```python
from dataclasses import dataclass
from dynamicadaptor.Message import RenderMessage

@dataclass
class SubTarget:
    uid: str
    nickname: str
    live_status: int  # 0=未开播 1=开播中

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
    content: bytes  # pickle.dumps(RenderMessage)

@dataclass
class BiliUserInfo:
    uid: str
    name: str
    is_following: bool
```

#### domain/events.py

```python
from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class DynamicDetected:
    dynamic: object        # RenderMessage
    dyn_id: str
    uname: str
    targets: List[Tuple[int, int]]  # [(group_id, bot_id), ...]
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
```

#### domain/interfaces/event_bus.py

```python
from abc import ABC, abstractmethod
from typing import Any, Callable, Type


class EventBus(ABC):
    @abstractmethod
    async def publish(self, event: Any) -> None:
        ...

    @abstractmethod
    def subscribe(self, event_type: Type, handler: Callable) -> None:
        ...
```

#### domain/interfaces/repository.py

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from arielbot.domain.entities import SubTarget, SubChannel, BotStatus, BiliCookie, DynamicCache


class SubTargetRepository(ABC):
    @abstractmethod
    async def get(self, uid: str) -> Optional[SubTarget]:
        ...

    @abstractmethod
    async def save(self, target: SubTarget) -> None:
        ...

    @abstractmethod
    async def update_live_status(self, uid: str, uname: str, status: int) -> None:
        ...


class SubChannelRepository(ABC):
    @abstractmethod
    async def get(self, uid: str, group_id: int, bot_id: int) -> Optional[SubChannel]:
        ...

    @abstractmethod
    async def save(self, channel: SubChannel) -> None:
        ...

    @abstractmethod
    async def update(self, channel: SubChannel) -> None:
        ...

    @abstractmethod
    async def find_push_targets_for_dyn(self, uid: str) -> List[Tuple[int, int]]:
        ...

    @abstractmethod
    async def find_push_targets_for_live(self, uid: str) -> List[Tuple[int, int]]:
        ...

    @abstractmethod
    async def find_live_check_uids(self) -> List[Tuple[str, int]]:
        ...

    @abstractmethod
    async def list_by_group(self, bot_id: int, group_id: int) -> List[Tuple[str, str, bool, bool]]:
        ...


class BotStatusRepository(ABC):
    @abstractmethod
    async def get(self, bot_id: int, group_id: int) -> Optional[BotStatus]:
        ...

    @abstractmethod
    async def save(self, status: BotStatus) -> None:
        ...

    @abstractmethod
    async def update_push(self, bot_id: int, group_id: int, active: bool) -> None:
        ...

    @abstractmethod
    async def update_active(self, bot_id: int, active: bool) -> None:
        ...

    @abstractmethod
    async def list_all_bots(self) -> List[int]:
        ...

    @abstractmethod
    async def shutdown_all(self) -> None:
        ...


class CookieRepository(ABC):
    @abstractmethod
    async def get(self) -> Optional[BiliCookie]:
        ...

    @abstractmethod
    async def save(self, cookie: BiliCookie) -> None:
        ...

    @abstractmethod
    async def update(self, cookie: BiliCookie, old_refresh_token: str) -> None:
        ...

    @abstractmethod
    async def clear(self) -> None:
        ...


class DynCacheRepository(ABC):
    @abstractmethod
    async def exists(self, dyn_id: str) -> bool:
        ...

    @abstractmethod
    async def save(self, cache: DynamicCache) -> None:
        ...

    @abstractmethod
    async def get(self, dyn_id: str) -> Optional[bytes]:
        ...
```

#### domain/interfaces/api.py

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from arielbot.domain.entities import BiliUserInfo


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
    async def get_dynamic_by_id(self, dyn_id: str) -> Optional[object]:
        ...

    @abstractmethod
    async def get_live_users(self) -> Optional[dict]:
        ...

    @abstractmethod
    async def get_room_info_by_uids(self, uids: List[str]) -> Optional[dict]:
        ...

    @abstractmethod
    async def get_user_info(self, uid: str) -> Optional[BiliUserInfo]:
        ...

    @abstractmethod
    async def follow_user(self, uid: str, act: int) -> bool:
        ...
```

#### domain/interfaces/renderer.py

```python
from abc import ABC, abstractmethod
from typing import List, Tuple


class DynRenderer(ABC):
    @abstractmethod
    async def render(self, dynamic: object) -> bytes:
        ...


class SubListRenderer(ABC):
    @abstractmethod
    async def render(self, data: List[Tuple[str, str, bool, bool]]) -> bytes:
        ...
```

---

### 2.2 Application Layer（应用层）— 依赖 Domain 接口

#### application/auth_service.py

```python
class AuthService:
    def __init__(self,
                 auth_api: BiliAuthAPI,
                 cookie_repo: CookieRepository,
                 bot_client: BotClient):
        self._auth_api = auth_api
        self._cookie_repo = cookie_repo
        self._bot_client = bot_client

    async def login(self, event) -> None:
        """
        扫码登录流程：
        1. 获取二维码 URL
        2. 发送二维码图片到群
        3. 轮询扫描结果
        4. 解析 cookie
        5. 存储 cookie
        """
        ...
```

#### application/subscription_service.py

```python
class SubscriptionService:
    def __init__(self,
                 content_api: BiliContentAPI,
                 sub_target_repo: SubTargetRepository,
                 sub_channel_repo: SubChannelRepository):
        self._api = content_api
        self._target_repo = sub_target_repo
        self._channel_repo = sub_channel_repo

    async def add_sub(self, uid: str, group_id: int, bot_id: int) -> str:
        """
        添加订阅：
        1. 检查是否已订阅
        2. 如果已存在但 disabled，重新启用
        3. 如果不存在，查用户信息 + 自动关注 + 写入数据库
        """
        ...

    async def del_sub(self, uid: str, group_id: int, bot_id: int) -> str:
        """删除订阅：设置 live_active=0, dyn_active=0"""
        ...

    async def toggle_live(self, uid: str, group_id: int, bot_id: int, active: bool) -> str:
        ...

    async def toggle_dyn(self, uid: str, group_id: int, bot_id: int, active: bool) -> str:
        ...
```

#### application/query_service.py

```python
class QueryService:
    def __init__(self,
                 content_api: BiliContentAPI,
                 dyn_cache_repo: DynCacheRepository,
                 sub_channel_repo: SubChannelRepository,
                 dyn_renderer: DynRenderer,
                 sub_list_renderer: SubListRenderer):
        ...

    async def get_dyn_image(self, dyn_id: str) -> Optional[bytes]:
        """查询动态图片（缓存优先，缓存未命中则拉取API）"""
        ...

    async def get_dyn_images(self, dyn_id: str) -> Optional[list]:
        """提取动态中的原始图片 URL 列表"""
        ...

    async def get_sub_list(self, bot_id: int, group_id: int) -> Optional[bytes]:
        """获取订阅列表渲染图片"""
        ...

    async def get_help_image(self) -> str:
        """获取帮助图片 URL"""
        ...
```

#### application/bot_status_service.py

```python
class BotStatusService:
    def __init__(self,
                 bot_repo: BotStatusRepository,
                 event_bus: EventBus):
        self._repo = bot_repo
        self._bus = event_bus

    async def toggle_push(self, bot_id: int, group_id: int, active: bool) -> Optional[str]:
        """切换群内推送到开启/关闭状态"""
        ...

    async def on_bot_connect(self, bot_id: int) -> None:
        """Bot 连接时设置 bot_active=1"""
        ...

    async def on_bot_disconnect(self, bot_id: int) -> None:
        """Bot 断开时设置 bot_active=0"""
        ...

    async def shutdown_all(self) -> None:
        """关闭所有 Bot"""
        ...
```

#### application/push/check_jobs.py

```python
class DynCheckJob:
    def __init__(self,
                 content_api: BiliContentAPI,
                 dyn_cache_repo: DynCacheRepository,
                 sub_channel_repo: SubChannelRepository,
                 dyn_renderer: DynRenderer,
                 event_bus: EventBus):
        ...

    async def run(self):
        """
        每 8 秒执行：
        1. 获取关注列表最新动态
        2. 对每条动态查缓存去重
        3. 查询推送目标群
        4. 渲染动态图片
        5. 缓存动态
        6. 发布 DynamicDetected 事件
        """
        ...


class LiveCheckJob:
    def __init__(self,
                 content_api: BiliContentAPI,
                 sub_target_repo: SubTargetRepository,
                 sub_channel_repo: SubChannelRepository,
                 event_bus: EventBus):
        ...

    async def run(self):
        """
        每 10 秒执行：
        1. 获取所有需要检查的 UID 列表
        2. 批量查询房间状态
        3. 对比状态变化
        4. 更新 live_status
        5. 发布 LiveStatusChanged 事件
        """
        ...
```

#### application/push/handlers.py

```python
class DynPushHandler:
    def __init__(self, bot_client: BotClient):
        self._client = bot_client

    async def handle(self, event: DynamicDetected):
        """接收 DynamicDetected 事件，向目标群发送动态推送消息"""
        for gid, bid in event.targets:
            message = f"{event.uname}发布了新动态:\n\n传送门→https://t.bilibili.com/{event.dyn_id}"
            await self._client.send_group_msg(gid, bid, message, image=event.rendered_image)


class LivePushHandler:
    def __init__(self, bot_client: BotClient):
        self._client = bot_client

    async def handle(self, event: LiveStatusChanged):
        """接收 LiveStatusChanged 事件，向目标群发送开播消息"""
        if not event.is_live:
            return
        for gid, bid in event.targets:
            message = f"【{event.uname}】开播啦!!!\n\n标题：{event.title}\n\n传送门：https://live.bilibili.com/{event.room_id}"
            await self._client.send_group_msg(gid, bid, message, cover=event.cover_url)


class BotLifecycleHandler:
    def __init__(self, bot_status_service: BotStatusService):
        self._service = bot_status_service

    async def on_connect(self, event: BotConnected):
        await self._service.on_bot_connect(event.bot_id)

    async def on_disconnect(self, event: BotDisconnected):
        await self._service.on_bot_disconnect(event.bot_id)

    async def on_shutdown(self, event: BotShutdown):
        await self._service.shutdown_all()
```

---

### 2.3 Presentation Layer（表现层）— 依赖 Application 服务

#### presentation/commands/registry.py

```python
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment


class CommandRegistry:
    _matchers = {}

    @classmethod
    def register(cls, name: str, handler, *,
                 permission=None, aliases=None, rule=None) -> None:
        matcher = on_command(name, permission=permission,
                             aliases=aliases, rule=rule)
        @matcher.handle()
        async def _():
            await handler()

    @classmethod
    def register_all(cls, services) -> None:
        """集中注册所有命令"""
        # 登录
        cls.register("login", make_login_handler(services.auth_service),
                     permission=SUPERUSER, aliases={"登录"})

        # 订阅管理
        cls.register("sub", make_sub_handler(services.sub_service),
                     permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                     rule=bot_is_active, aliases={"订阅"})

        cls.register("unsub", make_unsub_handler(services.sub_service),
                     permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                     rule=bot_is_active, aliases={"删除"})

        cls.register("live_on", make_live_toggle_handler(services.sub_service, True),
                     permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                     rule=bot_is_active)

        cls.register("live_off", make_live_toggle_handler(services.sub_service, False),
                     permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                     rule=bot_is_active)

        cls.register("dyn_on", make_dyn_toggle_handler(services.sub_service, True),
                     permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                     rule=bot_is_active)

        cls.register("dyn_off", make_dyn_toggle_handler(services.sub_service, False),
                     permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER,
                     rule=bot_is_active)

        # Bot 状态
        cls.register("bot_on", make_bot_status_handler(services.bot_status_service, True),
                     permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)

        cls.register("bot_off", make_bot_status_handler(services.bot_status_service, False),
                     permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)

        # 查询
        cls.register("list", make_list_handler(services.query_service),
                     rule=bot_is_active, aliases={"列表"})

        cls.register("help", make_help_handler(services.query_service))

        cls.register("sd", make_sd_handler(services.query_service))

        cls.register("img", make_img_handler(services.query_service))
```

#### presentation/commands/auth_commands.py

```python
def make_login_handler(auth_service: AuthService):
    async def handler(bot, event):
        await auth_service.login(bot, event)
    return handler
```

#### presentation/commands/sub_commands.py

```python
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import GroupMessageEvent


def make_sub_handler(sub_service: SubscriptionService):
    async def handler(event: GroupMessageEvent, args: Message = CommandArg()):
        uid = args.extract_plain_text()
        if not uid or not uid.isdigit():
            await matcher.finish("请携带正确的uid后重试")
        result = await sub_service.add_sub(uid, event.group_id, event.self_id)
        await matcher.finish(result)
    return handler


def make_unsub_handler(sub_service: SubscriptionService):
    async def handler(event: GroupMessageEvent, args: Message = CommandArg()):
        uid = args.extract_plain_text()
        if not uid or not uid.isdigit():
            await matcher.finish("请携带正确的uid后重试")
        result = await sub_service.del_sub(uid, event.group_id, event.self_id)
        await matcher.finish(result)
    return handler


def make_live_toggle_handler(sub_service: SubscriptionService, active: bool):
    async def handler(event: GroupMessageEvent, args: Message = CommandArg()):
        uid = args.extract_plain_text()
        if not uid or not uid.isdigit():
            await matcher.finish("请携带正确的uid后重试")
        result = await sub_service.toggle_live(uid, event.group_id, event.self_id, active)
        await matcher.finish(result)
    return handler


def make_dyn_toggle_handler(sub_service: SubscriptionService, active: bool):
    async def handler(event: GroupMessageEvent, args: Message = CommandArg()):
        uid = args.extract_plain_text()
        if not uid or not uid.isdigit():
            await matcher.finish("请携带正确的uid后重试")
        result = await sub_service.toggle_dyn(uid, event.group_id, event.self_id, active)
        await matcher.finish(result)
    return handler
```

#### presentation/commands/query_commands.py

```python
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment


def make_bot_status_handler(bot_status_service: BotStatusService, active: bool):
    async def handler(event: GroupMessageEvent):
        result = await bot_status_service.toggle_push(event.self_id, event.group_id, active)
        if result is not None:
            await matcher.finish(result)
    return handler


def make_list_handler(query_service: QueryService):
    async def handler(event: GroupMessageEvent):
        img = await query_service.get_sub_list(event.self_id, event.group_id)
        await matcher.finish(img)
    return handler


def make_help_handler(query_service: QueryService):
    async def handler():
        img = await query_service.get_help_image()
        await matcher.finish(MessageSegment.image(img))
    return handler


def make_sd_handler(query_service: QueryService):
    async def handler(args: Message = CommandArg()):
        dyn_id = args.extract_plain_text()
        if not dyn_id or not dyn_id.isdigit():
            return
        img = await query_service.get_dyn_image(dyn_id)
        if img is None:
            return
        await matcher.finish(MessageSegment.image(img))
    return handler


def make_img_handler(query_service: QueryService):
    async def handler(args: Message = CommandArg()):
        dyn_id = args.extract_plain_text()
        if not dyn_id or not dyn_id.isdigit():
            return
        result = await query_service.get_dyn_images(dyn_id)
        if result is None:
            return
        if isinstance(result, str):
            await matcher.finish(result)
        await matcher.finish(result)
    return handler
```

#### presentation/scheduler/__init__.py

```python
def register_scheduled_jobs(scheduler, dyn_check_job: DynCheckJob, live_check_job: LiveCheckJob):
    @scheduler.scheduled_job("cron", second="*/8", id="dyn_pusher", max_instances=1)
    async def _():
        await dyn_check_job.run()

    @scheduler.scheduled_job("cron", second="*/10", id="live_pusher", max_instances=1)
    async def _():
        await live_check_job.run()
```

#### presentation/middleware/__init__.py

```python
from nonebot.adapters.onebot.v11 import GroupMessageEvent


def make_bot_is_active_rule(bot_repo: BotStatusRepository):
    async def bot_is_active(event: GroupMessageEvent) -> bool:
        status = await bot_repo.get(event.self_id, event.group_id)
        if not status:
            await bot_repo.save(BotStatus(
                bot_id=event.self_id,
                group_id=event.group_id,
                push_active=True,
                bot_active=True
            ))
            return True
        return status.push_active and status.bot_active
    return bot_is_active


def register_lifecycle_hooks(driver, event_bus: EventBus):
    @driver.on_bot_connect
    async def _(bot):
        await event_bus.publish(BotConnected(bot.self_id))

    @driver.on_bot_disconnect
    async def _(bot):
        await event_bus.publish(BotDisconnected(bot.self_id))

    @driver.on_shutdown
    async def _():
        await event_bus.publish(BotShutdown())
```

---

### 2.4 Infrastructure Layer（基础设施层）— 实现 Domain 接口

#### infrastructure/container.py — DI 容器

```python
from arielbot.infrastructure.database import DatabaseManager
from arielbot.infrastructure.event_bus import SimpleEventBus
from arielbot.infrastructure.repositories import (
    SqlSubTargetRepository, SqlSubChannelRepository,
    SqlBotStatusRepository, SqlCookieRepository, SqlDynCacheRepository,
)
from arielbot.infrastructure.adapters import (
    BiliAuthAdapter, BiliContentAdapter,
    SkiaDynRenderer, SkiaSubListRenderer, QRCodeRenderer,
    NoneBotClient,
)
from arielbot.application import (
    AuthService, SubscriptionService, QueryService, BotStatusService,
)
from arielbot.application.push import DynCheckJob, LiveCheckJob
from arielbot.application.push import DynPushHandler, LivePushHandler, BotLifecycleHandler
from arielbot.domain.events import DynamicDetected, LiveStatusChanged, BotConnected, BotDisconnected, BotShutdown


class Container:
    def __init__(self):
        # === 数据库 ===
        self._db = DatabaseManager()

        # === 事件总线 ===
        self.event_bus = SimpleEventBus()

        # === 仓储 ===
        self.sub_target_repo = SqlSubTargetRepository(self._db)
        self.sub_channel_repo = SqlSubChannelRepository(self._db)
        self.bot_repo = SqlBotStatusRepository(self._db)
        self.cookie_repo = SqlCookieRepository(self._db)
        self.dyn_cache_repo = SqlDynCacheRepository(self._db)

        # === 外部适配器 ===
        self.bili_auth = BiliAuthAdapter(self.cookie_repo)
        self.bili_content = BiliContentAdapter(self.cookie_repo)
        self.dyn_renderer = SkiaDynRenderer()
        self.sub_list_renderer = SkiaSubListRenderer()
        self.qrcode_renderer = QRCodeRenderer()
        self.bot_client = NoneBotClient()

        # === 应用服务 ===
        self.auth_service = AuthService(
            self.bili_auth, self.cookie_repo, self.bot_client)
        self.sub_service = SubscriptionService(
            self.bili_content, self.sub_target_repo, self.sub_channel_repo)
        self.query_service = QueryService(
            self.bili_content, self.dyn_cache_repo,
            self.sub_channel_repo, self.dyn_renderer, self.sub_list_renderer)
        self.bot_status_service = BotStatusService(
            self.bot_repo, self.event_bus)

        # === 推送检查任务 ===
        self.dyn_check_job = DynCheckJob(
            self.bili_content, self.dyn_cache_repo,
            self.sub_channel_repo, self.dyn_renderer, self.event_bus)
        self.live_check_job = LiveCheckJob(
            self.bili_content, self.sub_target_repo,
            self.sub_channel_repo, self.event_bus)

        # === 注册事件处理器 ===
        self._register_event_handlers()

    def _register_event_handlers(self):
        bus = self.event_bus
        lifecycle = BotLifecycleHandler(self.bot_status_service)

        bus.subscribe(DynamicDetected, DynPushHandler(self.bot_client).handle)
        bus.subscribe(LiveStatusChanged, LivePushHandler(self.bot_client).handle)
        bus.subscribe(BotConnected, lifecycle.on_connect)
        bus.subscribe(BotDisconnected, lifecycle.on_disconnect)
        bus.subscribe(BotShutdown, lifecycle.on_shutdown)
```

#### infrastructure/event_bus.py

```python
import asyncio
from typing import Any, Callable, Dict, List, Optional, Type
from nonebot import logger
from arielbot.domain.interfaces.event_bus import EventBus


class SimpleEventBus(EventBus):
    """轻量级事件总线，基于 asyncio.Queue 实现"""

    def __init__(self):
        self._handlers: Dict[Type, List[Callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None

    def subscribe(self, event_type: Type, handler: Callable) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event: Any) -> None:
        await self._queue.put(event)

    async def start(self) -> None:
        self._task = asyncio.create_task(self._dispatch_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _dispatch_loop(self):
        while True:
            event = await self._queue.get()
            for handler in self._handlers.get(type(event), []):
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Event handler error for {type(event).__name__}: {e}")
```

#### infrastructure/database.py

```python
import aiosqlite
from contextlib import asynccontextmanager
from typing import Optional, AsyncIterator
from os import path, getcwd


class DatabaseManager:
    def __init__(self, db_path: str = None):
        self._db_path = db_path or path.join(getcwd(), "data.sqlite")

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[aiosqlite.Cursor]:
        db_exists = path.exists(self._db_path)
        conn = await aiosqlite.connect(self._db_path)
        cursor = await conn.cursor()
        await cursor.execute("BEGIN")
        try:
            if not db_exists:
                await cursor.execute("PRAGMA foreign_keys = ON;")
                await self._create_tables(cursor)
            yield cursor
            await conn.commit()
        except Exception:
            await conn.rollback()
            raise
        finally:
            await cursor.close()
            await conn.close()

    async def _create_tables(self, cursor):
        await cursor.executescript("""
            CREATE TABLE IF NOT EXISTS subTarget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                uid TEXT NOT NULL UNIQUE,
                live_status INTEGER NOT NULL DEFAULT 1 CHECK(live_status IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS subChennal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL,
                groupId INTEGER NOT NULL,
                bot INTEGER NOT NULL,
                live_active INTEGER NOT NULL DEFAULT 1 CHECK(live_active IN (0, 1)),
                dyn_active INTEGER NOT NULL DEFAULT 1 CHECK(dyn_active IN (0, 1)),
                FOREIGN KEY (uid) REFERENCES subTarget(uid) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS botStatus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot INTEGER NOT NULL,
                groupId INTEGER NOT NULL,
                push_active INTEGER NOT NULL DEFAULT 1 CHECK(push_active IN (0, 1)),
                bot_active INTEGER NOT NULL DEFAULT 1 CHECK(bot_active IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS Cookie (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie BLOB NOT NULL,
                refresh_token TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS Dynamic (
                dyn_id TEXT NOT NULL PRIMARY KEY,
                uname TEXT NOT NULL,
                dyn_content BLOB NOT NULL
            );
        """)
```

#### infrastructure/adapters/bot_client.py

```python
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Bot, MessageSegment


class BotClient:
    """封装 NoneBot 的 send 操作，方便测试时 mock"""

    async def send_group_msg(self, group_id: int, bot_id: int,
                              text: str = "", image: bytes = None,
                              cover: str = None) -> None:
        bot: Bot = get_bot(str(bot_id))
        message = MessageSegment.text(text)
        if image:
            message += MessageSegment.image(image)
        if cover:
            message += MessageSegment.image(cover)
        await bot.send_group_msg(group_id=group_id, message=message)
```

---

## 三、设计模式与六大原则对照

| 原则 | 当前问题 | 重构方案 | 使用模式 |
|------|---------|---------|---------|
| **SRP** | `ariel_tools.py` 含 4+ 职责；`ariel_push.py` 含获取/渲染/推送 | 每个 Service 单一职责；CheckJob 只管检查+发事件，Handler 只管推送 | Command Pattern, Service Layer |
| **OCP** | 新增推送类型需改多处代码；命令硬编码 | 事件总线 + 订阅者模式：新增推送类型 → 新增 CheckJob + Handler，不修改现有代码 | Observer, Event-Driven |
| **LSP** | CookieManager 子类基本可替换，但硬编码 RSA 公钥 | 所有接口通过 ABC 定义契约，子类符合契约即可替换 | Abstract Base Classes |
| **ISP** | DataManager 暴露 20+ 方法，各模块被迫依赖全部 | 按聚合拆分 5 个 Repository 接口，每个接口只暴露相关方法 | Repository Pattern |
| **DIP** | 所有模块直接依赖具体实现 `DataManager()`, `Dynamic()` | 所有服务依赖接口，Container 注入具体实现，可替换为 Mock | Dependency Injection, Adapter |
| **LoD** | `event.self_id`, `dynamic.major.opus.pics` 深层属性访问 | 命令只调用 Service，Service 只调用 Repository/API 接口；实体封装数据 | Facade, Repository |

---

## 四、数据流对比

```
【重构前】
定时任务 → DynPusher.push_dynamic()
  → Dynamic().get_dynamic_from_follow_list()    # API调用
  → DataManager().select_dyn_content()           # 去重
  → DataManager().select_dynamic_push()          # 查推送目标
  → DynRender().run()                            # 渲染
  → get_bot().send_group_msg()                   # 发送
  (一个方法完成所有事情，无法测试，无法扩展)

【重构后】
定时任务 → DynCheckJob.run()
  → content_api.get_follow_dynamics()            # API调用
  → dyn_cache_repo.exists()                      # 去重
  → sub_channel_repo.find_push_targets_for_dyn() # 查推送目标
  → dyn_renderer.render()                        # 渲染
  → event_bus.publish(DynamicDetected(...))      # 发布事件
       ↓
  DynPushHandler.handle(event)
      → bot_client.send_group_msg()              # 发送
  (每步独立，可单独测试，新增推送类型只需新增 CheckJob + Handler)
```

---

## 五、file 清单

| 层 | 文件数 | 关键文件 |
|----|--------|---------|
| domain/ | 6 | entities.py, events.py, interfaces/repository.py, interfaces/api.py, interfaces/renderer.py, interfaces/event_bus.py |
| application/ | 7 | auth_service.py, subscription_service.py, query_service.py, bot_status_service.py, push/check_jobs.py, push/handlers.py |
| presentation/ | 5 | commands/registry.py, commands/auth_commands.py, commands/sub_commands.py, commands/query_commands.py, scheduler/__init__.py, middleware/__init__.py |
| infrastructure/ | 11 | container.py, database.py, event_bus.py, repositories/ (4个), adapters/ (5个) |
| 根目录 | 2 | __init__.py, bot.py |
| **合计** | **31** | (原 10 个文件) |

---

## 六、实施步骤

### Step 1: 创建 domain/ 层（不依赖任何现有代码）
- [x] `domain/__init__.py`
- [x] `domain/entities.py` — 所有实体和值对象
- [x] `domain/events.py` — 所有领域事件
- [x] `domain/interfaces/__init__.py`
- [x] `domain/interfaces/event_bus.py` — 事件总线接口
- [x] `domain/interfaces/repository.py` — 5 个仓储接口
- [x] `domain/interfaces/api.py` — B站API接口
- [x] `domain/interfaces/renderer.py` — 渲染器接口

### Step 2: 创建 infrastructure/ 层（实现 Domain 接口）
- [x] `infrastructure/__init__.py`
- [x] `infrastructure/database.py` — 数据库连接管理
- [x] `infrastructure/event_bus.py` — SimpleEventBus 实现
- [x] `infrastructure/repositories/` — 4 个仓储实现
- [x] `infrastructure/adapters/` — 5 个适配器实现
- [x] `infrastructure/container.py` — DI 容器

### Step 3: 创建 application/ 层（依赖 Domain 接口）
- [x] `application/__init__.py`
- [x] `application/auth_service.py`
- [x] `application/subscription_service.py`
- [x] `application/query_service.py`
- [x] `application/bot_status_service.py`
- [x] `application/push/check_jobs.py`
- [x] `application/push/handlers.py`

### Step 4: 创建 presentation/ 层（依赖 Application 服务）
- [x] `presentation/__init__.py`
- [x] `presentation/commands/` — 命令注册 + 3 个命令文件
- [x] `presentation/scheduler/__init__.py` — 定时任务注册
- [x] `presentation/middleware/__init__.py` — 权限规则 + 生命周期钩子

### Step 5: 重构入口文件
- [x] `arielbot/__init__.py` — 调整为启动 container 和 event_bus
- [x] `arielbot/bot.py` — 保持 NoneBot 初始化逻辑
- [x] `plugins/Core/__init__.py` — 组装所有模块并启动

### Step 6: 清理
- [x] 删除旧文件：`ariel_cmd.py`, `ariel_bili.py`, `ariel_cookie.py`, `ariel_database.py`, `ariel_push.py`, `ariel_rule.py`, `ariel_tools.py`
- [x] 运行测试验证

---

## 七、事件驱动架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          EventBus (asyncio.Queue)                    │
│                                                                      │
│  ┌──────────────────┐                                                │
│  │  DynCheckJob     │──── publish(DynamicDetected) ──────────────┐   │
│  │  (每8秒)          │                                             │   │
│  └──────────────────┘                                             │   │
│                                                                   │   │
│  ┌──────────────────┐                                             │   │
│  │  LiveCheckJob    │──── publish(LiveStatusChanged) ─────────┐   │   │
│  │  (每10秒)         │                                          │   │   │
│  └──────────────────┘                                          │   │   │
│                                                                │   │   │
│  ┌──────────────────┐                                          │   │   │
│  │  driver.on_      │── publish(BotConnected/Disconnected) ─┐  │   │   │
│  │  bot_connect/     │                                        │  │   │   │
│  │  disconnect/      │                                        │  │   │   │
│  │  shutdown         │── publish(BotShutdown) ───┐            │  │   │   │
│  └──────────────────┘                             │            │  │   │   │
│                                                   │            │  │   │   │
│                    ┌────── dispatch loop ──────────┼────────────┼──┼───┼──┘
│                    │                              │            │  │   │
│                    ▼                              ▼            ▼  ▼   ▼
│  ┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  BotLifecycleHandler │  │  LivePushHandler │  │  DynPushHandler  │  │
│  │                       │  │                   │  │                   │  │
│  │  on_connect()         │  │  handle()         │  │  handle()         │  │
│  │  on_disconnect()      │  │    → 发送开播消息   │  │    → 发送动态消息   │  │
│  │  on_shutdown()        │  │                   │  │                   │  │
│  └──────────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 八、扩展性示例

### 新增推送类型（如"专栏投稿"）

```python
# 1. 新增领域事件
@dataclass
class ArticlePublished:
    uid: str
    uname: str
    article_id: str
    title: str
    targets: List[Tuple[int, int]]

# 2. 新增检查任务
class ArticleCheckJob:
    async def run(self):
        ...
        await self._event_bus.publish(ArticlePublished(...))

# 3. 新增事件处理器
class ArticlePushHandler:
    async def handle(self, event: ArticlePublished):
        ...

# 4. 在 container 中注册
bus.subscribe(ArticlePublished, ArticlePushHandler(client).handle)

# 5. 在 scheduler 中注册定时任务
@scheduler.scheduled_job("cron", second="*/30")
async def _():
    await container.article_check_job.run()
```

**无需修改任何现有文件！** 这就是 OCP 开闭原则的体现。

### 替换渲染器（如 Skia → Pillow）

```python
# 只需实现接口
class PillowDynRenderer(DynRenderer):
    async def render(self, dynamic) -> bytes:
        ...

# 在 container 中替换一行
self.dyn_renderer = PillowDynRenderer()
```

### 添加单元测试

```python
# 所有依赖都是接口，可以 mock
class MockBiliAPI(BiliContentAPI):
    async def get_follow_dynamics(self):
        return [mock_dynamic]

class MockDynCache(DynCacheRepository):
    async def exists(self, dyn_id):
        return False

async def test_dyn_check_job():
    job = DynCheckJob(
        content_api=MockBiliAPI(),
        dyn_cache_repo=MockDynCache(),
        sub_channel_repo=MockSubChannel(),
        dyn_renderer=MockRenderer(),
        event_bus=MockEventBus(),
    )
    await job.run()
    # assert event_bus.publish was called with DynamicDetected
```