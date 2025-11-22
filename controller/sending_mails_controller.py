# controller/send_mail_controller.py
import threading
import smtplib
from datetime import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from random import random
from .check_premium import CheckPremium
import pandas as pd

dummy_password= "<PASSWORD>"
dummy_email = "<EMAIL>"
class SendMailController:
    def __init__(self, bus):
        self.bus = bus
        self._sending = False
        self._thread = None
        self.info = None
        premium = CheckPremium(dummy_email, dummy_password)
        self.is_premium = premium.check_premium()


        # Subscribe to bus events
        self.bus.subscribe("start_sending", self.start_sending)
        self.bus.subscribe("stop_sending", self.stop_sending)

        # Supported providers
        self.EMAIL_PROVIDERS = {
            "gmail.com": {"smtp": "smtp.gmail.com", "port": 465, "use_ssl": True},
            "yahoo.com": {"smtp": "smtp.mail.yahoo.com", "port": 465, "use_ssl": True},
            "rocketmail.com": {"smtp": "smtp.mail.yahoo.com", "port": 465, "use_ssl": True},
            "hotmail.com": {"smtp": "smtp.office365.com", "port": 587, "use_ssl": False},
            "outlook.com": {"smtp": "smtp.office365.com", "port": 587, "use_ssl": False},
        }

    # -----------------------------------------------------
    # Event handler for starting email sending
    # -----------------------------------------------------
    def start_sending(self, info):
        if self._sending:
            self.bus.publish("log", "⚠️ Already sending emails.")
            return

        self._sending = True
        self.info = info
        self.professor_list = self.info.get("professor_list")
        self.professor_list["main_mail_applyche"] = []
        self.professor_list["reminder_first_applyche"] =[]
        self.professor_list["reminder_second_applyche"]=[]
        self.professor_list["reminder_third_applyche"] = []
        self._thread = threading.Thread(target=self._send_loop, daemon=True)
        self._thread.start()
        self.bus.publish("log", "🚀 Started sending emails...")

    # -----------------------------------------------------
    # Main sending loop (runs in a thread)
    # -----------------------------------------------------
    def _send_loop(self):
        sender = self.info.get("email")
        password = self.info.get("password")
        subject = self.info.get("txt_main_subject")
        body = self.info.get("body")
        domain = sender.split("@")[-1].lower()

        provider = self.EMAIL_PROVIDERS.get(domain)
        if not provider:
            self.bus.publish("log", f"❌ Unsupported email domain: {domain}")
            self._sending = False
            return

        # Extract recipients
        if isinstance(self.professor_list, pd.DataFrame) and "email" in self.professor_list.columns:
            recipients = self.professor_list["email"].dropna().astype(str).tolist()
        else:
            self.bus.publish("log", "❌ professor_list is invalid or missing 'email' column.")
            self._sending = False
            return

        host = provider["smtp"]
        port = provider["port"]
        use_ssl = provider["use_ssl"]

        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(host, port)
            else:
                server = smtplib.SMTP(host, port)
                server.starttls()

            server.login(sender, password)
            self.bus.publish("log", f"✅ Connected to {domain} SMTP server.")

            for i, row in self.professor_list.iterrows():
                if not self._sending:
                    self.bus.publish("log", "🛑 Sending stopped by user.")
                    server.quit()
                    self._sending = False
                    return

                recipient = row.get("email")
                if not recipient:
                    continue

                custom_body = body.format_map(row.to_dict())

                msg = MIMEMultipart()
                msg["From"] = sender
                msg["To"] = recipient
                msg["Subject"] = subject
                msg.attach(MIMEText(custom_body, "plain"))

                try:
                    server.send_message(msg)
                    self.bus.publish("log", f"📤 Email {i + 1}/{len(recipients)} sent to {recipient}")
                except Exception as e:
                    self.bus.publish("log", f"❌ Failed to send to {recipient}: {e}")

                # Delay 4.5–5.5 minutes to avoid spam flagging
                delay = random.uniform(270, 330)
                self.bus.publish("log", f"⏳ Waiting {delay / 60:.1f} minutes before next email...")
                for _ in range(int(delay)):
                    if not self._sending:
                        self.bus.publish("log", "🛑 Sending stopped by user during delay.")
                        server.quit()
                        self._sending = False
                        return
                    time.sleep(1)

            server.quit()
            self.bus.publish("log", "✅ All emails sent successfully.")
        except Exception as e:
            self.bus.publish("log", f"❌ Error: {e}")
        finally:
            self._sending = False

    # -----------------------------------------------------
    # Event handler for stopping email sending
    # -----------------------------------------------------
    def stop_sending(self, _=None):
        if not self._sending:
            self.bus.publish("log", "⚠️ No sending process active.")
            return
        self._sending = False
        self.bus.publish("log", "🛑 Stop command received.")
