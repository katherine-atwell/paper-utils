import json
import pandas as pd

# Function to recursively extract column hierarchy and values from a nested dict
    # while preserving original order
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