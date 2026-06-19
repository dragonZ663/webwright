# 两种环境模式对比：local_workspace vs local_browser

> 基于 `src/webwright/environments/local_workspace.py` 和 `src/webwright/environments/local_browser.py` 源码分析。

---

## 一、一句话总结

| | `local_workspace`（标准模式） | `local_browser`（实时浏览器模式） |
|---|---|---|
| **Agent 输出字段** | `bash_command` | `python_code` |
| **浏览器管理** | Agent 在脚本里**自己创建和销毁** | **环境持有**浏览器，Agent 直接驱动 |
| **工作空间** | 有（生成脚本、截图、日志等产物） | 无（不写文件，不创建产物） |
| **最终产物** | `final_script.py` + 截图 + 日志 + self_reflection 裁判 | 无需产物，直接报告答案 |

---

## 二、核心执行模型差异

### 2.1 `local_workspace` — 无状态，每次从头开始

```
┌─────────┐     ┌──────────────────────┐     ┌─────────┐
│ Agent   │────→│ bash 命令             │────→│ 新 Shell  │
│ (LLM)   │     │ python - <<'PY' ...   │     │ 子进程   │
└─────────┘     │ playwright.launch()   │     │ ← 进程结束│
                │ ...                   │     │ 状态全丢 │
                │ await browser.close() │     │         │
                └──────────────────────┘     └─────────┘
                                                  │
                                          下次又从头创建
                                          全新的浏览器会话
```

关键特征：
- 每步都是**独立的 Shell 子进程**（`subprocess.run()`）
- Agent 的脚本里必须自己 `playwright.chromium.launch()`，用完自己 `close()`
- **没有持久的状态**——下个 bash 命令启动时一切归零
- 提示词中明确强调：*"There is NO persistent browser state. Every Playwright run must create a fresh browser session"*

### 2.2 `local_browser` — 有状态，浏览器始终存活

```
┌─────────┐     ┌──────────────────────────┐     ┌──────────────┐
│ Agent   │────→│ python_code:              │────→│ 环境接管执行   │
│ (LLM)   │     │ await page.goto()         │     │ exec() 包装成  │
└─────────┘     │ print(await page.title()) │     │ async def    │
                └──────────────────────────┘     │ 注入 page,    │
                                                 │ context,     │
                                                 │ browser,     │
                                                 │ playwright   │
                                                 └──────┬───────┘
                                                        │
                                                浏览器始终存活
                                                下次继续用同一个 page
```

关键特征：
- 环境在 `prepare()` 时启动 Playwright，创建 `page`/`context`/`browser`
- Agent 的 `python_code` 通过 `exec()` + `asyncio` 执行，直接操作**已有的**浏览器对象
- **状态持久**——上一轮的 cookies、localStorage、对话框状态都在，无需重新导航

---

## 三、执行引擎对比

| 维度 | `local_workspace` | `local_browser` |
|---|---|---|
| **执行引擎** | `subprocess.run()` | `exec()` 包装成 async 函数 + `asyncio` |
| **命令字段** | `bash_command`（或 `command`/`python_code` 兼容） | `python_code` |
| **CWD 管理** | 限制在工作空间目录内，不得逃逸 | 无 CWD 概念 |
| **超时控制** | `command_timeout_seconds`（进程级 kill） | `step_execution_timeout_ms`（asyncio 超时） |
| **输出捕获** | stdout + stderr 合并 → `command_output` | Python print → `python_output` |
| **浏览器控制台** | 不捕获 | 监听 `page.on("console")`，自动捕获 |
| **执行方式** | 纯文本命令传给 `shell` | 注入 `page`/`context`/`browser`/`playwright` 后 exec |

---

## 四、观察信息差异

### 4.1 `local_workspace` 每步返回

```python
{
    "success": True/False,
    "exception": "错误信息",
    "command": "执行的命令",
    "returncode": 0,
    "workspace_dir": "/path/to/output",
    "cwd": "/path/to/output",
    "url": "",                      # ← 空！不自动获取
    "title": "",                    # ← 空！
    "aria_snapshot": "",            # ← 空！不自动抓取
    "console_output": "",           # ← 空！不捕获浏览器日志
    "recent_console": "",
    "command_output": "...截断的命令输出...",
    "log_path": "steps/step_0001.log",
    "task_metadata_path": "...",
    "final_script_path": "...",
    "final_script_exists": True,
    "final_script_preview": "...",
    "screenshot_path": "screenshots/xxx.png",
    "recent_screenshots": [...],
    "workspace_files": [...],       # 最近修改的文件列表
}
```

