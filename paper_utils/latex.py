from .utils import *

from collections import OrderedDict

def json_to_latex_table_with_multirow(
    data,
    multirow_columns=None,
    caption=None,
    label=None,
    position="h",
    float_precision=4,
    column_format=None,
    caption_position="bottom"
):
    """
    Convert a list of nested dictionaries to a LaTeX table with multicolumn headers
    and multirow cells for specified columns.
    
    Parameters:
    -----------
    data : list of dict or str
        List of nested dictionaries or a JSON string containing the data
    multirow_columns : list, optional
        List of column names where cells with identical consecutive values 
        should be merged using multirow
    caption : str, optional
        Caption for the LaTeX table
    label : str, optional
        Label for referencing the table in LaTeX
    position : str, optional
        Position specifier for the table environment (default: 'h')
    float_precision : int, optional
        Number of decimal places for floating-point values (default: 4)
    column_format : str, optional
        Custom column format for the tabular environment (e.g., 'lccc').
        If None, defaults to 'c' for each column
    caption_position : str, optional
        Position of the caption ('top' or 'bottom', default: 'bottom')
    
    Returns:
    --------
    str
        LaTeX table code
    """
    # If input is a string, parse it as JSON
    if isinstance(data, str):
        data = json.loads(data)
    
    # Ensure data is a list
    if not isinstance(data, list):
        data = [data]
    
    # Function to recursively extract column hierarchy and values from a nested dict
    def extract_columns_and_values(nested_dict, prefix=None, path_order=None):
        if prefix is None:
            prefix = []
        if path_order is None:
            path_order = {}
        
        columns = []
        flat_dict = {}
        
        # Process keys in the order they appear in the original JSON
        for key_idx, (key, value) in enumerate(nested_dict.items()):
            current_path = prefix + [key]
            current_path_tuple = tuple(current_path)
            
            # Store the original order of this path
            if current_path_tuple not in path_order:
                path_order[current_path_tuple] = (len(prefix), key_idx)
            
            if isinstance(value, dict):
                # If the value is a dictionary, recurse
                sub_columns, sub_values, path_order = extract_columns_and_values(value, current_path, path_order)
                columns.extend(sub_columns)
                flat_dict.update(sub_values)
            else:
                # If the value is a leaf node, store the path and value
                column_tuple = current_path_tuple
                columns.append(column_tuple)
                flat_dict[column_tuple] = value
                
        return columns, flat_dict, path_order
    
    # First pass: discover all possible column hierarchies
    all_columns = set()
    all_flat_items = []
    path_order = {}
    
    for item in data:
        # Extract column structure and flattened values
        columns, flat_item, updated_path_order = extract_columns_and_values(item, path_order=path_order)
        path_order.update(updated_path_order)
        all_columns.update(columns)
        all_flat_items.append(flat_item)
    
    # Determine the maximum depth of the hierarchy
    max_depth = max(len(col) for col in all_columns) if all_columns else 0
    
    # Normalize all column tuples to have the same length
    normalized_columns = []
    for col in all_columns:
        if len(col) < max_depth:
            # Pad with empty strings
            normalized_columns.append(col + ('',) * (max_depth - len(col)))
        else:
            normalized_columns.append(col)
    
    # Sort columns by their original order in the JSON structure
    def custom_sort_key(col):
        original_col = col[:len(col) - col.count('')]
        if original_col in path_order:
            return path_order[original_col]
        # For columns we don't have ordering info, sort them last
        return (float('inf'), float('inf'))
    
    sorted_columns = sorted(normalized_columns, key=custom_sort_key)
    
    # Create the MultiIndex
    multi_index = pd.MultiIndex.from_tuples(sorted_columns)
    
    # Create DataFrame with the multi-index columns
    df = pd.DataFrame(columns=multi_index)
    
    # Fill in the data
    for i, flat_item in enumerate(all_flat_items):
        for col, value in flat_item.items():
            # Normalize the column tuple if needed
            if len(col) < max_depth:
                norm_col = col + ('',) * (max_depth - len(col))
            else:
                norm_col = col
            
            df.loc[i, norm_col] = value
    
    # Find column indices for multirow columns
    multirow_column_indices = {}
    if multirow_columns:
        for col_name in multirow_columns:
            # Look for exact matches in any level of MultiIndex
            for i, col in enumerate(df.columns):
                for level in range(len(col)):
                    if col[level] == col_name:
                        multirow_column_indices[i] = col_name
                        break
    
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
    for level in range(max_depth):
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
        if level == max_depth - 1:
            latex_code.append("\\midrule")
    
    # Prepare multirow data
    # For each specified column, find runs of identical values
    multirow_runs = {}
    for col_idx, col_name in multirow_column_indices.items():
        multirow_runs[col_idx] = []
        values = df.iloc[:, col_idx].values
        
        # Find runs of the same value
        i = 0
        while i < len(values):
            start = i
            value = values[i]
            
            # Check if we need to start a new multirow because a column to the left changed
            force_new_row = False
            
            # Check all columns to the left that are in multirow_column_indices
            for left_col_idx in multirow_column_indices:
                if left_col_idx < col_idx:  # It's to the left
                    # If this is the start of a multirow in the left column, force a new row here too
                    for left_start, left_run_length in multirow_runs.get(left_col_idx, []):
                        if i == left_start:
                            force_new_row = True
                            break
                if force_new_row:
                    break
            
            # Count how many consecutive rows have the same value
            j = i + 1
            run_length = 1
            
            while j < len(values) and (pd.isna(values[j]) and pd.isna(value) or values[j] == value) and not force_new_row:
                # Check if any column to the left is starting a new multirow at this position
                for left_col_idx in multirow_column_indices:
                    if left_col_idx < col_idx:
                        for left_start, left_run_length in multirow_runs.get(left_col_idx, []):
                            if j == left_start:
                                # Stop extending this run
                                j -= 1
                                force_new_row = True
                                break
                        if force_new_row:
                            break
                
                if force_new_row:
                    break
                
                # No left column is starting a new multirow, so continue
                run_length += 1
                j += 1
            
            multirow_runs[col_idx].append((start, run_length))
            i = start + run_length
    
    # Add the data rows
    for row_idx in range(len(df)):
        row_values = []
        
        # First column is the index
        row_values.append(str(df.index[row_idx]))
        
        # Process each column
        for col_idx in range(len(df.columns)):
            value = df.iloc[row_idx, col_idx]
            
            # Format the value
            if isinstance(value, float):
                formatted_value = f"{value:.{float_precision}f}"
            elif pd.isna(value):
                formatted_value = ""
            else:
                formatted_value = str(value)
            
            # Check if this is a multirow column
            if col_idx in multirow_runs:
                # Check if this is the start of a multirow
                is_multirow_start = False
                multirow_length = 1
                
                for start, length in multirow_runs[col_idx]:
                    if row_idx == start:
                        is_multirow_start = True
                        multirow_length = length
                        break
                
                if is_multirow_start and multirow_length > 1:
                    # Create a multirow cell
                    row_values.append(f"\\multirow{{{multirow_length}}}{{*}}{{{formatted_value}}}")
                elif is_multirow_start:
                    # Single row, just use the formatted value
                    row_values.append(formatted_value)
                else:
                    # Check if this is part of a multirow that already started
                    is_in_multirow = False
                    for start, length in multirow_runs[col_idx]:
                        if start < row_idx < start + length:
                            is_in_multirow = True
                            break
                    
                    if is_in_multirow:
                        # Part of a multirow that already started, leave empty
                        row_values.append("")
                    else:
                        # Not part of a multirow, use the formatted value
                        row_values.append(formatted_value)
            else:
                # Regular column, use the formatted value
                row_values.append(formatted_value)
        
        # Add the row to the table
        latex_code.append(" & ".join(row_values) + " \\\\")
    
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

