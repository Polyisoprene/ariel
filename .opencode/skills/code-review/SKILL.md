---
name: code-review
description: Python 代码审查规范和 Clean Architecture 检查清单
---

## 审查检查清单

### Clean Architecture 检查
- [ ] Domain 层不 import 任何外层模块
- [ ] Application 层只依赖 Domain 接口（ABC）
- [ ] Infrastructure 层实现 Domain 接口
- [ ] Presentation 层只依赖 Application 服务
- [ ] 所有依赖通过 Container 注入

### Python 检查
- [ ] 所有 async 函数正确使用 await
- [ ] 数据库操作使用参数化查询
- [ ] 异常有明确的处理逻辑，不裸 except
- [ ] 文件/连接使用 context manager 或 try-finally

### NoneBot2 检查
- [ ] Matcher 正确注册
- [ ] 权限装饰器正确使用
- [ ] CommandArg 参数提取正确处理