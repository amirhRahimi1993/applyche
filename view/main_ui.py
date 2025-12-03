import os
import sys
from functools import partial
from typing import Optional

from PyQt6 import QtCore
import webbrowser
import pandas as pd
import requests
from PyQt6 import QtWidgets, uic, QtGui
from PyQt6.QtCharts import QPieSeries, QChartView, QChart, QBarSeries, QBarSet
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QPainter, QPen, QTextCharFormat, QFont, QIcon, QGuiApplication
from PyQt6.QtWidgets import (
    QVBoxLayout,
    QSizePolicy,
    QMessageBox,
    QFileDialog,
    QTableWidgetItem,
    QDialog,
    QLineEdit,
    QHBoxLayout,
    QProgressBar,
    QFrame,
    QPushButton,
    QTextEdit,
    QLabel,
)

from controller.professors_controller import ProfessorsController
from middle_wares.coordinator_sending_mails import Coordinator
from events.event_bus import EventBus
from middle_wares.middle_info_pass import middle_info_pass
from api_client import ApplyCheAPIClient
from view.ui_style_manager import UIStyleManager
from utility.university_location import get_country_city_string
import resources


class WarningsDialog(QDialog):
    """Dialog to display all warnings from CSV/Excel upload"""
    def __init__(self, parent=None, warnings=None):
        super().__init__(parent)
        self.setWindowTitle("Upload Warnings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Upload Warnings")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Warnings text area
        if warnings:
            warnings_text = QTextEdit()
            warnings_text.setReadOnly(True)
            warnings_text.setPlainText("\n".join(warnings))
            warnings_text.setStyleSheet("""
                background-color: #fff3cd; 
                padding: 10px; 
                border: 1px solid #ffc107;
                color: black;
            """)
            layout.addWidget(warnings_text)
        else:
            no_warnings_label = QLabel("No warnings found.")
            no_warnings_label.setStyleSheet("color: green; font-size: 14px; padding: 10px;")
            layout.addWidget(no_warnings_label)
        
        # OK button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)


class LoadingOverlay(QtWidgets.QWidget):
    """Minimal loading screen to avoid blank UI while widgets hydrate."""

    def __init__(self):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame()
        container.setObjectName("loadingContainer")
        container.setStyleSheet(
            "QFrame#loadingContainer {background-color: #0F172A; border-radius: 18px;}"
        )

        inner = QVBoxLayout(container)
        inner.setContentsMargins(32, 28, 32, 28)
        inner.setSpacing(12)

        title = QtWidgets.QLabel("Loading ApplyChe…")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #F8FAFC; font-size: 18px; font-weight: 600;")

        subtitle = QtWidgets.QLabel("Preparing dashboard and syncing templates")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px;")

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(
            """
            QProgressBar {
                border-radius: 8px;
                background-color: #1E293B;
                height: 10px;
            }
            QProgressBar::chunk {
                border-radius: 8px;
                background-color: #38BDF8;
            }
            """
        )

        inner.addWidget(title)
        inner.addWidget(subtitle)
        inner.addWidget(self.progress)

        layout.addWidget(container)
        self.resize(420, 200)
        self._center_on_screen()

    def _center_on_screen(self):
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geometry = screen.availableGeometry()
        self.move(
            geometry.center().x() - self.width() // 2,
            geometry.center().y() - self.height() // 2,
        )


class LoginDialog(QtWidgets.QDialog):
    """Modern login dialog that authenticates via FastAPI."""

    def __init__(self, api_client: ApplyCheAPIClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.user_email: Optional[str] = None
        self.display_name: Optional[str] = None

        self.setWindowTitle("Sign in to ApplyChe")
        self.setFixedSize(420, 360)
        self.setModal(True)
        self.setWindowIcon(QIcon("../images/applyche.jpg"))
        self.setStyleSheet("background-color: #0F172A; color: #E2E8F0;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Welcome back 👋")
        title.setStyleSheet("font-size: 22px; font-weight: 600; color: #F8FAFC;")

        subtitle = QtWidgets.QLabel("Sign in with your ApplyChe account")
        subtitle.setStyleSheet("color: #94A3B8;")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        self.email_input.setClearButtonEnabled(True)
        self.email_input.setStyleSheet(self._input_style())

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self._input_style())

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: #F87171; min-height: 18px;")

        self.login_button = QPushButton("Sign in")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.setStyleSheet(self._primary_button_style())
        self.login_button.clicked.connect(self._attempt_login)

        secondary_row = QHBoxLayout()
        secondary_row.addWidget(self.status_label)
        secondary_row.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(10)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addLayout(secondary_row)
        layout.addWidget(self.login_button)

        helper = QtWidgets.QLabel("Need an account? Seed demo data or contact admin.")
        helper.setStyleSheet("color: #64748B; font-size: 12px;")
        helper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        layout.addWidget(helper)

        self.password_input.returnPressed.connect(self._attempt_login)

    def _input_style(self) -> str:
        return (
            "background-color: #1E293B; border: 1px solid #334155; "
            "border-radius: 10px; padding: 10px 14px; color: #E2E8F0;"
        )

    def _primary_button_style(self) -> str:
        return (
            "QPushButton {background-color: #2563EB; border: none; border-radius: 10px;"
            "padding: 12px 16px; font-weight: 600; color: #F8FAFC;}"
            "QPushButton:hover {background-color: #1D4ED8;}"
            "QPushButton:disabled {background-color: #1E40AF; color: #94A3B8;}"
        )

    def _attempt_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            self._show_status("Email and password are required.")
            return

        self._set_loading(True)
        try:
            response = self.api_client.login(email=email, password=password)
            self.user_email = response.get("email", email)
            self.display_name = response.get("display_name") or self.user_email
            self.accept()
        except requests.exceptions.HTTPError as exc:
            message = "Invalid email or password."
            if exc.response is not None:
                try:
                    detail = exc.response.json()
                    if isinstance(detail, dict) and detail.get("detail"):
                        message = detail["detail"]
                except ValueError:
                    pass
            self._show_status(message)
        except requests.exceptions.RequestException:
            self._show_status("Unable to reach the API server. Please try again.")
        finally:
            self._set_loading(False)

    def _set_loading(self, is_loading: bool):
        self.login_button.setDisabled(is_loading)
        if is_loading:
            QtWidgets.QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        else:
            QtWidgets.QApplication.restoreOverrideCursor()

    def _show_status(self, message: str):
        self.status_label.setText(message)


