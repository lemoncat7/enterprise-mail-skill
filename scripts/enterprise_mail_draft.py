#!/usr/bin/env python3
"""
Enterprise Mail Sender - 支持草稿箱
Usage: 
  python3 enterprise_mail_draft.py "Subject" "Content" [draft|send]
  默认是 draft (保存草稿箱)，send 是直接发送
"""

import json
import imaplib
import email
from email.mime.text import MIMEText
from email.header import Header
import subprocess
import sys
import os
import socket
import time
import datetime

socket.setdefaulttimeout(30)

CONFIG_PATH = os.path.expanduser("~/.openclaw/conf/enterprise-mail/config.json")

def load_config():
    """Load configuration file"""
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config file not found: {CONFIG_PATH}")
        return None
    
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    
    required = ["smtp", "auth", "from", "to"]
    for key in required:
        if key not in config:
            print(f"❌ Missing required config: {key}")
            return None
    
    return config

def save_draft(subject, content, recipients=None, cc_recipients=None):
    """保存邮件到草稿箱 via IMAP"""
    config = load_config()
    if not config:
        return False
    
    if not recipients:
        recipients = config.get("to", [])
    if not cc_recipients:
        cc_recipients = config.get("cc", [])
    
    # IMAP 配置
    IMAP_HOST = "imap.exmail.qq.com"
    IMAP_PORT = 993
    USER = config["auth"]["user"]
    PASSWORD = config["auth"]["password"]
    
    try:
        print(f"连接 IMAP {IMAP_HOST}:{IMAP_PORT}...")
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=20)
        mail.login(USER, PASSWORD)
        print("登录成功!")
        
        # 选择草稿箱
        status, _ = mail.select('"Drafts"')
        if status != 'OK':
            print(f"❌ 选择草稿箱失败: {status}")
            return False
        print("选择草稿箱成功!")
        
        # 构建邮件
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = config["from"]
        msg['To'] = ", ".join(recipients)
        if cc_recipients:
            msg['Cc'] = ", ".join(cc_recipients)
        msg['Subject'] = Header(subject, 'utf-8')
        
        # 保存草稿
        mail.append(
            '"Drafts"',
            '\\Draft',
            time.time(),
            msg.as_string().encode('utf-8')
        )
        
        mail.logout()
        print(f"\n✅ 草稿保存成功!")
        print(f"主题: {subject}")
        print(f"收件人: {', '.join(recipients)}")
        return True
        
    except Exception as e:
        print(f"❌ 草稿保存失败: {e}")
        return False

def send_email(subject, content, recipients=None, cc_recipients=None):
    """发送邮件 via SMTP (curl)"""
    config = load_config()
    if not config:
        return False
    
    if not recipients:
        recipients = config.get("to", [])
    if not cc_recipients:
        cc_recipients = config.get("cc", [])
    
    mail_lines = [f"From: {config['from']}"]
    for r in recipients:
        mail_lines.append(f"To: {r}")
    if cc_recipients:
        for c in cc_recipients:
            mail_lines.append(f"Cc: {c}")
    mail_lines.append(f"Subject: {subject}")
    mail_lines.append("Content-Type: text/plain; charset=UTF-8")
    mail_lines.append("MIME-Version: 1.0")
    mail_lines.append("")
    mail_lines.append(content)
    
    mail_content = "\n".join(mail_lines)
    
    mail_file = "/tmp/enterprise_mail.txt"
    with open(mail_file, "w", encoding="utf-8") as f:
        f.write(mail_content)
    
    protocol = "smtps" if config["smtp"].get("ssl", False) else "smtp"
    cmd = [
        "curl",
        "--url", f"{protocol}://{config['smtp']['host']}:{config['smtp']['port']}",
    ]
    
    if config["smtp"].get("ssl", False):
        cmd.append("--ssl-reqd")
    
    cmd.extend(["--mail-from", config["from"]])
    
    for r in recipients:
        cmd.extend(["--mail-rcpt", r])
    for c in cc_recipients:
        cmd.extend(["--mail-rcpt", c])
    
    cmd.extend([
        "--upload-file", mail_file,
        "--user", f"{config['auth']['user']}:{config['auth']['password']}"
    ])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Email sent!")
        print(f"To: {', '.join(recipients)}")
    else:
        print(f"❌ Failed: {result.stderr[-300:]}")
    
    return result.returncode == 0

def get_report_path():
    """获取今天的日报路径"""
    config = load_config()
    if not config:
        return None
    
    report_config = config.get("report", {})
    report_path = os.path.expanduser(report_config.get("path", "~/.openclaw/workspace/record/日报/"))
    prefix = report_config.get("prefix", "日报-")
    
    today = subprocess.run(["date", "+%Y-%m-%d"], capture_output=True, text=True).stdout.strip()
    return os.path.join(report_path, f"{prefix}{today}.md")

