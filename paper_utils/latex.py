def to_latex(df, caption=None, label=None, index=False):
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