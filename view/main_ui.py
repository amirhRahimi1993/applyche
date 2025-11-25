import os
from functools import partial
from PyQt6 import QtCore
import webbrowser
import pandas as pd
import requests
from PyQt6 import QtWidgets, uic ,QtGui
from PyQt6.QtCharts import QPieSeries, QChartView, QChart, QBarSeries, QBarSet
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QPainter, QPen, QTextCharFormat, QFont, QIcon
from PyQt6.QtWidgets import QVBoxLayout, QSizePolicy, QMessageBox, QFileDialog, QTableWidgetItem, QDialog

from controller.professors_controller import ProfessorsController
from middle_wares.coordinator_sending_mails import Coordinator
from events.event_bus import EventBus
from middle_wares.middle_info_pass import middle_info_pass
from api_client import ApplyCheAPIClient
import resources
class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.middle_info_pass = middle_info_pass()
        uic.loadUi( "../applyche_main_ui.ui", self)
        self.setWindowTitle("ApplyChe")

        # Set the window icon
        self.setWindowIcon(QIcon("../images/applyche.jpg"))  # Use .ico, .png, etc.

        self.show()

        # Enforce stretch (20% vs 80%)
        layout = self.widget_content.layout()
        if layout:
            layout.setStretch(0, 1)  # widget_menu
            layout.setStretch(1, 4)  # right content widget

        # Prevent widgets from shrinking below minimum size
        self.widget_menu.setMinimumWidth(150)
        self.widget_content.setMinimumWidth(400)

        # Example: switch stacked menu pages on startup
        if self.stacked_content.count() > 0:
            self.stacked_content.setCurrentIndex(0)

        # TODO: Get user_email from authentication/session
        # For now, using a placeholder - replace with actual user email
        user_email = "user@example.com"  # Replace with actual user email from session
        self.email_Temp = EmailEditor(self.page_email_template, self.middle_info_pass, user_email)
        self.professorList = Professor_lists(self.page_professor_list,self.middle_info_pass)
        self.email_prep = Prepare_send_mail(self.page_prepare_send_email,self.middle_info_pass)

        self.statics = Statics(self.page_statics)
        self.dashboard = Dashboard(self.page_Dashboard)
        self.dashboard.report()
        self.dashboard.chart_email_answered_by_professor()
        self.dashboard.chart_email_send_remain()
        self.dashboard.chart_emaill_send_by_reminder()


        self.current_page = 0
        self.btn_hamburger.clicked.connect(self.hamburger_toggle)
        self.btn_home.clicked.connect(self.__btn_page_home_arise)
        self.btn_email_template.clicked.connect(self.__btn_page_email_template)
        self.btn_expriences.clicked.connect(self.btn_page_expriences)
        self.btn_results.clicked.connect(self.btn_page_results)
        self.btn_prepare_send_email.clicked.connect(self.btn_page_prepare_send_email)
        self.btn_statics.clicked.connect(self.btn_page_statics)
        self.btn_professor_list.clicked.connect(self.btn_page_professor_list)

        self.btn_profile.clicked.connect(self.__btn_page_profile)
        self.btn_log_out.clicked.connect(self.btn_page_logout)

    def __btn_page_profile(self):
        self.stacked_content.setCurrentWidget(self.page_profile)

    def __btn_page_home_arise(self):
        self.stacked_content.setCurrentWidget(self.page_Dashboard)
        self.dashboard.report()
        self.dashboard.chart_email_answered_by_professor()
        self.dashboard.chart_email_send_remain()
        self.dashboard.chart_emaill_send_by_reminder()

    def __btn_page_email_template(self):
        self.stacked_content.setCurrentWidget(self.page_email_template)

    def btn_page_expriences(self):
        self.stacked_content.setCurrentWidget(self.page_write_your_exprience)

    def btn_page_results(self):
        self.stacked_content.setCurrentWidget(self.page_results)

    def btn_page_prepare_send_email(self):
        self.stacked_content.setCurrentWidget(self.page_prepare_send_email)

    def btn_page_statics(self):
        self.stacked_content.setCurrentWidget(self.page_statics)

    def btn_page_professor_list(self):
        self.stacked_content.setCurrentWidget(self.page_professor_list)

    def btn_page_setting(self):
        self.stacked_content.setCurrentWidget(self.page_settings)

    def btn_page_help(self):
        self.stacked_content.setCurrentWidget(self.page_help)

    def btn_page_logout(self):
        pass

    def hamburger_toggle(self):
        self.stacked_menu.setCurrentIndex(self.current_page)
        self.current_page = 1 - self.current_page