Agent 必须自己在脚本里 `print(await page.title())`、`print(await page.locator("body").aria_snapshot())` 来获取页面信息。

### 4.2 `local_browser` 每步返回

```python
{
    "success": True/False,
    "exception": "错误信息",
    "url": "https://example.com",             # ← ✅ 自动获取
    "title": "Example Domain",                # ← ✅ 自动获取
    "aria_snapshot": "[button] ...",          # ← ✅ 自动抓取 ARIA 树！
    "python_code": "await page.goto(...)",    # 执行的代码
    "python_output": "...打印输出...",
    "console_output": "...浏览器 console...",  # ← ✅ 自动捕获！
    "recent_console": "...历史 console...",
    "screenshot_path": "screenshots/step_0001.png",  # 自动截图
}
```

环境自动执行三件事：
1. `page.title()` — 获取页面标题
2. `page.locator("body").aria_snapshot()` — 抓取 ARIA 无障碍树
3. `page.screenshot()` — 保存截图到磁盘

Agent 无需手动打印这些信息，每步观察中自然包含。

---

## 五、配置差异

| 配置 | `local_workspace`（`base.yaml`） | `local_browser`（`local_browser.yaml`） |
|---|---|---|
| `environment_class` | `local_workspace` | `local_browser` |
| `action_field` | `bash_command` | `python_code` |
| `require_self_reflection_success` | `true` | `false` |
| `keep_last_n_observations` | 无（默认保留全部） | `1`（只保留最近 1 步的 ARIA） |
| `summary_every_n_steps` | 20 | 20（但使用不同的 summary prompt） |
| `summary_user_prompt` | 默认（含 workspace 产物） | 自定义（针对浏览器状态） |

---

## 六、提示词体系差异

### 6.1 JSON 响应格式

**`local_workspace`：**
```json
{
  "thought": "...",
  "bash_command": "python - <<'PY' ... PY",
  "done": false,
  "final_response": ""
}
```

**`local_browser`：**
```json
{
  "thought": "...",
  "python_code": "await page.goto('...')\nprint(await page.title())",
  "done": false,
  "final_response": ""
}
```

### 6.2 浏览器示例代码

**`local_workspace`** — 完整的 heredoc 脚本模板（需自己 launch/close）：
```python
async with async_playwright() as playwright:
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(viewport={"width": 1280, "height": 1800})
    page = await context.new_page()
    await page.goto("...")
    # ...
    await browser.close()
```

**`local_browser`** — 极简，直接操作已有对象：
```python
await page.goto("...", wait_until="domcontentloaded")
print("URL:", page.url)
print("TITLE:", await page.title())
print("ARIA:", await page.locator("body").aria_snapshot())
```

### 6.3 规则数量

| 规则类别 | `local_workspace` | `local_browser` |
|---|---|---|
| 全局约束 | 8 条 | 8 条（无 workspace/no browser state 相关） |
| 浏览器模式说明 | 2 条 | 2 条 |
| Playwright 示例 | 完整 heredoc | 简短的 python_code |
| Rules | 11 条 | 9 条（无 screenshot / artifact 相关） |
| Task Reflection Tool | 详细说明（含 CLI、JSON schema、4 prompts） | **无** |
| Image QA Tool | 详细说明 | **无** |
| Completion Gate | 5 个严格条件 | **无** |
| 总计 | ≈ 220 行模板 | ≈ 100 行模板 |

### 6.4 工作流程步骤

**`local_workspace` — 6 步严格流程：**
1. **规划**：解析关键检查点，写入 `plan.md`
2. **编写配置**：写 `self_reflect_config.json`（含 4 条提示词）
3. **探索**：创建探索脚本，用 `image_qa` 验证 UI
4. **最终脚本**：写 `final_script.py`，截图 + 日志
5. **运行裁判**：`self_reflection` 验证结果
6. **声明完成**：仅当裁判 PASS

**`local_browser` — 3 步简化流程：**
1. 分析任务和约束
2. 一步步驱动实时浏览器
3. 任务满足后声明完成

---

## 七、工作空间与产物差异

### 7.1 目录结构

