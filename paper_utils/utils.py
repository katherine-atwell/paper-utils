import json
import pandas as pd

# Function to recursively extract column hierarchy and values from a nested dict
def extract_columns_and_values(nested_dict, prefix=None):
    if prefix is None:
        prefix = []
    
    columns = []
    flat_dict = {}
    
    for key, value in nested_dict.items():
        current_path = prefix + [key]
        
        if isinstance(value, dict):
            # If the value is a dictionary, recurse
            sub_columns, sub_values = extract_columns_and_values(value, current_path)
            columns.extend(sub_columns)
            flat_dict.update(sub_values)
        else:
            # If the value is a leaf node, store the path and value
            column_tuple = tuple(current_path)
            columns.append(column_tuple)
            flat_dict[column_tuple] = value
            
    return columns, flat_dict

def json_to_df(data):
    '''Convert a JSON file to a DataFrame, with support for nested dictionaries and multi-level headers.'''
    # Extract all column hierarchies
    all_columns = set()
    all_flat_items = []
    row_ids = []

    for item in data:
        # Extract potential row ID
        if 'id' in item:
            row_ids.append(item['id'])
        
        # Extract column structure and flattened values
        columns, flat_item = extract_columns_and_values(item)
        all_columns.update(columns)
        all_flat_items.append(flat_item)

    # Determine the maximum depth of the hierarchy
    max_depth = max(len(col) for col in all_columns)

    # Normalize all column tuples to have the same length
    normalized_columns = []
    for col in all_columns:
        if len(col) < max_depth:
            # Pad with empty strings
            normalized_columns.append(col + ('',) * (max_depth - len(col)))
        else:
            normalized_columns.append(col)

    # Create the MultiIndex
    multi_index = pd.MultiIndex.from_tuples(sorted(normalized_columns))

    # Create DataFrame with the multi-index columns
    df = pd.DataFrame(index=row_ids, columns=multi_index)

    # Fill in the data
    for i, flat_item in enumerate(all_flat_items):
        row_idx = row_ids[i] if i < len(row_ids) else i
        
        for col, value in flat_item.items():
            # Normalize the column tuple if needed
            if len(col) < max_depth:
                norm_col = col + ('',) * (max_depth - len(col))
            else:
                norm_col = col
            
            df.loc[row_idx, norm_col] = value
    return df