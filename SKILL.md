---
name: enterprise-mail
description: Send work reports and emails via enterprise SMTP with draft box support. Use when user says "发送工作日报", "发日报", "发送日报", "发送邮件", "发邮件", or wants to send emails via corporate SMTP.
---

# Enterprise Mail Skill

发送企业邮件，支持 SMTP 直接发送和 IMAP 草稿箱两种模式。

## 触发关键词

- 发送工作日报 / 发日报 / 发送日报
- 发送邮件 / 发邮件
- Send work report
- 用企业邮箱发送

## 配置要求

在 `~/.openclaw/conf/enterprise-mail/config.json` 中配置：

```json
{
  "smtp": {
    "host": "smtp.exmail.qq.com",
    "port": 465,
    "ssl": true
  },
  "auth": {
    "user": "your-email@company.com",
    "password": "your-auth-code"
  },
  "from": "your-email@company.com",
  "to": [
    "recipient1@company.com"
  ],
  "report": {
    "path": "~/.openclaw/workspace/record/日报/",
    "prefix": "日报-"
  }
}
```

**注意**: `password` 字段需要填写 IMAP 授权码（不是登录密码），用于草稿箱功能。

## 工作流程（默认：草稿箱模式）

### 完整流程
1. **用户说"发送日报"** → 保存到草稿箱（不直接发送）
2. **用户说"发送"** → 从草稿箱取出，发送邮件，然后删除草稿箱

### 为什么用草稿箱？
- 先让用户确认内容后再发送
- 避免发错/发早

## 使用方式

### 默认：保存草稿箱（两步操作）

```bash
# 步骤1: 保存草稿（今天日报自动读取）
python3 ~/.openclaw/workspace/skills/enterprise-mail/scripts/enterprise_mail_draft.py -f 日报-2026-03-20.md

# 步骤2: 用户确认后发送
python3 ~/.openclaw/workspace/skills/enterprise-mail/scripts/enterprise_mail_draft.py send
```

### 直接发送（不走草稿箱）

```bash
python3 ~/.openclaw/workspace/skills/enterprise-mail/scripts/enterprise_mail_draft.py send -f 日报-2026-03-20.md
```

### 原始脚本（仅发送，无草稿箱）

```bash
python3 ~/.openclaw/workspace/skills/enterprise-mail/scripts/enterprise_mail.py "Subject" "Content"
```

## 脚本说明

### enterprise_mail_draft.py（推荐）

- 默认保存草稿箱
- `send` 参数：从草稿箱取出发送（发送后自动删除草稿）
- `-f` 参数：读取文件内容

### enterprise_mail.py（基础版）

- 直接通过 SMTP 发送，无草稿箱功能

## 功能特性

- 📧 SMTP SSL 发送
- 📝 IMAP 草稿箱支持（先存草稿，确认后再发）
- 🗑️ 发送后自动删除草稿
- 👥 支持多人发送
- 📄 文件内容作为邮件正文发送

## 文件位置

- Skill: `~/.openclaw/workspace/skills/enterprise-mail/`
- Config: `~/.openclaw/conf/enterprise-mail/config.json`
- 主脚本: `~/.openclaw/workspace/skills/enterprise-mail/scripts/enterprise_mail_draft.py`
- 基础脚本: `~/.openclaw/workspace/skills/enterprise-mail/scripts/enterprise_mail.py`

## 注意事项

- 腾讯企业邮箱需要开启 IMAP 服务并使用授权码
- 草稿箱功能使用 IMAP 协议（端口 993）
- 发送使用 SMTP 协议（端口 465）
