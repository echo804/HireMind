# HireMind 简历管理模块 — 开发问题总结

> 记录在简历上传、解析、AI 分析模块中遇到的**高重复性、高难度**问题及其最终解决方案。

---

## 1. WSL 与 Windows 代码双副本不同步

### 现象
- 修改了 Windows 侧 `D:\...\HireMind\` 的代码，但 WSL 侧 `~/HireMind/` 仍在运行旧代码
- 前端页面不更新、后端 API 行为与预期不符、`import` 报错 `ModuleNotFoundError`
- 每次改代码都要手动 `cp`，极易遗漏

### 根因
WSL 中的 `~/HireMind` 是**独立副本**（非 `/mnt/d/` 挂载），venv、node_modules 都是 WSL 原生安装，与 Windows 侧完全隔离。

### 解决方案
创建 `scripts/sync_to_wsl.sh` 一键同步脚本：
```bash
cp -r /mnt/d/.../HireMind/app/* ~/HireMind/app/
cp -r /mnt/d/.../HireMind/frontend/src/* ~/HireMind/frontend/src/
touch ~/HireMind/app/main.py  # 触发 uvicorn reload
```
**教训**：改代码前后各跑一次，或直接改成 `/mnt/d/` 挂载方式运行。

---

## 2. 异步后台任务被 uvicorn reload 杀死

### 现象
- 上传简历后卡在 `processing` 状态，progress 固定在 10%/30%/50%，永不完成
- 后端日志无任何报错，任务静默消失

### 根因
`asyncio.create_task()` 创建的后台任务在 uvicorn `--reload` 时被取消。

### 解决方案
**放弃异步模式，改为「上传秒返 + 详情页同步触发」**：
```python
# upload: 保存 → 返回 processing（不启动后台任务）
# get_by_id: 检测到 processing → 同步执行 _process_resume
```
前端上传后自动跳转详情页，1.5秒轮询拿到进度。

**教训**：开发环境 reload 与异步后台任务互斥。

---

## 3. API Key 掩码覆盖真实 Key

### 现象
- 设置页修改模型后保存，API 报 `Incorrect API key`
- 数据库存的是 `sk-w****...5TvQ`（掩码值）

### 根因
`get_settings` 返回脱敏 key，前端展示掩码值。用户改其他字段提交，掩码被原样发回覆盖真实 key。

### 解决方案
```python
if "api_key" in key and val and "**" in val:
    continue  # 跳过掩码值
```

---

## 4. 数据库枚举不同步

### 现象
上传报错 `invalid input value for enum resumestatus: "PROCESSING"`

### 根因
Python 加了 `PROCESSING = "processing"`，DB 没同步。

### 解决方案
```sql
ALTER TYPE resumestatus ADD VALUE IF NOT EXISTS 'PROCESSING';
```

---

## 5. 去重检查导致重新上传失败

### 现象
上传→成功→删除→再上传→"Duplicate resume"。DB 中 FAILED 记录残留了哈希。

### 根因
`find_by_hash` 查询所有记录（含 FAILED），删除成功记录后旧哈希仍存在。

### 解决方案
**移除去重检查**。开发/测试阶段去重干扰远大于收益。

---

## 6. 删除 API 参数顺序颠倒

### 现象
前端删除无反应，返回 404。

### 根因
`service.delete_resume(resume_id, user_id)` → 方法签名是 `(user_id, resume_id)`

### 解决方案
调换参数顺序：`service.delete_resume(str(user_id), resume_id)`

---

## 7. 异步任务跨 Session 问题

### 现象
`Instance is not persistent within this Session`

### 根因
FastAPI 请求结束时关闭 DB session，后台任务持有的 entity 脱离 session。

### 解决方案
独立 session factory + `db.merge(entity)`。

---

## 总结

| # | 问题 | 难度 | 重复性 | 最终方案 |
|---|------|------|--------|----------|
| 1 | WSL/Windows 代码不同步 | 中 | 极高 | sync_to_wsl.sh |
| 2 | 异步任务被杀 | 高 | 高 | 改为同步触发 |
| 3 | API Key 掩码覆盖 | 低 | 中 | 后端跳过 `**` |
| 4 | 枚举不同步 | 低 | 低 | ALTER TYPE |
| 5 | 去重导致再上传失败 | 中 | 极高 | 移除去重 |
| 6 | 删除参数颠倒 | 低 | 低 | 调换参数顺序 |
| 7 | Session 分离 | 高 | 中 | 独立 session factory |

**核心经验**：
1. 开发环境 reload 与异步任务互斥
2. WSL 双副本是万恶之源
3. 去重不要过早加 — 核心流程稳定前它是 bug 制造机
4. 敏感字段单向脱敏 — 永远不要让前端回传掩码值