class Dashboard:
    def __init__(self, widget):
        self.widget = widget
        self.lbl_report = self.widget.findChild(QtWidgets.QLabel, "lbl_report")
        self.report()

    def __fetch_report_from_controller(self):
        info = {
            "email_you_send": 80,
            "first_reminder_send": 60,
            "second_reminder_send": 40,
            "third_reminder_send": 20,
            "number_of_email_professor_answered": 10
        }
        return info

    def print_tree(self, widget, indent=0):
        print("  " * indent + f"{widget.objectName()} [{type(widget).__name__}]")
        for child in widget.children():
            self.print_tree(child, indent + 1)

    def report(self):
        info = self.__fetch_report_from_controller()
        widget_report = self.widget.findChild(QtWidgets.QWidget, "widget_report")
        self.lbl_report = widget_report.findChild(QtWidgets.QLabel, "lbl_send_emails")
        self.lbl_report.setText(fr"The number of emails send by applyche: {info['email_you_send']}")
        self.lbl_report = widget_report.findChild(QtWidgets.QLabel, "lbl_first_reminder_send")
        self.lbl_report.setText(fr"The number of emails send by applyche: {info['first_reminder_send']}")
        self.lbl_report = widget_report.findChild(QtWidgets.QLabel, "lbl_second_reminder_send")
        self.lbl_report.setText(fr"The number of emails send by applyche: {info['second_reminder_send']}")
        self.lbl_report = widget_report.findChild(QtWidgets.QLabel, "lbl_third_reminder_send")
        self.lbl_report.setText(fr"The number of emails send by applyche: {info['third_reminder_send']}")
        self.lbl_report = widget_report.findChild(QtWidgets.QLabel, "lbl_professors_answered")
        self.lbl_report.setText(fr"The number of emails send by applyche: {info['number_of_email_professor_answered']}")
    def __draw_the_pie_chart(self, widget_want_to_draw, series, title):
        slice0 = series.slices()[0]
        slice0.setExploded(True)
        slice0.setLabelVisible(True)
        slice0.setPen(QPen(Qt.GlobalColor.darkGreen, 2))
        slice0.setBrush(Qt.GlobalColor.green)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setVisible(True)

        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

        chartview = QChartView(chart)
        chartview.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.pieChart_professor = widget_want_to_draw
        layout = QVBoxLayout(self.pieChart_professor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(chartview)

        self.pieChart_professor.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

    def chart_email_answered_by_professor(self):
        series = QPieSeries()
        series.append("SendMail", 800)
        series.append("Answered", 30)
        main_widget = self.widget.findChild(QtWidgets.QWidget, "widget_main")
        pieChart_professor = main_widget.findChild(QtWidgets.QWidget, "widget_professor_answered")
        self.__draw_the_pie_chart(pieChart_professor, series, "Email send VS Email answered")

    def chart_email_send_remain(self):
        title = "Email send VS Email Remain"
        series = QPieSeries()
        series.append("Send Emails", 800)
        series.append("Remain Emails", 1200)
        main_widget = self.widget.findChild(QtWidgets.QWidget, "widget_main")
        pieChart_sendvsnotsend = main_widget.findChild(QtWidgets.QWidget, "widget_send_email_remainEmail")
        self.__draw_the_pie_chart(pieChart_sendvsnotsend, series, title)

    def chart_emaill_send_by_reminder(self):
        title = "All Emails sends"
        series = QPieSeries()
        series.append("Main Emails", 800)
        series.append("Remainder1", 600)
        series.append("Remainder2", 400)
        series.append("Remainder3", 0)
        main_widget = self.widget.findChild(QtWidgets.QWidget, "widget_main")
        pieChart_sendvsnotsend = main_widget.findChild(QtWidgets.QWidget, "widget_sended_mails")
        self.__draw_the_pie_chart(pieChart_sendvsnotsend, series, title)

class EmailEditor(QtCore.QObject):
    def __init__(self, widget, middle_info_pass, user_email: str = "user@example.com"):
        super().__init__(widget)
        self.widget = widget
        self.stacked_widget = self.widget.findChild(QtWidgets.QStackedWidget, "stacked_email_template")
        self.middle_info_pass = middle_info_pass
        self.user_email = user_email
        
        # Initialize API client (always create it, check availability when needed)
        try:
            self.api_client = ApplyCheAPIClient("http://localhost:8000", timeout=3)
            # Check if API is available (don't fail if it's not)
            if not self.api_client.is_available():
                print("Info: FastAPI server is not running. Templates will be saved locally only.")
                # Keep the client - it will be checked again when saving
        except Exception as e:
            print(f"Info: API client initialization failed: {e}")
            # Still create the client - it might work later when server starts
            try:
                self.api_client = ApplyCheAPIClient("http://localhost:8000", timeout=3)
            except:
                self.api_client = None

        # Store uploaded files per editor
        self.uploaded_files = {}
        self.saved_templates = {}
        self.template_ids = {}  # Store template IDs for updates
        self.save_btns= {
            "main_template":self.stacked_widget.findChild(QtWidgets.QPushButton, "btn_save_main_temp"),
            "first_reminder": self.stacked_widget.findChild(QtWidgets.QPushButton, "btn_save_first_temp"),
            "second_reminder": self.stacked_widget.findChild(QtWidgets.QPushButton, "btn_save_second_temp"),
            "third_reminder": self.stacked_widget.findChild(QtWidgets.QPushButton, "btn_save_third_temp")
        }
        btn_previous_pages = [
            "btn_previous_page_first_temp",
            "btn_previous_page_second_temp",
            "btn_previous_page_third_temp"
        ]
        previous_pages =[
            "page_main_email",
            "page_reminder_one",
            "page_reminder_two",
        ]
        btn_names = [
            "btn_next_page",
            "btn_next_page_first_temp",
            "btn_next_page_second_temp",
            "btn_next_page_third_temp",
        ]
        page_names = [
            "page_reminder_one",
            "page_reminder_two",
            "page_reminder_third",
            "page_main_email",
        ]

        # Dynamically find widgets and connect
        for i, (btn_name, page_name) in enumerate(zip(btn_names, page_names)):
            btn = self.widget.findChild(QtWidgets.QPushButton, btn_name)
            page = self.stacked_widget.findChild(QtWidgets.QWidget, page_name)

            if btn and page:
                btn.clicked.connect(lambda _, index=i + 1: self.stacked_widget.setCurrentIndex(index%len(page_names)))

        for i , (btn_previous_page,page_previous_page) in enumerate(zip(btn_previous_pages,previous_pages)):
            btn = self.stacked_widget.findChild(QtWidgets.QPushButton, btn_previous_page)
            page = self.stacked_widget.findChild(QtWidgets.QWidget,page_previous_page)
            if btn and page:
                btn.clicked.connect(lambda _,index= i: self.stacked_widget.setCurrentIndex(index%len(btn_previous_pages)))
        for key,btn in self.save_btns.items():
            if not btn:
                raise "No save button found!!"
            btn.clicked.connect(partial(self.save_template_data,key))
        # find text editors
        self.txt_main_subject = widget.findChild(QtWidgets.QLineEdit,"txt_subject")
        self.txt_main_mail = widget.findChild(QtWidgets.QTextEdit, "txt_main_mail")
        self.txt_first_reminder = widget.findChild(QtWidgets.QTextEdit, "txt_first_reminder")
        self.txt_second_reminder = widget.findChild(QtWidgets.QTextEdit, "txt_second_reminder")
        self.txt_third_reminder = widget.findChild(QtWidgets.QTextEdit, "txt_third_reminder")

        self.text_edits = [
            self.txt_main_mail,
            self.txt_first_reminder,
            self.txt_second_reminder,
            self.txt_third_reminder,
        ]

        # make them editable
        for editor in self.text_edits:
            if not editor:
                continue
            editor.setReadOnly(False)
            editor.setAcceptRichText(True)
            editor.viewport().installEventFilter(self)
            editor.setAcceptDrops(True)
            editor.installEventFilter(self)
            self.uploaded_files[editor] = []

        # find buttons
        bold_names = ["btn_bold", "btn_bold_first", "btn_bold_second", "btn_bold_third"]
        italic_names = ["btn_italic", "btn_italic_first", "btn_italic_second", "btn_italic_third"]
        link_names = ["btn_link", "btn_link_first", "btn_link_second", "btn_link_third"]
        upload_names = ["btn_upload", "btn_upload_first", "btn_upload_second", "btn_upload_third"]

        self.bold_buttons = [widget.findChild(QtWidgets.QPushButton, n) for n in bold_names]
        self.italic_buttons = [widget.findChild(QtWidgets.QPushButton, n) for n in italic_names]
        self.link_buttons = [widget.findChild(QtWidgets.QPushButton, n) for n in link_names]
        self.upload_buttons = [widget.findChild(QtWidgets.QPushButton, n) for n in upload_names]

        # create attachment display areas
        self.attachment_areas = {}
        for editor in self.text_edits:
            if not editor:
                continue
            container = QtWidgets.QWidget()
            v_layout = QtWidgets.QVBoxLayout(container)
            v_layout.setContentsMargins(4, 2, 4, 2)
            v_layout.setSpacing(2)

            chip_area = QtWidgets.QWidget()
            chip_layout = QtWidgets.QHBoxLayout(chip_area)
            chip_layout.setContentsMargins(0, 0, 0, 0)
            chip_layout.setSpacing(6)
            chip_area.setLayout(chip_layout)

            total_label = QtWidgets.QLabel()
            total_label.setStyleSheet("color: #555; font-size: 11px; margin-left: 6px;")

            v_layout.addWidget(chip_area)
            v_layout.addWidget(total_label)

            parent_layout = editor.parentWidget().layout()
            if parent_layout:
                parent_layout.addWidget(container)
            container.hide()

            self.attachment_areas[editor] = (container, chip_area, total_label)

        # connect buttons
        for i, editor in enumerate(self.text_edits):
            if not editor:
                continue
            bbtn = self.bold_buttons[i] if i < len(self.bold_buttons) else None
            ibtn = self.italic_buttons[i] if i < len(self.italic_buttons) else None
            lbtn = self.link_buttons[i] if i < len(self.link_buttons) else None
            ubtn = self.upload_buttons[i] if i < len(self.upload_buttons) else None

            if bbtn:
                bbtn.setCheckable(True)
                bbtn.setStyleSheet("background-color: gray; color: white;")
                bbtn.clicked.connect(partial(self.toggle_bold, editor, bbtn))

            if ibtn:
                ibtn.setCheckable(True)
                ibtn.setStyleSheet("background-color: gray; color: white;")
                ibtn.clicked.connect(partial(self.toggle_italic, editor, ibtn))

            if lbtn:
                lbtn.clicked.connect(partial(self.insert_link, editor))

            if ubtn:
                ubtn.clicked.connect(partial(self.insert_file_attachment, editor))

            editor.cursorPositionChanged.connect(partial(self.update_button_states, editor))
        
        # Load templates from database after UI is set up
        self._load_templates_from_db()

    # ====================================================
    # =============== Load Templates from DB =============
    # ====================================================
    def _load_templates_from_db(self):
        """Load email templates from database and populate UI
        Optimized to use a single batch API call instead of 4 separate calls
        Silently fails if API is not available - app continues to work in offline mode
        """
        if not self.api_client:
            # API not available - app will work in offline mode
            return
        
        # Check if API is actually available before trying to load
        try:
            if not self.api_client.is_available():
                # API server is not running - silently continue
                return
        except Exception:
            # Connection check failed - silently continue
            return
        
        # Template type mapping: 0=main, 1=first_reminder, 2=second_reminder, 3=third_reminder
        template_mapping = {
            "main_template": (0, self.txt_main_mail),
            "first_reminder": (1, self.txt_first_reminder),
            "second_reminder": (2, self.txt_second_reminder),
            "third_reminder": (3, self.txt_third_reminder)
        }
        
        try:
            # Use batch API call to fetch all templates at once (much faster)
            template_types = [0, 1, 2, 3]
            templates = self.api_client.get_templates_by_types(self.user_email, template_types)
            
            # Create a lookup dictionary by template_type
            templates_by_type = {t.get("template_type"): t for t in templates}
            
            # Process each template
            for template_key, (template_type, editor) in template_mapping.items():
                template = templates_by_type.get(template_type)
                if template:
                    # Store template ID for updates
                    self.template_ids[template_key] = template.get("id")
                    
                    # Load HTML content into editor
                    if editor:
                        editor.setHtml(template.get("template_body", ""))
                    
                    # Load subject for main template
                    if template_key == "main_template" and self.txt_main_subject:
                        self.txt_main_subject.setText(template.get("subject", ""))
                    
                    # Load file paths
                    file_paths = template.get("file_paths", [])
                    if file_paths and editor:
                        # Clear existing files
                        self.uploaded_files[editor] = []
                        
                        # Add files from database
                        for file_path in file_paths:
                            if os.path.exists(file_path):
                                file_name = os.path.basename(file_path)
                                file_size = os.path.getsize(file_path)
                                self.uploaded_files[editor].append(file_path)
                                
                                # Create attachment chip
                                container, chip_area, _ = self.attachment_areas.get(editor, (None, None, None))
                                if container and chip_area:
                                    chip = self._create_attachment_chip(file_name, file_path, file_size, editor)
                                    chip_area.layout().addWidget(chip)
                                    container.show()
                        
                        # Update attachment summary
                        self._update_attachment_summary(editor)
        except (requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError) as e:
            # API server is not available or returned an error - silently continue (offline mode)
            # Don't print error messages for connection issues - this is expected if server isn't running
            pass
        except Exception as e:
            # Other unexpected errors - log but don't crash
            # Only log if it's not a connection-related error
            if not isinstance(e, (requests.exceptions.RequestException, requests.exceptions.HTTPError)):
                print(f"Info: Could not load templates from database: {type(e).__name__}")
            # Don't try fallback if connection failed - it will just fail again

    # ====================================================
    # =============== Bold / Italic ======================
    # ====================================================
    def toggle_bold(self, editor, button):
        fmt = QTextCharFormat()
        if button.isChecked():
            fmt.setFontWeight(QFont.Weight.Bold)
            button.setStyleSheet("background-color: #0078D7; color: white;")
        else:
            fmt.setFontWeight(QFont.Weight.Normal)
            button.setStyleSheet("background-color: gray; color: white;")

        editor.mergeCurrentCharFormat(fmt)
        editor.setFocus()  # keep typing immediately

    def toggle_italic(self, editor, button):
        fmt = QTextCharFormat()
        if button.isChecked():
            button.setStyleSheet("background-color: #0078D7; color: white;")
        else:
            button.setStyleSheet("background-color: gray; color: white;")
        fmt.setFontItalic(button.isChecked())
        editor.mergeCurrentCharFormat(fmt)
        editor.setFocus()

    def save_template_data(self, template_key):
        """Save template to database via API"""
        editor_map = {
            "main_template": (0, self.txt_main_mail),
            "first_reminder": (1, self.txt_first_reminder),
            "second_reminder": (2, self.txt_second_reminder),
            "third_reminder": (3, self.txt_third_reminder)
        }
        
        template_info = editor_map.get(template_key)
        if not template_info:
            QtWidgets.QMessageBox.warning(None, "Warning", f"Unknown template key: {template_key}")
            return
        
        template_type, editor = template_info
        if not editor:
            QtWidgets.QMessageBox.warning(None, "Warning", f"Editor not found for {template_key}")
            return
        
        html_content = editor.toHtml()
        file_paths = self.uploaded_files.get(editor, [])
        
        # Get subject for main template
        subject = None
        if template_key == "main_template" and self.txt_main_subject:
            subject = self.txt_main_subject.text()
            self.middle_info_pass.store_data("txt_main_subject", subject)
        
        # Save to local storage (for backward compatibility)
        self.saved_templates[template_key] = {
            "html": html_content,
            "attachments": file_paths.copy()
        }
        self.middle_info_pass.store_data(template_key, self.saved_templates[template_key])
        
        # Save to database via API
        # Try to ensure API client exists
        if not self.api_client:
            try:
                self.api_client = ApplyCheAPIClient("http://localhost:8000", timeout=3)
            except Exception as e:
                print(f"Could not create API client: {e}")
        
        # Check if API is available and try to save
        api_saved = False
        if self.api_client:
            try:
                # Check if API is available before attempting to save
                if self.api_client.is_available():
                    template_id = self.template_ids.get(template_key)
                    
                    if template_id:
                        # Update existing template
                        self.api_client.update_email_template(
                            template_id=template_id,
                            user_email=self.user_email,
                            template_body=html_content,
                            template_type=template_type,
                            subject=subject,
                            file_paths=file_paths
                        )
                    else:
                        # Create new template
                        result = self.api_client.create_email_template(
                            user_email=self.user_email,
                            template_body=html_content,
                            template_type=template_type,
                            subject=subject,
                            file_paths=file_paths
                        )
                        # Store the new template ID
                        self.template_ids[template_key] = result.get("id")
                    
                    api_saved = True
                else:
                    # API server is not running
                    print("API server is not available - saving locally only")
            except requests.exceptions.ConnectionError:
                # Connection error - API server is not running
                print("API server connection failed - saving locally only")
            except Exception as e:
                # Other errors
                print(f"Error saving template to API: {e}")
                QtWidgets.QMessageBox.warning(
                    editor,
                    "Save Warning",
                    f"Template saved locally but failed to save to database:\n{str(e)}\n\n"
                    f"Please ensure the FastAPI server is running on http://localhost:8000"
                )
        
        # Show success message
        if api_saved:
            QtWidgets.QMessageBox.information(
                editor,
                "Template Saved",
                f"✅ {template_key.replace('_', ' ').title()} has been saved successfully to database.\n\n"
                f"Attachments: {len(file_paths)} file(s)",
            )
        else:
            # Saved locally only
            QtWidgets.QMessageBox.information(
                editor,
                "Template Saved Locally",
                f"✅ {template_key.replace('_', ' ').title()} has been saved locally.\n\n"
                f"Attachments: {len(file_paths)} file(s)\n\n"
                f"Note: FastAPI server is not running. To save to database, please start the API server:\n"
                f"  python -m uvicorn api.main:app --reload",
            )
        
        print(f"Saved {template_key}: {self.saved_templates[template_key]}")

    # ====================================================
    # =============== Add Link ===========================
    # ====================================================

    def insert_link(self, editor):
        cursor = editor.textCursor()
        if not cursor.hasSelection():
            QtWidgets.QMessageBox.warning(editor, "Add Link", "Please highlight text to make it a link.")
            return

        url, ok = QtWidgets.QInputDialog.getText(editor, "Insert Link", "Enter URL:")
        if not ok or not url.strip():
            return

        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "http://" + url

        selected_text = cursor.selectedText()

        cursor.beginEditBlock()
        cursor.removeSelectedText()

        # --- Apply link format ---
        link_format = QtGui.QTextCharFormat()
        link_format.setAnchor(True)
        link_format.setAnchorHref(url)
        link_format.setForeground(QtGui.QBrush(QtGui.QColor("#0000EE")))
        link_format.setFontUnderline(True)

        cursor.insertText(selected_text, link_format)

        # --- Insert a format boundary ---
        # Add a space with default formatting (visually invisible if space already exists)
        normal_format = QtGui.QTextCharFormat()
        normal_format.setAnchor(False)
        normal_format.setFontUnderline(False)
        normal_format.setForeground(editor.palette().text())

        # This ensures that typing continues in normal text, not within the link
        cursor.insertText(" ", normal_format)
        editor.setTextCursor(cursor)

        cursor.endEditBlock()
        editor.setFocus()

    # ====================================================
    # =============== Upload Files (Multi, Gmail-style) ===
    # ====================================================
    def insert_file_attachment(self, editor):
        file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(editor, "Attach Files", "", "All Files (*)")
        if not file_paths:
            return

        for file_path in file_paths:
            if not file_path:
                continue
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            self.uploaded_files[editor].append(file_path)
            container, chip_area, _ = self.attachment_areas.get(editor, (None, None, None))
            if not container or not chip_area:
                continue
            chip = self._create_attachment_chip(file_name, file_path, file_size, editor)
            chip_area.layout().addWidget(chip)
            container.show()

        self._update_attachment_summary(editor)
        editor.setFocus()

    def _create_attachment_chip(self, file_name, file_path, file_size, editor):
        chip = QtWidgets.QFrame()
        chip.setStyleSheet("""
            QFrame {
                background-color: #e6e6e6;
                border: 1px solid #ccc;
                border-radius: 8px;
            }
        """)
        chip_layout = QtWidgets.QHBoxLayout(chip)
        chip_layout.setContentsMargins(8, 2, 8, 2)
        chip_layout.setSpacing(6)

        icon = QtWidgets.QLabel("📎")
        icon.setStyleSheet("font-size:14px;")
        chip_layout.addWidget(icon)

        label = QtWidgets.QLabel(file_name)
        label.setStyleSheet("color: black; font-size: 12px;")
        label.setToolTip(f"{file_path}\n{self._format_size(file_size)}")
        chip_layout.addWidget(label)

        remove_btn = QtWidgets.QPushButton("✕")
        remove_btn.setFixedSize(18, 18)
        remove_btn.setStyleSheet("""
            QPushButton {
                border: none;
                color: #666;
                font-weight: bold;
            }
            QPushButton:hover { color: red; }
        """)
        chip_layout.addWidget(remove_btn)

        # double-click opens file
        def open_file(event):
            if event.type() == QtCore.QEvent.Type.MouseButtonDblClick:
                QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(file_path))

        chip.mouseDoubleClickEvent = open_file

        def remove_file():
            chip.setParent(None)
            chip.deleteLater()
            if file_path in self.uploaded_files[editor]:
                self.uploaded_files[editor].remove(file_path)
            self._update_attachment_summary(editor)

        remove_btn.clicked.connect(remove_file)
        return chip

    def _update_attachment_summary(self, editor):
        container, chip_area, total_label = self.attachment_areas.get(editor, (None, None, None))
        files = self.uploaded_files.get(editor, [])
        if not files:
            if container:
                container.hide()
            return

        total_size = sum(os.path.getsize(f) for f in files if os.path.exists(f))
        total_label.setText(
            f"{len(files)} attachment{'s' if len(files) != 1 else ''} – {self._format_size(total_size)} total"
        )
        if container:
            container.show()

    def _format_size(self, size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024**2:
            return f"{size/1024:.1f} KB"
        elif size < 1024**3:
            return f"{size/1024**2:.1f} MB"
        else:
            return f"{size/1024**3:.1f} GB"

    # ====================================================
    # =============== Drag and Drop Support ==============
    # ====================================================
    def eventFilter(self, watched, event):
        # Open link click
        if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            for editor in self.text_edits:
                if not editor:
                    continue
                if watched is editor.viewport():
                    pos = event.position().toPoint()
                    href = editor.anchorAt(pos)
                    if href:
                        webbrowser.open(href)
                        return True

        # Handle drag & drop files
        if isinstance(watched, QtWidgets.QTextEdit):
            editor = watched
            if event.type() == QEvent.Type.DragEnter:
                if event.mimeData().hasUrls():
                    event.acceptProposedAction()
                    return True
            elif event.type() == QEvent.Type.Drop:
                urls = event.mimeData().urls()
                file_paths = [u.toLocalFile() for u in urls if u.isLocalFile()]
                if file_paths:
                    for f in file_paths:
                        file_name = os.path.basename(f)
                        file_size = os.path.getsize(f)
                        self.uploaded_files[editor].append(f)
                        container, chip_area, _ = self.attachment_areas.get(editor, (None, None, None))
                        chip = self._create_attachment_chip(file_name, f, file_size, editor)
                        chip_area.layout().addWidget(chip)
                        container.show()
                    self._update_attachment_summary(editor)
                    event.acceptProposedAction()
                    return True
        return super().eventFilter(watched, event)

    # ====================================================
    # =============== Utility ============================
    # ====================================================
    def get_uploaded_files(self, editor=None):
        if editor:
            return self.uploaded_files.get(editor, [])
        all_files = []
        for paths in self.uploaded_files.values():
            all_files.extend(paths)
        return all_files

    def update_button_states(self, editor):
        fmt = editor.currentCharFormat()
        try:
            idx = self.text_edits.index(editor)
        except ValueError:
            return
        bold_btn = self.bold_buttons[idx] if idx < len(self.bold_buttons) else None
        italic_btn = self.italic_buttons[idx] if idx < len(self.italic_buttons) else None

        if bold_btn:
            is_bold = fmt.fontWeight() == QFont.Weight.Bold
            bold_btn.setChecked(is_bold)
            color = "#0078D7" if is_bold else "gray"
            text_color = "white"
            bold_btn.setStyleSheet(f"background-color: {color}; color: {text_color};")

        if italic_btn:
            italic_btn.setChecked(fmt.fontItalic())

class Prepare_send_mail(QtWidgets.QWidget):
    def __init__(self, widget,middle_info_pass):
        super().__init__(widget)  # <-- important
        bus = EventBus()
        self.middle_info_pass = middle_info_pass
        self.bus = bus
        self.is_test = False
        self.send_main_info = {
            "txt_number_of_main_mails": 0,
            "txt_number_of_first_reminder": 0,
            "txt_number_of_second_reminder": 0,
            "txt_number_of_third_reminder": 0,
            "txt_number_of_email_per_university": -1,
            "txt_preiod_between_reminders":0,
        }
        self.time_send = {"txt_start_time": [], "txt_end_time": []}
        self.send_mail_status = True
        self.prof_local_time = False
        self.main_widget = widget.findChild(QtWidgets.QStackedWidget,"stackedWidget_send")
        self.page_email_info = self.main_widget.findChild(QtWidgets.QWidget,"page_email_info")
        self.page_log = self.main_widget.findChild(QtWidgets.QWidget,"page_log")

        self.widget = widget.findChild(QtWidgets.QWidget, "page_email_conditions")

        fields = [
            "txt_number_of_main_mails",
            "txt_number_of_first_reminder",
            "txt_number_of_second_reminder",
            "txt_number_of_third_reminder",
            "txt_number_of_email_per_university",
            "txt_start_time",
            "txt_end_time"
        ]
        for name in fields:
            line_edit = self.widget.findChild(QtWidgets.QLineEdit, name)
            if line_edit:
                value = self.__load_data_from_DB(name)
                line_edit.setText(str(value))



        self.stackedWidget_send = widget.findChild(QtWidgets.QStackedWidget, "stackedWidget_send")
        self.btn_next_page = self.widget.findChild(QtWidgets.QPushButton, "btn_next_to_send")

        print("widget:", self.widget)
        print("stackedWidget_send:", self.stackedWidget_send)
        print("btn_next_page:", self.btn_next_page)

        if self.stackedWidget_send is not None:
            self.stackedWidget_send.setCurrentIndex(0)
        if self.btn_next_page is not None:
            self.btn_next_page.clicked.connect(self.next_page)
        self.btn_email_info_back = self.page_email_info.findChild(QtWidgets.QPushButton,"btn_email_info_back")
        self.btn_send_test_mail = self.page_email_info.findChild(QtWidgets.QPushButton, "btn_send_test")
        self.btn_send_real_mail = self.page_email_info.findChild(QtWidgets.QPushButton, "btn_send_email")

        self.btn_send_test_mail.clicked.connect(self.__send_test_mail)
        self.btn_send_real_mail.clicked.connect(self.__send_real_mails)
        self.btn_email_info_back.clicked.connect(self.__back_send_mail)

        self.btn_stop_start_sending = self.page_log.findChild(QtWidgets.QPushButton, "btn_stop_sending")
        self.btn_stop_start_sending.clicked.connect(self.__change_send_status)

        self.total_page = 3
    def __get_data_from_user(self):
        self.txt_number_of_main_mails = self.widget.findChild(QtWidgets.QLineEdit, "txt_number_of_main_mails").text()
        self.txt_number_of_first_reminder = self.widget.findChild(QtWidgets.QLineEdit, "txt_number_of_first_reminder").text()
        self.txt_number_of_second_reminder = self.widget.findChild(QtWidgets.QLineEdit,"txt_number_of_second_reminder").text()
        self.txt_number_of_third_reminder = self.widget.findChild(QtWidgets.QLineEdit, "txt_number_of_third_reminder").text()
        self.txt_number_of_email_per_university = self.widget.findChild(QtWidgets.QLineEdit, "txt_number_of_email_per_university").text()
        self.txt_start_time = self.widget.findChild(QtWidgets.QLineEdit,"txt_start_time").text()
        self.txt_end_time = self.widget.findChild(QtWidgets.QLineEdit,"txt_end_time").text()
        self.txt_period_day = self.widget.findChild(QtWidgets.QLineEdit,"txt_preiod_between_reminders").text()
        self.is_send_working_day_only = self.widget.findChild(QtWidgets.QWidget, "is_send_working_day_only").isChecked()
        self.is_professor_local_time = self.widget.findChild(QtWidgets.QCheckBox, "is_professor_local_time").isChecked()
    def __check_time(self):
        if len(self.txt_start_time.split(":"))!=2 or len(self.txt_end_time.split(":"))!=2:
            QMessageBox.critical(
                None,
                "Error",
                "In time format you can only use HOUR:MINUTE the format you used is different",
                QMessageBox.StandardButton.Ok
            )
            return False
        start_hour = self.time_send["txt_start_time"][0]
        end_hour = self.time_send["txt_end_time"][0]
        start_minute = self.time_send["txt_start_time"][1]
        end_minute = self.time_send["txt_end_time"][1]
        if(start_hour.isdecimal() and end_hour.isdecimal() and start_minute.isdecimal() and end_minute.isdecimal()) == False:
            QMessageBox.critical(
            None,
            "Error",
            "Only and Only decimal number like 2,3,4,5 and : are acceptable any other thing like space, PM or AM cause error!!! ",
            QMessageBox.StandardButton.Ok
            )
            return False
        if (len(start_minute) != 2 or len(end_minute) != 2):
            QMessageBox.critical(
                None,
                "Error",
                "The minute should have 2 digit like 10:02 or 23:09 or 18:15 !!! ",
                QMessageBox.StandardButton.Ok
            )
            return False
        start_hour = int(start_hour)
        end_hour = int(end_hour)
        start_minute = int(start_minute)
        end_minute = int(end_minute)

        if (start_hour >23 or start_hour < 0) or (end_hour >23 or end_hour < 0 ):
            QMessageBox.critical(
                None,
                "Error",
                "hours should be between 0 and 23(included)!",
                QMessageBox.StandardButton.Ok
            )
            return False
        if (start_minute >59 or start_minute < 0) or (end_minute >59 or end_minute < 0):
            QMessageBox.critical(
                None,
                "Error",
                "Minutes should be between 0 and 59(included)!",
                QMessageBox.StandardButton.Ok
            )
            return False
        if(start_hour > end_hour) or (start_hour == end_hour and start_minute> end_minute):
            QMessageBox.critical(
                None,
                "Error",
                "start hour cannot be greater than end hour!!",
                QMessageBox.StandardButton.Ok
            )
            return False

        return True
    def next_page(self):
        self.__get_data_from_user()
        for k in self.send_main_info.keys():
            self.send_main_info[k] = getattr(self,k) if getattr(self,k) != None and getattr(self,k) !="" else 0
        for k in self.send_main_info.keys():
            if str(self.send_main_info[k]).isdigit() == False or str(self.send_main_info[k]).isdigit() < 0:
                QMessageBox.critical(
                    None,
                    "Error",
                    "Only number(Integer) above 0 is acceptable!!",
                    QMessageBox.StandardButton.Ok
                )
                return
        self.time_send["txt_start_time"]= self.txt_start_time.split(":")

        self.time_send["txt_end_time"] = self.txt_end_time.split(":")
        if (self.__check_time() == False):
            return
        self.prof_local_time = self.is_professor_local_time
        self.main_widget.setCurrentWidget(self.page_email_info)

    def __back_send_mail(self):
        self.main_widget.setCurrentWidget(self.widget)
    def __send_test_mail(self):
        self.is_test = True
        self.password = self.page_email_info.findChild(QtWidgets.QLineEdit, "txt_password").text()
        self.email = self.page_email_info.findChild(QtWidgets.QLineEdit, "txt_email").text()
        self.stackedWidget_send.setCurrentWidget(self.page_log)
        self.__start_sending_mails()
    def __send_real_mails(self):
        self.is_test = False
        self.password = self.page_email_info.findChild(QtWidgets.QLineEdit, "txt_password").text()
        self.email = self.page_email_info.findChild(QtWidgets.QLineEdit, "txt_email").text()
        self.stackedWidget_send.setCurrentWidget(self.page_log)
        self.__start_sending_mails()

    def __start_sending_mails(self):
        # Create coordinator if not already done
        if not hasattr(self, "coordinator"):
            self.coordinator = Coordinator(self.bus)
            self.coordinator.set_view(self)

        info = self.send_information_to_controller()
        self.coordinator.start_sending(info)

    def __kill_or_continue_sending(self):
        if hasattr(self, "coordinator"):
            self.coordinator.stop_sending()

    def display_log(self, message):
        """This is called by coordinator when log messages arrive."""
        print(f"[LOG] {message}")
        # Optionally show logs on UI (if you have a QTextEdit or QLabel)
        log_text = self.page_log.findChild(QtWidgets.QPlainTextEdit, "txt_log")
        message=message + "\n"
        log_text.appendPlainText(message)
    def __move_file_into_safe_place(self):
        if os.path.exists("AppData/Local") == False:
            os.mkdir("AppData/Local")
        temp_place = ["main_template","first_reminder"]

    def send_information_to_controller(self):

        information = {
            "is_test": self.is_test,
            "email": self.email,
            "password": self.password,
            "txt_number_of_main_mails":self.txt_number_of_main_mails,
            "txt_number_of_first_reminder": self.txt_number_of_first_reminder,
            "txt_number_of_second_reminder": self.txt_number_of_second_reminder,
            "txt_number_of_third_reminder": self.txt_number_of_third_reminder,
            "txt_number_of_email_per_university":self.txt_number_of_email_per_university,
            "txt_start_time": self.txt_start_time,
            "txt_end_time": self.txt_end_time,
            "is_professor_local_time": self.is_professor_local_time,
            "main_template" : self.middle_info_pass.get_data("main_template"),
            "first_reminder" : self.middle_info_pass.get_data("first_reminder"),
            "second_reminder" : self.middle_info_pass.get_data("second_reminder"),
            "third_reminder" : self.middle_info_pass.get_data("third_reminder"),
            "professor_list" : self.middle_info_pass.get_data("professor_list"),
            "txt_main_subject": self.middle_info_pass.get_data("txt_main_subject")
        }
        return information
    def __change_send_status(self):
        if self.send_mail_status:
            self.btn_stop_start_sending.setText("START SENDING MAILs")
            self.btn_stop_start_sending.setStyleSheet("""
            QPushButton {
                background-color: green;
            }
        """)
        else:
            self.btn_stop_start_sending.setText("STOP SENDING MAILs")
            self.btn_stop_start_sending.setStyleSheet("""
                        QPushButton {
                            background-color: red;
                        }
                    """)
        self.send_mail_status = not self.send_mail_status
        if self.send_mail_status:
            self.__start_sending_mails()
        else:
            self.__kill_or_continue_sending()

    def __load_data_from_DB(self,id):
        return -1


class FetchUniversityDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("Fetch_university.ui", self)
class Professor_lists():
    def __init__(self,widget,middle_info_pass):
        self.middle_info_pass = middle_info_pass
        # This assumes you've already loaded your UI with tbl_professors_list and btn_local_upload
        self.widget = widget.findChild(QtWidgets.QWidget,"page_professors")
        self.tbl_professors_list: QtWidgets.QTableWidget = self.widget.findChild(QtWidgets.QTableWidget, "tbl_professors_list")
        self.btn_local_upload: QtWidgets.QPushButton = self.widget.findChild(QtWidgets.QPushButton, "btn_local_upload")
        self.btn_download_from_applyche: QtWidgets.QPushButton = self.widget.findChild(QtWidgets.QPushButton, "btn_download_from_applyche")

        # Connect button to upload function
        self.btn_local_upload.clicked.connect(self.upload_data_from_local)
        self.btn_download_from_applyche.clicked.connect(self.popup_the_download_list)

    def popup_the_download_list(self):
        dialog = FetchUniversityDialog()
        dialog.exec()
    def upload_data_from_local(self):

        # Let user choose file
        file_path, _ = QFileDialog.getOpenFileName(
            self.widget,
            "Select CSV or Excel File",
            "",
            "CSV Files (*.csv);;Excel Files (*.xls *.xlsx)"
        )
        if not file_path:  # If user cancels
            return

        try:
            P = ProfessorsController(file_path)
            values = P.send_professor_info()
            df= values["df"]
            headers= values["header"]
            nans = values["nans"]
            self.middle_info_pass.store_data("professor_list",df)
        except Exception as e:
            QMessageBox.critical(self.widget, "Error", f"Failed to read file:\n{str(e)}")
            return
        for k in nans.keys():
            QMessageBox.warning(self.widget,"Some columns are empty",f"I have find {len(nans[k])} empty value in {k} column it may affect on your email process!!")
        df.columns = df.columns.str.strip().str.lower()

        # Populate table
        self._populate_table(df)

    def _populate_table(self, df: pd.DataFrame):
        self.tbl_professors_list.clear()
        self.tbl_professors_list.setRowCount(len(df))
        self.tbl_professors_list.setColumnCount(len(df.columns))
        self.tbl_professors_list.setHorizontalHeaderLabels(df.columns)

        for row_idx, row_data in df.iterrows():
            for col_idx, value in enumerate(row_data):
                self.tbl_professors_list.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))

    def get_data_from_applyche(self):
        pass

    def __send_data_to_servers(self):
        pass

    def __merge_two_tables(self):
        pass
