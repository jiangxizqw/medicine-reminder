# 💊 药品库存提醒

每天自动检查药品剩余天数，当有药品库存不足时，自动发送邮件提醒购买。

---

## ✨ 功能特点

- **自动计算**：每天自动计算所有药品剩余天数
- **智能提醒**：剩余天数少于 7 天自动发送邮件
- **状态标识**：邮件中用颜色区分「急需购买 / 即将不足 / 充足」
- **一键更新**：买了新药后，只需改一行日期，push 到仓库即可
- **零成本**：完全免费，利用 GitHub Actions 定时运行

---

## 📁 仓库结构

```
.
├── .github/
│   └── workflows/
│       └── medicine.yml          # GitHub Actions 工作流
├── medicine_reminder.py          # 主脚本（买药时改这里）
└── README.md                     # 本文件
```

---

## 🚀 快速开始

### 第一步：Fork 或创建仓库

将本仓库 Fork 到您的 GitHub 账号，或新建一个仓库，把 `medicine_reminder.py` 和 `.github/workflows/medicine.yml` 上传上去。

### 第二步：配置 Secrets

进入仓库 **Settings → Secrets and variables → Actions → New repository secret**，添加以下 3 个密钥：

| Secret 名称 | 说明 | 示例 |
|---|---|---|
| `YX_SENDER_EMAIL` | 发件人 QQ 邮箱 | `123456@qq.com` |
| `YX_SENDER_PASSWORD` | QQ 邮箱 **授权码**（不是登录密码！） | `abcdefghijklmnop` |
| `YX_RECEIVER_EMAIL` | 收件人邮箱（可填同一个 QQ 邮箱） | `123456@qq.com` |