def send_from_draft(subject_hint=None):
    """从草稿箱取出邮件并发送"""
    config = load_config()
    if not config:
        return False
    
    recipients = config.get("to", [])
    
    USER = config["auth"]["user"]
    AUTH_CODE = config["auth"]["password"]
    
    try:
        print(f"连接 IMAP...")
        mail = imaplib.IMAP4_SSL("imap.exmail.qq.com", 993, timeout=20)
        mail.login(USER, AUTH_CODE)
        print("登录成功!")
        
        status, _ = mail.select('"Drafts"')
        if status != 'OK':
            print("❌ 选择草稿箱失败")
            return False
        
        # 获取最新草稿
        status, msgs = mail.search(None, "ALL")
        
        if status != 'OK' or not msgs[0]:
            print("❌ 草稿箱为空")
            return False
        
        msg_ids = msgs[0].split()
        latest_id = msg_ids[-1]
        latest_id_str = latest_id.decode()
        
        status, msg_data = mail.fetch(latest_id, "(RFC822)")
        if status != 'OK':
            print("❌ 获取邮件失败")
            return False
        
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        subject = msg['Subject']
        # 提取邮件正文
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8')
                    break
        else:
            body = msg.get_payload(decode=True).decode('utf-8')
        
        print(f"找到草稿: {subject}")
        print(f"内容预览: {body[:100]}...")
        
        # 用 SMTP 发送
        print("\n通过 SMTP 发送...")
        success = send_email(subject, body, recipients)
        
        if success:
            # 删除草稿箱里的这封
            mail.store(latest_id_str, '+FLAGS', '\\Deleted')
            mail.expunge()
            print("已删除草稿箱中的邮件")
        
        mail.logout()
        return success
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

if __name__ == "__main__":
    mode = "draft"  # 默认保存草稿
    
    if len(sys.argv) >= 2 and sys.argv[1] == "send":
        mode = "send"
        args = sys.argv[2:]
    else:
        args = sys.argv[1:]
    
    # 如果没有参数
    if len(args) < 1:
        if mode == "send":
            # send 模式：发送草稿箱最新邮件
            subject = None
            content = None
        else:
            # 草稿模式：尝试读取今日日报
            report_path = get_report_path()
            
            if report_path and os.path.exists(report_path):
                with open(report_path, encoding="utf-8") as f:
                    content = f.read()
                
                today = subprocess.run(["date", "+%Y-%m-%d"], capture_output=True, text=True).stdout.strip()
                subject = f"日报 - {today}"
            else:
                print("用法:")
                print("  python3 enterprise_mail_draft.py send                          # 发送草稿箱")
                print("  python3 enterprise_mail_draft.py send '主题' '内容'             # 发送邮件")
                print("  python3 enterprise_mail_draft.py send -f 日报-2026-03-20.md     # 发送文件")
                print("  python3 enterprise_mail_draft.py '主题' '内容'                  # 保存草稿")
                print("  python3 enterprise_mail_draft.py -f 日报-2026-03-20.md          # 文件存草稿")
                sys.exit(1)
    else:
        # 检查是否是 -f 文件模式
        if args[0] == "-f" and len(args) >= 2:
            # 读取文件内容
            file_path = os.path.expanduser(args[1])
            if not os.path.exists(file_path):
                # 尝试在日报目录找
                config = load_config()
                if config:
                    report_dir = os.path.expanduser(config.get("report", {}).get("path", "~/.openclaw/workspace/record/日报/"))
                    file_path = os.path.join(report_dir, args[1])
            
            if os.path.exists(file_path):
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                # 从文件名提取标题
                filename = os.path.basename(file_path)
                subject = f"日报 - {filename.replace('日报-', '').replace('.md', '')}"
                print(f"读取文件: {file_path} ({len(content)} 字符)")
            else:
                print(f"❌ 文件不存在: {file_path}")
                sys.exit(1)
        elif args[0] == "-f":
            print("❌ -f 需要指定文件路径")
            sys.exit(1)
        else:
            subject = args[0]
            content = args[1] if len(args) > 1 else ""
    
    config = load_config()
    recipients = config.get("to", []) if config else []
    cc_recipients = config.get("cc", []) if config else []
    
    if mode == "send":
        # send 模式：
        # - 如果有内容（文件或参数），直接发送
        # - 否则从草稿箱发送
        if content:
            success = send_email(subject, content, recipients, cc_recipients)
        else:
            success = send_from_draft(subject if subject else None)
    else:
        success = save_draft(subject, content, recipients, cc_recipients)
    
    sys.exit(0 if success else 1)