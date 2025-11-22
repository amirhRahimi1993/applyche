"""
Example of how to integrate the FastAPI client into main_ui.py
"""
from api_client import ApplyCheAPIClient


# Example: Update Dashboard class to use API
class DashboardExample:
    """
    Example showing how to modify the Dashboard class in main_ui.py
    to use the FastAPI backend instead of direct database access
    """
    def __init__(self, widget):
        self.widget = widget
        self.api_client = ApplyCheAPIClient("http://localhost:8000")
        self.user_email = "user@example.com"  # Get from session/auth in real app
    
    def __fetch_report_from_controller(self):
        """
        Fetch dashboard statistics from API instead of hardcoded values
        """
        try:
            stats = self.api_client.get_dashboard_stats(self.user_email)
            return {
                "email_you_send": stats.get("email_you_send", 0),
                "first_reminder_send": stats.get("first_reminder_send", 0),
                "second_reminder_send": stats.get("second_reminder_send", 0),
                "third_reminder_send": stats.get("third_reminder_send", 0),
                "number_of_email_professor_answered": stats.get("number_of_email_professor_answered", 0)
            }
        except Exception as e:
            print(f"Error fetching dashboard stats: {e}")
            # Fallback to default values
            return {
                "email_you_send": 0,
                "first_reminder_send": 0,
                "second_reminder_send": 0,
                "third_reminder_send": 0,
                "number_of_email_professor_answered": 0
            }


# Example: Update EmailEditor to save templates via API
class EmailEditorExample:
    """
    Example showing how to save email templates via API
    """
    def __init__(self, widget, middle_info_pass):
        self.widget = widget
        self.middle_info_pass = middle_info_pass
        self.api_client = ApplyCheAPIClient("http://localhost:8000")
        self.user_email = "user@example.com"  # Get from session/auth
    
    def save_template_data(self, template_key):
        """
        Save email template to database via API
        """
        editor_map = {
            "main_template": self.txt_main_mail,
            "first_reminder": self.txt_first_reminder,
            "second_reminder": self.txt_second_reminder,
            "third_reminder": self.txt_third_reminder
        }
        
        editor = editor_map.get(template_key)
        if not editor:
            return
        
        html_content = editor.toHtml()
        
        # Map template keys to template types
        template_type_map = {
            "main_template": 0,
            "first_reminder": 1,
            "second_reminder": 2,
            "third_reminder": 3
        }
        
        try:
            # Save via API
            subject = None
            if template_key == "main_template":
                subject = self.txt_main_subject.text()
            
            template = self.api_client.create_email_template(
                user_email=self.user_email,
                template_body=html_content,
                template_type=template_type_map.get(template_key, 0),
                subject=subject
            )
            
            # Also store locally for immediate use
            self.middle_info_pass.store_data(template_key, {
                "html": html_content,
                "template_id": template.get("id"),
                "attachments": self.uploaded_files.get(editor, [])
            })
            
            print(f"Template saved via API: {template}")
            
        except Exception as e:
            print(f"Error saving template via API: {e}")
            # Fallback to local storage only
            self.middle_info_pass.store_data(template_key, {
                "html": html_content,
                "attachments": self.uploaded_files.get(editor, [])
            })


# Example: Update Prepare_send_mail to load/save sending rules via API
class PrepareSendMailExample:
    """
    Example showing how to load and save sending rules via API
    """
    def __init__(self, widget, middle_info_pass):
        self.widget = widget
        self.middle_info_pass = middle_info_pass
        self.api_client = ApplyCheAPIClient("http://localhost:8000")
        self.user_email = "user@example.com"  # Get from session/auth
    
    def __load_data_from_DB(self, field_name):
        """
        Load sending rules from API
        """
        try:
            rules = self.api_client.get_sending_rules(self.user_email)
            
            # Map field names to API response keys
            field_mapping = {
                "txt_number_of_main_mails": "main_mail_number",
                "txt_number_of_first_reminder": "reminder_one",
                "txt_number_of_second_reminder": "reminder_two",
                "txt_number_of_third_reminder": "reminder_three",
                "txt_number_of_email_per_university": "max_email_per_university",
                "txt_preiod_between_reminders": "period_between_reminders",
                "txt_start_time": "start_time_send",
                "txt_end_time": None  # Not in sending_rules table, might need separate handling
            }
            
            api_key = field_mapping.get(field_name)
            if api_key and api_key in rules:
                return rules[api_key]
            
            return -1  # Default value if not found
            
        except Exception as e:
            print(f"Error loading sending rules: {e}")
            return -1
    
    def save_sending_rules(self):
        """
        Save sending rules to API
        """
        try:
            self.api_client.create_sending_rules(
                user_email=self.user_email,
                main_mail_number=int(self.txt_number_of_main_mails),
                reminder_one=int(self.txt_number_of_first_reminder),
                reminder_two=int(self.txt_number_of_second_reminder),
                reminder_three=int(self.txt_number_of_third_reminder),
                max_email_per_university=int(self.txt_number_of_email_per_university),
                period_between_reminders=int(self.txt_period_day),
                local_professor_time=self.is_professor_local_time,
                send_working_day_only=self.is_send_working_day_only,
                start_time_send=self.txt_start_time
            )
            print("Sending rules saved via API")
        except Exception as e:
            print(f"Error saving sending rules: {e}")


