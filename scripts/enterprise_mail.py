#!/usr/bin/env python3
"""
Enterprise Mail Sender
Usage: python3 enterprise_mail.py "Subject" "Content"
"""

import json
import subprocess
import sys
import os

CONFIG_PATH = os.path.expanduser("~/.openclaw/conf/enterprise-mail/config.json")

def load_config():
    """Load configuration file"""
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config file not found: {CONFIG_PATH}")
        print("""
Please create config file at: ~/.openclaw/conf/enterprise-mail/config.json

Required format:
{
  "smtp": {"host": "smtp.example.com", "port": 465, "ssl": true},
  "auth": {"user": "your@email.com", "password": "auth-code"},
  "from": "your@email.com",
  "to": ["recipient1@example.com"],
  "report": {"path": "~/.openclaw/workspace/record/日报/", "prefix": "日报-"}
}
""")
        return None
    
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    
    # Validate required fields
    required = ["smtp", "auth", "from", "to"]
    for key in required:
        if key not in config:
            print(f"❌ Missing required config: {key}")
            return None
    
    required_smtp = ["host", "port"]
    for key in required_smtp:
        if key not in config["smtp"]:
            print(f"❌ Missing smtp.{key}")
            return None
    
    required_auth = ["user", "password"]
    for key in required_auth:
        if key not in config["auth"]:
            print(f"❌ Missing auth.{key}")
            return None
    
    if not isinstance(config.get("to"), list) or len(config["to"]) == 0:
        print("❌ 'to' must be non-empty array")
        return None
    
    return config

def send_email(subject, content, recipients=None):
    """Send email via SMTP"""
    config = load_config()
    if not config:
        return False
    
    if not recipients:
        recipients = config.get("to", [])
    
    # Build email content with proper UTF-8 encoding
    mail_lines = [f"From: {config['from']}"]
    for r in recipients:
        mail_lines.append(f"To: {r}")
    mail_lines.append(f"Subject: {subject}")
    mail_lines.append("Content-Type: text/plain; charset=UTF-8")
    mail_lines.append("MIME-Version: 1.0")
    mail_lines.append("")
    mail_lines.append(content)
    
    mail_content = "\n".join(mail_lines)
    
    # Write to temp file
    mail_file = "/tmp/enterprise_mail.txt"
    with open(mail_file, "w", encoding="utf-8") as f:
        f.write(mail_content)
    
    # Build curl command
    protocol = "smtps" if config["smtp"].get("ssl", False) else "smtp"
    cmd = [
        "curl",
        "--url", f"{protocol}://{config['smtp']['host']}:{config['smtp']['port']}",
    ]
    
    if config["smtp"].get("ssl", False):
        cmd.append("--ssl-reqd")
    
    cmd.extend(["--mail-from", config["from"]])
    
    # Add recipients
    for r in recipients:
        cmd.extend(["--mail-rcpt", r])
    
    cmd.extend([
        "--upload-file", mail_file,
        "--user", f"{config['auth']['user']}:{config['auth']['password']}"
    ])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Email sent!")
        print(f"From: {config['from']}")
        print(f"To: {', '.join(recipients)}")
    else:
        print(f"❌ Failed: {result.stderr[-300:]}")
    
    return result.returncode == 0

def get_report_path():
    """Get today's report path from config"""
    config = load_config()
    if not config:
        return None
    
    report_config = config.get("report", {})
    report_path = os.path.expanduser(report_config.get("path", "~/.openclaw/workspace/record/日报/"))
    prefix = report_config.get("prefix", "日报-")
    
    # Get today's date
    today = subprocess.run(
        ["date", "+%Y-%m-%d"],
        capture_output=True, text=True
    ).stdout.strip()
    
    return os.path.join(report_path, f"{prefix}{today}.md")

if __name__ == "__main__":
    # If no args, try to send today's report
    if len(sys.argv) < 3:
        report_path = get_report_path()
        
        if report_path and os.path.exists(report_path):
            with open(report_path, encoding="utf-8") as f:
                content = f.read()
            
            today = subprocess.run(
                ["date", "+%Y-%m-%d"],
                capture_output=True, text=True
            ).stdout.strip()
            subject = f"日报 - {today}"
        else:
            print("Usage: python3 enterprise_mail.py 'Subject' 'Content'")
            print(f"Or ensure report exists: {report_path}")
            sys.exit(1)
    else:
        subject = sys.argv[1]
        content = sys.argv[2]
    
    recipients = sys.argv[3:] if len(sys.argv) > 3 else None
    
    success = send_email(subject, content, recipients)
    sys.exit(0 if success else 1)
