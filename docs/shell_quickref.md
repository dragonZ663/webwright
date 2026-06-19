# Shell 常用命令速查

> 本项目提示词模板中常见命令的快速参考。

---

## 1. 变量

### 定义变量
```bash
VAR_NAME="值"
```
注意：等号两侧**不能有空格**。
```bash
RUN_DIR="final_runs/run_003"   # ✅ 正确
RUN_DIR = "final_runs/run_003" # ❌ 错误
```

### 引用变量
```bash
echo "$VAR_NAME"      # 双引号安全，推荐
echo ${VAR_NAME}       # 同上
echo $VAR_NAME         # 简化写法
```

### 命令替换
```bash
# 执行命令，把输出结果作为值
ACTION_LOG="$(tail -n 80 file.txt)"   # 推荐写法
ACTION_LOG="`tail -n 80 file.txt`"    # 旧写法，不建议
```

---

## 2. 查看文件内容

| 命令 | 作用 | 示例 |
|---|---|---|
| `cat file` | 输出**全部**内容 | `cat final_script_log.txt` |
| `head -n 20 file` | 看文件**前** N 行 | `head -n 50 final_script.py` |
| `tail -n 20 file` | 看文件**末** N 行 | `tail -n 80 final_script_log.txt` |
| `sed -n '1,220p' file` | 看文件**指定范围**行 | `sed -n '50,100p' final_script.py` |

### 示例对比
```bash
# 看 final_script.py 的前 220 行
sed -n '1,220p' final_script.py

# 看 final_script_log.txt 的最后 80 行
tail -n 80 final_script_log.txt

# 看 final_script_log.txt 的第 3 行到第 8 行
sed -n '3,8p' final_script_log.txt
```

---

## 3. 列出文件

| 命令 | 作用 |
|---|---|
| `ls` | 列出当前目录下的文件和目录（不含隐藏文件） |
| `ls -R` | **递归**列出所有子目录的内容 |
| `ls -R final_runs` | 只看 `final_runs/` 及其子目录的所有内容 |

### 常用组合
```bash
ls                        # 精简列表
ls -l                     # 详情列表（权限、大小、修改时间）
ls -la                    # 详情列表 + 显示隐藏文件
ls -R                     # 递归展示完整目录树
ls -R final_runs          # 确认最终运行产物的结构
```

---

## 4. `&&` 与 `||`

| 运算符 | 含义 | 行为 |
|---|---|---|
| `cmd1 && cmd2` | **与** | cmd1 成功（退出码 0）后才执行 cmd2 |
| `cmd1 \|\| cmd2` | **或** | cmd1 失败（退出码非 0）后才执行 cmd2 |

```bash
# 先确认目录存在，再查看日志（目录不存在就不看了）
ls -R final_runs && sed -n '1,200p' final_runs/run_003/final_script_log.txt

# 如果目录不存在则创建
ls -R final_runs || mkdir -p final_runs/run_004
```

---

## 5. 字符串拼接

```bash
DIR="final_runs/run_003"
FILE="${DIR}/final_script_log.txt"    # 结果：final_runs/run_003/final_script_log.txt
LOG="${DIR}/screenshots/shot.png"     # 结果：final_runs/run_003/screenshots/shot.png
```

---

## 6. 换行：反斜杠 `\`

长命令用 `\` 换行，提高可读性：

```bash
# 一行写完（长，难以阅读）
python -m webwright.tools.image_qa --workspace-dir "dir" --image a.png --question "question text"

# 反斜杠换行（清晰）
python -m webwright.tools.image_qa \
  --workspace-dir "{{ workspace_dir }}" \
  --image screenshots/explore.png \
  --question "Is the BMW filter chip visibly selected?"
```

---

## 7. heredoc：`<<'PY'`

在 bash 命令中嵌入多行 Python 脚本：

```bash
python - <<'PY'
import asyncio
print("Hello from Python!")
PY
```

- `<<'PY'` 表示接下来的内容重定向给 `python`，直到遇到 `PY` 为止
- 用引号括起来（`'PY'`）可以阻止 shell 变量替换

---

## 8. 退出码

每条命令执行完后都有一个退出码（exit code）：

| 值 | 含义 |
|---|---|
| `0` | 成功 |
| 非 0 | 失败（具体数字不同的错误类型） |

```bash
ls final_runs && echo "目录存在"    # 只有 ls 成功（退出码 0）才会打印
ls /nonexistent && echo "不会执行" # ls 失败（退出码 非0），跳过 &&
```

---

## 9. 完整组合示例

```bash
# 定义变量 → 提取日志末尾内容 → 传入 image_qa 做验证
RUN_DIR="final_runs/run_003" && \
ACTION_LOG="$(tail -n 80 "${RUN_DIR}/final_script_log.txt")" && \
python -m webwright.tools.image_qa \
  --workspace-dir "{{ workspace_dir }}" \
  --image "${RUN_DIR}/screenshots/shot1.png" \
  --image "${RUN_DIR}/screenshots/shot2.png" \
  --question "Action log:\n${ACTION_LOG}\n\nAre all constraints satisfied?"
```