class MyWindow(QtWidgets.QMainWindow):
    def __init__(
        self,
        user_email: str,
        display_name: Optional[str] = None,
        api_client: Optional[ApplyCheAPIClient] = None,
    ):
        super().__init__()
        self.middle_info_pass = middle_info_pass()
        self.user_email = user_email
        self.display_name = display_name or user_email
        self.api_client = api_client or ApplyCheAPIClient("http://localhost:8000", timeout=5)
        uic.loadUi("../applyche_main_ui.ui", self)
        self.setWindowTitle("ApplyChe")

        # Set the window icon
        self.setWindowIcon(QIcon("../images/applyche.jpg"))  # Use .ico, .png, etc.

        self.brand_label = self.findChild(QtWidgets.QLabel, "txt_applyche")
        if self.brand_label:
            self.brand_label.setText(f"Welcome, {self.display_name}")
        if self.statusBar():
            self.statusBar().setStyleSheet("color: #CBD5F5; font-weight: 500;")
            self.statusBar().showMessage(f"Signed in as {self.user_email}")

        self.page_title_label = self.findChild(QtWidgets.QLabel, "lbl_page_title")
        self._nav_buttons = [
            getattr(self, "btn_home", None),
            getattr(self, "btn_email_template", None),
            getattr(self, "btn_professor_list", None),
            getattr(self, "btn_prepare_send_email", None),
            getattr(self, "btn_statics", None),
            getattr(self, "btn_expriences", None),
            getattr(self, "btn_results", None),
            getattr(self, "btn_profile", None),
        ]
        self._nav_buttons = [btn for btn in self._nav_buttons if btn is not None]
        self._apply_global_styles()
        self._assign_nav_icons()

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

        self.email_Temp = EmailEditor(
            self.page_email_template,
            self.middle_info_pass,
            user_email=self.user_email,
            api_client=self.api_client,
        )
        self.professorList = Professor_lists(
            self.page_professor_list,
            self.middle_info_pass,
            user_email=self.user_email,
            api_client=self.api_client
        )
        self.email_prep = Prepare_send_mail(
            self.page_prepare_send_email, 
            self.middle_info_pass,
            user_email=self.user_email,
            api_client=self.api_client
        )

        self.statics = Statics(self.page_statics)
        self.dashboard = Dashboard(
            self.page_Dashboard,
            api_client=self.api_client,
            user_email=self.user_email,
        )
        self.dashboard.report()
        self.dashboard.chart_email_answered_by_professor()
        self.dashboard.chart_email_send_remain()
        self.dashboard.chart_emaill_send_by_reminder()


        self.btn_home.clicked.connect(self.__btn_page_home_arise)
        self.btn_email_template.clicked.connect(self.__btn_page_email_template)
        self.btn_expriences.clicked.connect(self.btn_page_expriences)
        self.btn_results.clicked.connect(self.btn_page_results)
        self.btn_prepare_send_email.clicked.connect(self.btn_page_prepare_send_email)
        self.btn_statics.clicked.connect(self.btn_page_statics)
        self.btn_professor_list.clicked.connect(self.btn_page_professor_list)

        self.btn_profile.clicked.connect(self.__btn_page_profile)
        self.btn_log_out.clicked.connect(self.btn_page_logout)
        self.__btn_page_home_arise()

    def __btn_page_profile(self):
        self._set_active_nav(self.btn_profile if hasattr(self, "btn_profile") else None, "Profile", self.page_profile)
        self.stacked_content.setCurrentWidget(self.page_profile)

    def __btn_page_home_arise(self):
        self._set_active_nav(self.btn_home, "Dashboard", self.page_Dashboard)
        self.stacked_content.setCurrentWidget(self.page_Dashboard)
        self.dashboard.report()
        self.dashboard.chart_email_answered_by_professor()
        self.dashboard.chart_email_send_remain()
        self.dashboard.chart_emaill_send_by_reminder()

    def __btn_page_email_template(self):
        self._set_active_nav(self.btn_email_template, "Email Templates", self.page_email_template)
        self.stacked_content.setCurrentWidget(self.page_email_template)
        # Load templates from database when user clicks the button
        if hasattr(self, 'email_Temp') and self.email_Temp:
            self.email_Temp.load_templates_from_database()
        # Load professor list and show in table when email template page is opened
        if hasattr(self, 'professorList') and self.professorList:
            self.professorList.load_professor_list_from_db()

    def btn_page_expriences(self):
        self._set_active_nav(self.btn_expriences, "Experiences", self.page_write_your_exprience)
        self.stacked_content.setCurrentWidget(self.page_write_your_exprience)

    def btn_page_results(self):
        self._set_active_nav(self.btn_results, "Results", self.page_results)
        self.stacked_content.setCurrentWidget(self.page_results)

    def btn_page_prepare_send_email(self):
        self._set_active_nav(self.btn_prepare_send_email, "Send Email", self.page_prepare_send_email)
        self.stacked_content.setCurrentWidget(self.page_prepare_send_email)
        # Load sending rules from database when page is shown
        if hasattr(self, 'email_prep') and self.email_prep:
            self.email_prep.load_sending_rules_from_db()

    def btn_page_statics(self):
        self._set_active_nav(self.btn_statics, "Statistics", self.page_statics)
        self.stacked_content.setCurrentWidget(self.page_statics)

    def btn_page_professor_list(self):
        self._set_active_nav(self.btn_professor_list, "Professors", self.page_professor_list)
        self.stacked_content.setCurrentWidget(self.page_professor_list)
        # Load professor list from database when page is shown
        if hasattr(self, 'professorList') and self.professorList:
            self.professorList.load_professor_list_from_db()

    def btn_page_setting(self):
        self._set_active_nav(None, "Settings", self.page_settings)
        self.stacked_content.setCurrentWidget(self.page_settings)

    def btn_page_help(self):
        self._set_active_nav(None, "Help", self.page_help)
        self.stacked_content.setCurrentWidget(self.page_help)

    def btn_page_logout(self):
        reply = QMessageBox.question(
            self,
            "Sign out",
            "Are you sure you want to sign out of ApplyChe?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._relaunch_after_logout()

    def _relaunch_after_logout(self):
        """
        Close the current window and bring the LoginDialog back up.
        If the user cancels the login, exit the app.
        """
        app = QtWidgets.QApplication.instance()
        if not app:
            self.close()
            return

        self.hide()

        def _open_login():
            new_window = launch_main_window(app)
            if not new_window:
                app.quit()

            # Current window is no longer needed.
            self.deleteLater()

        QtCore.QTimer.singleShot(0, _open_login)

    def _set_active_nav(self, button, title, page_widget=None):
        if page_widget is not None and self.stacked_content.currentWidget() is not page_widget:
            self.stacked_content.setCurrentWidget(page_widget)

        for nav_button in self._nav_buttons:
            nav_button.setProperty("active", nav_button is button)
            nav_button.style().unpolish(nav_button)
            nav_button.style().polish(nav_button)

        if self.page_title_label and title:
            self.page_title_label.setText(title)

    def _apply_global_styles(self):
        """Apply global styles using the centralized style manager"""
        # Apply global stylesheet
        self.setStyleSheet(UIStyleManager.get_global_stylesheet())
        
        # Apply additional component-specific styles
        additional_styles = f"""
            #widget_main_value {{
                background-color: {UIStyleManager.COLORS['bg_primary']};
                border-radius: {UIStyleManager.RADIUS['2xl']};
            }}
            #widget_content {{
                background-color: {UIStyleManager.COLORS['bg_primary']};
                border-radius: {UIStyleManager.RADIUS['2xl']};
            }}
            #widget_header {{
                background-color: {UIStyleManager.COLORS['bg_primary']};
                border-radius: {UIStyleManager.RADIUS['xl']};
            }}
            #lineEdit {{
                {UIStyleManager.get_input_style()}
            }}
            #btn_search_professor {{
                {UIStyleManager.get_button_secondary_style()}
            }}
            #btn_notification {{
                background-color: transparent;
            }}
            #widget_menu QPushButton {{
                background-color: transparent;
                color: {UIStyleManager.COLORS['text_muted']};
                border: none;
                border-radius: {UIStyleManager.RADIUS['lg']};
                padding: {UIStyleManager.SPACING['md']} {UIStyleManager.SPACING['xl']};
                text-align: left;
                font-weight: {UIStyleManager.FONTS['weight_medium']};
                font-size: {UIStyleManager.FONTS['size_base']};
            }}
            #widget_menu QPushButton:hover {{
                background-color: rgba(37, 99, 235, 0.15);
                color: {UIStyleManager.COLORS['text_primary']};
            }}
            #widget_menu QPushButton[active="true"] {{
                background-color: {UIStyleManager.COLORS['bg_active']};
                color: {UIStyleManager.COLORS['text_primary']};
            }}
            QTextEdit {{
                {UIStyleManager.get_input_style()}
            }}
            QStackedWidget {{
                background-color: {UIStyleManager.COLORS['bg_primary']};
                border-radius: {UIStyleManager.RADIUS['xl']};
            }}
            QLabel#lbl_page_title {{
                {UIStyleManager.get_label_style('2xl', 'semibold')}
            }}
        """
        self.setStyleSheet(self.styleSheet() + additional_styles)

    def _assign_nav_icons(self):
        icon_mapping = {
            getattr(self, "btn_home", None): QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon,
            getattr(self, "btn_email_template", None): QtWidgets.QStyle.StandardPixmap.SP_FileIcon,
            getattr(self, "btn_professor_list", None): QtWidgets.QStyle.StandardPixmap.SP_DirIcon,
            getattr(self, "btn_prepare_send_email", None): QtWidgets.QStyle.StandardPixmap.SP_ArrowForward,
            getattr(self, "btn_statics", None): QtWidgets.QStyle.StandardPixmap.SP_DesktopIcon,
            getattr(self, "btn_expriences", None): QtWidgets.QStyle.StandardPixmap.SP_FileDialogInfoView,
            getattr(self, "btn_results", None): QtWidgets.QStyle.StandardPixmap.SP_DialogApplyButton,
            getattr(self, "btn_profile", None): QtWidgets.QStyle.StandardPixmap.SP_FileDialogContentsView,
        }

        for button, icon_enum in icon_mapping.items():
            if not button:
                continue
            button.setIcon(self.style().standardIcon(icon_enum))
            button.setIconSize(QtCore.QSize(20, 20))


class Dashboard:
    def __init__(
        self,
        widget,
        api_client: Optional[ApplyCheAPIClient] = None,
        user_email: str = "",
    ):
        self.widget = widget
        self.api_client = api_client
        self.user_email = user_email
        self.latest_stats = {
            "email_you_send": 0,
            "first_reminder_send": 0,
            "second_reminder_send": 0,
            "third_reminder_send": 0,
            "number_of_email_professor_answered": 0,
            "emails_remaining": 0,
        }
        self.lbl_report = self.widget.findChild(QtWidgets.QLabel, "lbl_report")
        self.report()

    def __fetch_report_from_controller(self):
        fallback = self.latest_stats.copy()
        if self.api_client and self.user_email:
            try:
                stats = self.api_client.get_dashboard_stats(self.user_email)
                return {
                    "email_you_send": stats.get("email_you_send", 0),
                    "first_reminder_send": stats.get("first_reminder_send", 0),
                    "second_reminder_send": stats.get("second_reminder_send", 0),
                    "third_reminder_send": stats.get("third_reminder_send", 0),
                    "number_of_email_professor_answered": stats.get(
                        "number_of_email_professor_answered", 0
                    ),
                    "emails_remaining": stats.get("emails_remaining", 0),
                }
            except requests.exceptions.RequestException:
                print("Info: Dashboard API not reachable, showing offline data.")
            except Exception as exc:
                print(f"Info: Failed to fetch dashboard stats: {exc}")
        return fallback

    def print_tree(self, widget, indent=0):
        print("  " * indent + f"{widget.objectName()} [{type(widget).__name__}]")
        for child in widget.children():
            self.print_tree(child, indent + 1)

    def report(self):
        info = self.__fetch_report_from_controller()
        self.latest_stats = info
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
        total_sent = sum(
            [
                self.latest_stats.get("email_you_send", 0),
                self.latest_stats.get("first_reminder_send", 0),
                self.latest_stats.get("second_reminder_send", 0),
                self.latest_stats.get("third_reminder_send", 0),
            ]
        )
        answered = self.latest_stats.get("number_of_email_professor_answered", 0)
        unanswered = max(total_sent - answered, 0)
        series.append("Answered", answered or 1)
        series.append("Awaiting Reply", unanswered or 1)
        main_widget = self.widget.findChild(QtWidgets.QWidget, "widget_main")
        pieChart_professor = main_widget.findChild(QtWidgets.QWidget, "widget_professor_answered")
        self.__draw_the_pie_chart(pieChart_professor, series, "Email send VS Email answered")

    def chart_email_send_remain(self):
        title = "Email send VS Email Remain"
        series = QPieSeries()
        total_sent = sum(
            [
                self.latest_stats.get("email_you_send", 0),
                self.latest_stats.get("first_reminder_send", 0),
                self.latest_stats.get("second_reminder_send", 0),
                self.latest_stats.get("third_reminder_send", 0),
            ]
        )
        remaining = self.latest_stats.get("emails_remaining", 0)
        series.append("Sent Emails", total_sent or 1)
        series.append("Remaining in Queue", remaining or 1)
        main_widget = self.widget.findChild(QtWidgets.QWidget, "widget_main")
        pieChart_sendvsnotsend = main_widget.findChild(QtWidgets.QWidget, "widget_send_email_remainEmail")
        self.__draw_the_pie_chart(pieChart_sendvsnotsend, series, title)

    def chart_emaill_send_by_reminder(self):
        title = "All Emails sends"
        series = QPieSeries()
        series.append("Main Emails", self.latest_stats.get("email_you_send", 0) or 1)
        series.append("Reminder 1", self.latest_stats.get("first_reminder_send", 0))
        series.append("Reminder 2", self.latest_stats.get("second_reminder_send", 0))
        series.append("Reminder 3", self.latest_stats.get("third_reminder_send", 0))
        main_widget = self.widget.findChild(QtWidgets.QWidget, "widget_main")
        pieChart_sendvsnotsend = main_widget.findChild(QtWidgets.QWidget, "widget_sended_mails")
        self.__draw_the_pie_chart(pieChart_sendvsnotsend, series, title)

class EmailEditor(QtCore.QObject):
    def __init__(
        self,
        widget,
        middle_info_pass,
        user_email: str = "user@example.com",
        api_client: Optional[ApplyCheAPIClient] = None,
    ):
        super().__init__(widget)
        self.widget = widget
        self.stacked_widget = self.widget.findChild(QtWidgets.QStackedWidget, "stacked_email_template")
        self.middle_info_pass = middle_info_pass
        self.user_email = user_email
        
        # Initialize API client (always create it, check availability when needed)
        self.api_client = api_client
        if self.api_client is None:
            try:
                self.api_client = ApplyCheAPIClient("http://localhost:8000", timeout=3)
            except Exception as exc:
                print(f"Info: API client initialization failed: {exc}")
                self.api_client = None

        if self.api_client:
            try:
                if not self.api_client.is_available():
                    print("Info: FastAPI server is not running. Templates will be saved locally only.")
            except Exception:
                pass

        # Store uploaded files per editor
        self.uploaded_files = {}  # Maps editor -> list of file_paths
        self.file_ids_map = {}  # Maps (editor, file_path) -> file_id for database files
        self.saved_templates = {}
        self.template_ids = {}  # Store template IDs for updates
        
        # Initialize file manager for email attachments
        from utility.file_manager import FileManager
        self.file_manager = FileManager()
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
                    
                    # Load file paths and file IDs
                    file_paths = template.get("file_paths", [])
                    files_data = template.get("files", [])  # List of TemplateFileResponse with file_id
                    if (file_paths or files_data) and editor:
                        # Clear existing files
                        self.uploaded_files[editor] = []
                        # Clear file IDs for this editor
                        self.file_ids_map = {k: v for k, v in self.file_ids_map.items() if k[0] != editor}
                        
                        # Use files_data if available (has file_id), otherwise fall back to file_paths
                        if files_data:
                            for file_data in files_data:
                                file_path = file_data.get("file_path") or file_data.get("file_path")
                                file_id = file_data.get("file_id")
                                if file_path and os.path.exists(file_path):
                                    file_name = os.path.basename(file_path)
                                    file_size = os.path.getsize(file_path)
                                    self.uploaded_files[editor].append(file_path)
                                    
                                    # Store file_id mapping
                                    if file_id:
                                        self.file_ids_map[(editor, file_path)] = file_id
                                    
                                    # Create attachment chip
                                    container, chip_area, _ = self.attachment_areas.get(editor, (None, None, None))
                                    if container and chip_area:
                                        chip = self._create_attachment_chip(file_name, file_path, file_size, editor, file_id)
                                        chip_area.layout().addWidget(chip)
                                        container.show()
                        else:
                            # Fallback to file_paths (no file_id available)
                            for file_path in file_paths:
                                if os.path.exists(file_path):
                                    file_name = os.path.basename(file_path)
                                    file_size = os.path.getsize(file_path)
                                    self.uploaded_files[editor].append(file_path)
                                    
                                    # Create attachment chip (no file_id)
                                    container, chip_area, _ = self.attachment_areas.get(editor, (None, None, None))
                                    if container and chip_area:
                                        chip = self._create_attachment_chip(file_name, file_path, file_size, editor, None)
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

    def load_templates_from_database(self):
        """
        Public method to load templates from database when button is clicked.
        Fetches templates from email_templates table and populates the appropriate text editors
        based on template_type:
        - template_type 0 → txt_main_subject and txt_main_mail
        - template_type 1 → txt_first_reminder
        - template_type 2 → txt_second_reminder
        - template_type 3 → txt_third_reminder
        
        HTML content is preserved with formatting (bold, italic, links) using QTextEdit's setHtml().
        """
        if not self.api_client:
            # Try to initialize API client if not available
            try:
                self.api_client = ApplyCheAPIClient("http://localhost:8000", timeout=3)
            except Exception as exc:
                QtWidgets.QMessageBox.warning(
                    None,
                    "API Not Available",
                    f"Cannot load templates: API client not available.\n{str(exc)}"
                )
                return
        
        # Check if API is available
        try:
            if not self.api_client.is_available():
                QtWidgets.QMessageBox.warning(
                    None,
                    "API Server Not Running",
                    "Cannot load templates: FastAPI server is not running.\n"
                    "Please start the server: python -m uvicorn api.main:app --reload"
                )
                return
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                None,
                "Connection Error",
                f"Cannot connect to API server.\n{str(e)}"
            )
            return
        
        # Template type mapping: 0=main, 1=first_reminder, 2=second_reminder, 3=third_reminder
        template_mapping = {
            0: ("main_template", self.txt_main_mail, self.txt_main_subject),
            1: ("first_reminder", self.txt_first_reminder, None),
            2: ("second_reminder", self.txt_second_reminder, None),
            3: ("third_reminder", self.txt_third_reminder, None)
        }
        
        try:
            # Fetch all templates at once (types 0, 1, 2, 3)
            template_types = [0, 1, 2, 3]
            templates = self.api_client.get_templates_by_types(self.user_email, template_types)
            
            if not templates:
                QtWidgets.QMessageBox.information(
                    None,
                    "No Templates Found",
                    "No email templates found in the database for your account."
                )
                return
            
            # Process each template based on template_type
            templates_loaded = 0
            for template in templates:
                template_type = template.get("template_type")
                template_key, editor, subject_field = template_mapping.get(template_type, (None, None, None))
                
                if not template_key or not editor:
                    continue
                
                # Store template ID for updates
                self.template_ids[template_key] = template.get("id")
                
                # Load HTML content into editor (QTextEdit preserves HTML formatting)
                template_body = template.get("template_body", "")
                if editor and template_body:
                    editor.setHtml(template_body)
                    templates_loaded += 1
                
                # Load subject for main template (template_type 0)
                if template_type == 0 and subject_field and self.txt_main_subject:
                    subject = template.get("subject", "")
                    if subject:
                        self.txt_main_subject.setText(subject)
                
                # Load file paths and file IDs
                file_paths = template.get("file_paths", [])
                files_data = template.get("files", [])  # List of TemplateFileResponse with file_id
                if (file_paths or files_data) and editor:
                    # Clear existing files for this editor
                    if editor in self.uploaded_files:
                        # Remove existing attachment chips
                        container, chip_area, _ = self.attachment_areas.get(editor, (None, None, None))
                        if container and chip_area:
                            # Clear all existing chips
                            while chip_area.layout().count():
                                item = chip_area.layout().takeAt(0)
                                if item.widget():
                                    item.widget().deleteLater()
                        
                        self.uploaded_files[editor] = []
                    
                    # Clear file IDs for this editor
                    self.file_ids_map = {k: v for k, v in self.file_ids_map.items() if k[0] != editor}
                    
                    # Use files_data if available (has file_id), otherwise fall back to file_paths
                    if files_data:
                        for file_data in files_data:
                            file_path = file_data.get("file_path")
                            file_id = file_data.get("file_id")
                            if file_path:
                                # Check if file exists (may be on server)
                                if os.path.exists(file_path):
                                    file_name = os.path.basename(file_path)
                                    file_size = os.path.getsize(file_path)
                                    self.uploaded_files[editor].append(file_path)
                                    
                                    # Store file_id mapping
                                    if file_id:
                                        self.file_ids_map[(editor, file_path)] = file_id
                                    
                                    # Create attachment chip
                                    container, chip_area, _ = self.attachment_areas.get(editor, (None, None, None))
                                    if container and chip_area:
                                        chip = self._create_attachment_chip(file_name, file_path, file_size, editor, file_id)
                                        chip_area.layout().addWidget(chip)
                                        container.show()
                                else:
                                    print(f"Warning: File not found: {file_path}")
                    else:
                        # Fallback to file_paths (no file_id available)
                        for file_path in file_paths:
                            if file_path and os.path.exists(file_path):
                                file_name = os.path.basename(file_path)
                                file_size = os.path.getsize(file_path)
                                self.uploaded_files[editor].append(file_path)
                                
                                # Create attachment chip (no file_id)
                                container, chip_area, _ = self.attachment_areas.get(editor, (None, None, None))
                                if container and chip_area:
                                    chip = self._create_attachment_chip(file_name, file_path, file_size, editor, None)
                                    chip_area.layout().addWidget(chip)
                                    container.show()
                    
                    # Update attachment summary
                    self._update_attachment_summary(editor)
            
            # Show success message
            if templates_loaded > 0:
                QtWidgets.QMessageBox.information(
                    None,
                    "Templates Loaded",
                    f"Successfully loaded {templates_loaded} template(s) from the database.\n\n"
                    f"Formatting (bold, italic, links) has been preserved."
                )
            else:
                QtWidgets.QMessageBox.warning(
                    None,
                    "No Content",
                    "Templates were found but had no content to load."
                )
                
        except requests.exceptions.HTTPError as e:
            error_msg = "Error loading templates from database."
            if e.response is not None:
                try:
                    detail = e.response.json()
                    if isinstance(detail, dict) and detail.get("detail"):
                        error_msg = detail["detail"]
                except ValueError:
                    pass
            QtWidgets.QMessageBox.critical(
                None,
                "API Error",
                f"{error_msg}\n\nPlease check your connection and try again."
            )
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            QtWidgets.QMessageBox.critical(
                None,
                "Connection Error",
                f"Cannot connect to API server.\n{str(e)}\n\n"
                f"Please ensure the FastAPI server is running:\n"
                f"python -m uvicorn api.main:app --reload"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                None,
                "Unexpected Error",
                f"An error occurred while loading templates:\n{str(e)}"
            )

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
        
        # Ensure all files are saved to server (convert local paths to server paths if needed)
        server_file_paths = []
        for file_path in file_paths:
            # Check if file is already in server location
            if "uploaded_folders" in str(file_path) and "email_file" in str(file_path):
                server_file_paths.append(str(file_path))
            else:
                # File is local, need to save to server
                success, msg, saved_path = self.file_manager.save_email_file(
                    source_path=str(file_path),
                    user_email=self.user_email,
                    existing_files=server_file_paths
                )
                if success and saved_path:
                    server_file_paths.append(str(saved_path))
                else:
                    QtWidgets.QMessageBox.warning(
                        editor,
                        "Save Warning",
                        f"Could not save {os.path.basename(file_path)} to server:\n{msg}"
                    )
        
        # Get subject for main template
        subject = None
        if template_key == "main_template" and self.txt_main_subject:
            subject = self.txt_main_subject.text()
            self.middle_info_pass.store_data("txt_main_subject", subject)
        
        # Save to local storage (for backward compatibility)
        self.saved_templates[template_key] = {
            "html": html_content,
            "attachments": server_file_paths.copy()
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
                            file_paths=server_file_paths  # Use server paths
                        )
                    else:
                        # Create new template
                        result = self.api_client.create_email_template(
                            user_email=self.user_email,
                            template_body=html_content,
                            template_type=template_type,
                            subject=subject,
                            file_paths=server_file_paths  # Use server paths
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
        
        # Calculate total size for display
        total_size = sum(os.path.getsize(f) for f in server_file_paths if os.path.exists(f))
        total_size_mb = total_size / (1024 * 1024)
        
        # Show success message
        if api_saved:
            QtWidgets.QMessageBox.information(
                editor,
                "Template Saved",
                f"✅ {template_key.replace('_', ' ').title()} has been saved successfully to database.\n\n"
                f"Attachments: {len(server_file_paths)} file(s)\n"
                f"Total size: {total_size_mb:.2f} MB / 60 MB",
            )
        else:
            # Saved locally only
            QtWidgets.QMessageBox.information(
                editor,
                "Template Saved Locally",
                f"✅ {template_key.replace('_', ' ').title()} has been saved locally.\n\n"
                f"Attachments: {len(server_file_paths)} file(s)\n"
                f"Total size: {total_size_mb:.2f} MB / 60 MB\n\n"
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
        """Upload and attach files to email template with size limits"""
        file_paths, _ = QtWidgets.QFileDialog.getOpenFileNames(editor, "Attach Files", "", "All Files (*)")
        if not file_paths:
            return

        # Get existing files for this editor to check total size
        existing_files = self.uploaded_files.get(editor, [])
        
        failed_files = []
        for file_path in file_paths:
            if not file_path:
                continue
            
            # Save file to server with size checks
            success, message, saved_path = self.file_manager.save_email_file(
                source_path=file_path,
                user_email=self.user_email,
                existing_files=existing_files
            )
            
            if not success:
                failed_files.append((os.path.basename(file_path), message))
                continue
            
            # File saved successfully, add to editor
            file_name = os.path.basename(saved_path)
            file_size = os.path.getsize(saved_path)
            self.uploaded_files[editor].append(str(saved_path))
            existing_files.append(str(saved_path))  # Update for next iteration
            
            container, chip_area, _ = self.attachment_areas.get(editor, (None, None, None))
            if not container or not chip_area:
                continue
            
            # New files don't have file_id until saved to database
            chip = self._create_attachment_chip(file_name, str(saved_path), file_size, editor, file_id=None)
            chip_area.layout().addWidget(chip)
            container.show()

        # Show results
        if failed_files:
            error_msg = "Some files could not be attached:\n\n"
            for filename, reason in failed_files:
                error_msg += f"• {filename}: {reason}\n"
            QtWidgets.QMessageBox.warning(editor, "Upload Warning", error_msg)
        
        if len(failed_files) < len(file_paths):
            # Some files succeeded
            success_count = len(file_paths) - len(failed_files)
            QtWidgets.QMessageBox.information(
                editor,
                "Files Attached",
                f"Successfully attached {success_count} file(s)."
            )

        self._update_attachment_summary(editor)
        editor.setFocus()

    def _create_attachment_chip(self, file_name, file_path, file_size, editor, file_id: Optional[int] = None):
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
            """Remove file from UI, move to deleted folder, and update database"""
            # Get template_id for this editor
            template_key = None
            for key, (_, ed) in {
                "main_template": (0, self.txt_main_mail),
                "first_reminder": (1, self.txt_first_reminder),
                "second_reminder": (2, self.txt_second_reminder),
                "third_reminder": (3, self.txt_third_reminder)
            }.items():
                if ed == editor:
                    template_key = key
                    break
            
            template_id = self.template_ids.get(template_key) if template_key else None
            
            # Remove from UI first
            chip.setParent(None)
            chip.deleteLater()
            if file_path in self.uploaded_files[editor]:
                self.uploaded_files[editor].remove(file_path)
            
            # Remove from file_ids_map
            if (editor, file_path) in self.file_ids_map:
                del self.file_ids_map[(editor, file_path)]
            
            self._update_attachment_summary(editor)
            
            # Move file to deleted folder instead of permanent deletion
            if os.path.exists(file_path):
                success, msg, deleted_path = self.file_manager.move_to_deleted(
                    file_path=file_path,
                    user_email=self.user_email
                )
                if success:
                    print(f"File moved to deleted folder: {deleted_path}")
                else:
                    print(f"Warning: {msg}")
            
            # Delete from database if file_id exists and API is available
            if file_id and self.api_client:
                try:
                    if self.api_client.is_available():
                        # Delete file from database (removes from template and deletes File if not used elsewhere)
                        self.api_client.delete_template_file(
                            file_id=file_id,
                            user_email=self.user_email,
                            template_id=template_id  # Only remove from this template
                        )
                        print(f"File {file_id} deleted from database")
                    else:
                        print("API not available - file removed from UI only")
                except requests.exceptions.HTTPError as e:
                    error_msg = f"Failed to delete file from database"
                    if e.response is not None:
                        try:
                            detail = e.response.json()
                            if isinstance(detail, dict) and detail.get("detail"):
                                error_msg = detail["detail"]
                        except ValueError:
                            pass
                    QtWidgets.QMessageBox.warning(
                        editor,
                        "Delete Warning",
                        f"{error_msg}\n\nFile removed from UI but may still exist in database."
                    )
                except Exception as e:
                    print(f"Error deleting file from database: {e}")
                    QtWidgets.QMessageBox.warning(
                        editor,
                        "Delete Warning",
                        f"File removed from UI but failed to delete from database:\n{str(e)}"
                    )

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
                        # New files from drag-and-drop don't have file_id until saved
                        chip = self._create_attachment_chip(file_name, f, file_size, editor, file_id=None)
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
    def __init__(self, widget, middle_info_pass, user_email: str = "", api_client: Optional[ApplyCheAPIClient] = None):
        super().__init__(widget)  # <-- important
        bus = EventBus()
        self.middle_info_pass = middle_info_pass
        self.user_email = user_email
        self.api_client = api_client
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

        # Note: Data will be loaded from database when page is shown (in btn_page_prepare_send_email)
        # This allows the page to always show the latest data from the database



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
        
        # Apply modern UI/UX styling to page_email_info
        self._apply_email_info_styles()
        
    def load_sending_rules_from_db(self):
        """Load sending rules from database and populate UI elements"""
        if not self.user_email:
            print("Warning: User email not set, cannot load sending rules from database")
            return
        
        if not self.api_client:
            # Try to initialize API client if not available
            try:
                self.api_client = ApplyCheAPIClient("http://localhost:8000", timeout=3)
            except Exception as e:
                print(f"Warning: Could not create API client: {e}")
                return
        
        # Check if API is available
        try:
            if not self.api_client.is_available():
                print("Info: API server is not running. Cannot load sending rules from database.")
                return
        except Exception:
            print("Info: Could not check API availability. Cannot load sending rules from database.")
            return
        
        try:
            # Fetch sending rules from database
            rules = self.api_client.get_sending_rules(self.user_email)
            
            # Map database fields to UI elements
            # Text fields
            field_mapping = {
                "txt_number_of_main_mails": rules.get("main_mail_number", 0),
                "txt_number_of_first_reminder": rules.get("reminder_one", 0),
                "txt_number_of_second_reminder": rules.get("reminder_two", 0),
                "txt_number_of_third_reminder": rules.get("reminder_three", 0),
                "txt_number_of_email_per_university": rules.get("max_email_per_university", -1),
                "txt_preiod_between_reminders": rules.get("period_between_reminders", 0),
            }
            
            # Populate text fields
            for field_name, value in field_mapping.items():
                line_edit = self.widget.findChild(QtWidgets.QLineEdit, field_name)
                if line_edit:
                    line_edit.setText(str(value))
            
            # Handle time fields (convert from TIME format "HH:MM:SS" or "HH:MM:SS+00" to "HH:MM")
            start_time = rules.get("start_time_send")
            if start_time:
                # Extract HH:MM from time string (could be "09:00:00" or "09:00:00+00:00")
                time_str = str(start_time).strip()
                # Remove timezone info if present (e.g., "+00:00" or "+00")
                if "+" in time_str:
                    time_str = time_str.split("+")[0]
                elif "-" in time_str and time_str.count("-") > 1:
                    # Handle negative timezone (unlikely but possible)
                    parts = time_str.rsplit("-", 1)
                    if len(parts) == 2:
                        time_str = parts[0]
                
                # Split by ":" and take first two parts (HH:MM)
                time_parts = time_str.split(":")
                if len(time_parts) >= 2:
                    formatted_time = f"{time_parts[0].zfill(2)}:{time_parts[1].zfill(2)}"
                    start_time_edit = self.widget.findChild(QtWidgets.QLineEdit, "txt_start_time")
                    if start_time_edit:
                        start_time_edit.setText(formatted_time)
            
            end_time = rules.get("end_time_send")
            if end_time:
                # Extract HH:MM from time string
                time_str = str(end_time).strip()
                # Remove timezone info if present
                if "+" in time_str:
                    time_str = time_str.split("+")[0]
                elif "-" in time_str and time_str.count("-") > 1:
                    parts = time_str.rsplit("-", 1)
                    if len(parts) == 2:
                        time_str = parts[0]
                
                # Split by ":" and take first two parts (HH:MM)
                time_parts = time_str.split(":")
                if len(time_parts) >= 2:
                    formatted_time = f"{time_parts[0].zfill(2)}:{time_parts[1].zfill(2)}"
                    end_time_edit = self.widget.findChild(QtWidgets.QLineEdit, "txt_end_time")
                    if end_time_edit:
                        end_time_edit.setText(formatted_time)
            
            # Handle checkboxes
            local_prof_time = rules.get("local_professor_time", False)
            is_prof_local_checkbox = self.widget.findChild(QtWidgets.QCheckBox, "is_professor_local_time")
            if is_prof_local_checkbox:
                is_prof_local_checkbox.setChecked(bool(local_prof_time))
            
            send_working_day = rules.get("send_working_day_only", False)
            is_send_working_day_widget = self.widget.findChild(QtWidgets.QCheckBox, "is_send_working_day_only")
            if is_send_working_day_widget:
                is_send_working_day_widget.setChecked(bool(send_working_day))
            else:
                # Fallback: try as QWidget if checkbox not found
                widget = self.widget.findChild(QtWidgets.QWidget, "is_send_working_day_only")
                if widget and hasattr(widget, 'setChecked'):
                    widget.setChecked(bool(send_working_day))
            
            print(f"Sending rules loaded successfully for {self.user_email}")
            
        except requests.exceptions.HTTPError as e:
            # 404 means no rules exist yet - that's okay, user can create new ones
            if e.response is not None and e.response.status_code == 404:
                print("Info: No sending rules found in database. User can create new rules.")
            else:
                error_msg = "Error loading sending rules from database."
                if e.response is not None:
                    try:
                        detail = e.response.json()
                        if isinstance(detail, dict) and detail.get("detail"):
                            error_msg = detail["detail"]
                    except ValueError:
                        pass
                print(f"Warning: {error_msg}")
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"Info: Cannot connect to API server. Cannot load sending rules: {str(e)}")
        except Exception as e:
            print(f"Warning: Unexpected error loading sending rules: {str(e)}")
    
    def __get_data_from_user(self):
        self.txt_number_of_main_mails = self.widget.findChild(QtWidgets.QLineEdit, "txt_number_of_main_mails").text()
        self.txt_number_of_first_reminder = self.widget.findChild(QtWidgets.QLineEdit, "txt_number_of_first_reminder").text()
        self.txt_number_of_second_reminder = self.widget.findChild(QtWidgets.QLineEdit,"txt_number_of_second_reminder").text()
        self.txt_number_of_third_reminder = self.widget.findChild(QtWidgets.QLineEdit, "txt_number_of_third_reminder").text()
        self.txt_number_of_email_per_university = self.widget.findChild(QtWidgets.QLineEdit, "txt_number_of_email_per_university").text()
        self.txt_start_time = self.widget.findChild(QtWidgets.QLineEdit,"txt_start_time").text()
        self.txt_end_time = self.widget.findChild(QtWidgets.QLineEdit,"txt_end_time").text()
        self.txt_period_day = self.widget.findChild(QtWidgets.QLineEdit,"txt_preiod_between_reminders").text()
        is_send_working_day_widget = self.widget.findChild(QtWidgets.QCheckBox, "is_send_working_day_only")
        if is_send_working_day_widget:
            self.is_send_working_day_only = is_send_working_day_widget.isChecked()
        else:
            # Fallback: try as QWidget if checkbox not found
            widget = self.widget.findChild(QtWidgets.QWidget, "is_send_working_day_only")
            self.is_send_working_day_only = widget.isChecked() if widget and hasattr(widget, 'isChecked') else False
        
        is_prof_local_widget = self.widget.findChild(QtWidgets.QCheckBox, "is_professor_local_time")
        self.is_professor_local_time = is_prof_local_widget.isChecked() if is_prof_local_widget else False
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
        
        # Validate txt_number_of_main_mails, txt_number_of_first_reminder, 
        # txt_number_of_second_reminder, txt_number_of_third_reminder (must be integer >= 0)
        reminder_fields = {
            "txt_number_of_main_mails": self.txt_number_of_main_mails,
            "txt_number_of_first_reminder": self.txt_number_of_first_reminder,
            "txt_number_of_second_reminder": self.txt_number_of_second_reminder,
            "txt_number_of_third_reminder": self.txt_number_of_third_reminder
        }
        
        for field_name, field_value in reminder_fields.items():
            if not field_value or field_value.strip() == "":
                QMessageBox.critical(
                    None,
                    "Validation Error",
                    f"{field_name.replace('_', ' ').title()} is required.",
                    QMessageBox.StandardButton.Ok
                )
                return
            
            try:
                value = int(field_value.strip())
                if value < 0:
                    QMessageBox.critical(
                        None,
                        "Validation Error",
                        f"{field_name.replace('_', ' ').title()} must be an integer greater than or equal to 0.",
                        QMessageBox.StandardButton.Ok
                    )
                    return
            except ValueError:
                QMessageBox.critical(
                    None,
                    "Validation Error",
                    f"{field_name.replace('_', ' ').title()} must be an integer.",
                    QMessageBox.StandardButton.Ok
                )
                return
        
        # Validate txt_preiod_between_reminders (must be integer > 0)
        if not self.txt_period_day or self.txt_period_day.strip() == "":
            QMessageBox.critical(
                None,
                "Validation Error",
                "Period between reminders is required.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        try:
            period_value = int(self.txt_period_day.strip())
            if period_value <= 0:
                QMessageBox.critical(
                    None,
                    "Validation Error",
                    "Period between reminders must be an integer greater than 0.",
                    QMessageBox.StandardButton.Ok
                )
                return
        except ValueError:
            QMessageBox.critical(
                None,
                "Validation Error",
                "Period between reminders must be an integer.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        # Validate txt_number_of_email_per_university (must be > 0 or -1)
        if not self.txt_number_of_email_per_university or self.txt_number_of_email_per_university.strip() == "":
            QMessageBox.critical(
                None,
                "Validation Error",
                "Number of emails per university is required.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        try:
            email_per_uni_value = int(self.txt_number_of_email_per_university.strip())
            if email_per_uni_value != -1 and email_per_uni_value <= 0:
                QMessageBox.critical(
                    None,
                    "Validation Error",
                    "Number of emails per university must be greater than 0 or -1.",
                    QMessageBox.StandardButton.Ok
                )
                return
        except ValueError:
            QMessageBox.critical(
                None,
                "Validation Error",
                "Number of emails per university must be an integer.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        # Validate time format (integer:integer for hour:minute)
        if not self.txt_start_time or not self.txt_end_time:
            QMessageBox.critical(
                None,
                "Validation Error",
                "Start time and end time are required.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        self.time_send["txt_start_time"] = self.txt_start_time.split(":")
        self.time_send["txt_end_time"] = self.txt_end_time.split(":")
        
        if self.__check_time() == False:
            return
        
        # All validations passed, save to database
        self._save_sending_rules_to_db()
        
        self.prof_local_time = self.is_professor_local_time
        self.main_widget.setCurrentWidget(self.page_email_info)

    def _save_sending_rules_to_db(self):
        """Save validated sending rules to database"""
        if not self.user_email:
            print("Warning: User email not set, cannot save sending rules to database")
            return
        
        if not self.api_client:
            # Try to initialize API client if not available
            try:
                self.api_client = ApplyCheAPIClient("http://localhost:8000", timeout=3)
            except Exception as e:
                print(f"Warning: Could not create API client: {e}")
                return
        
        # Check if API is available
        try:
            if not self.api_client.is_available():
                print("Warning: API server is not running. Sending rules will not be saved to database.")
                return
        except Exception:
            print("Warning: Could not check API availability. Sending rules will not be saved to database.")
            return
        
        # Convert time strings to HH:MM:SS format for database
        # Pad hours and minutes to ensure 2-digit format
        start_hour = str(self.time_send['txt_start_time'][0]).zfill(2)
        start_min = str(self.time_send['txt_start_time'][1]).zfill(2)
        end_hour = str(self.time_send['txt_end_time'][0]).zfill(2)
        end_min = str(self.time_send['txt_end_time'][1]).zfill(2)
        
        start_time_str = f"{start_hour}:{start_min}:00"
        end_time_str = f"{end_hour}:{end_min}:00"
        
        # Prepare data for API
        rules_data = {
            "main_mail_number": int(self.txt_number_of_main_mails.strip()),
            "reminder_one": int(self.txt_number_of_first_reminder.strip()),
            "reminder_two": int(self.txt_number_of_second_reminder.strip()),
            "reminder_three": int(self.txt_number_of_third_reminder.strip()),
            "period_between_reminders": int(self.txt_period_day.strip()),
            "max_email_per_university": int(self.txt_number_of_email_per_university.strip()),
            "local_professor_time": self.is_professor_local_time,
            "send_working_day_only": self.is_send_working_day_only,
            "start_time_send": start_time_str,
            "end_time_send": end_time_str
        }
        
        try:
            self.api_client.create_sending_rules(
                user_email=self.user_email,
                **rules_data
            )
            print(f"Sending rules saved successfully for {self.user_email}")
        except requests.exceptions.HTTPError as e:
            error_msg = "Error saving sending rules to database."
            if e.response is not None:
                try:
                    detail = e.response.json()
                    if isinstance(detail, dict) and detail.get("detail"):
                        error_msg = detail["detail"]
                except ValueError:
                    pass
            QMessageBox.warning(
                self.widget,
                "Save Warning",
                f"{error_msg}\n\nRules validated but not saved to database."
            )
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            QMessageBox.warning(
                self.widget,
                "Connection Error",
                f"Cannot connect to API server.\n{str(e)}\n\nRules validated but not saved to database."
            )
        except Exception as e:
            QMessageBox.warning(
                self.widget,
                "Unexpected Error",
                f"An error occurred while saving sending rules:\n{str(e)}\n\nRules validated but not saved to database."
            )

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

    def _apply_email_info_styles(self):
        """Apply modern UI/UX styling to page_email_info elements using style manager"""
        if not self.page_email_info:
            return
        
        # Style input fields using style manager
        txt_email = self.page_email_info.findChild(QtWidgets.QLineEdit, "txt_email")
        if txt_email:
            txt_email.setStyleSheet(UIStyleManager.get_input_style())
            txt_email.setPlaceholderText("Your email address")
        
        txt_password = self.page_email_info.findChild(QtWidgets.QLineEdit, "txt_password")
        if txt_password:
            txt_password.setStyleSheet(UIStyleManager.get_input_style())
            txt_password.setPlaceholderText("Your email password")
            txt_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        
        # Style buttons using style manager
        if self.btn_send_real_mail:
            self.btn_send_real_mail.setStyleSheet(UIStyleManager.get_button_primary_style())
            self.btn_send_real_mail.setCursor(Qt.CursorShape.PointingHandCursor)
        
        if self.btn_send_test_mail:
            self.btn_send_test_mail.setStyleSheet(UIStyleManager.get_button_secondary_style())
            self.btn_send_test_mail.setCursor(Qt.CursorShape.PointingHandCursor)
        
        if self.btn_email_info_back:
            self.btn_email_info_back.setStyleSheet(UIStyleManager.get_button_tertiary_style())
            self.btn_email_info_back.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Style labels using style manager
        for label in self.page_email_info.findChildren(QtWidgets.QLabel):
            if label.objectName():
                obj_name = label.objectName()
                # Determine label size based on object name
                if "email_info_notice" in obj_name:
                    # Important notice - larger
                    label.setStyleSheet(UIStyleManager.get_label_style('lg', 'semibold'))
                elif "email_field" in obj_name or "password_field" in obj_name:
                    # Field labels - medium size
                    label.setStyleSheet(UIStyleManager.get_label_style('lg', 'semibold'))
                elif "label" in obj_name.lower():
                    # Default labels
                    label.setStyleSheet(UIStyleManager.get_label_style('base', 'medium'))
    
    def __load_data_from_DB(self, id):
        """Legacy method - kept for backward compatibility"""
        # This method is no longer used - data is loaded via load_sending_rules_from_db()
        return -1


class FetchUniversityDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("Fetch_university.ui", self)
class Professor_lists():
    def __init__(self, widget, middle_info_pass, user_email: str = "", api_client: Optional[ApplyCheAPIClient] = None):
        self.middle_info_pass = middle_info_pass
        self.user_email = user_email
        self.api_client = api_client
        
        # Initialize file manager
        from utility.file_manager import FileManager
        self.file_manager = FileManager()
        
        # This assumes you've already loaded your UI with tbl_professors_list and btn_local_upload
        self.widget = widget.findChild(QtWidgets.QWidget, "page_professors")
        self.tbl_professors_list: QtWidgets.QTableWidget = self.widget.findChild(QtWidgets.QTableWidget, "tbl_professors_list")
        self.btn_local_upload: QtWidgets.QPushButton = self.widget.findChild(QtWidgets.QPushButton, "btn_local_upload")
        self.btn_download_from_applyche: QtWidgets.QPushButton = self.widget.findChild(QtWidgets.QPushButton, "btn_download_from_applyche")

        # Connect button to upload function
        self.btn_local_upload.clicked.connect(self.upload_data_from_local)
        self.btn_download_from_applyche.clicked.connect(self.popup_the_download_list)
        
        # Load professor list from database if available
        self.load_professor_list_from_db()

    def popup_the_download_list(self):
        dialog = FetchUniversityDialog()
        dialog.exec()
    
    def load_professor_list_from_db(self):
        """Load professor list from database and display in table"""
        if not self.user_email or not self.api_client:
            return
        
        try:
            if not self.api_client.is_available():
                return  # API not available, skip loading
            
            professor_list = self.api_client.get_professor_list(self.user_email)
            if professor_list and professor_list.get("file_path"):
                file_path = professor_list["file_path"]
                
                # Check if file exists
                if os.path.exists(file_path):
                    try:
                        P = ProfessorsController(file_path)
                        values = P.send_professor_info()
                        df = values["df"]
                        headers = values["header"]
                        nans = values["nans"]
                        self.middle_info_pass.store_data("professor_list", df)
                        
                        df.columns = df.columns.str.strip().str.lower()
                        self._populate_table(df)
                    except Exception as e:
                        print(f"Error loading professor list from {file_path}: {e}")
        except Exception as e:
            print(f"Error loading professor list from database: {e}")
    
    def upload_data_from_local(self):
        """Upload CSV/Excel file with file size limits, folder cleanup, and rate limiting"""
        warnings = []  # Collect all warnings here
        
        if not self.user_email:
            QMessageBox.warning(
                self.widget,
                "User Not Set",
                "User email is not set. Cannot upload file."
            )
            return

        # Let user choose file
        file_path, _ = QFileDialog.getOpenFileName(
            self.widget,
            "Select CSV or Excel File",
            "",
            "CSV Files (*.csv);;Excel Files (*.xls *.xlsx)"
        )
        if not file_path:  # If user cancels
            return

        # Check rate limit
        allowed, rate_msg = self.file_manager.check_rate_limit(self.user_email)
        if not allowed:
            warnings.append(f"Upload Limit Reached: {rate_msg}")
            dialog = WarningsDialog(self.widget, warnings)
            dialog.exec()
            return

        # Check file size
        valid_size, size_msg = self.file_manager.check_file_size(file_path)
        if not valid_size:
            warnings.append(f"File Too Large: {size_msg}")
            dialog = WarningsDialog(self.widget, warnings)
            dialog.exec()
            return

        # Process file first to validate it
        try:
            P = ProfessorsController(file_path)
            values = P.send_professor_info()
            df = values["df"]
            headers = values["header"]
            nans = values["nans"]
        except Exception as e:
            warnings.append(f"Failed to read file: {str(e)}")
            dialog = WarningsDialog(self.widget, warnings)
            dialog.exec()
            return

        # Check for professor_email column (case-insensitive)
        professor_email_col = None
        for col in df.columns:
            if col.lower().strip() == 'professor_email':
                professor_email_col = col
                break
        
        if professor_email_col is None:
            QMessageBox.critical(
                self.widget,
                "Missing Required Column",
                "There is no professor_email column. Please create (or rename) a column called professor_email containing professor emails."
            )
            return

        # Check for country_city column and validate format
        country_city_col = None
        for col in df.columns:
            if col.lower().strip() == 'country_city':
                country_city_col = col
                break
        
        country_city_warning = None
        if country_city_col is None:
            # Column is missing
            country_city_warning = "If country_city is empty I cannot send email based on professor local time and I have to send email based on your local time."
        else:
            # Validate format: should be "country/city"
            invalid_rows = []
            empty_rows = []
            for idx, row in df.iterrows():
                value = row[country_city_col]
                if pd.notna(value) and value:
                    value_str = str(value).strip()
                    # Check if format is "country/city" (contains exactly one forward slash)
                    if '/' not in value_str or value_str.count('/') != 1:
                        invalid_rows.append(idx + 1)  # +1 for 1-based row numbers
                else:
                    empty_rows.append(idx + 1)
            
            if invalid_rows or empty_rows:
                warning_parts = []
                if invalid_rows:
                    warning_parts.append(f"Found invalid format in row(s): {', '.join(map(str, invalid_rows[:10]))}"
                                       f"{' and more...' if len(invalid_rows) > 10 else ''}")
                if empty_rows:
                    warning_parts.append(f"Found empty values in row(s): {', '.join(map(str, empty_rows[:10]))}"
                                       f"{' and more...' if len(empty_rows) > 10 else ''}")
                
                country_city_warning = f"If country_city is empty I cannot send email based on professor local time and I have to send email based on your local time.\n\n" + "\n".join(warning_parts) + "\n\nPlease ensure the format is 'country/city' (e.g., 'iran/tehran', 'usa/new york')."
        
        # Add country_city warning to warnings list (not as popup, as per user request)
        if country_city_warning:
            warnings.append(country_city_warning)

        # Add required columns if they don't exist
        required_columns = {
            'main_mail_time': None,
            'reminder_one_time': None,
            'reminder_second_time': None,
            'reminder_thrid_time': None,
            'message_id': None
        }
        
        for col_name in required_columns.keys():
            if col_name not in df.columns:
                df[col_name] = None

        # Add country_city_applyche column if it doesn't exist
        if 'country_city_applyche' not in df.columns:
            df['country_city_applyche'] = None

        # Populate country_city_applyche based on professor_email
        for idx, row in df.iterrows():
            email = row[professor_email_col]
            if pd.notna(email) and email:
                country_city = get_country_city_string(str(email))
                df.at[idx, 'country_city_applyche'] = country_city

        # Validate that first row is header (pandas requirement)
        if len(df.columns) == 0:
            warnings.append("File must have a header row as the first row. Please ensure your CSV/Excel file has column names in the first row.")
            dialog = WarningsDialog(self.widget, warnings)
            dialog.exec()
            return
        
        # Save modified dataframe back to the original file in raw, simple format
        try:
            if file_path.endswith('.xlsx'):
                # Save as raw Excel without formatting
                df.to_excel(file_path, index=False, engine='openpyxl', header=True)
            elif file_path.endswith('.csv'):
                # Save as raw CSV without formatting
                df.to_csv(file_path, index=False, header=True, encoding='utf-8')
            elif file_path.endswith('.xls'):
                # For .xls files, convert to xlsx format (raw)
                new_path = file_path.replace('.xls', '.xlsx')
                df.to_excel(new_path, index=False, engine='openpyxl', header=True)
                if new_path != file_path:
                    file_path = new_path
        except Exception as e:
            warnings.append(f"Failed to save modifications to file: {str(e)}. Continuing with original file...")

        # Collect warnings for empty columns
        for k in nans.keys():
            warnings.append(f"Found {len(nans[k])} empty value(s) in '{k}' column. This may affect your email process!")

        # Save file to uploaded_folders/{user_email}/professor_list/
        success, save_msg, saved_path = self.file_manager.save_file(
            source_path=file_path,
            user_email=self.user_email,
            subfolder="professor_list"
        )

        if not success:
            warnings.append(f"Save Failed: {save_msg}")
            dialog = WarningsDialog(self.widget, warnings)
            dialog.exec()
            return

        # Ensure saved_path has the modified dataframe (save again to be safe) in raw format
        if saved_path:
            try:
                if str(saved_path).endswith('.xlsx'):
                    # Save as raw Excel without formatting
                    df.to_excel(str(saved_path), index=False, engine='openpyxl', header=True)
                elif str(saved_path).endswith('.csv'):
                    # Save as raw CSV without formatting
                    df.to_csv(str(saved_path), index=False, header=True, encoding='utf-8')
            except Exception as e:
                print(f"Warning: Could not update saved file with modifications: {e}")

        # Save to database via API
        db_saved = False
        if self.api_client:
            try:
                if self.api_client.is_available():
                    # Upsert professor list (one row per user)
                    self.api_client.upsert_professor_list(
                        user_email=self.user_email,
                        file_path=str(saved_path)
                    )
                    db_saved = True
                else:
                    print("API not available - file saved locally but not to database")
            except Exception as e:
                print(f"Error saving to database: {e}")
                warnings.append(f"File saved locally but failed to save to database: {str(e)}")

        # Store in memory for immediate use
        df.columns = df.columns.str.strip().str.lower()
        self.middle_info_pass.store_data("professor_list", df)

        # Populate table
        self._populate_table(df)

        # Show warnings dialog if there are any warnings, otherwise show success message
        if warnings:
            dialog = WarningsDialog(self.widget, warnings)
            dialog.exec()
        else:
            # Show success popup with green OK button
            success_msg = QMessageBox(self.widget)
            success_msg.setWindowTitle("Upload Successful")
            success_msg.setText("Your CSV/Excel satisfied all requirements!")
            success_msg.setIcon(QMessageBox.Icon.Information)
            success_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            # Style the OK button to be green
            ok_button = success_msg.button(QMessageBox.StandardButton.Ok)
            if ok_button:
                ok_button.setStyleSheet("""
                    QPushButton {
                        background-color: #28a745;
                        color: white;
                        padding: 8px 20px;
                        border-radius: 4px;
                        font-size: 14px;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #218838;
                    }
                """)
            success_msg.exec()

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

def launch_main_window(app: QtWidgets.QApplication) -> Optional[QtWidgets.QMainWindow]:
    api_client = ApplyCheAPIClient("http://localhost:8000", timeout=5)
    login_dialog = LoginDialog(api_client)
    result = login_dialog.exec()
    if result != QDialog.DialogCode.Accepted or not login_dialog.user_email:
        return None

    loading = LoadingOverlay()
    loading.show()
    QtWidgets.QApplication.processEvents()
    try:
        window = MyWindow(
            user_email=login_dialog.user_email,
            display_name=login_dialog.display_name,
            api_client=api_client,
        )
    finally:
        loading.close()

    window.show()
    return window


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = launch_main_window(app)
    if not window:
        sys.exit(0)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


