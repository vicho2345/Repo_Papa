import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_whatsapp_notification(jobs: list):
    """Envía email a Ronald con las ofertas nuevas."""
    sender   = os.getenv("MAIL_SENDER")
    password = os.getenv("MAIL_PASSWORD")
    recipient = os.getenv("MAIL_RECIPIENT")

    if not all([sender, password, recipient]):
        print("[Email] Credenciales no configuradas.")
        return

    count = len(jobs)
    s = "s" if count > 1 else ""
    frontend_url = os.getenv("FRONTEND_URL", "")

    # ── Cuerpo en HTML ──────────────────────────────
    rows = ""
    for job in jobs:
        rows += f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #eee;">
            <strong style="font-size:15px;color:#1a1a1a;">{job['title']}</strong><br>
            <span style="color:#555;">{job['company']}</span><br>
            <span style="font-size:12px;color:#888;">{job['portal']}</span>
            {f'<br><span style="font-size:12px;color:#2e7d32;">{job["relevance_reason"]}</span>' if job.get("relevance_reason") else ""}
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;text-align:center;white-space:nowrap;">
            <a href="{job['url']}" style="color:#1a73e8;font-size:13px;">Ver oferta</a>
          </td>
        </tr>"""

    ver_mas = f'<p style="margin-top:20px;"><a href="{frontend_url}" style="background:#1a73e8;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:bold;">Abrir dashboard y descargar CVs</a></p>' if frontend_url else ""

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <h2 style="color:#1a73e8;">Agente Empleo — {count} oferta{s} nueva{s}</h2>
      <table style="width:100%;border-collapse:collapse;">
        {rows}
      </table>
      {ver_mas}
      <p style="margin-top:24px;font-size:12px;color:#aaa;">
        Este correo fue enviado automáticamente por tu agente de búsqueda de empleo.
      </p>
    </div>"""

    # ── Armar y enviar ───────────────────────────────
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Agente Empleo: {count} oferta{s} relevante{s} encontrada{s}"
    msg["From"]    = sender
    msg["To"]      = recipient
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, recipient, msg.as_string())
        print(f"[Email] Enviado a {recipient} ({count} oferta{s})")
    except Exception as e:
        print(f"[Email] Error: {e}")