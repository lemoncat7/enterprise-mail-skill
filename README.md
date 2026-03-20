# Enterprise Mail Skill

Send work reports and emails via enterprise SMTP for OpenClaw.

## Features

- 📧 Send emails via SMTP (SSL supported)
- 👥 Support multiple recipients (bulk send)
- 📝 Auto-read configuration
- 📎 Support sending reports and custom content

## Quick Start

### 1. Install

Clone this skill to your OpenClaw skills directory:

```bash
git clone https://github.com/lemoncat7/enterprise-mail-skill.git ~/.openclaw/workspace/skills/enterprise-mail
```

### 2. Configure

Create config file at `~/.openclaw/conf/enterprise-mail/config.json`:

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
    "recipient1@company.com",
    "recipient2@company.com"
  ],
  "report": {
    "path": "~/.openclaw/workspace/record/日报/",
    "prefix": "日报-"
  }
}
```

### 3. Usage

Just tell the AI:
- "发送工作日报" (send work report)
- "发日报"
- "发送邮件"

Or use manually:

```bash
python3 ~/.openclaw/workspace/skills/enterprise-mail/scripts/enterprise_mail.py "Subject" "Content"
```

## Configuration Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| smtp.host | ✅ | SMTP server address |
| smtp.port | ✅ | SMTP port (465 or 587) |
| smtp.ssl | ✅ | Enable SSL |
| auth.user | ✅ | SMTP username |
| auth.password | ✅ | SMTP auth code |
| from | ✅ | Sender email |
| to | ✅ | Recipient list |
| report.path | ❌ | Report directory |
| report.prefix | ❌ | Report filename prefix |

## Supported SMTP Services

- Tencent Exmail (smtp.exmail.qq.com)
- QQ Mail (smtp.qq.com)
- Gmail (smtp.gmail.com)
- Any SMTP server with SSL support

## License

MIT
