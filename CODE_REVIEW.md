# Clean Architecture 重构代码审查报告

> 审查时间: 2026-05-31
> 审查提交: 6c5502e + 8b84431
> 审查范围: 50 文件，+1820/-1467 行

---

## 一、变更概要

| 提交        | 类型       | 说明                                                             |
| --------- | -------- | -------------------------------------------------------------- |
| `6c5502e` | Refactor | 创建 domain/application/infrastructure/presentation 四层架构，31 个新文件 |
| `8b84431` | Docs     | README 增加架构文档                                                  |

**已删除 7 个旧文件**: `ariel_bili.py`, `ariel_cmd.py`, `ariel_cookie.py`, `ariel_database.py`, `ariel_push.py`, `ariel_rule.py`, `ariel_tools.py`

**新增分层**:

| 层                 | 文件数 | 职责                       |
| ----------------- | --- | ------------------------ |
| `domain/`         | 8   | 实体、事件、ABC 接口             |
| `application/`    | 7   | 业务 Service、推送检查任务、事件处理器  |
| `infrastructure/` | 15  | 数据库、仓储实现、B站适配器、DI容器、事件总线 |
| `presentation/`   | 8   | 命令注册、定时任务、中间件            |

---

## 二、架构合规性检查

| 检查项                 | 状态  | 备注                                                   |
| ------------------- | --- | ---------------------------------------------------- |
| 分层架构 (4层)           | ✅   | Domain / Application / Infrastructure / Presentation |
| ABC 抽象接口            | ✅   | 9 个接口: 5 Repository + 2 API + 2 Renderer             |
| DI 容器集中注入           | ✅   | `Container` 管理所有依赖创建和注入                              |
| 事件驱动解耦              | ✅   | `SimpleEventBus` + 5 种领域事件                           |
| 仓储模式                | ⚠️  | 缺 `SqlSubTargetRepository` 实现                        |
| DIP (Application 层) | 🟡  | `handlers.py` 直接 import Infrastructure               |
| 参数化查询               | ✅   | 全部使用 `?` 占位符                                         |
| 异步非阻塞               | 🔴  | `httpx` 同步调用 + `time.sleep` 遗留                       |

---

## 三、问题清单

### 🔴 Critical (4 项，必须修复)

#### C1 — `SqlSubTargetRepository` 类未定义，启动即崩溃

- **严重程度**: P0 - 应用无法启动
- **文件**: `arielbot/infrastructure/container.py:4, 39`
- **问题**: `container.py` 中 `from arielbot.infrastructure.repositories.sub_repository import SqlSubTargetRepository` 导入了一个不存在的类。`sub_repository.py` 只定义了 `SqlSubChannelRepository`，缺少 `SqlSubTargetRepository`
- **影响**: `ImportError`，应用程序完全无法启动
- **修复**: 在 `infrastructure/repositories/sub_repository.py` 中添加实现:

