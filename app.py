#!/usr/bin/env python3
"""
Helseboliger.no — Flask backend
"""
import json, os, smtplib, uuid
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "investors.json")
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

EMAIL_FROM = "heidimybot@gmail.com"
EMAIL_PASS = "rdfsfbvwzbjahaia"
EMAIL_TO   = "david@myrann.com"

def load_investors():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return []

def save_investors(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def send_notification(lead):
    try:
        body = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px;">
        <h2 style="color:#C9A84C;">🏢 Ny investorhenvendelse — Helseboliger</h2>
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:10px;border-bottom:1px solid #eee;color:#666;width:140px;">Navn</td><td style="padding:10px;border-bottom:1px solid #eee;font-weight:600;">{lead['name']}</td></tr>
          <tr><td style="padding:10px;border-bottom:1px solid #eee;color:#666;">Selskap</td><td style="padding:10px;border-bottom:1px solid #eee;">{lead.get('company','–')}</td></tr>
          <tr><td style="padding:10px;border-bottom:1px solid #eee;color:#666;">E-post</td><td style="padding:10px;border-bottom:1px solid #eee;"><a href="mailto:{lead['email']}">{lead['email']}</a></td></tr>
          <tr><td style="padding:10px;border-bottom:1px solid #eee;color:#666;">Telefon</td><td style="padding:10px;border-bottom:1px solid #eee;">{lead.get('phone','–')}</td></tr>
          <tr><td style="padding:10px;border-bottom:1px solid #eee;color:#666;">Kapasitet</td><td style="padding:10px;border-bottom:1px solid #eee;">{lead.get('size','–')}</td></tr>
          <tr><td style="padding:10px;color:#666;vertical-align:top;">Melding</td><td style="padding:10px;">{lead.get('message','–')}</td></tr>
        </table>
        <p style="margin-top:20px;color:#999;font-size:12px;">Mottatt {lead['timestamp']}</p>
        </div>"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🏢 Ny investorhenvendelse fra {lead['name']} — Helseboliger"
        msg["From"]    = f"Helseboliger <{EMAIL_FROM}>"
        msg["To"]      = EMAIL_TO
        msg.attach(MIMEText(body, "html", "utf-8"))
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.ehlo(); s.starttls()
            s.login(EMAIL_FROM, EMAIL_PASS)
            s.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    except Exception as e:
        print(f"E-post feil: {e}")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/helseforetak", methods=["POST"])
def helseforetak():
    data = request.get_json(force=True, silent=True) or {}
    name  = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    if not name or not email or "@" not in email:
        return jsonify({"error": "Navn og gyldig e-post er påkrevd"}), 400
    lead = {
        "id":        str(uuid.uuid4())[:8],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type":      "helseforetak",
        "name":      name,
        "org":       data.get("org", ""),
        "email":     email,
        "phone":     data.get("phone", ""),
        "behov":     data.get("behov", ""),
        "message":   data.get("message", ""),
    }
    investors = load_investors()
    investors.append(lead)
    save_investors(investors)
    try:
        body = f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px;">
        <h2 style="color:#C9A84C;">🏥 Ny henvendelse fra helseforetak — Helseboliger</h2>
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:10px;border-bottom:1px solid #eee;color:#666;width:140px;">Navn</td><td style="padding:10px;border-bottom:1px solid #eee;font-weight:600;">{lead['name']}</td></tr>
          <tr><td style="padding:10px;border-bottom:1px solid #eee;color:#666;">Organisasjon</td><td style="padding:10px;border-bottom:1px solid #eee;">{lead.get('org','–')}</td></tr>
          <tr><td style="padding:10px;border-bottom:1px solid #eee;color:#666;">E-post</td><td style="padding:10px;border-bottom:1px solid #eee;">{lead['email']}</td></tr>
          <tr><td style="padding:10px;border-bottom:1px solid #eee;color:#666;">Telefon</td><td style="padding:10px;border-bottom:1px solid #eee;">{lead.get('phone','–')}</td></tr>
          <tr><td style="padding:10px;border-bottom:1px solid #eee;color:#666;">Behov</td><td style="padding:10px;border-bottom:1px solid #eee;">{lead.get('behov','–')}</td></tr>
          <tr><td style="padding:10px;color:#666;vertical-align:top;">Melding</td><td style="padding:10px;">{lead.get('message','–')}</td></tr>
        </table></div>"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🏥 Ny helseforetak-henvendelse fra {lead['name']} — Helseboliger"
        msg["From"]    = f"Helseboliger <{EMAIL_FROM}>"
        msg["To"]      = EMAIL_TO
        msg.attach(MIMEText(body, "html", "utf-8"))
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.ehlo(); s.starttls()
            s.login(EMAIL_FROM, EMAIL_PASS)
            s.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    except Exception as e:
        print(f"E-post feil: {e}")
    return jsonify({"ok": True})

@app.route("/api/investor", methods=["POST"])
def investor():
    data = request.get_json(force=True, silent=True) or {}
    name  = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    if not name or not email or "@" not in email:
        return jsonify({"error": "Navn og gyldig e-post er påkrevd"}), 400
    lead = {
        "id":        str(uuid.uuid4())[:8],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "name":      name,
        "company":   data.get("company", ""),
        "email":     email,
        "phone":     data.get("phone", ""),
        "size":      data.get("size", ""),
        "message":   data.get("message", ""),
    }
    investors = load_investors()
    investors.append(lead)
    save_investors(investors)
    send_notification(lead)
    return jsonify({"ok": True})

@app.route("/api/investors")
def list_investors():
    return jsonify(load_investors())

if __name__ == "__main__":
    app.run(debug=True, port=5001)
