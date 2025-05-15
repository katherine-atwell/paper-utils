from utils import *

def to_latex(data, caption=None, label=None, index=False):
    """
    Convert a DataFrame to a LaTeX table with custom formatting.
    Args:
        data (List[dict]): List of dictionaries containing the data to be converted.
        caption (str): The caption for the LaTeX table.
        label (str): The label for the LaTeX table.
        index (bool): Whether to include the index in the LaTeX table."""
    df = json_to_df(data)
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