# Bot Orchestrator: 从下载到任务交接

[English](tutorial.en.md) | 简体中文 · [首页](../README.zh-CN.md)

本教程对应 **v1.2.1**.

## 1. 下载与校验

下载完整 bot-orchestrator-v1.2.1.zip 与 SHA256SUMS.txt；只安装技能可选 skill 包。用 macOS 的 shasum -a 256、Linux 的 sha256sum 或 PowerShell 的 Get-FileHash -Algorithm SHA256 比较完整校验值，再解压。需要 Python 3.9+ 与标准库，无需 pip 依赖。Windows 下可把 python3 换成 py -3。

## 2. 运行并检查第一个任务

```sh
python3 scripts/demo.py
```

结果应为 ok: true、goalStatus: done，并列出 facts.json、summary.md、board.sqlite3。打开打印出的工作目录，核对两个金额与总和 42。演示是本地自审，不是独立审阅。

安装技能后也可直接运行 scripts/demo.py。演示创建临时目录并保留产物，查看后可删除自己这次创建的目录。

## 3. 安装与配置

```sh
python3 scripts/board.py --help
```

目标必须是源目录之外的新目录。通过宿主支持的技能路径加载完整文件夹，确认读取 SKILL.md 及 references。宿主提供账号、模型、工具和授权；任务板自己不需要 API 密钥。每个工作目标都应使用明确的数据库及工作区路径。

## 4. 建立自己的任务板

以下路径为示例，请替换为自己的绝对路径：

```sh
python3 scripts/board.py --db /path/to/job/board.sqlite3 init --workspace /path/to/job --goal "Prepare an expense summary" --acceptance "Values match the source and total 42"
python3 scripts/board.py --db /path/to/job/board.sqlite3 add facts --objective "Record amounts 17 and 25" --check "Both values retained; total is 42" --deliverable facts.json
python3 scripts/board.py --db /path/to/job/board.sqlite3 next
```

在已安装技能内，命令路径改为 scripts/board.py。先 start facts，再真实生成交件与检查文件，使用 submit facts --evidence 检查文件 --note 说明 提交；审阅后用 review facts --decision accept 或 rework，并附 --evidence 和 --reason。参数中有空格时使用引号。完整命令见板内 references/board.md。

## 5. 进阶：证据变化、等待与修复

用 status --full 读取当前记录，verify 检查证据。修改一份已验收交件后观察 verify 的非零结果；不要用文字声称旧验收仍有效。reopen 重新打开任务时，下游验收会失效。mark 的 waiting、blocked、cancelled 状态需要明确原因；resume 后重新检查真实条件。

```sh
python3 scripts/moa_demo.py
```

MOA 示例检查候选、发现错误、修复并复检。它使用本地适配器，不发送模型请求。连接真实适配器前，先检查调用协议、权限、预算、超时、可重放性和实际回执。不要把示例通过当成宿主或提供商已接通。

## 6. 排查与验证

退出码：0 为命令成功，verify 的 1 表示证据变化，2 表示输入、生命周期、冲突或 I/O 问题。目标目录存在时先检查旧安装，不要强制覆盖。找不到技能时检查宿主技能根目录并刷新发现。结果不明的外部发送应先核对结果，再决定重试。

```sh
python3 -B scripts/test_board.py
python3 -B scripts/test_moa.py
python3 -B scripts/demo.py
```

## 7. 升级、回退与卸载

完成当前写入，分别备份技能和任务数据库，核对新版本后安装到新目录再切换。保留旧技能以便回退，保留较新的真实任务事实。移除技能目录不会取消曾在宿主另行注册的调度；应在真实宿主内取消并确认。卸载时只移除已核对的技能路径，不删除工作区数据。

[MIT](../LICENSE) · [NOTICE](../NOTICE)
