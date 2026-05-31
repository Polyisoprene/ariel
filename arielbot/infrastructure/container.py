from arielbot.infrastructure.database import DatabaseManager
from arielbot.infrastructure.event_bus import SimpleEventBus
from arielbot.infrastructure.repositories.sub_repository import (
    SqlSubTargetRepository,
    SqlSubChannelRepository,
)
from arielbot.infrastructure.repositories.bot_repository import SqlBotStatusRepository
from arielbot.infrastructure.repositories.cookie_repository import SqlCookieRepository
from arielbot.infrastructure.repositories.dyn_repository import SqlDynCacheRepository
from arielbot.infrastructure.adapters.bili_auth import BiliAuthAdapter, CookieManager
from arielbot.infrastructure.adapters.bili_api import BiliContentAdapter
from arielbot.infrastructure.adapters.renderer import SkiaDynRenderer, SkiaSubListRenderer
from arielbot.infrastructure.adapters.bot_client import BotClient
from arielbot.infrastructure.adapters.bili_wbi import parse_login_cookie, serialize_cookie
from arielbot.application.auth_service import AuthService
from arielbot.application.subscription_service import SubscriptionService
from arielbot.application.query_service import QueryService
from arielbot.application.bot_status_service import BotStatusService
from arielbot.application.push.check_jobs import DynCheckJob, LiveCheckJob
from arielbot.application.push.handlers import (
    DynPushHandler,
    LivePushHandler,
    BotLifecycleHandler,
)
from arielbot.domain.events import (
    DynamicDetected,
    LiveStatusChanged,
    BotConnected,
    BotDisconnected,
    BotShutdown,
)


class Container:
    def __init__(self):
        self._db = DatabaseManager()
        self.event_bus = SimpleEventBus()

        self.sub_target_repo = SqlSubTargetRepository(self._db)
        self.sub_channel_repo = SqlSubChannelRepository(self._db)
        self.bot_repo = SqlBotStatusRepository(self._db)
        self.cookie_repo = SqlCookieRepository(self._db)
        self.dyn_cache_repo = SqlDynCacheRepository(self._db)

        self.bili_auth = BiliAuthAdapter()
        self.cookie_manager = CookieManager(self.cookie_repo)
        self.bili_content = BiliContentAdapter(self.cookie_manager)
        self.dyn_renderer = SkiaDynRenderer()
        self.sub_list_renderer = SkiaSubListRenderer()
        self.bot_client = BotClient()

        self.auth_service = AuthService(
            self.bili_auth, self.cookie_repo, self.bot_client,
            parse_login_cookie, serialize_cookie,
        )
        self.sub_service = SubscriptionService(
            self.bili_content, self.sub_target_repo, self.sub_channel_repo,
        )
        self.query_service = QueryService(
            self.bili_content, self.dyn_cache_repo,
            self.sub_channel_repo, self.dyn_renderer, self.sub_list_renderer,
        )
        self.bot_status_service = BotStatusService(self.bot_repo, self.event_bus)

        self.dyn_check_job = DynCheckJob(
            self.bili_content, self.dyn_cache_repo,
            self.sub_channel_repo, self.dyn_renderer, self.event_bus,
        )
        self.live_check_job = LiveCheckJob(
            self.bili_content, self.sub_target_repo,
            self.sub_channel_repo, self.event_bus,
        )

        self._register_event_handlers()

    def _register_event_handlers(self):
        bus = self.event_bus
        lifecycle = BotLifecycleHandler(self.bot_status_service)

        bus.subscribe(DynamicDetected, DynPushHandler(self.bot_client).handle)
        bus.subscribe(LiveStatusChanged, LivePushHandler(self.bot_client).handle)
        bus.subscribe(BotConnected, lifecycle.on_connect)
        bus.subscribe(BotDisconnected, lifecycle.on_disconnect)
        bus.subscribe(BotShutdown, lifecycle.on_shutdown)