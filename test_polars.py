"""Test polars conversion."""

import pandas as pd
import polars as pl

# Test conversion
df = pd.DataFrame({'a': [1, 2, 3]})
pl_df = pl.from_pandas(df)
print("Pandas to Polars conversion works!")
print(pl_df)
