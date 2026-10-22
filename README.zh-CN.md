# Bot Orchestrator

[English](README.md) | 简体中文

把跨多次会话的任务留在一块可检查的本地任务板上。任务、依赖、交件与审阅结果保存在 SQLite 中，继续工作前可以先核对证据是否已经变化。

[下载 v1.2.1](https://github.com/KarmenLoop/bot-orchestrator/releases/tag/v1.2.1) · [完整教程](docs/tutorial.zh-CN.md) · [Issues](https://github.com/KarmenLoop/bot-orchestrator/issues)

## 用途与范围

依赖任务只有在前置工作通过审阅后才会就绪。verify 会检查已记录证据的变化；reopen 可以使下游验收失效。任务板记录状态，真正的执行仍由宿主工具完成。

单独的可选 MOA 驱动能调用明确配置的适配器，处理候选、审阅、修复与复检。离线示例只使用本地子进程，不连接模型账号。

![本地任务板演示结果](docs/images/local-demo-v1.2.1.svg)

*v1.2.1 的真实演示摘要，工作目录显示为占位符；非宿主界面截图。*

## 开始使用

下载完整仓库包 bot-orchestrator-v1.2.1.zip 并核对 SHA256SUMS.txt，解压后使用 Python 3.9+：

```sh
python3 examples/local_demo.py
python3 examples/moa_demo.py
```

第一个示例真实创建任务板、生成金额 17 与 25、检查总和 42、审阅两项任务并关闭目标。它会打印工作目录，便于查看产物。第二个示例展示一次失败后的修复与复检。

## 安装技能

```sh
python3 scripts/install_skill.py --destination ../installed-skills/bot-orchestrator
```

选择新目录，再按宿主支持的方式加载。安装器拒绝覆盖已有目录。较小的 bot-orchestrator-skill-1.2.1.zip 可直接解压到技能目录，包内也保留双语入门文档。

## 常见问题

**时间到了会自动继续吗？** 不会。等待状态需要真实的调度器或人工复查。安装不会注册后台任务，也不会授权对外操作。

**数据在哪里？** 数据库路径由 --db 明确指定；交件和证据留在所选工作区。不要将真实任务数据库或私人文件提交到公共仓库。

## 文档与许可证

[下载到进阶使用](docs/tutorial.zh-CN.md) · [命令参考](skills/bot-orchestrator/references/board.md) · [MIT](LICENSE) · [NOTICE](NOTICE)

宿主、模型、连接器与真实设备验收需分别确认。包测试不等于外部集成通过。