> 💡 **如何获取 QQ 邮箱授权码？**
> 1. 电脑登录网页版 [QQ邮箱](https://mail.qq.com)
> 2. 点击顶部「设置」→「账户」
> 3. 找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务」
> 4. 开启「SMTP服务」，按提示发送短信验证
> 5. 获得 16 位授权码，复制粘贴到 Secret 中

### 第三步：修改药品数据

打开 `medicine_reminder.py`，修改以下两部分：

#### 1. 药品记录日期

```python
# 📅 药品记录日期（买了新药后，改成今天的日期，push 到仓库即可）
RECORD_DATE = "2026-08-12"
```

改成您**开始吃这批药的日期**（或今天）。

#### 2. 药品列表（按需修改）

```python
MEDICINES = [
    {"name": "盐酸沙格雷酯片",     "initial_days": 60, "usage": "每日3次，一次1片", "note": ""},
    {"name": "阿司匹林肠溶片",     "initial_days": 60, "usage": "每日1次，一次1片", "note": "刺激胃部，导致咳嗽，备点胃药"},
    {"name": "阿托伐汀钙片",       "initial_days": 60, "usage": "每日1次，一次1片", "note": ""},
    {"name": "阿卡波糖片",         "initial_days": 60, "usage": "每日3次，一次1片", "note": "饭前吃"},
    {"name": "盐酸二甲双胍片",     "initial_days": 60, "usage": "每日1次，一次1片", "note": ""},
    {"name": "硝苯地平控释片",     "initial_days": 60, "usage": "每日1次，一次1片", "note": ""},
    {"name": "沙库巴曲缬沙坦钠片", "initial_days": 60, "usage": "每日1次，一次1片", "note": ""},
]
```

| 字段 | 说明 |
|---|---|
| `name` | 药品名称 |
| `initial_days` | 这批药能吃多少天（新买的数量） |
| `usage` | 用法用量，邮件中显示 |
| `note` | 注意事项，邮件中显示（没有可留空） |

### 第四步：提交并测试

```bash
git add .
git commit -m "初始化药品提醒"
git push
```

然后进入仓库 **Actions** 标签页，找到 `Medicine Reminder` 工作流，点击 **Run workflow** 手动运行一次测试。

如果配置正确，您会收到一封邮件，显示所有药品的当前剩余天数。

---

## 🔄 买了新药后如何更新？

**只需改一行日期，push 即可：**

1. 打开 `medicine_reminder.py`
2. 把 `RECORD_DATE` 改成今天的日期：
   ```python
   RECORD_DATE = "2026-08-17"   # ← 改成今天
   ```
3. 如果有药品数量变了，同步修改对应 `initial_days`
4. Push 到仓库：
   ```bash
   git add medicine_reminder.py
   git commit -m "更新药品记录日期"
   git push
   ```

下次定时任务运行时，会自动以新日期重新计算所有药品的剩余天数。

> 💡 也可以直接在 GitHub 网页上编辑 `medicine_reminder.py`，保存后会自动提交。

---

## ⏰ 定时规则

默认每天 **北京时间 9:00** 运行一次。

如需修改，编辑 `.github/workflows/medicine.yml` 中的 cron 表达式：

```yaml
on:
  schedule:
    - cron: '0 1 * * *'   # UTC 1:00 = 北京时间 9:00
```

| 北京时间 | UTC 时间 | cron |
|---|---|---|
| 早上 8:00 | 00:00 | `0 0 * * *` |
| 早上 9:00 | 01:00 | `0 1 * * *` |
| 晚上 8:00 | 12:00 | `0 12 * * *` |
| 晚上 9:00 | 13:00 | `0 13 * * *` |

---

## 📧 邮件效果

邮件包含以下内容：

- **提醒摘要**：多少种药品、多少种库存不足
- **药品明细表**：名称、用法用量、剩余天数、注意事项、状态标签
- **状态颜色**：
  - 🔴 红色 — 少于 7 天，急需购买
  - 🟠 橙色 — 7~14 天，即将不足
  - 🟢 绿色 — 充足

---

## ⚙️ 高级配置

### 修改提醒阈值

默认剩余天数 **少于 7 天** 时发送邮件。如需调整，修改脚本中的：

```python
ALERT_THRESHOLD = 7   # 改成您想要的数字，如 10 或 14
```

### 使用其他邮箱

默认使用 QQ 邮箱（`smtp.qq.com:465`）。如需换用 163 邮箱或其他：

在 `.github/workflows/medicine.yml` 的 `Run medicine reminder` step 中添加：

```yaml
env:
  YX_SMTP_SERVER: smtp.163.com
  YX_SMTP_PORT: 465
  YX_SENDER_EMAIL: ${{ secrets.YX_SENDER_EMAIL }}
  YX_SENDER_PASSWORD: ${{ secrets.YX_SENDER_PASSWORD }}
  YX_RECEIVER_EMAIL: ${{ secrets.YX_RECEIVER_EMAIL }}
```

| 邮箱 | SMTP 服务器 | 端口 |
|---|---|---|
| QQ 邮箱 | `smtp.qq.com` | 465 |
| 163 邮箱 | `smtp.163.com` | 465 |
| Gmail | `smtp.gmail.com` | 465/587 |

> ⚠️ Gmail 需要开启两步验证并生成应用专用密码，且国内连接可能不稳定。

---

## ❓ 常见问题

### Q1: 邮件发送失败，提示认证错误？

请检查：
- `YX_SENDER_PASSWORD` 填的是**授权码**，不是 QQ 登录密码
- QQ 邮箱的 SMTP 服务已开启
- 邮箱账号没有异常（新注册邮箱需等待 14 天才能使用 SMTP）

### Q2: 邮件里日期显示不对？

Workflow 中已设置 `TZ: Asia/Shanghai`，确保使用北京时间。如果仍不对，请检查 GitHub Actions 日志中的 `Check timezone` 步骤输出。

### Q3: 可以设置多个收件人吗？

可以，在 `YX_RECEIVER_EMAIL` 中用逗号分隔多个邮箱：

```
123456@qq.com,789012@qq.com
```

### Q4: 每天会发多少封邮件？

- **有药品不足 7 天**：发送 1 封提醒邮件
- **所有药品都充足**：不发送邮件（避免打扰）

### Q5: QQ 邮箱有发送限制吗？

有，但您的场景完全够用：
- QQ 邮箱每天约 100~200 封上限
- 您每天最多发 1 封，离限制很远

---

## 📜 开源协议

MIT License

---

> 💡 **温馨提示**：本工具仅作药品库存提醒参考，具体用药请遵医嘱。如有身体不适，请及时就医。
