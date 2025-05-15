from .utils import *

def pandas_to_latex_with_multicolumn(df, caption=None, label=None, position="h"):
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
    col_format = "|" + "c|" * n_cols
    latex_code.append(f"\\begin{{tabular}}{{{col_format}}}")
    latex_code.append("\\hline")
    
    # Generate multicolumn headers for each level
    for level in range(n_levels):
        header_row = []
        
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
        latex_code.append("\\hline")
    
    # Add the data rows
    for _, row in df.iterrows():
        latex_code.append(" & ".join([str(x) for x in row.values]) + " \\\\")
        latex_code.append("\\hline")
    
    # End the environments
    latex_code.append("\\end{tabular}")
    latex_code.append("\\end{table}")
    
    return "\n".join(latex_code)

def to_latex(data, caption=None, label=None, index=False):
    """
    Convert a DataFrame to a LaTeX table with custom formatting.
    Args:
        data (List[dict]): List of dictionaries containing the data to be converted.
        caption (str): The caption for the LaTeX table.
        label (str): The label for the LaTeX table.
        index (bool): Whether to include the index in the LaTeX table."""
    df = json_to_df(data)
    if isinstance(df.columns, pd.MultiIndex):
        latex_table_custom = pandas_to_latex_with_multicolumn(df, caption=caption, label=label)
    else:
        latex_table_custom = df.to_latex(
                index=index,
                header=True,
                float_format="%.2f",
                caption=caption,
                label=label,
                multicolumn=True,
                multirow=True
            )
    print(latex_table_custom)
    return latex_table_custom