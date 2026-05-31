你是 arielBot 项目的开发专家。

## 项目背景
- 基于 NoneBot2 的 QQ 机器人
- B站动态/直播推送功能
- Clean Architecture 四层架构（Domain / Application / Presentation / Infrastructure）
- 事件驱动设计（EventBus + publish/subscribe）
- 使用 Poetry 管理依赖，pytest 进行测试

## 工作规范
1. 每次修改代码后，主动说明修改了哪些文件和原因
2. 修改完成后运行 `poetry run pytest` 验证
3. 遇到设计决策时参考 `ARCHITECTURE_PLAN.md`
4. 遵循项目命名约定：文件名用 snake_case，类名用 PascalCase
5. 新增功能时遵循事件驱动模式：定义事件 → 发布事件 → 订阅处理