from .utils import *

def pandas_to_latex_with_multicolumn(
    df, 
    caption=None, 
    label=None, 
    position="h", 
    float_precision=2,
    column_format=None,
    caption_position="bottom",
    multirow_columns=None
):
    """
    Convert a pandas DataFrame with MultiIndex columns to a LaTeX table with multicolumn headers
    and multirow cells for specified columns.
    
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
        Custom column format for the tabular environment (e.g., 'lccc').
        If None, defaults to 'c' for each column
    caption_position : str, optional
        Position of the caption ('top' or 'bottom', default: 'bottom')
    multirow_columns : list, optional
        List of column names or indices where cells with identical consecutive values 
        should be merged using multirow
    
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
    
    # Add caption at the top if requested
    if caption and caption_position.lower() == "top":
        latex_code.append(f"\\caption{{{caption}}}")
        if label:
            latex_code.append(f"\\label{{{label}}}")
    
    # Begin tabular environment
    # Get the correct number of columns
    n_cols = len(df.columns)
    
    # Use custom column format if provided, otherwise default to centered columns
    if column_format is None:
        # Add one extra column for row index
        col_format = "c" * (n_cols + 1)
    else:
        col_format = column_format
        
    latex_code.append(f"\\begin{{tabular}}{{{col_format}}}")
    
    # Add toprule
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
            header_row.append(f"\\multicolumn{{{span}}}{{c}}{{{value}}}")
        
        latex_code.append(" & ".join(header_row) + " \\\\")
        
        # Add a cmidrule after the last header level
        if level == n_levels - 1:
            latex_code.append("\\midrule")
    
    # Process multirow columns if provided
    multirow_data = {}
    multirow_column_indices = []
    
    if multirow_columns:
        # Convert column names to column indices if necessary
        for col in multirow_columns:
            if isinstance(col, str):
                # Find all columns where the lowest level matches this name
                matching_cols = [i for i, c in enumerate(df.columns) 
                                if c[-1] == col or c[0] == col]
                multirow_column_indices.extend(matching_cols)
            else:
                # Assume it's already a column index
                multirow_column_indices.append(col)
        
        # For each multirow column, find runs of identical values
        for col_idx in multirow_column_indices:
            col_name = df.columns[col_idx]
            values = df.iloc[:, col_idx].values
            multirow_data[col_idx] = []
            
            # Find consecutive runs of the same value
            current_value = values[0]
            current_start = 0
            current_length = 1
            
            for i in range(1, len(values)):
                if pd.isna(values[i]) and pd.isna(current_value) or values[i] == current_value:
                    current_length += 1
                else:
                    multirow_data[col_idx].append((current_start, current_length, current_value))
                    current_value = values[i]
                    current_start = i
                    current_length = 1
            
            # Add the last run
            multirow_data[col_idx].append((current_start, current_length, current_value))
    
    # Add the data rows
    for row_idx, (idx, row) in enumerate(df.iterrows()):
        # Format row values
        row_values = []
        for col_idx, value in enumerate(row.values):
            cell = ""
            
            # Check if this cell should be part of a multirow
            if col_idx in multirow_data:
                is_multirow_start = False
                multirow_length = 0
                
                # Check if this is the start of a multirow
                for start, length, _ in multirow_data[col_idx]:
                    if row_idx == start:
                        is_multirow_start = True
                        multirow_length = length
                        break
                
                # If this is the start of a multirow, create a multirow cell
                if is_multirow_start and multirow_length > 1:
                    # Format the value
                    if isinstance(value, float):
                        formatted_value = f"{value:.{float_precision}f}"
                    else:
                        formatted_value = str(value)
                    
                    cell = f"\\multirow{{{multirow_length}}}{{*}}{{{formatted_value}}}"
                # If this is part of a multirow but not the start, leave empty
                elif not is_multirow_start:
                    # Check if this row is part of a multirow (not the start)
                    is_in_multirow = False
                    for start, length, _ in multirow_data[col_idx]:
                        if start < row_idx < start + length:
                            is_in_multirow = True
                            break
                    
                    if is_in_multirow:
                        cell = ""
                    else:
                        # Not part of a multirow, format normally
                        if isinstance(value, float):
                            cell = f"{value:.{float_precision}f}"
                        else:
                            cell = str(value)
                else:
                    # Single-row cell, format normally
                    if isinstance(value, float):
                        cell = f"{value:.{float_precision}f}"
                    else:
                        cell = str(value)
            else:
                # Regular cell, format normally
                if isinstance(value, float):
                    cell = f"{value:.{float_precision}f}"
                else:
                    cell = str(value)
            
            row_values.append(cell)
        
        # Add the index value as the first column
        row_with_index = [str(idx)] + row_values
        latex_code.append(" & ".join(row_with_index) + " \\\\")
    
    # Add bottomrule after last data row
    latex_code.append("\\bottomrule")
    
    # End the tabular environment
    latex_code.append("\\end{tabular}")
    
    # Add caption at the bottom if requested (default)
    if caption and caption_position.lower() != "top":
        latex_code.append(f"\\caption{{{caption}}}")
        if label:
            latex_code.append(f"\\label{{{label}}}")
    
    # End the table environment
    latex_code.append("\\end{table}")
    
    # Add a note about required packages
    latex_code.append("% Note: This table requires \\usepackage{booktabs} and \\usepackage{multirow} in your LaTeX preamble")
    
    return "\n".join(latex_code)


def to_latex(data, caption=None, label=None, index=False, float_precision=2, multirow_columns=None):
    """
    Convert a DataFrame to a LaTeX table with custom formatting.
    Args:
        data (List[dict]): List of dictionaries containing the data to be converted.
        caption (str): The caption for the LaTeX table.
        label (str): The label for the LaTeX table.
        index (bool): Whether to include the index in the LaTeX table.
        float_precision (int): The number of decimal places for floating-point numbers.
        multirow_columns (list): List of column names or indices where cells with 
        identical consecutive values should be merged using multirow."""
    df = json_to_df(data)
    print(df)
    print(multirow_columns)
    if isinstance(df.columns, pd.MultiIndex):
        latex_table_custom = pandas_to_latex_with_multicolumn(df, caption=caption, label=label, float_precision=float_precision, multirow_columns=multirow_columns)
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