**`local_workspace`：**
```
outputs/task_id_timestamp/
├── task.json                    # 任务元数据
├── plan.md                      # 关键检查点清单
├── final_script.py              # 最终脚本
├── config_snapshot/             # 配置快照
│   ├── merged_config.yaml
│   ├── 00_base.yaml
│   ├── 01_model_claude.yaml
│   └── config_spec_manifest.json
├── final_runs/
│   └── run_001/
│       ├── final_script.py
│       ├── final_script_log.txt
│       ├── self_reflect_result.json
│       └── screenshots/
│           ├── final_execution_1_open_page.png
│           ├── final_execution_2_apply_filter.png
│           └── ...
├── steps/                       # 每一步的命令记录
│   ├── step_0001.sh
│   ├── step_0002.sh
│   └── ...
├── logs/                        # 每一步的输出记录
├── screenshots/                 # 探索阶段的截图
├── command_history.sh
└── .tmp/
```

**`local_browser`：**
```
outputs/
├── task.json
├── screenshots/
│   ├── step_0001.png
│   ├── step_0002.png
│   └── ...
├── steps/
│   ├── step_0001.py
│   ├── step_0002.py
│   └── ...
└── script.py                    # 所有步骤代码的拼接文件
```

### 7.2 产物要求对比

| 产物 | `local_workspace` | `local_browser` |
|---|---|---|
| `plan.md` | ✅ **必需** | ❌ 不需要 |
| `self_reflect_config.json` | ✅ **必需** | ❌ 不需要 |
| `final_script.py` | ✅ **必需** | ❌ 不需要 |
| `final_runs/` | ✅ **必需** | ❌ 不需要 |
| 截图 | ✅ 关键检查点截图 | ✅ 自动每步截图 |
| 操作日志 | ✅ `final_script_log.txt` | ❌ 不需要 |
| 裁判结果 | ✅ `self_reflect_result.json` | ❌ 不需要 |

---

## 八、适用场景

| 场景 | 推荐模式 | 原因 |
|---|---|---|
| 自动化批处理作业 | `local_workspace` | 有完整产物、可回溯、可通过 `self_reflection` 裁判 |
| 开发调试 | `local_browser` + `debug` 标志 | 实时交互、能看到浏览器、快速迭代 |
| 需要登录态（如 Google 账号） | `local_browser`（`local_cdp` 模式） | 持久化用户数据目录，登录态保持 |
| 需要筛选验证（复杂度高） | `local_workspace` | 必须通过裁判，结果可信 |
| 简单查询（"打开页面告诉我标题"） | `local_browser` | 快速、无冗余产物 |
| 研究 / 探索性任务 | `local_browser` | 灵活、Agent 可随时调整策略 |
| 需提交最终脚本供审查 | `local_workspace` | `final_script.py` 可被审查和重放 |

---

## 九、启动命令示例

### 标准模式（`local_workspace`）

```bash
python -m webwright.run.cli \
  -c base.yaml -c model_claude.yaml \
  -t "Search for flights" \
  --start-url https://www.google.com/flights \
  --task-id demo \
  -o outputs/default
```

### 实时浏览器模式（`local_browser`）

```bash
python -m webwright.run.cli \
  -c base.yaml -c local_browser.yaml -c model_openai.yaml \
  -t "Open example.com and report the title" \
  --start-url https://example.com
```

### 实时浏览器 + 调试模式

```bash
python -m webwright.run.cli \
  -c base.yaml -c local_browser.yaml -c model_claude.yaml \
  -t "..." \
  --start-url https://... \
  --debug
```

`--debug` 标志会设置 `headless=false`、`devtools=true`、`keep_open_on_exit=true`，让你能看到浏览器界面。

---

## 十、内部类结构对比

| 维度 | `LocalWorkspaceEnvironment` | `LocalBrowserEnvironment` |
|---|---|---|
| 所在文件 | `local_workspace.py` | `local_browser.py` |
| 配置类 | `LocalWorkspaceEnvironmentConfig` | `LocalBrowserEnvironmentConfig` |
| 配置项数量 | 11 个 | 18 个 |
| 浏览器配置 | 仅传 `BROWSER_MODE` 环境变量 | 直接管理 Playwright 的 headless/viewport/timeout |
| 浏览器启动 | 由 Agent 脚本内部处理 | 环境在 `prepare()` 自动启动 |
| 浏览器模式 | `browserbase` / `local` | `local_cdp` / `local_launch` / `local_persistent` |
| 截图方式 | Agent 脚本自己调用 `page.screenshot()` | 环境每步自动截图 |
| 关闭清理 | `close()` 为空（不操作） | `close()`：关闭 Playwright、终止浏览器进程 |