def pandas_to_latex_with_multicolumn_and_multirow(
    df, 
    caption=None, 
    label=None, 
    position="h", 
    float_precision=4,
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
        Number of decimal places for floating-point values (default: 4)
    column_format : str, optional
        Custom column format for the tabular environment (e.g., 'lccc').
        If None, defaults to 'c' for each column
    caption_position : str, optional
        Position of the caption ('top' or 'bottom', default: 'bottom')
    multirow_columns : list, optional
        List of column names where cells with identical consecutive values 
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
    
    # Find column indices for multirow columns
    multirow_column_indices = {}
    if multirow_columns:
        for col_name in multirow_columns:
            # Look for exact matches in the last level of MultiIndex
            for i, col in enumerate(df.columns):
                if isinstance(col, tuple) and col[-1] == col_name:
                    multirow_column_indices[i] = col_name
                elif not isinstance(col, tuple) and col == col_name:
                    multirow_column_indices[i] = col_name
    
    # Prepare multirow data
    # For each specified column, find runs of identical values
    multirow_runs = {}
    for col_idx, col_name in multirow_column_indices.items():
        multirow_runs[col_idx] = []
        values = df.iloc[:, col_idx].values
        
        # Find runs of the same value
        i = 0
        while i < len(values):
            start = i
            value = values[i]
            
            # Check if we need to start a new multirow because a column to the left changed
            force_new_row = False
            if col_idx > 0:  # Not the leftmost column
                # Check all columns to the left that are in multirow_column_indices
                for left_col_idx in multirow_column_indices:
                    if left_col_idx < col_idx:  # It's to the left
                        # If this is the start of a multirow in the left column, force a new row here too
                        for left_start, left_run_length in multirow_runs.get(left_col_idx, []):
                            if i == left_start:
                                force_new_row = True
                                break
                    if force_new_row:
                        break
            
            # Count how many consecutive rows have the same value
            j = i + 1
            run_length = 1
            
            while j < len(values) and values[j] == value and not force_new_row:
                # Check if any column to the left is starting a new multirow at this position
                if col_idx > 0:
                    for left_col_idx in multirow_column_indices:
                        if left_col_idx < col_idx:
                            for left_start, left_run_length in multirow_runs.get(left_col_idx, []):
                                if j == left_start:
                                    # Stop extending this run
                                    j -= 1
                                    break
                            else:
                                continue
                            break
                    else:
                        # No left column is starting a new multirow, so continue
                        run_length += 1
                        j += 1
                        continue
                    # A left column is starting a new multirow, so stop here
                    break
                else:
                    # Leftmost column, just count consecutive identical values
                    run_length += 1
                    j += 1
            
            multirow_runs[col_idx].append((start, run_length))
            i = j
    
    # Add the data rows
    for row_idx in range(len(df)):
        row_values = []
        
        # First column is the index
        row_values.append(str(df.index[row_idx]))
        
        # Process each column
        for col_idx in range(len(df.columns)):
            value = df.iloc[row_idx, col_idx]
            
            # Format the value
            if isinstance(value, float):
                formatted_value = f"{value:.{float_precision}f}"
            else:
                formatted_value = str(value)
            
            # Check if this is a multirow column
            if col_idx in multirow_runs:
                # Check if this is the start of a multirow
                is_multirow_start = False
                multirow_length = 1
                
                for start, length in multirow_runs[col_idx]:
                    if row_idx == start:
                        is_multirow_start = True
                        multirow_length = length
                        break
                
                if is_multirow_start and multirow_length > 1:
                    # Create a multirow cell
                    row_values.append(f"\\multirow{{{multirow_length}}}{{*}}{{{formatted_value}}}")
                elif is_multirow_start:
                    # Single row, just use the formatted value
                    row_values.append(formatted_value)
                else:
                    # Check if this is part of a multirow that already started
                    is_in_multirow = False
                    for start, length in multirow_runs[col_idx]:
                        if start < row_idx < start + length:
                            is_in_multirow = True
                            break
                    
                    if is_in_multirow:
                        # Part of a multirow that already started, leave empty
                        row_values.append("")
                    else:
                        # Not part of a multirow, use the formatted value
                        row_values.append(formatted_value)
            else:
                # Regular column, use the formatted value
                row_values.append(formatted_value)
        
        # Add the row to the table
        latex_code.append(" & ".join(row_values) + " \\\\")
    
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
        latex_table_custom = pandas_to_latex_with_multicolumn_and_multirow(df, caption=caption, label=label, float_precision=float_precision, multirow_columns=multirow_columns)
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