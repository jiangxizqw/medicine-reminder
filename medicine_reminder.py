#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青龙面板 — 药品库存提醒脚本
功能：每天自动检查药品剩余天数，如有药品少于7天，自动发送QQ邮件提醒
定时任务建议：0 9 * * * （每天早上9点运行）

使用方法：
1. 将本脚本放入青龙 /ql/scripts/ 目录
2. 在青龙面板「环境变量」中添加以下变量：
   - YX_SENDER_EMAIL    : 发件人QQ邮箱，如 123456@qq.com
   - YX_SENDER_PASSWORD : QQ邮箱授权码（不是登录密码！）
   - YX_RECEIVER_EMAIL  : 收件人邮箱（可填同一个QQ邮箱）
   - YX_RECORD_DATE     : 药品记录日期，格式 YYYY-MM-DD，默认今天
3. 在青龙面板「定时任务」中添加任务：task medicine_reminder.py
4. 买了新药后，只需修改 YX_RECORD_DATE 环境变量为今天的日期即可
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
ALERT_THRESHOLD = 7

# 药品数据（请根据实际情况修改）
# 所有药品共用同一个 record_date（从环境变量 YX_RECORD_DATE 读取）
# 买了新药后，只需在青龙环境变量中修改 YX_RECORD_DATE 为今天的日期
MEDICINES = [
    {"name": "盐酸沙格雷酯片",     "initial_days": 60, "usage": "每日3次，一次1片", "note": ""},
    {"name": "阿司匹林肠溶片",     "initial_days": 60, "usage": "每日1次，一次1片", "note": "刺激胃部，导致咳嗽，备点胃药"},
    {"name": "阿托伐汀钙片",       "initial_days": 60, "usage": "每日1次，一次1片", "note": ""},
    {"name": "阿卡波糖片",         "initial_days": 60, "usage": "每日3次，一次1片", "note": "饭前吃"},
    {"name": "盐酸二甲双胍片",     "initial_days": 60, "usage": "每日1次，一次1片", "note": ""},
    {"name": "硝苯地平控释片",     "initial_days": 60, "usage": "每日1次，一次1片", "note": ""},
    {"name": "沙库巴曲缬沙坦钠片", "initial_days": 60, "usage": "每日1次，一次1片", "note": ""},
]