class Profile(QtWidgets.QWidget):
    def __init__(self):
        pass
    def __fetch_user_data_from_applyche(self):
        pass
    def show_data(self):
        pass

class Results(QtWidgets.QWidget):
    def __init__(self):
        pass
    def __sentimental_analysis_invoker(self):
        pass
    def __fetch_results_data_from_applyche(self):
        '''
        got data from emails and based on sentimental analysis say thoes emails are positive or negative or neutral
        :return:
        '''
        pass
    def __fetch_email_from_user(self):
        pass
    def next_button(self):
        pass
    def previous_button(self):
        pass
    def __plot_data(self):
        pass



class Statics(QtWidgets.QWidget):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.__get_sucess_rate_based_country()

        # Get combo box
        layout_widget = self.widget.findChild(QtWidgets.QWidget, "layoutWidget7")
        if layout_widget is None:
            print("❌ layoutWidget7 not found!")
            return

        self.combo = layout_widget.findChild(QtWidgets.QComboBox, "combo_charts")
        if self.combo is None:
            print("❌ combo_charts not found!")
            return

        # Fill combo box with keys
        self.combo.clear()
        self.combo.addItems(self.dict_info.keys())

        # Get chart area widget
        self.chart_widget = self.widget.findChild(QtWidgets.QWidget, "widget_draw_statics")
        if self.chart_widget is None:
            print("❌ widget_draw_statics not found!")
            return

        # Layout for chart area
        self.chart_layout = QVBoxLayout(self.chart_widget)

        # Connect signal
        self.combo.currentIndexChanged.connect(self.update_chart_widget)

        # Draw first chart
        self.update_chart_widget()

    def __get_sucess_rate_based_country(self):
        self.dict_info = {
            "Success rate based on country": [
                ["Canada", "USA", "Germany", "UK", "NetherLand", "Austerlia", "Austeria"],
                [10, 12, 5, 4, 8, 1, 7],
                ['pie']
            ],
            "Success rate based university rank": [
                ["1 to 50", "51 to 100", "101 to 200", "201 to 300", "301 to 400", "401 to 500", "more than 501"],
                [10, 12, 5, 4, 8, 1, 7],
                ['bar']
            ],
            "Distribution of university rank": [
                ["1 to 50", "51 to 100", "101 to 200", "201 to 300", "301 to 400", "401 to 500", "more than 501"],
                [25, 30, 50, 44, 82, 12, 34],
                ['bar']
            ],
            "Distribution of country": [
                ["Canada", "USA", "Germany", "UK", "NetherLand", "Austerlia", "Austeria"],
                [15, 18, 6, 13, 14, 54, 20],
                ['bar']
            ],
            "Answer rate based on country": [
                ["Canada", "USA", "Germany", "UK", "NetherLand", "Austerlia", "Austeria"],
                [10, 12, 5, 4, 8, 1, 7],
                ['pie']
            ],
            "Answer rate based on university rank": [
                ["1 to 50", "51 to 100", "101 to 200", "201 to 300", "301 to 400", "401 to 500", "more than 501"],
                [10, 12, 5, 4, 8, 1, 7],
                ['bar']
            ],
            "On which email you got answer": [
                ["Main Mail", "First Reminder", "Second Reminder", "Third Reminder"],
                [10, 32, 43, 22],
                ['pie']
            ]
        }

    def update_chart_widget(self):
        # Clear old chart
        while self.chart_layout.count():
            item = self.chart_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        combo_text = self.combo.currentText()
        labels, values, chart_type = self.dict_info[combo_text]
        chart_type = chart_type[0]  # 'pie' or 'bar'

        if chart_type == 'pie':
            series = QPieSeries()
            for label, value in zip(labels, values):
                series.append(label, value)
            chart = self.__create_pie_chart(series, combo_text)

        else:  # bar chart
            bar_set = QBarSet(combo_text)
            bar_set.append(values)
            series = QBarSeries()
            series.append(bar_set)
            chart = self.__create_bar_chart(series, labels, combo_text)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_layout.addWidget(chart_view)

    def __create_pie_chart(self, series, title):
        if series.slices():
            slice0 = series.slices()[0]
            slice0.setExploded(True)
            slice0.setLabelVisible(True)
            slice0.setPen(QPen(Qt.GlobalColor.darkGreen, 2))
            slice0.setBrush(Qt.GlobalColor.green)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        return chart

    def __create_bar_chart(self, series, categories, title):
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.createDefaultAxes()
        chart.axes()[0].setCategories(categories)
        chart.legend().setVisible(False)
        return chart

class Search_Professors(QtWidgets.QWidget):
    def __init__(self):
        pass
    def match_name(self):
        pass
    def __load_professors(self):
        pass
    def __load_professors_data(self):
        pass


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = MyWindow()
    window.show()
    app.exec()


