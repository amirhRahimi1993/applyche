"""
Email Sending Controller
Handles sending emails based on professor list with timezone, working day, and reminder logic
"""
import pandas as pd
import smtplib
import time
import threading
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, List, Tuple
import pytz
import requests
from email_template_putter import email_modifyer
from api_client import ApplyCheAPIClient


class EmailSender:
    """Main class for sending emails based on professor list"""
    
    EMAIL_PROVIDERS = {
        "gmail.com": {"smtp": "smtp.gmail.com", "port": 465, "use_ssl": True},
        "yahoo.com": {"smtp": "smtp.mail.yahoo.com", "port": 465, "use_ssl": True},
        "rocketmail.com": {"smtp": "smtp.mail.yahoo.com", "port": 465, "use_ssl": True},
        "hotmail.com": {"smtp": "smtp.office365.com", "port": 587, "use_ssl": False},
        "outlook.com": {"smtp": "smtp.office365.com", "port": 587, "use_ssl": False},
    }
    
    # Timezone mapping for countries/cities
    TIMEZONE_MAP = {
        "iran/tehran": "Asia/Tehran",
        "usa/new york": "America/New_York",
        "usa/chicago": "America/Chicago",
        "usa/los angeles": "America/Los_Angeles",
        "uk/london": "Europe/London",
        "uk/oxford": "Europe/London",
        "uk/cambridge": "Europe/London",
        "canada/toronto": "America/Toronto",
        "canada/vancouver": "America/Vancouver",
        "germany/berlin": "Europe/Berlin",
        "germany/munich": "Europe/Berlin",
        "france/paris": "Europe/Paris",
        "italy/rome": "Europe/Rome",
        "netherlands/amsterdam": "Europe/Amsterdam",
        "sweden/stockholm": "Europe/Stockholm",
        "switzerland/zurich": "Europe/Zurich",
        "switzerland/lausanne": "Europe/Zurich",
        "australia/sydney": "Australia/Sydney",
        "japan/tokyo": "Asia/Tokyo",
        "china/beijing": "Asia/Shanghai",
        "south korea/seoul": "Asia/Seoul",
        "singapore/singapore": "Asia/Singapore",
        "hong kong/hong kong": "Asia/Hong_Kong",
    }
    
    def __init__(
        self,
        email: str,
        app_password: str,
        professor_list_path: str,
        api_client: Optional[ApplyCheAPIClient] = None,
        user_email: Optional[str] = None
    ):
        """
        Initialize EmailSender
        
        Args:
            email: Sender email address
            app_password: App password for email
            professor_list_path: Path to professor list CSV/Excel file
            api_client: API client for database operations
            user_email: User email for API operations
        """
        self.email = email
        self.app_password = app_password
        self.professor_list_path = professor_list_path
        self.api_client = api_client
        self.user_email = user_email
        self._sending = False
        self._thread = None
        
        # Load professor list
        self.df = self._load_professor_list()
        
    def _load_professor_list(self) -> pd.DataFrame:
        """Load professor list from CSV/Excel"""
        if self.professor_list_path.endswith('.xlsx'):
            df = pd.read_excel(self.professor_list_path, header=0, engine='openpyxl')
        elif self.professor_list_path.endswith('.csv'):
            df = pd.read_csv(self.professor_list_path, header=0)
        else:
            raise ValueError("Unsupported file format. Use .csv or .xlsx")
        return df
    
    def _save_professor_list(self):
        """Save professor list back to file"""
        if self.professor_list_path.endswith('.xlsx'):
            self.df.to_excel(self.professor_list_path, index=False, engine='openpyxl', header=True)
        elif self.professor_list_path.endswith('.csv'):
            self.df.to_csv(self.professor_list_path, index=False, header=True, encoding='utf-8')
    
    def _get_timezone(self, country_city: str) -> Optional[pytz.timezone]:
        """Get timezone from country/city string"""
        if not country_city or pd.isna(country_city):
            return None
        
        country_city_lower = str(country_city).lower().strip()
        
        # Direct lookup
        if country_city_lower in self.TIMEZONE_MAP:
            return pytz.timezone(self.TIMEZONE_MAP[country_city_lower])
        
        # Try to extract country and find default timezone
        if '/' in country_city_lower:
            country = country_city_lower.split('/')[0].strip()
            # Default timezones by country (simplified)
            country_defaults = {
                "iran": "Asia/Tehran",
                "usa": "America/New_York",
                "uk": "Europe/London",
                "canada": "America/Toronto",
                "germany": "Europe/Berlin",
                "france": "Europe/Paris",
                "italy": "Europe/Rome",
                "netherlands": "Europe/Amsterdam",
                "sweden": "Europe/Stockholm",
                "switzerland": "Europe/Zurich",
                "australia": "Australia/Sydney",
                "japan": "Asia/Tokyo",
                "china": "Asia/Shanghai",
                "south korea": "Asia/Seoul",
                "singapore": "Asia/Singapore",
                "hong kong": "Asia/Hong_Kong",
            }
            if country in country_defaults:
                return pytz.timezone(country_defaults[country])
        
        return None
    
    def _convert_to_local_time(self, dt: datetime, country_city: str) -> datetime:
        """Convert datetime to local timezone based on country/city"""
        tz = self._get_timezone(country_city)
        if tz:
            # Assume dt is in UTC, convert to local timezone
            if dt.tzinfo is None:
                dt = pytz.UTC.localize(dt)
            return dt.astimezone(tz)
        return dt
    
    def _is_working_day(self, date: datetime, country: str) -> bool:
        """
        Check if date is a working day using Negar.Date API
        
        Args:
            date: Date to check
            country: Country name (e.g., "iran", "usa")
            
        Returns:
            True if working day, False if holiday
            
        Note:
            You need to adjust the API endpoint based on actual Negar.Date API documentation.
            Common endpoints might be:
            - https://api.negar.date/holiday
            - https://api.negar.date/check
            - Or other endpoints as per Negar.Date API documentation
        """
        try:
            # Negar.Date API endpoint - ADJUST THIS BASED ON ACTUAL API DOCUMENTATION
            api_url = "https://api.negar.date/holiday"  # Replace with actual endpoint
            params = {
                "date": date.strftime("%Y-%m-%d"),
                "country": country.lower()
            }
            response = requests.get(api_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Adjust based on actual API response structure
                # Common response formats:
                # - {"is_holiday": true/false}
                # - {"holiday": true/false}
                # - {"is_working_day": true/false}
                is_holiday = data.get("is_holiday", False) or data.get("holiday", False)
                return not is_holiday
        except Exception as e:
            print(f"Error checking working day via Negar.Date API: {e}")
            print("Defaulting to working day (True)")
            # Default to True if API fails (assume it's a working day)
            return True
        
        return True
    
    def _is_within_time_window(self, current_time: datetime, start_time: str, end_time: str, 
                               country_city: Optional[str] = None) -> bool:
        """Check if current time is within start_time and end_time window"""
        try:
            # Parse time strings (format: "HH:MM")
            start_hour, start_min = map(int, start_time.split(":"))
            end_hour, end_min = map(int, end_time.split(":"))
            
            # Convert to local timezone if needed
            if country_city:
                current_time = self._convert_to_local_time(current_time, country_city)
            
            current_hour = current_time.hour
            current_min = current_time.minute
            current_minutes = current_hour * 60 + current_min
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min
            
            return start_minutes <= current_minutes <= end_minutes
        except Exception:
            return True  # Default to True if parsing fails
    
    def _check_replies(self):
        """
        Check for email replies and update answered/answer_text columns
        
        Note:
            This method needs to be implemented based on your email provider:
            - For Gmail: Use Gmail API (google-api-python-client)
            - For other providers: Use IMAP protocol
            
            Implementation steps:
            1. Connect to email account
            2. Search for replies to messages with In-Reply-To header matching message_id
            3. Extract reply text
            4. Update answered column to True
            5. Update answer_text column with reply content
        """
        # TODO: Implement actual reply checking
        # Example for Gmail API (requires google-api-python-client):
        # from googleapiclient.discovery import build
        # service = build('gmail', 'v1', credentials=creds)
        # messages = service.users().messages().list(userId='me', q=f'inreplyto:{message_id}').execute()
        # if messages.get('messages'):
        #     # Process reply and update DataFrame
        
        # Example for IMAP:
        # import imaplib
        # mail = imaplib.IMAP4_SSL('imap.gmail.com')
        # mail.login(self.email, self.app_password)
        # mail.select('inbox')
        # status, messages = mail.search(None, f'HEADER "In-Reply-To" "{message_id}"')
        # if messages[0]:
        #     # Process reply and update DataFrame
        
        # Placeholder - implement based on your email provider
        for idx, row in self.df.iterrows():
            message_id = row.get('message_id')
            if pd.notna(message_id) and message_id:
                # TODO: Implement actual reply checking
                # When implementing:
                # 1. Check for replies to this message_id
                # 2. Extract reply text
                # 3. Update answered column in DataFrame to True
                # 4. Update answer_text column in DataFrame with reply content
                # 5. Update answer field in send_log table using:
                #    self.api_client.update_send_log_answer(log_id, answer_text, self.user_email)
                #    (You'll need to find the log_id by message_id)
                # For now, this is a placeholder
                pass
    
    def _get_email_template(self, template_type: int = 0) -> Optional[Dict]:
        """Get email template from database via API"""
        if not self.api_client or not self.user_email:
            return None
        
        try:
            template = self.api_client.get_template_by_type(self.user_email, template_type)
            return template
        except Exception as e:
            print(f"Error getting email template: {e}")
            return None
    
    def _get_template_id(self, template_type: int = 0) -> Optional[int]:
        """Get template ID for a given template type"""
        template = self._get_email_template(template_type)
        if template:
            return template.get("id")
        return None
    
    def _substitute_template(self, template_body: str, subject: Optional[str], row_idx: int) -> Tuple[str, Optional[str], List[str]]:
        """
        Substitute template placeholders with professor list values
        
        Returns:
            Tuple of (substituted_body, substituted_subject, missing_columns)
        """
        modifier = email_modifyer(subject=subject, template_body=template_body, template_type=0)
        modifier.set_professor_list_df(self.df)
        
        missing_columns = []
        try:
            substituted_body = modifier.get_substituted_template(row_idx)
            substituted_subject = modifier.get_substituted_subject(row_idx) if subject else None
            
            # Check for None or empty values in substituted text
            # Extract placeholders and check their values
            import re
            placeholders = re.findall(r'\{([^}]+)\}', template_body)
            if subject:
                placeholders.extend(re.findall(r'\{([^}]+)\}', subject))
            
            for placeholder in placeholders:
                # Find corresponding column
                col_name = None
                for col in self.df.columns:
                    if col.lower().strip() == placeholder.lower().strip():
                        col_name = col
                        break
                
                if col_name:
                    value = self.df.iloc[row_idx][col_name]
                    if pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
                        missing_columns.append(col_name)
            
            return substituted_body, substituted_subject, missing_columns
        except Exception as e:
            print(f"Error substituting template: {e}")
            return template_body, subject, [str(e)]
    
    def _send_email(self, to_email: str, subject: str, body: str, 
                   in_reply_to: Optional[str] = None, references: Optional[str] = None) -> Optional[str]:
        """
        Send email via SMTP
        
        Returns:
            message_id if successful, None otherwise
        """
        try:
            # Extract domain from email
            domain = to_email.split('@')[1] if '@' in to_email else "gmail.com"
            sender_domain = self.email.split('@')[1] if '@' in self.email else "gmail.com"
            
            # Get SMTP settings
            provider = self.EMAIL_PROVIDERS.get(sender_domain, self.EMAIL_PROVIDERS["gmail.com"])
            host = provider["smtp"]
            port = provider["port"]
            use_ssl = provider["use_ssl"]
            
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = to_email
            msg["Subject"] = subject
            if in_reply_to:
                msg["In-Reply-To"] = in_reply_to
            if references:
                msg["References"] = references
            
            msg.attach(MIMEText(body, "plain"))
            
            # Connect and send
            if use_ssl:
                server = smtplib.SMTP_SSL(host, port)
            else:
                server = smtplib.SMTP(host, port)
                server.starttls()
            
            server.login(self.email, self.app_password)
            server.send_message(msg)
            server.quit()
            
            # Generate message_id (simplified - in production, use actual message-id from server)
            message_id = f"<{int(time.time())}@{sender_domain}>"
            return message_id
            
        except Exception as e:
            print(f"Error sending email to {to_email}: {e}")
            return None
    
    def start_sending(
        self,
        txt_number_of_main_mails: int,
        txt_start_time: str,
        txt_end_time: str,
        is_professor_local_time: bool,
        is_sending_working_day_only: bool,
        txt_period_between_reminders: int,
        txt_number_of_first_reminder: int = 0,
        txt_number_of_second_reminder: int = 0,
        txt_number_of_third_reminder: int = 0,
        callback=None
    ):
        """
        Start sending emails in a separate thread
        
        Args:
            txt_number_of_main_mails: Number of main mails to send
            txt_start_time: Start time (HH:MM format)
            txt_end_time: End time (HH:MM format)
            is_professor_local_time: Use professor local time
            is_sending_working_day_only: Only send on working days
            txt_period_between_reminders: Days between reminders
            txt_number_of_first_reminder: Number of first reminders
            txt_number_of_second_reminder: Number of second reminders
            txt_number_of_third_reminder: Number of third reminders
            callback: Optional callback function for log messages
        """
        if self._sending:
            if callback:
                callback("⚠️ Already sending emails.")
            return
        
        self._sending = True
        self._thread = threading.Thread(
            target=self._send_loop,
            args=(
                txt_number_of_main_mails,
                txt_start_time,
                txt_end_time,
                is_professor_local_time,
                is_sending_working_day_only,
                txt_period_between_reminders,
                txt_number_of_first_reminder,
                txt_number_of_second_reminder,
                txt_number_of_third_reminder,
                callback
            ),
            daemon=True
        )
        self._thread.start()
    
    def stop_sending(self):
        """Stop sending emails"""
        self._sending = False
    
    def _send_loop(
        self,
        txt_number_of_main_mails: int,
        txt_start_time: str,
        txt_end_time: str,
        is_professor_local_time: bool,
        is_sending_working_day_only: bool,
        txt_period_between_reminders: int,
        txt_number_of_first_reminder: int,
        txt_number_of_second_reminder: int,
        txt_number_of_third_reminder: int,
        callback
    ):
        """Main sending loop"""
        try:
            # Get email template
            template = self._get_email_template(template_type=0)
            if not template:
                if callback:
                    callback("❌ Error: Email template not found")
                self._sending = False
                return
            
            template_body = template.get("template_body", "")
            template_subject = template.get("subject", "")
            
            # Check for replies first
            self._check_replies()
            
            # Send main mails
            main_mails_sent = 0
            while main_mails_sent < txt_number_of_main_mails and self._sending:
                # Find professors who need main mail
                for idx, row in self.df.iterrows():
                    if not self._sending:
                        break
                    
                    # Check if answered
                    answered = row.get('answered', '')
                    if pd.notna(answered) and str(answered).lower().strip() == 'true':
                        continue
                    
                    # Check if main_mail_time is empty
                    main_mail_time = row.get('main_mail_time')
                    if pd.notna(main_mail_time) and main_mail_time:
                        continue
                    
                    # Get professor email
                    professor_email_col = None
                    for col in self.df.columns:
                        if col.lower().strip() == 'professor_email':
                            professor_email_col = col
                            break
                    
                    if not professor_email_col:
                        continue
                    
                    professor_email = row[professor_email_col]
                    if pd.isna(professor_email) or not professor_email:
                        continue
                    
                    # Check time window
                    current_time = datetime.now()
                    country_city = row.get('country_city') if is_professor_local_time else None
                    
                    if not self._is_within_time_window(current_time, txt_start_time, txt_end_time, country_city):
                        continue
                    
                    # Check working day
                    if is_sending_working_day_only and country_city:
                        country = str(country_city).split('/')[0].strip() if '/' in str(country_city) else None
                        if country and not self._is_working_day(current_time, country):
                            continue
                    
                    # Substitute template
                    substituted_body, substituted_subject, missing_columns = self._substitute_template(
                        template_body, template_subject, idx
                    )
                    
                    # Check for missing values
                    if missing_columns:
                        error_msg = f"Email not sent because {', '.join(missing_columns)} are none or empty"
                        if 'applyche_description' in self.df.columns:
                            self.df.at[idx, 'applyche_description'] = error_msg
                        if callback:
                            callback(f"⚠️ Skipped {professor_email}: {error_msg}")
                        self._save_professor_list()
                        continue
                    
                    # Send email
                    if callback:
                        callback(f"📤 Attempting to send main mail to {professor_email}...")
                    
                    message_id = self._send_email(
                        to_email=str(professor_email),
                        subject=substituted_subject or "No Subject",
                        body=substituted_body
                    )
                    
                    if message_id:
                        # Update professor list
                        self.df.at[idx, 'message_id'] = message_id
                        self.df.at[idx, 'main_mail_time'] = current_time.strftime("%Y-%m-%d %H:%M:%S")
                        self._save_professor_list()
                        
                        # Save to database via API
                        if self.api_client and self.user_email:
                            try:
                                self.api_client.upsert_professor_list(
                                    user_email=self.user_email,
                                    file_path=self.professor_list_path
                                )
                                
                                # Save to send_log table
                                template_id = self._get_template_id(template_type=0)
                                self.api_client.create_send_log(
                                    user_email=self.user_email,
                                    sent_to=str(professor_email),
                                    send_type=0,  # 0 = main mail
                                    subject=substituted_subject or "No Subject",
                                    body=substituted_body,
                                    template_id=template_id,
                                    delivery_status=1,  # 1 = sent successfully
                                    message_id=message_id,
                                    answer=None  # Will be updated when reply is received
                                )
                            except Exception as e:
                                print(f"Error saving to database: {e}")
                        
                        main_mails_sent += 1
                        if callback:
                            callback(f"✅ Sending successful: Main mail {main_mails_sent}/{txt_number_of_main_mails} sent to {professor_email}")
                    else:
                        if callback:
                            callback(f"❌ Sending failed: Failed to send main mail to {professor_email}")
                
                # Wait 5 minutes before next batch
                if main_mails_sent < txt_number_of_main_mails:
                    if callback:
                        callback("⏳ Waiting 5 minutes before next batch to prevent spam detection...")
                    for remaining in range(300, 0, -1):  # 5 minutes = 300 seconds
                        if not self._sending:
                            break
                        minutes = remaining // 60
                        secs = remaining % 60
                        if callback and remaining % 10 == 0:  # Update every 10 seconds
                            callback(f"⏳ Preventing detecting spam, you should wait {minutes:02d}:{secs:02d}")
                        time.sleep(1)
            
            # Send first reminders
            if txt_number_of_first_reminder > 0:
                self._send_reminders(
                    reminder_type=1,
                    number_to_send=txt_number_of_first_reminder,
                    txt_start_time=txt_start_time,
                    txt_end_time=txt_end_time,
                    is_professor_local_time=is_professor_local_time,
                    is_sending_working_day_only=is_sending_working_day_only,
                    period_days=txt_period_between_reminders,
                    previous_time_col='main_mail_time',
                    current_time_col='reminder_one_time',
                    callback=callback
                )
            
            # Send second reminders
            if txt_number_of_second_reminder > 0:
                self._send_reminders(
                    reminder_type=2,
                    number_to_send=txt_number_of_second_reminder,
                    txt_start_time=txt_start_time,
                    txt_end_time=txt_end_time,
                    is_professor_local_time=is_professor_local_time,
                    is_sending_working_day_only=is_sending_working_day_only,
                    period_days=txt_period_between_reminders,
                    previous_time_col='reminder_one_time',
                    current_time_col='reminder_second_time',
                    callback=callback
                )
            
            # Send third reminders
            if txt_number_of_third_reminder > 0:
                self._send_reminders(
                    reminder_type=3,
                    number_to_send=txt_number_of_third_reminder,
                    txt_start_time=txt_start_time,
                    txt_end_time=txt_end_time,
                    is_professor_local_time=is_professor_local_time,
                    is_sending_working_day_only=is_sending_working_day_only,
                    period_days=txt_period_between_reminders,
                    previous_time_col='reminder_second_time',
                    current_time_col='reminder_thrid_time',
                    callback=callback
                )
            
            if callback:
                callback("✅ Email sending completed")
            
        except Exception as e:
            if callback:
                callback(f"❌ Error in sending loop: {e}")
        finally:
            self._sending = False
    
    def _send_reminders(
        self,
        reminder_type: int,
        number_to_send: int,
        txt_start_time: str,
        txt_end_time: str,
        is_professor_local_time: bool,
        is_sending_working_day_only: bool,
        period_days: int,
        previous_time_col: str,
        current_time_col: str,
        callback
    ):
        """Send reminders of a specific type"""
        try:
            # Get reminder template
            template = self._get_email_template(template_type=reminder_type)
            if not template:
                if callback:
                    callback(f"⚠️ Reminder {reminder_type} template not found, skipping")
                return
            
            template_body = template.get("template_body", "")
            template_subject = template.get("subject", "")
            
            reminders_sent = 0
            while reminders_sent < number_to_send and self._sending:
                # Find professors who need this reminder
                for idx, row in self.df.iterrows():
                    if not self._sending or reminders_sent >= number_to_send:
                        break
                    
                    # Check if answered
                    answered = row.get('answered', '')
                    if pd.notna(answered) and str(answered).lower().strip() == 'true':
                        continue
                    
                    # Check if current reminder time is empty
                    current_reminder_time = row.get(current_time_col)
                    if pd.notna(current_reminder_time) and current_reminder_time:
                        continue
                    
                    # Check if previous time exists
                    previous_time = row.get(previous_time_col)
                    if pd.isna(previous_time) or not previous_time:
                        continue
                    
                    # Check if period has passed
                    try:
                        if isinstance(previous_time, str):
                            prev_dt = datetime.strptime(str(previous_time), "%Y-%m-%d %H:%M:%S")
                        else:
                            prev_dt = previous_time
                        
                        current_dt = datetime.now()
                        days_passed = (current_dt - prev_dt).days
                        
                        if days_passed < period_days:
                            continue
                    except Exception:
                        continue
                    
                    # Get professor email
                    professor_email_col = None
                    for col in self.df.columns:
                        if col.lower().strip() == 'professor_email':
                            professor_email_col = col
                            break
                    
                    if not professor_email_col:
                        continue
                    
                    professor_email = row[professor_email_col]
                    if pd.isna(professor_email) or not professor_email:
                        continue
                    
                    # Check time window
                    current_time = datetime.now()
                    country_city = row.get('country_city') if is_professor_local_time else None
                    
                    if not self._is_within_time_window(current_time, txt_start_time, txt_end_time, country_city):
                        continue
                    
                    # Check working day
                    if is_sending_working_day_only and country_city:
                        country = str(country_city).split('/')[0].strip() if '/' in str(country_city) else None
                        if country and not self._is_working_day(current_time, country):
                            continue
                    
                    # Get message_id for reply
                    message_id = row.get('message_id')
                    if pd.isna(message_id) or not message_id:
                        continue
                    
                    # Substitute template
                    substituted_body, substituted_subject, missing_columns = self._substitute_template(
                        template_body, template_subject, idx
                    )
                    
                    # Check for missing values
                    if missing_columns:
                        error_msg = f"Email not sent because {', '.join(missing_columns)} are none or empty"
                        if 'applyche_description' in self.df.columns:
                            self.df.at[idx, 'applyche_description'] = error_msg
                        if callback:
                            callback(f"⚠️ Skipped reminder {reminder_type} to {professor_email}: {error_msg}")
                        self._save_professor_list()
                        continue
                    
                    # Send email as reply
                    if callback:
                        callback(f"📤 Attempting to send reminder {reminder_type} to {professor_email}...")
                    
                    reply_message_id = self._send_email(
                        to_email=str(professor_email),
                        subject=substituted_subject or "No Subject",
                        body=substituted_body,
                        in_reply_to=str(message_id),
                        references=str(message_id)
                    )
                    
                    if reply_message_id:
                        # Update professor list
                        self.df.at[idx, current_time_col] = current_time.strftime("%Y-%m-%d %H:%M:%S")
                        self._save_professor_list()
                        
                        # Save to database via API
                        if self.api_client and self.user_email:
                            try:
                                self.api_client.upsert_professor_list(
                                    user_email=self.user_email,
                                    file_path=self.professor_list_path
                                )
                                
                                # Save to send_log table
                                template_id = self._get_template_id(template_type=reminder_type)
                                self.api_client.create_send_log(
                                    user_email=self.user_email,
                                    sent_to=str(professor_email),
                                    send_type=reminder_type,  # 1, 2, or 3 for reminders
                                    subject=substituted_subject or "No Subject",
                                    body=substituted_body,
                                    template_id=template_id,
                                    delivery_status=1,  # 1 = sent successfully
                                    message_id=reply_message_id,
                                    answer=None  # Will be updated when reply is received
                                )
                            except Exception as e:
                                print(f"Error saving to database: {e}")
                        
                        reminders_sent += 1
                        if callback:
                            callback(f"✅ Sending successful: Reminder {reminder_type} {reminders_sent}/{number_to_send} sent to {professor_email}")
                    else:
                        if callback:
                            callback(f"❌ Sending failed: Failed to send reminder {reminder_type} to {professor_email}")
                
                # Wait 5 minutes before next batch
                if reminders_sent < number_to_send:
                    if callback:
                        callback(f"⏳ Waiting 5 minutes before next reminder {reminder_type} batch to prevent spam detection...")
                    for remaining in range(300, 0, -1):  # 5 minutes
                        if not self._sending:
                            break
                        minutes = remaining // 60
                        secs = remaining % 60
                        if callback and remaining % 10 == 0:  # Update every 10 seconds
                            callback(f"⏳ Preventing detecting spam, you should wait {minutes:02d}:{secs:02d}")
                        time.sleep(1)
                        
        except Exception as e:
            if callback:
                callback(f"❌ Error sending reminders {reminder_type}: {e}")