# 邮件配置（优先从青龙环境变量读取）
SMTP_SERVER = os.environ.get("YX_SMTP_SERVER", "smtp.qq.com")
SMTP_PORT   = int(os.environ.get("YX_SMTP_PORT", "465"))
SENDER_EMAIL    = os.environ.get("YX_SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("YX_SENDER_PASSWORD", "")
RECEIVER_EMAIL  = os.environ.get("YX_RECEIVER_EMAIL", "")

# 药品记录日期（所有药品统一使用此日期）
# 格式：YYYY-MM-DD，默认今天
RECORD_DATE_STR = os.environ.get("YX_RECORD_DATE", date.today().strftime("%Y-%m-%d"))

# ==================== 核心逻辑 ====================

def log(msg):
    """打印日志（带时间戳）"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")
    sys.stdout.flush()

def calculate_remaining_days(initial_days, record_date):
    """计算药品当前剩余天数"""
    days_passed = (date.today() - record_date).days
    remaining = initial_days - days_passed
    return max(0, remaining)

def build_email_html(medicines_result, record_date):
    """构建邮件HTML正文"""
    today_str = date.today().strftime("%Y年%m月%d日")
    record_str = record_date.strftime("%Y年%m月%d日")

    # 统计
    low_count = sum(1 for m in medicines_result if m["remaining"] < ALERT_THRESHOLD)
    total_count = len(medicines_result)

    rows_html = ""
    for med in medicines_result:
        remaining = med["remaining"]
        name = med["name"]
        usage = med["usage"]
        note = med["note"] if med["note"] else "—"

        if remaining < 7:
            status_color = "#C62828"
            status_bg = "#FFEBEE"
            status_text = "⚠️ 急需购买"
        elif remaining < 14:
            status_color = "#E65100"
            status_bg = "#FFF3E0"
            status_text = "⏰ 即将不足"
        else:
            status_color = "#2E7D32"
            status_bg = "#E8F5E9"
            status_text = "✅ 充足"

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
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0;padding:0;background:#F5F5F5;font-family:'Microsoft YaHei','PingFang SC',sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F5F5F5;">
            <tr>
                <td align="center" style="padding:24px 16px;">
                    <table width="600" cellpadding="0" cellspacing="0" border="0" style="background:#FFFFFF;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);max-width:600px;width:100%;">
                        <tr>
                            <td style="background:#2D2D2D;padding:24px 32px;text-align:center;">
                                <div style="font-size:22px;font-weight:bold;color:#FFFFFF;">💊 药品库存提醒</div>
                                <div style="font-size:13px;color:#AAAAAA;margin-top:6px;">{today_str}</div>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:24px 32px 0;">
                                <div style="background:#FFF8E1;border-left:4px solid #FFB300;padding:16px 20px;border-radius:0 8px 8px 0;">
                                    <div style="font-size:15px;font-weight:bold;color:#333;margin-bottom:4px;">📢 提醒摘要</div>
                                    <div style="font-size:14px;color:#555;line-height:1.6;">
                                        您共有 <strong style="color:#333;">{total_count}</strong> 种药品，
                                        其中 <strong style="color:#C62828;">{low_count}</strong> 种药品剩余天数不足 <strong>{ALERT_THRESHOLD}</strong> 天，
                                        请及时购买补充。
                                    </div>
                                    <div style="font-size:13px;color:#888;margin-top:8px;">
                                        📅 药品记录日期：<strong>{record_str}</strong>（所有药品统一以此日期计算）
                                    </div>
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:20px 32px;">
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
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:0 32px 24px;">
                                <div style="border-top:1px solid #EEEEEE;padding-top:16px;font-size:12px;color:#999;line-height:1.8;">
                                    <div>💡 本邮件由青龙面板自动发送，每天检查一次药品库存。</div>
                                    <div>📅 买了新药后，只需在青龙环境变量中修改 YX_RECORD_DATE 为今天的日期即可。</div>
                                    <div>🔧 当前记录日期：{record_str}，如需校准请修改环境变量 YX_RECORD_DATE。</div>
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html

def send_email(subject, html_content):
    """发送邮件"""
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        log("❌ 邮件配置不完整，请检查环境变量 YX_SENDER_EMAIL / YX_SENDER_PASSWORD / YX_RECEIVER_EMAIL")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    text_content = "药品库存提醒，请使用支持HTML的邮件客户端查看。"
    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=30) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL.split(","), msg.as_string())
        log(f"✅ 邮件发送成功！收件人: {RECEIVER_EMAIL}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        log(f"❌ 邮件发送失败：认证错误，请检查邮箱和授权码是否正确。错误: {e}")
        return False
    except Exception as e:
        log(f"❌ 邮件发送失败：{e}")
        return False

def main():
    log("=" * 50)
    log("🚀 药品库存提醒脚本启动")
    log(f"📅 今天: {date.today().strftime('%Y-%m-%d')}")
    log(f"⚠️  提醒阈值: {ALERT_THRESHOLD} 天")

    # 解析记录日期
    try:
        record_date = datetime.strptime(RECORD_DATE_STR, "%Y-%m-%d").date()
    except ValueError:
        log(f"❌ 环境变量 YX_RECORD_DATE 格式错误: '{RECORD_DATE_STR}'，应为 YYYY-MM-DD 格式")
        log(f"💡 已自动使用今天日期: {date.today().strftime('%Y-%m-%d')}")
        record_date = date.today()

    log(f"📦 药品记录日期: {record_date.strftime('%Y-%m-%d')}（所有药品统一）")
    log("=" * 50)

    # 计算所有药品剩余天数
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

    # 判断是否需要发送邮件
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
