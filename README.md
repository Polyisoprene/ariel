# arielBot

基于 [NoneBot2](https://github.com/nonebot/nonebot2) + Clean Architecture 的 B站 动态/直播 推送 QQ 机器人。

## 功能

- 订阅 B站 UP 主的动态和直播
- 自动推送新动态（Skia 渲染卡片）和开播通知到 QQ 群
- 扫码登录 B站，自动刷新 Cookie
- 按群开关推送、按订阅开关动态/直播推送

## 架构

```
arielbot/
├── domain/              # 领域层：实体、事件、抽象接口
│   ├── entities.py      # SubTarget, SubChannel, BotStatus, BiliCookie 等
│   ├── events.py        # DynamicDetected, LiveStatusChanged, BotConnected 等
│   └── interfaces/      # ABC: Repository, API, Renderer, EventBus
├── application/         # 应用层：业务逻辑
│   ├── auth_service.py          # 扫码登录
│   ├── subscription_service.py  # 订阅管理
│   ├── query_service.py        # 查询（动态/图片/订阅列表）
│   ├── bot_status_service.py   # Bot 状态
│   └── push/                   # 推送子系统
│       ├── check_jobs.py       # 定时检查（8s 动态, 10s 直播）
│       └── handlers.py         # 事件处理器
├── presentation/        # 表现层：命令、调度、中间件
│   ├── commands/        # 12 个命令注册
│   ├── scheduler/       # APScheduler 定时任务
│   └── middleware/      # 权限规则、生命周期钩子
├── infrastructure/      # 基础设施层：实现 Domain 接口
│   ├── database.py      # SQLite 事务管理
│   ├── event_bus.py     # asyncio.Queue 事件总线
│   ├── container.py     # DI 容器
│   ├── repositories/    # 5 个仓储实现
│   └── adapters/        # B站 API、登录、渲染器、Bot 客户端
├── bot.py               # NoneBot 初始化
└── __init__.py          # CLI 入口 (click)
```

### 设计原则

| 原则 | 实现 |
|------|------|
| **SRP** 单一职责 | 每层、每个 Service/Repository 单一职责 |
| **OCP** 开闭原则 | 事件总线：新增推送类型只需添加 CheckJob + Handler |
| **LSP** 里氏替换 | ABC 接口定义契约，实现可替换 |
| **ISP** 接口隔离 | 5 个 Repository 接口，各司其职 |
| **DIP** 依赖反转 | 服务依赖接口，Container 注入具体实现 |

### 数据流

```
定时任务 → CheckJob.run()
  → API 获取数据 → 缓存去重 → 查推送目标 → 渲染
  → event_bus.publish(事件)
     ↓
  Handler.handle(事件) → bot_client.send_group_msg()
```

## 安装

```bash
git clone https://github.com/Polyisoprene/ariel.git
cd ariel
poetry install
```

## 运行

```bash
poetry run ariel run
```

首次运行会自动在项目根目录创建 `.env.prod` 配置文件和 `plugins/` 目录。

## 命令

| 命令 | 别名 | 权限 | 说明 |
|------|------|------|------|
| `/login` | 登录 | SUPERUSER | 扫码登录 B站 |
| `/sub <uid>` | 订阅 | 管理员 | 订阅 UP 主 |
| `/unsub <uid>` | 删除 | 管理员 | 取消订阅 |
| `/live_on <uid>` | - | 管理员 | 开启直播推送 |
| `/live_off <uid>` | - | 管理员 | 关闭直播推送 |
| `/dyn_on <uid>` | - | 管理员 | 开启动态推送 |
| `/dyn_off <uid>` | - | 管理员 | 关闭动态推送 |
| `/bot_on` | - | 管理员 | 开启群内推送 |
| `/bot_off` | - | 管理员 | 关闭群内推送 |
| `/list` | 列表 | - | 查看订阅列表 |
| `/help` | - | - | 帮助 |
| `/sd <dyn_id>` | - | - | 查看动态卡片 |
| `/img <dyn_id>` | - | - | 提取动态图片 |

## License

MIT