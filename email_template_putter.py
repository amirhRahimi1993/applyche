import pandas as pd
from typing import Optional
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
    
    def set_professor_list(self, professor_list_path: str):
        """
        Load professor list from CSV or Excel file.
        
        Args:
            professor_list_path: Path to the CSV or Excel file
        """
        try:
            prof_list = professor_list(professor_list_path)
            self.professor_list_df = prof_list.returner_file()
            # Normalize column names to lowercase and strip whitespace for matching
            self.professor_list_df.columns = self.professor_list_df.columns.str.strip().str.lower()
        except Exception as e:
            raise ValueError(f"Error loading professor list: {e}")
    
    def set_professor_list_df(self, df: pd.DataFrame):
        """
        Set professor list directly from a pandas DataFrame.
        
        Args:
            df: pandas DataFrame containing professor data
        """
        if not isinstance(df, pd.DataFrame):
            raise ValueError("professor_list must be a pandas DataFrame")
        self.professor_list_df = df.copy()
        # Normalize column names to lowercase and strip whitespace for matching
        self.professor_list_df.columns = self.professor_list_df.columns.str.strip().str.lower()
    
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
        
        # Also create a dictionary with normalized keys (lowercase, stripped) for matching
        # This handles cases where template uses {professor_name} but CSV has "Professor_Name"
        normalized_dict = {}
        for key, value in row_dict.items():
            # Original key
            normalized_dict[key] = value
            # Also add with underscores replaced (for flexibility)
            normalized_dict[key.replace(' ', '_')] = value
            normalized_dict[key.replace('-', '_')] = value
        
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
        
        # Create normalized dictionary for matching
        normalized_dict = {}
        for key, value in row_dict.items():
            normalized_dict[key] = value
            normalized_dict[key.replace(' ', '_')] = value
            normalized_dict[key.replace('-', '_')] = value
        
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

