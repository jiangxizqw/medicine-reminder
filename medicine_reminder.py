#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions / 青龙面板 — 药品库存提醒脚本
功能：每天自动检查药品剩余天数，如有药品少于7天，自动发送QQ邮件提醒

使用方法：
1. 将本脚本放入仓库根目录（GitHub Actions）或 /ql/scripts/（青龙）
2. 在仓库 Settings → Secrets 中添加：
   - YX_SENDER_EMAIL    : 发件人QQ邮箱
   - YX_SENDER_PASSWORD : QQ邮箱授权码
   - YX_RECEIVER_EMAIL  : 收件人邮箱
3. 买了新药后，修改下方 RECORD_DATE 为今天的日期，push 到仓库即可
"""

import os
import sys
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date

# ==================== 用户配置区域 ====================

# 提醒阈值：剩余天数小于此值时发送邮件
ALERT_THRESHOLD = 10

# 📅 药品记录日期（买了新药后，改成今天的日期，push 到仓库即可）
# 格式：YYYY-MM-DD
RECORD_DATE = "2026-06-12"

# 药品数据（请根据实际情况修改）
# 买了新药后，只需修改上面的 RECORD_DATE，无需改下面
MEDICINES = [
    {"name": "盐酸沙格雷酯片",     "initial_days": 78, "usage": "每日3次，一次1片", "note": ""},
    {"name": "阿司匹林肠溶片",     "initial_days": 80, "usage": "每日1次，一次1片", "note": "刺激胃部，导致咳嗽，备点胃药"},
    {"name": "阿托伐汀钙片",       "initial_days": 75, "usage": "每日1次，一次1片", "note": ""},
    {"name": "阿卡波糖片",         "initial_days": 70, "usage": "每日3次，一次1片", "note": "饭前吃"},
    {"name": "盐酸二甲双胍片",     "initial_days": 70, "usage": "每日1次，一次1片", "note": ""},
    {"name": "硝苯地平控释片",     "initial_days": 60, "usage": "每日1次，一次1片", "note": ""},
    {"name": "沙库巴曲缬沙坦钠片", "initial_days": 36, "usage": "每日1次，一次1片", "note": ""},
    {"name": "奥美拉唑肠溶胶囊",   "initial_days": 56, "usage": "每日1次，一次1片", "note": "胃药，饭前吃"},
   #{"name": "-------", "initial_days": 60, "usage": "每日1次，一次1片", "note": ""},
]

# 邮件配置（从环境变量读取）
SMTP_SERVER = os.environ.get("YX_SMTP_SERVER", "smtp.qq.com")
SMTP_PORT   = int(os.environ.get("YX_SMTP_PORT", "465"))
SENDER_EMAIL    = os.environ.get("YX_SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("YX_SENDER_PASSWORD", "")
RECEIVER_EMAIL  = os.environ.get("YX_RECEIVER_EMAIL", "")

# ==================== 核心逻辑 ====================

def log(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")
    sys.stdout.flush()

def calculate_remaining_days(initial_days, record_date):
    days_passed = (date.today() - record_date).days
    remaining = initial_days - days_passed
    return max(0, remaining)

def build_email_html(medicines_result, record_date):
    today_str = date.today().strftime("%Y年%m月%d日")
    record_str = record_date.strftime("%Y年%m月%d日")
    low_count = sum(1 for m in medicines_result if m["remaining"] < ALERT_THRESHOLD)
    total_count = len(medicines_result)

    rows_html = ""
    for med in medicines_result:
        remaining = med["remaining"]
        name = med["name"]
        usage = med["usage"]
        note = med["note"] if med["note"] else "—"

        if remaining < 7:
            status_color, status_bg, status_text = "#C62828", "#FFEBEE", "⚠️ 急需购买"
        elif remaining < 14:
            status_color, status_bg, status_text = "#E65100", "#FFF3E0", "⏰ 即将不足"
        else:
            status_color, status_bg, status_text = "#2E7D32", "#E8F5E9", "✅ 充足"

        rows_html += f"""
        <tr style="border-bottom:1px solid #E0E0E0;">
            <td style="padding:12px 16px;font-size:14px;color:#333;">{name}</td>
            <td style="padding:12px 16px;font-size:13px;color:#666;">{usage}</td>
            <td style="padding:12px 16px;font-size:14px;font-weight:bold;color:{status_color};text-align:center;">{remaining} 天</td>
            <td style="padding:12px 16px;font-size:12px;color:#666;">{note}</td>
            <td style="padding:12px 16px;text-align:center;">
                <span style="display:inline-block;padding:4px 10px;border-radius:4px;font-size:12px;font-weight:500;background:{status_bg};color:{status_color};">{status_text}</span>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="margin:0;padding:0;background:#F5F5F5;font-family:'Microsoft YaHei','PingFang SC',sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F5F5F5;">
            <tr><td align="center" style="padding:24px 16px;">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background:#FFFFFF;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);max-width:600px;width:100%;">
                    <tr><td style="background:#2D2D2D;padding:24px 32px;text-align:center;">
                        <div style="font-size:22px;font-weight:bold;color:#FFFFFF;">💊 药品库存提醒</div>
                        <div style="font-size:13px;color:#AAAAAA;margin-top:6px;">{today_str}</div>
                    </td></tr>
                    <tr><td style="padding:24px 32px 0;">
                        <div style="background:#FFF8E1;border-left:4px solid #FFB300;padding:16px 20px;border-radius:0 8px 8px 0;">
                            <div style="font-size:15px;font-weight:bold;color:#333;margin-bottom:4px;">📢 提醒摘要</div>
                            <div style="font-size:14px;color:#555;line-height:1.6;">
                                您共有 <strong style="color:#333;">{total_count}</strong> 种药品，
                                其中 <strong style="color:#C62828;">{low_count}</strong> 种药品剩余天数不足 <strong>{ALERT_THRESHOLD}</strong> 天，
                                请及时购买补充。
                            </div>
                            <div style="font-size:13px;color:#888;margin-top:8px;">
                                📅 药品记录日期：<strong>{record_str}</strong>
                            </div>
                        </div>
                    </td></tr>
                    <tr><td style="padding:20px 32px;">
                        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
                            <thead>
                                <tr style="background:#F8F8F8;border-bottom:2px solid #E0E0E0;">
                                    <th style="padding:12px 16px;font-size:13px;font-weight:600;color:#555;text-align:left;">药品名</th>
                                    <th style="padding:12px 16px;font-size:13px;font-weight:600;color:#555;text-align:left;">用法用量</th>
                                    <th style="padding:12px 16px;font-size:13px;font-weight:600;color:#555;text-align:center;">剩余天数</th>
                                    <th style="padding:12px 16px;font-size:13px;font-weight:600;color:#555;text-align:left;">注意事项</th>
                                    <th style="padding:12px 16px;font-size:13px;font-weight:600;color:#555;text-align:center;">状态</th>
                                </tr>
                            </thead>
                            <tbody>{rows_html}</tbody>
                        </table>
                    </td></tr>
                    <tr><td style="padding:0 32px 24px;">
                        <div style="border-top:1px solid #EEEEEE;padding-top:16px;font-size:12px;color:#999;line-height:1.8;">
                            <div>💡 本邮件由 GitHub Actions 自动发送，每天检查一次药品库存。</div>
                            <div>📅 买了新药后，修改脚本中的 RECORD_DATE 为今天的日期，push 到仓库即可。</div>
                            <div>🔧 当前记录日期：{record_str}</div>
                        </div>
                    </td></tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """
    return html

def send_email(subject, html_content):
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        log("❌ 邮件配置不完整，请检查环境变量 YX_SENDER_EMAIL / YX_SENDER_PASSWORD / YX_RECEIVER_EMAIL")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    msg.attach(MIMEText("药品库存提醒，请使用支持HTML的邮件客户端查看。", "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=30) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL.split(","), msg.as_string())
        log(f"✅ 邮件发送成功！收件人: {RECEIVER_EMAIL}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        log(f"❌ 认证错误，请检查邮箱和授权码。错误: {e}")
        return False
    except Exception as e:
        log(f"❌ 邮件发送失败：{e}")
        return False

def main():
    log("=" * 50)
    log("🚀 药品库存提醒脚本启动")
    log(f"📅 今天: {date.today().strftime('%Y-%m-%d')}")
    log(f"⚠️  提醒阈值: {ALERT_THRESHOLD} 天")

    try:
        record_date = datetime.strptime(RECORD_DATE, "%Y-%m-%d").date()
    except ValueError:
        log(f"❌ RECORD_DATE 格式错误: '{RECORD_DATE}'，应为 YYYY-MM-DD")
        return

    log(f"📦 药品记录日期: {record_date.strftime('%Y-%m-%d')}")
    log("=" * 50)

    medicines_result = []
    low_medicines = []

    for med in MEDICINES:
        remaining = calculate_remaining_days(med["initial_days"], record_date)
        med_copy = med.copy()
        med_copy["remaining"] = remaining
        medicines_result.append(med_copy)

        status = "⚠️ 不足" if remaining < ALERT_THRESHOLD else "✅ 正常"
        log(f"  {med['name']}: 剩余 {remaining} 天 [{status}]")

        if remaining < ALERT_THRESHOLD:
            low_medicines.append(med_copy)

    log("-" * 50)

    if low_medicines:
        log(f"🚨 发现 {len(low_medicines)} 种药品库存不足，准备发送邮件...")
        subject = f"【药品提醒】有{len(low_medicines)}种药品库存不足，请及时购买"
        html_content = build_email_html(medicines_result, record_date)

        success = send_email(subject, html_content)
        if success:
            log("🎉 任务完成，邮件已发送！")
        else:
            log("⚠️ 任务完成，但邮件发送失败。")
    else:
        log("✅ 所有药品库存充足，无需发送邮件。")

    log("=" * 50)

if __name__ == "__main__":
    main()
