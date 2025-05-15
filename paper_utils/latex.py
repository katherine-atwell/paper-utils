from .utils import *

def pandas_to_latex_with_multicolumn(
    df, 
    caption=None, 
    label=None, 
    position="h", 
    float_precision=2,
    column_format=None
):
    """
    Convert a pandas DataFrame with MultiIndex columns to a LaTeX table with multicolumn headers.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with MultiIndex columns to convert
    caption : str, optional
        Caption for the LaTeX table
    label : str, optional
        Label for referencing the table in LaTeX
    position : str, optional
        Position specifier for the table environment (default: 'h')
    float_precision : int, optional
        Number of decimal places for floating-point values (default: 2)
    column_format : str, optional
        Custom column format for the tabular environment (e.g., '|l|c|c|').
        If None, defaults to '|c|' for each column
    
    Returns:
    --------
    str
        LaTeX table code
    """
    # Check if the DataFrame has MultiIndex columns
    if not isinstance(df.columns, pd.MultiIndex):
        raise ValueError("DataFrame must have MultiIndex columns")
    
    # Get the number of levels in the column MultiIndex
    n_levels = df.columns.nlevels
    
    # Start building the LaTeX table
    latex_code = []
    
    # Begin table environment
    latex_code.append(f"\\begin{{table}}[{position}]")
    latex_code.append("\\centering")
    
    # Add caption and label if provided
    if caption:
        latex_code.append(f"\\caption{{{caption}}}")
    if label:
        latex_code.append(f"\\label{{{label}}}")
    
    # Begin tabular environment
    # Get the correct number of columns
    n_cols = len(df.columns)
    
    # Use custom column format if provided, otherwise default to centered columns
    if column_format is None:
        # Add one extra column for row index
        col_format = "|" + "c|" * (n_cols + 1)
    else:
        col_format = column_format
        
    latex_code.append(f"\\begin{{tabular}}{{{col_format}}}")
    latex_code.append("\\toprule")
    
    # Add index name as the first column header if it exists
    index_name = df.index.name if df.index.name else ""
    
    # Generate multicolumn headers for each level
    for level in range(n_levels):
        header_row = [index_name] if level == 0 else [""]
        
        # Get unique values and their spans at this level
        level_values = df.columns.get_level_values(level)
        spans = []
        
        current_value = level_values[0]
        current_span = 1
        
        for i in range(1, len(level_values)):
            if level_values[i] == current_value:
                current_span += 1
            else:
                spans.append((current_value, current_span))
                current_value = level_values[i]
                current_span = 1
                
        # Add the last span
        spans.append((current_value, current_span))
        
        # Create multicolumn entries
        for value, span in spans:
            header_row.append(f"\\multicolumn{{{span}}}{{|c|}}{{{value}}}")
        
        latex_code.append(" & ".join(header_row) + " \\\\")
        latex_code.append("\\midrule")
    
    # Add the data rows
    for idx, row in df.iterrows():
        # Format floating point values with specified precision
        row_values = []
        for value in row.values:
            if isinstance(value, float):
                # Format float with specified precision
                row_values.append(f"{value:.{float_precision}f}")
            else:
                row_values.append(str(value))
        
        # Add the index value as the first column
        row_with_index = [str(idx)] + row_values
        latex_code.append(" & ".join(row_with_index) + " \\\\")
    latex_code.append("\\bottomrule")
    
    # End the environments
    latex_code.append("\\end{tabular}")
    latex_code.append("\\end{table}")
    
    return "\n".join(latex_code)


def to_latex(data, caption=None, label=None, index=False, float_precision=2):
    """
    Convert a DataFrame to a LaTeX table with custom formatting.
    Args:
        data (List[dict]): List of dictionaries containing the data to be converted.
        caption (str): The caption for the LaTeX table.
        label (str): The label for the LaTeX table.
        index (bool): Whether to include the index in the LaTeX table."""
    df = json_to_df(data)
    print(df)
    if isinstance(df.columns, pd.MultiIndex):
        latex_table_custom = pandas_to_latex_with_multicolumn(df, caption=caption, label=label, float_precision=float_precision)
    else:
        latex_table_custom = df.to_latex(
                index=index,
                header=True,
                float_format=f"%.{float_precision}f",
                caption=caption,
                label=label,
                multicolumn=True,
                multirow=True
            )
    print(latex_table_custom)
    return latex_table_custom