from arielbot.infrastructure.database import DatabaseManager
from arielbot.infrastructure.event_bus import SimpleEventBus
from arielbot.infrastructure.repositories.target_repository import SqlSubTargetRepository
from arielbot.infrastructure.repositories.sub_repository import SqlSubChannelRepository
from arielbot.infrastructure.repositories.bot_repository import SqlBotStatusRepository
from arielbot.infrastructure.repositories.cookie_repository import SqlCookieRepository
from arielbot.infrastructure.repositories.dyn_repository import SqlDynCacheRepository
from arielbot.infrastructure.adapters.bili_auth import BiliAuthAdapter, CookieManager
from arielbot.infrastructure.adapters.bili_api import BiliContentAdapter
from arielbot.infrastructure.adapters.renderer import SkiaDynRenderer, SkiaSubListRenderer, SkiaHelpRenderer
from arielbot.infrastructure.adapters.bot_client import BotClient
from arielbot.infrastructure.adapters.bili_cookie_utils import parse_login_cookie, serialize_cookie
from arielbot.presentation.message_utils import text, image
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
    def __init__(self) -> None:
        self._db: DatabaseManager = DatabaseManager()
        self.event_bus: SimpleEventBus = SimpleEventBus()

        self.sub_target_repo: SqlSubTargetRepository = SqlSubTargetRepository(self._db)
        self.sub_channel_repo: SqlSubChannelRepository = SqlSubChannelRepository(self._db)
        self.bot_repo: SqlBotStatusRepository = SqlBotStatusRepository(self._db)
        self.cookie_repo: SqlCookieRepository = SqlCookieRepository(self._db)
        self.dyn_cache_repo: SqlDynCacheRepository = SqlDynCacheRepository(self._db)

        self.bili_auth: BiliAuthAdapter = BiliAuthAdapter()
        self.cookie_manager: CookieManager = CookieManager(self.cookie_repo)
        self.bili_content: BiliContentAdapter = BiliContentAdapter(self.cookie_manager)
        self.dyn_renderer: SkiaDynRenderer = SkiaDynRenderer()
        self.sub_list_renderer: SkiaSubListRenderer = SkiaSubListRenderer()
        self.help_renderer: SkiaHelpRenderer = SkiaHelpRenderer()
        self.bot_client: BotClient = BotClient()

        self.auth_service: AuthService = AuthService(
            self.bili_auth, self.cookie_repo, self.bot_client,
            parse_login_cookie, serialize_cookie,
            cookie_manager=self.cookie_manager,
            build_text=text, build_image=image,
        )
        self.sub_service: SubscriptionService = SubscriptionService(
            self.bili_content, self.sub_target_repo, self.sub_channel_repo,
        )
        self.query_service: QueryService = QueryService(
            self.bili_content, self.dyn_cache_repo,
            self.sub_channel_repo, self.dyn_renderer, self.sub_list_renderer,
            self.help_renderer,
        )
        self.bot_status_service: BotStatusService = BotStatusService(self.bot_repo, self.event_bus)

        self.dyn_check_job: DynCheckJob = DynCheckJob(
            self.bili_content, self.dyn_cache_repo,
            self.sub_target_repo, self.sub_channel_repo,
            self.dyn_renderer, self.event_bus,
        )
        self.live_check_job: LiveCheckJob = LiveCheckJob(
            self.bili_content,
            self.sub_channel_repo, self.event_bus,
        )

        self._register_event_handlers()

    def _register_event_handlers(self) -> None:
        bus = self.event_bus
        lifecycle = BotLifecycleHandler(self.bot_status_service)

        bus.subscribe(DynamicDetected, DynPushHandler(self.bot_client).handle)
        bus.subscribe(LiveStatusChanged, LivePushHandler(self.bot_client).handle)
        
        bus.subscribe(BotConnected, lifecycle.on_connect)
        bus.subscribe(BotDisconnected, lifecycle.on_disconnect)
        bus.subscribe(BotShutdown, lifecycle.on_shutdown)

    async def close(self) -> None:
        await self.bili_auth.close()
        await self.cookie_manager.close()
        await self.bili_content.close()