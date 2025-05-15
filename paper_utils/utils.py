import json
import pandas as pd

def json_to_df(data, row_id_field=None):
    '''Convert a JSON file to a DataFrame, with support for nested dictionaries and multi-level headers.'''
    # First pass: discover all possible column hierarchies
    all_columns = set()
    all_flat_items = []
    row_ids = []
    path_order = {}
    
    for item in data:
        # Extract potential row ID if specified
        if row_id_field and row_id_field in item:
            row_ids.append(item[row_id_field])
        
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
    if row_id_field and row_ids:
        df = pd.DataFrame(index=row_ids, columns=multi_index)
    else:
        df = pd.DataFrame(columns=multi_index)
    
    # Fill in the data
    for i, flat_item in enumerate(all_flat_items):
        row_idx = row_ids[i] if row_id_field and i < len(row_ids) else i
        
        for col, value in flat_item.items():
            # Normalize the column tuple if needed
            if len(col) < max_depth:
                norm_col = col + ('',) * (max_depth - len(col))
            else:
                norm_col = col
            
            df.loc[row_idx, norm_col] = value
    return df