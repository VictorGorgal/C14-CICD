"""
Script de notificação por e-mail para o pipeline CI/CD.
Todas as configurações sensíveis são lidas de variáveis de ambiente -
nenhum endereço ou credencial está fixado no código.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ── Leitura das variáveis de ambiente ──────────────────────────────────────
NOTIFY_EMAIL   = os.environ["NOTIFY_EMAIL"]      # GitHub Variable (vars.)
SMTP_USER      = os.environ["SMTP_USER"]          # GitHub Secret
SMTP_PASSWORD  = os.environ["SMTP_PASSWORD"]      # GitHub Secret
SMTP_HOST      = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.environ.get("SMTP_PORT", "587"))

STATUS         = os.environ.get("PIPELINE_STATUS", "unknown")
REPO_NAME      = os.environ.get("REPO_NAME", "repositório")
RUN_URL        = os.environ.get("RUN_URL", "#")
COMMIT_SHA     = os.environ.get("COMMIT_SHA", "N/A")[:7]
BRANCH         = os.environ.get("BRANCH", "N/A")
TIMESTAMP      = datetime.utcnow().strftime("%d/%m/%Y às %H:%M UTC")

# ── Montagem do conteúdo ───────────────────────────────────────────────────
STATUS_EMOJI  = "✅" if STATUS == "success" else "❌"
STATUS_LABEL  = "SUCESSO" if STATUS == "success" else "FALHA"
STATUS_COLOR  = "#22c55e" if STATUS == "success" else "#ef4444"

subject = f"{STATUS_EMOJI} [{REPO_NAME}] Pipeline CI/CD - {STATUS_LABEL}"

html_body = f"""
<html>
  <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 24px;">
    <div style="max-width: 600px; margin: auto; background: #fff;
                border-radius: 8px; overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,.1);">

      <div style="background: {STATUS_COLOR}; padding: 20px 24px;">
        <h2 style="color: #fff; margin: 0;">
          {STATUS_EMOJI} Pipeline CI/CD - {STATUS_LABEL}
        </h2>
      </div>

      <div style="padding: 24px;">
        <table style="width: 100%; border-collapse: collapse;">
          <tr>
            <td style="padding: 8px 0; color: #555; width: 140px;"><b>Repositório</b></td>
            <td style="padding: 8px 0;">{REPO_NAME}</td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #555;"><b>Branch</b></td>
            <td style="padding: 8px 0;"><code>{BRANCH}</code></td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #555;"><b>Commit</b></td>
            <td style="padding: 8px 0;"><code>{COMMIT_SHA}</code></td>
          </tr>
          <tr>
            <td style="padding: 8px 0; color: #555;"><b>Executado em</b></td>
            <td style="padding: 8px 0;">{TIMESTAMP}</td>
          </tr>
        </table>

        <div style="margin-top: 24px; text-align: center;">
          <a href="{RUN_URL}"
             style="background: #0f172a; color: #fff; padding: 12px 28px;
                    border-radius: 6px; text-decoration: none; font-weight: bold;">
            Ver execução no GitHub Actions
          </a>
        </div>
      </div>

    </div>
  </body>
</html>
"""

text_body = (
    f"Pipeline CI/CD - {STATUS_LABEL}\n\n"
    f"Repositório : {REPO_NAME}\n"
    f"Branch      : {BRANCH}\n"
    f"Commit      : {COMMIT_SHA}\n"
    f"Executado em: {TIMESTAMP}\n\n"
    f"Ver execução: {RUN_URL}\n"
)

# ── Envio ──────────────────────────────────────────────────────────────────
msg = MIMEMultipart("alternative")
msg["Subject"] = subject
msg["From"]    = SMTP_USER
msg["To"]      = NOTIFY_EMAIL
msg.attach(MIMEText(text_body, "plain"))
msg.attach(MIMEText(html_body, "html"))

with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
    server.ehlo()
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.sendmail(SMTP_USER, NOTIFY_EMAIL, msg.as_string())

print(f"[notify] E-mail enviado para {NOTIFY_EMAIL} - status: {STATUS_LABEL}")