```python
from typing import Optional
from arielbot.domain.interfaces.repository import SubTargetRepository
from arielbot.infrastructure.database import DatabaseManager

class SqlSubTargetRepository(SubTargetRepository):
    def __init__(self, db: DatabaseManager):
        self._db = db

    async def get(self, uid: str) -> Optional[tuple]:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "SELECT nickname FROM subTarget WHERE uid=?",
                (uid,),
            )
            return await cursor.fetchone()
    
    async def save(self, uid: str, nickname: str, live_status: int) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "INSERT INTO subTarget (uid, nickname, live_status) VALUES (?, ?, ?)",
                (uid, nickname, live_status),
            )
    
    async def update(self, nickname: str, live_status: int, uid: str) -> None:
        async with self._db.transaction() as cursor:
            await cursor.execute(
                "UPDATE subTarget SET nickname=?, live_status=? WHERE uid=?",
                (nickname, live_status, uid),
            )

C2 — 16 处 httpx 同步调用阻塞事件循环

- 严重程度: P0 - 运行时性能严重退化
- 文件:
- arielbot/infrastructure/adapters/bili_auth.py: 行 36, 49, 106, 139
- arielbot/infrastructure/adapters/bili_api.py: 行 43, 85, 118, 136, 149, 165, 191
- 问题: 在 async def 方法中使用同步 httpx.get() / httpx.post()，阻塞整个事件循环
- 影响: Cookie 刷新期间推送延迟 5-10 秒；登录轮询期间所有命令无响应；多个定时任务互相阻塞
- 修复: 全部替换为 httpx.AsyncClient
  
  # 修改前
  
  response = httpx.get(url, headers=self.headers, cookies=self.cookie)

# 修改后

async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=self.headers, cookies=self.cookie)
涉及的所有位置:
文件    行号    方法
bili_auth.py    36    BiliAuthAdapter.get_qrcode
bili_auth.py    49    BiliAuthAdapter.poll_scan
bili_auth.py    106    CookieManager._get_correspond_path
bili_auth.py    139    CookieManager._get_new_cookie
bili_api.py    43    BiliContentAdapter._get_wbi_keys
bili_api.py    85    BiliContentAdapter.get_follow_dynamics
bili_api.py    118    BiliContentAdapter.get_dynamic_by_id
bili_api.py    136    BiliContentAdapter.get_live_users
bili_api.py    149    BiliContentAdapter.get_room_info_by_uids
bili_api.py    165    BiliContentAdapter.get_user_info
bili_api.py    191    BiliContentAdapter.follow_user
注意: bili_api.py:43 (_get_wbi_keys) 和 bili_api.py:149 (get_room_info_by_uids) 无需 cookie，调用路径稍简。
C3 — time.sleep(3) 阻塞事件循环

- 严重程度: P0 - 运行时阻塞
- 文件: arielbot/application/auth_service.py:46
- 问题: time.sleep(3) 同步阻塞，登录轮询期间整个事件循环卡死 3 秒
- 影响: 登录过程中的 3 秒内，推送任务、其他命令全部无法执行
- 修复:
  
  # 文件顶部添加
  
  import asyncio

# 行 46 修改

# 修改前

time.sleep(3)

# 修改后

await asyncio.sleep(3)
C4 — Application 层违反 DIP（直接导入 Infrastructure）

- 严重程度: P0 - 架构违规，破坏可测试性
- 文件: arielbot/application/push/handlers.py:3
- 问题: from arielbot.infrastructure.adapters.bot_client import BotClient — Application 层直接依赖 Infrastructure 层具体类，违反依赖倒置原则
- 影响: 无法对 DynPushHandler / LivePushHandler 进行单元测试（无法 mock BotClient）
- 修复方案 A（推荐）: 在 Domain 层定义接口
  
  # 新增: arielbot/domain/interfaces/bot_client.py
  
  from abc import ABC, abstractmethod

class BotClient(ABC):
    @abstractmethod
    async def send_group_msg(self, group_id: int, bot_id: int,
                              text: str = "", image: bytes = None,
                              cover: str = None) -> None:
        ...

# 修改: arielbot/infrastructure/adapters/bot_client.py

from arielbot.domain.interfaces.bot_client import BotClient as BotClientABC

class BotClient(BotClientABC):
    ...

# 修改: arielbot/application/push/handlers.py

# 修改前

from arielbot.infrastructure.adapters.bot_client import BotClient

# 修改后

from arielbot.domain.interfaces.bot_client import BotClient

- 修复方案 B（简易）: handlers 通过 bot_client 参数注入，不做类型注解
  🟡 Warning (6 项，建议改进)
  W1 — CookieManager 双重实例化
- 文件: container.py:46, bili_api.py:26
- 问题: container.py 创建 self.cookie_manager = CookieManager(self.cookie_repo)，但 BiliContentAdapter.__init__ 内部又自己 new CookieManager(cookie_repo)。产生两个独立 CookieManager 实例，cookie 状态不同步
- 影响: container.cookie_manager 的 cookie 和 BiliContentAdapter._cookie_mgr 的 cookie 各自独立刷新，可能不一致
- 建议: BiliContentAdapter 接收 CookieManager 实例而非自行创建
  
  # container.py
  
  class BiliContentAdapter(BiliContentAPI):
    def __init__(self, cookie_manager: CookieManager):  # 接收实例
  
        self._cookie_mgr = cookie_manager

# container.__init__

self.cookie_manager = CookieManager(self.cookie_repo)
self.bili_content = BiliContentAdapter(self.cookie_manager)  # 传入
W2 — register_all(container, container) 参数混淆

- 文件: plugins/Core/__init__.py:16
- 问题: CommandRegistry.register_all(container, container) 将 container 同时作为两个不同语义的参数传入，导致 register_all 内部 services 和 container 指向同一对象，无法区分
- 建议: 重构为单一参数:
  
  # plugins/Core/__init__.py
  
  CommandRegistry.register_all(container)

# presentation/commands/registry.py

@classmethod
def register_all(cls, container) -> None:
    bot_is_active = make_bot_is_active_rule(container.bot_repo)
    # ... 所有命令通过 container.xxx_service 访问
W3 — 命令处理器内 lazy import（13 处）

- 文件: presentation/commands/registry.py
- 问题: 13 个 handler 函数内部包含 from ... import ...，每次命令触发都重新执行 import，增加运行时开销
- 影响: 轻微性能损耗，不符合 PEP 8 规范
- 涉及位置: 行 31, 44, 57, 68, 80, 92, 103, 115, 127, 136, 144, 152, 160
- 建议: 所有 import 移到文件顶部
  
  # 修改前 (行 31)
  
  async def _(bot: Bot, event: GroupMessageEvent):
    from arielbot.presentation.commands.auth_commands import make_login_handler
    ...

# 修改后 (文件顶部)

from arielbot.presentation.commands.auth_commands import make_login_handler
from arielbot.presentation.commands.sub_commands import (
    make_sub_handler, make_unsub_handler, make_live_toggle_handler, make_dyn_toggle_handler,
)
from arielbot.presentation.commands.query_commands import (
    make_bot_status_handler, make_list_handler, make_help_handler,
    make_sd_handler, make_img_handler,
)
W4 — follow_user 返回类型不一致

- 文件: infrastructure/adapters/bili_api.py:176
- 问题: 接口声明返回 bool，实现中 return None（未登录/请求失败时）
- 建议: 修改接口签名为 -> Optional[bool]：
  
  # domain/interfaces/api.py:37
  
  async def follow_user(self, uid: str, act: int) -> Optional[bool]:
    ...
  W5 — Presentation 层直接依赖 Infrastructure Repository
- 文件: presentation/commands/registry.py:23, presentation/middleware/__init__.py:5
- 问题: make_bot_is_active_rule(container.bot_repo) 将 SqlBotStatusRepository 具体实现传递到 Presentation 层
- 建议: 通过 BotStatusService 封装，或保持现状并在 ADR 中记录此技术债务
  
  # 方案: BotStatusService 增加方法
  
  class BotStatusService:
    async def is_bot_active(self, bot_id: int, group_id: int) -> bool:
  
        result = await self._repo.get(bot_id, group_id)
        if not result:
            await self._repo.save(bot_id, group_id, 1, 1)
            return True
        return bool(result[0] and result[1])
  
  W6 — bili_auth.py CookieManager 同时使用 self.cookie 和 self._cookie_repo
- 文件: infrastructure/adapters/bili_auth.py:57-100
- 问题: CookieManager 既在内存中缓存 self.cookie，又通过 self._cookie_repo 访问数据库。两种状态源可能不同步（例如 load_cookie 后 _check_expire 刷新了 cookie 但外部调用者在 load_cookie 之前已经读取了旧值）
- 建议: 统一状态管理，增加受保护的访问方法:
  @property
  def cookie(self):
    return self._cookie

async def ensure_cookie(self) -> Optional[dict]:
    if self._cookie is None:
        await self.load_cookie()
    return self._cookie
🟢 Good Practices (9 项)

1. Clean Architecture 严格执行: Domain 层 8 个文件零外部依赖，纯 Python + ABC
2. ABC 接口设计规范: 5 Repository + 2 API + 2 Renderer，接口清晰
3. DI 容器依赖链正确: DB → Repos → Adapters → Services → Jobs，创建顺序无误
4. 事件驱动解耦: DynCheckJob/LiveCheckJob 只发布事件不直接推送，符合 OCP
5. 数据库事务管理: @asynccontextmanager 确保 commit/rollback/close，资源管理安全
6. SQL 参数化查询: 100% 使用 ? 占位符，无 SQL 注入风险
7. 历史 Bug 全部修复: delete_cookie→clean_cookie、f-string 引号、None 初始化、KeyError、拼写错误×2 全部修复
8. RSA 公钥模块级常量: 不再每次实例化重新导入 RSA key
9. README 完整: 包含分层架构图、文件清单、OCP 扩展示例
   四、修复优先级
   优先级    问题    修复工作量
   🔴 P0    C1: SqlSubTargetRepository 缺失    ~30 行
   🔴 P0    C2: httpx 同步调用 (11 处)    ~40 行
   🔴 P0    C3: time.sleep(3)    1 行
   🔴 P0    C4: handlers.py DIP 违规    ~20 行
   🟡 P1    W1: CookieManager 双重实例    ~15 行
   🟡 P1    W2: register_all 参数混淆    ~10 行
   🟡 P2    W3: lazy import (13 处)    ~15 行
   🟡 P2    W4: 返回类型不一致    1 行
   🟡 P2    W5: Presentation 依赖 Repo    ~15 行
   🟡 P3    W6: CookieManager 状态管理    ~20 行
   五、总结
   整体重构质量高，分层清晰，接口设计合理。BiliAuth/CookieManager 从旧 ariel_cookie.py 继承的逻辑完整保留。
   核心问题集中在两个领域:
10. 异步阻塞: httpx 同步调用 + time.sleep 是旧代码的遗留问题，重构后未修复，需全量替换为 async 版本
11. 漏实现: SqlSubTargetRepository 缺失导致启动崩溃，是本次重构唯一的遗漏实现
    建议优先修复 4 个 🔴 P0 问题后即可合并。🟡 问题可分批在后续 PR 中处理。
