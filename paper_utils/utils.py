import json
import pandas as pd

def json_to_df(json_file):
    '''Convert a JSON file to a DataFrame, with support for nested dictionaries and multi-level headers.'''
    with open(json_file, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df = pd.DataFrame([
        {
            (outer_key, inner_key if isinstance(value, dict) else ''): inner_value 
            for outer_key, value in row.items()
            for inner_key, inner_value in (value.items() if isinstance(value, dict) else [(None, value)])
        }
        for row in data
    ])

    df = df.rename(columns={('', ''): ''})

    return df
