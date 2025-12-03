import pandas as pd
from typing import Optional
from datetime import datetime
import re
from model.professor_list import professor_list


class email_modifyer:
    """
    Class to modify email templates by substituting values from professor lists (CSV/Excel).
    """
    
    def __init__(self, subject: Optional[str] = None, template_body: str = "", template_type: int = 0):
        """
        Initialize the email modifier.
        
        Args:
            subject: Email subject (optional, can be None)
            template_body: The email template body with placeholders like {professor_name}
            template_type: Type of the email template
        """
        self.subject = subject
        self.template_body = template_body
        self.template_type = template_type
        self.professor_list_df: Optional[pd.DataFrame] = None
        self._original_columns: Optional[list] = None  # Preserve original column names
    
    def set_professor_list(self, professor_list_path: str):
        """
        Load professor list from CSV or Excel file.
        Preserves original column names and format.
        
        Args:
            professor_list_path: Path to the CSV or Excel file
        """
        try:
            prof_list = professor_list(professor_list_path)
            self.professor_list_df = prof_list.returner_file()
            # Preserve original column names (do not modify CSV format)
            self._original_columns = self.professor_list_df.columns.tolist()
        except Exception as e:
            raise ValueError(f"Error loading professor list: {e}")
    
    def set_professor_list_df(self, df: pd.DataFrame):
        """
        Set professor list directly from a pandas DataFrame.
        Preserves original column names and format.
        
        Args:
            df: pandas DataFrame containing professor data
        """
        if not isinstance(df, pd.DataFrame):
            raise ValueError("professor_list must be a pandas DataFrame")
        self.professor_list_df = df.copy()
        # Preserve original column names (do not modify DataFrame format)
        self._original_columns = self.professor_list_df.columns.tolist()
    
    def get_substituted_template(self, index: int = 0) -> str:
        """
        Get the template body with substituted values from the professor list.
        
        Args:
            index: Index of the row to use from professor_list (0 for first row)
            
        Returns:
            Template body with substituted values
            
        Raises:
            ValueError: If professor_list is not set or index is out of range
        """
        if self.professor_list_df is None or self.professor_list_df.empty:
            raise ValueError("Professor list is not set or is empty. Use set_professor_list() or set_professor_list_df() first.")
        
        if index < 0 or index >= len(self.professor_list_df):
            raise ValueError(f"Index {index} is out of range. Professor list has {len(self.professor_list_df)} rows.")
        
        # Get the row at the specified index
        row = self.professor_list_df.iloc[index]
        
        # Convert row to dictionary, handling NaN values
        row_dict = {}
        for col in self.professor_list_df.columns:
            value = row[col]
            # Convert NaN/None to empty string
            if pd.isna(value):
                row_dict[col] = ""
            else:
                row_dict[col] = str(value)
        
        # Create a dictionary with normalized keys for matching (without modifying original data)
        # This handles cases where template uses {professor_name} but CSV has "Professor_Name"
        normalized_dict = {}
        for key, value in row_dict.items():
            # Original key (preserve case and format)
            normalized_dict[key] = value
            # Normalized variants for flexible matching
            key_lower = key.lower().strip()
            normalized_dict[key_lower] = value
            normalized_dict[key_lower.replace(' ', '_')] = value
            normalized_dict[key_lower.replace('-', '_')] = value
            normalized_dict[key_lower.replace('_', ' ')] = value
            normalized_dict[key_lower.replace('_', '-')] = value
        
        try:
            # Use format_map to substitute values
            # This will replace {professor_name} with the value from the CSV
            substituted_body = self.template_body.format_map(normalized_dict)
            return substituted_body
        except KeyError as e:
            # If a placeholder is not found in the CSV, raise a helpful error
            missing_key = str(e).strip("'")
            available_keys = ', '.join(self.professor_list_df.columns.tolist())
            raise ValueError(
                f"Placeholder '{missing_key}' not found in professor list. "
                f"Available columns: {available_keys}"
            )
    
    def get_substituted_subject(self, index: int = 0) -> Optional[str]:
        """
        Get the subject with substituted values from the professor list.
        
        Args:
            index: Index of the row to use from professor_list (0 for first row)
            
        Returns:
            Subject with substituted values, or None if subject was not set
        """
        if self.subject is None:
            return None
        
        if self.professor_list_df is None or self.professor_list_df.empty:
            raise ValueError("Professor list is not set or is empty. Use set_professor_list() or set_professor_list_df() first.")
        
        if index < 0 or index >= len(self.professor_list_df):
            raise ValueError(f"Index {index} is out of range. Professor list has {len(self.professor_list_df)} rows.")
        
        # Get the row at the specified index
        row = self.professor_list_df.iloc[index]
        
        # Convert row to dictionary
        row_dict = {}
        for col in self.professor_list_df.columns:
            value = row[col]
            if pd.isna(value):
                row_dict[col] = ""
            else:
                row_dict[col] = str(value)
        
        # Create normalized dictionary for matching (without modifying original data)
        normalized_dict = {}
        for key, value in row_dict.items():
            # Original key (preserve case and format)
            normalized_dict[key] = value
            # Normalized variants for flexible matching
            key_lower = key.lower().strip()
            normalized_dict[key_lower] = value
            normalized_dict[key_lower.replace(' ', '_')] = value
            normalized_dict[key_lower.replace('-', '_')] = value
            normalized_dict[key_lower.replace('_', ' ')] = value
            normalized_dict[key_lower.replace('_', '-')] = value
        
        try:
            substituted_subject = self.subject.format_map(normalized_dict)
            return substituted_subject
        except KeyError as e:
            missing_key = str(e).strip("'")
            available_keys = ', '.join(self.professor_list_df.columns.tolist())
            raise ValueError(
                f"Placeholder '{missing_key}' not found in professor list. "
                f"Available columns: {available_keys}"
            )
    
    def _extract_placeholders(self, text: str) -> set:
        """
        Extract all placeholders from a template string.
        
        Args:
            text: Template string with placeholders like {professor_name}
            
        Returns:
            Set of placeholder names (without braces)
        """
        if not text:
            return set()
        # Find all {placeholder} patterns
        pattern = r'\{([^}]+)\}'
        placeholders = re.findall(pattern, text)
        return set(placeholders)
    
    def _get_normalized_column_name(self, placeholder: str, available_columns: list) -> Optional[str]:
        """
        Find the matching column name for a placeholder.
        
        Args:
            placeholder: Placeholder name like "professor_name"
            available_columns: List of available column names in the DataFrame
            
        Returns:
            Matching column name or None if not found
        """
        placeholder_lower = placeholder.lower().strip()
        
        for col in available_columns:
            col_normalized = col.lower().strip()
            # Direct match
            if col_normalized == placeholder_lower:
                return col
            # Match with spaces/underscores/hyphens replaced
            col_variants = [
                col_normalized.replace(' ', '_'),
                col_normalized.replace('-', '_'),
                col_normalized.replace('_', ' '),
                col_normalized.replace('_', '-')
            ]
            if placeholder_lower in col_variants or col_normalized in [
                placeholder_lower.replace(' ', '_'),
                placeholder_lower.replace('-', '_'),
                placeholder_lower.replace('_', ' '),
                placeholder_lower.replace('_', '-')
            ]:
                return col
        
        return None
    
    def validate_and_add_report(self) -> str:
        """
        Validate all substitutions and add make_report column to professor_list.
        If all substitutions are valid (no None or empty values), adds date and hour.
        If any value is None or empty, writes "NoneError" and returns "-1".
        
        Returns:
            "-1" if any error found, otherwise returns success message
        """
        if self.professor_list_df is None or self.professor_list_df.empty:
            raise ValueError("Professor list is not set or is empty. Use set_professor_list() or set_professor_list_df() first.")
        
        # Extract all placeholders from template_body and subject
        placeholders = self._extract_placeholders(self.template_body)
        if self.subject:
            placeholders.update(self._extract_placeholders(self.subject))
        
        if not placeholders:
            # No placeholders to validate, all rows are valid
            self.professor_list_df['make_report'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return "Success: No placeholders to validate"
        
        # Get available columns (excluding make_report if it already exists)
        # Use original column names without modification
        available_columns = [col for col in self.professor_list_df.columns if col != 'make_report']
        
        # Map placeholders to actual column names (matching without modifying original columns)
        placeholder_to_column = {}
        for placeholder in placeholders:
            col_name = self._get_normalized_column_name(placeholder, available_columns)
            if col_name is None:
                # Placeholder not found in columns, all rows will fail
                self.professor_list_df['make_report'] = "NoneError"
                return "-1"
            placeholder_to_column[placeholder] = col_name
        
        # Initialize make_report column
        make_report_values = []
        has_error = False
        
        # Check each row
        for idx in range(len(self.professor_list_df)):
            row = self.professor_list_df.iloc[idx]
            row_has_error = False
            
            # Check if all required values are non-empty
            for placeholder, col_name in placeholder_to_column.items():
                value = row[col_name]
                # Check if value is None, NaN, or empty string
                if pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
                    row_has_error = True
                    has_error = True
                    break
            
            if row_has_error:
                make_report_values.append("NoneError")
            else:
                # All values are valid, add date and hour
                make_report_values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Add make_report column to DataFrame
        self.professor_list_df['make_report'] = make_report_values
        
        if has_error:
            return "-1"
        else:
            return f"Success: All {len(self.professor_list_df)} rows validated successfully"

