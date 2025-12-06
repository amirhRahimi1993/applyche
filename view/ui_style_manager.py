"""
UI Style Manager - Centralized styling for ApplyChe application
Follows separation of concerns: UI structure in .ui file, styling in Python
"""
from PyQt6.QtCore import Qt
from typing import Dict, Optional


class UIStyleManager:
    """Centralized style management for the ApplyChe application"""
    
    # Color Palette - Modern Dark Theme
    COLORS = {
        # Backgrounds
        'bg_primary': '#0F172A',      # Main background
        'bg_secondary': '#1E293B',    # Card/panel background
        'bg_tertiary': '#334155',      # Input fields, borders
        'bg_hover': '#475569',         # Hover states
        'bg_active': '#2563EB',        # Active/selected states
        
        # Text
        'text_primary': '#F8FAFC',    # Primary text
        'text_secondary': '#E2E8F0',  # Secondary text
        'text_muted': '#94A3B8',      # Muted/disabled text
        'text_accent': '#60A5FA',     # Accent text
        
        # Semantic Colors
        'success': '#10B981',          # Success/green
        'success_hover': '#059669',
        'success_pressed': '#047857',
        'warning': '#F59E0B',          # Warning/amber
        'error': '#EF4444',            # Error/red
        'info': '#2563EB',             # Info/blue
        'info_hover': '#1D4ED8',
        'info_pressed': '#1E40AF',
        
        # Borders
        'border_default': '#334155',
        'border_hover': '#475569',
        'border_focus': '#60A5FA',
        
        # Shadows (for elevation)
        'shadow_sm': 'rgba(0, 0, 0, 0.1)',
        'shadow_md': 'rgba(0, 0, 0, 0.15)',
        'shadow_lg': 'rgba(0, 0, 0, 0.2)',
    }
    
    # Typography
    FONTS = {
        'family_primary': 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        'size_xs': '11px',
        'size_sm': '12px',
        'size_base': '14px',
        'size_lg': '16px',
        'size_xl': '18px',
        'size_2xl': '20px',
        'size_3xl': '24px',
        'size_4xl': '36px',
        'weight_normal': '400',
        'weight_medium': '500',
        'weight_semibold': '600',
        'weight_bold': '700',
    }
    
    # Spacing
    SPACING = {
        'xs': '4px',
        'sm': '8px',
        'md': '12px',
        'lg': '16px',
        'xl': '20px',
        '2xl': '24px',
        '3xl': '32px',
    }
    
    # Border Radius
    RADIUS = {
        'sm': '6px',
        'md': '10px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '20px',
        'full': '9999px',
    }
    
    @classmethod
    def get_input_style(cls, focused: bool = False) -> str:
        """Get style for input fields (QLineEdit, QTextEdit, QComboBox)"""
        border_color = cls.COLORS['border_focus'] if focused else cls.COLORS['border_default']
        return f"""
            background-color: {cls.COLORS['bg_secondary']};
            border: 1px solid {border_color};
            border-radius: {cls.RADIUS['md']};
            padding: {cls.SPACING['lg']} {cls.SPACING['xl']};
            color: {cls.COLORS['text_primary']};
            font-size: {cls.FONTS['size_base']};
            font-family: {cls.FONTS['family_primary']};
            min-height: 44px;
        """
    
    @classmethod
    def get_button_primary_style(cls) -> str:
        """Get style for primary action buttons"""
        return f"""
            QPushButton {{
                background-color: {cls.COLORS['success']};
                border: none;
                border-radius: {cls.RADIUS['md']};
                padding: {cls.SPACING['lg']} {cls.SPACING['2xl']};
                font-weight: {cls.FONTS['weight_semibold']};
                font-size: {cls.FONTS['size_base']};
                color: #FFFFFF;
                min-height: 44px;
            }}
            QPushButton:hover {{
                background-color: {cls.COLORS['success_hover']};
            }}
            QPushButton:pressed {{
                background-color: {cls.COLORS['success_pressed']};
            }}
            QPushButton:disabled {{
                background-color: {cls.COLORS['bg_tertiary']};
                color: {cls.COLORS['text_muted']};
            }}
        """
    
    @classmethod
    def get_button_secondary_style(cls) -> str:
        """Get style for secondary action buttons"""
        return f"""
            QPushButton {{
                background-color: {cls.COLORS['info']};
                border: none;
                border-radius: {cls.RADIUS['md']};
                padding: {cls.SPACING['lg']} {cls.SPACING['2xl']};
                font-weight: {cls.FONTS['weight_semibold']};
                font-size: {cls.FONTS['size_base']};
                color: #FFFFFF;
                min-height: 44px;
            }}
            QPushButton:hover {{
                background-color: {cls.COLORS['info_hover']};
            }}
            QPushButton:pressed {{
                background-color: {cls.COLORS['info_pressed']};
            }}
            QPushButton:disabled {{
                background-color: {cls.COLORS['bg_tertiary']};
                color: {cls.COLORS['text_muted']};
            }}
        """
    
    @classmethod
    def get_button_tertiary_style(cls) -> str:
        """Get style for tertiary/ghost buttons"""
        return f"""
            QPushButton {{
                background-color: {cls.COLORS['bg_tertiary']};
                border: 1px solid {cls.COLORS['border_default']};
                border-radius: {cls.RADIUS['md']};
                padding: {cls.SPACING['md']} {cls.SPACING['xl']};
                font-weight: {cls.FONTS['weight_medium']};
                font-size: {cls.FONTS['size_base']};
                color: {cls.COLORS['text_secondary']};
                min-height: 40px;
            }}
            QPushButton:hover {{
                background-color: {cls.COLORS['bg_hover']};
                border-color: {cls.COLORS['border_hover']};
            }}
            QPushButton:pressed {{
                background-color: {cls.COLORS['bg_secondary']};
            }}
        """
    
    @classmethod
    def get_label_style(cls, size: str = 'base', weight: str = 'medium') -> str:
        """Get style for labels"""
        font_size = cls.FONTS.get(f'size_{size}', cls.FONTS['size_base'])
        font_weight = cls.FONTS.get(f'weight_{weight}', cls.FONTS['weight_medium'])
        return f"""
            color: {cls.COLORS['text_secondary']};
            font-size: {font_size};
            font-weight: {font_weight};
            font-family: {cls.FONTS['family_primary']};
        """
    
    @classmethod
    def get_card_style(cls) -> str:
        """Get style for card/panel containers"""
        return f"""
            background-color: {cls.COLORS['bg_secondary']};
            border: 1px solid {cls.COLORS['border_default']};
            border-radius: {cls.RADIUS['xl']};
            padding: {cls.SPACING['2xl']};
        """
    
    @classmethod
    def get_global_stylesheet(cls) -> str:
        """Get global stylesheet for the entire application"""
        return f"""
            QMainWindow {{
                background-color: {cls.COLORS['bg_primary']};
                color: {cls.COLORS['text_primary']};
            }}
            
            QWidget {{
                font-family: {cls.FONTS['family_primary']};
                font-size: {cls.FONTS['size_base']};
            }}
            
            QScrollBar:vertical {{
                background: {cls.COLORS['bg_secondary']};
                width: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {cls.COLORS['bg_tertiary']};
                border-radius: 6px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {cls.COLORS['bg_hover']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background: {cls.COLORS['bg_secondary']};
                height: 12px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal {{
                background: {cls.COLORS['bg_tertiary']};
                border-radius: 6px;
                min-width: 30px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background: {cls.COLORS['bg_hover']};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """
    
    @classmethod
    def apply_styles_to_widget(cls, widget, widget_type: str, **kwargs):
        """Apply appropriate style to a widget based on its type"""
        from PyQt6 import QtWidgets
        
        if isinstance(widget, QtWidgets.QLineEdit):
            widget.setStyleSheet(cls.get_input_style())
        elif isinstance(widget, QtWidgets.QTextEdit):
            widget.setStyleSheet(cls.get_input_style())
        elif isinstance(widget, QtWidgets.QComboBox):
            widget.setStyleSheet(cls.get_input_style())
        elif isinstance(widget, QtWidgets.QPushButton):
            button_type = kwargs.get('button_type', 'primary')
            if button_type == 'primary':
                widget.setStyleSheet(cls.get_button_primary_style())
            elif button_type == 'secondary':
                widget.setStyleSheet(cls.get_button_secondary_style())
            elif button_type == 'tertiary':
                widget.setStyleSheet(cls.get_button_tertiary_style())
        elif isinstance(widget, QtWidgets.QLabel):
            size = kwargs.get('size', 'base')
            weight = kwargs.get('weight', 'medium')
            widget.setStyleSheet(cls.get_label_style(size, weight))

