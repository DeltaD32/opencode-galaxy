---
name: python-data-quality
description: "Code review and improvement for Python data science and ML engineering code. Activates when the user asks to review, improve, or debug Python code involving pandas, polars, numpy, scikit-learn, or data pipelines. Also activates for requests about type hints in data code, vectorization, memory-efficient DataFrame operations, avoiding common pandas anti-patterns, null handling, schema validation with Pydantic or pandera, or writing unit tests for data transformation functions."
metadata:
  tags:
    - python
    - pandas
    - data-quality
    - code-review
    - type-hints
  authors:
    - Rahul Raghatate (FG-AM-55) <rahul.raghatate@bmwna.com>
  version: "1.0.0"
---

# python-data-quality

You are an expert Python data engineer. You review and improve pandas, polars, and
numpy code for correctness, performance, type safety, and testability.

## When This Skill Activates

Load this skill when the user:

- Asks to review or improve Python data code
- Mentions pandas, polars, numpy, scikit-learn, or data frames
- Uses `iterrows`, `itertuples`, `apply`, or chained assignment
- Asks about type hints for data functions
- Needs schema validation, null handling, or test coverage for transforms
- Says "this is slow", "review my code", or "how do I make this more Pythonic"

## Top Anti-Patterns to Catch and Fix

### 1. Iterating rows with `iterrows` (slow)

```python
# BAD — Python loop over DataFrame rows
for idx, row in df.iterrows():
    df.at[idx, "total"] = row["price"] * row["qty"]

# GOOD — vectorized operation
df["total"] = df["price"] * df["qty"]
```

### 2. Chained assignment (silent no-op)

```python
# BAD — may silently fail due to copy vs view
df[df["status"] == "active"]["value"] = 0

# GOOD — use .loc
df.loc[df["status"] == "active", "value"] = 0
```

### 3. `pd.concat` inside a loop (O(n²) memory)

```python
# BAD — creates a new DataFrame on every iteration
result = pd.DataFrame()
for chunk in chunks:
    result = pd.concat([result, process(chunk)])

# GOOD — collect then concat once
parts = [process(chunk) for chunk in chunks]
result = pd.concat(parts, ignore_index=True)
```

### 4. Missing explicit dtypes

```python
# BAD — pandas infers dtype (may default to object)
df = pd.read_csv("data.csv")

# GOOD — specify dtypes upfront
df = pd.read_csv("data.csv", dtype={
    "id": "int32",
    "price": "float32",
    "category": "category",
})
```

### 5. Silent null propagation

```python
# BAD — nulls silently propagate through calculations
df["margin"] = df["revenue"] - df["cost"]

# GOOD — check and handle nulls explicitly
if not df[["revenue", "cost"]].notna().all().all():
    raise ValueError("Unexpected nulls in revenue or cost columns")
df["margin"] = df["revenue"].fillna(0) - df["cost"].fillna(0)
```

## Type Hints for Data Functions

<!-- skill-lint: ignore -->
```python
import pandas as pd

# Annotate DataFrame-in, DataFrame-out transforms clearly
def normalize_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Scale price column to [0, 1] range."""
    min_price = df["price"].min()
    max_price = df["price"].max()
    if min_price == max_price:
        df = df.copy()
        df["price_norm"] = 0.0
        return df
    df = df.copy()
    df["price_norm"] = (df["price"] - min_price) / (max_price - min_price)
    return df

# Use TypedDict for config dicts in pipelines
from typing import TypedDict

class PipelineConfig(TypedDict):
    source_bucket: str
    target_prefix: str
    partition_col: str
```

## Schema Validation with Pydantic

Validate DataFrames at pipeline entry points:

```python
from pydantic import BaseModel, field_validator
import pandas as pd


class SalesRecord(BaseModel):
    order_id: str
    amount: float
    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"pending", "complete", "cancelled"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}, got {v!r}")
        return v


def validate_sales_df(df: pd.DataFrame) -> list[SalesRecord]:
    return [SalesRecord(**row) for row in df.to_dict("records")]
```

## Schema Validation with pandera (DataFrame-level)

<!-- skill-lint: ignore -->
```python
import pandera as pa
from pandera.typing import DataFrame, Series


class SalesSchema(pa.DataFrameModel):
    order_id: Series[str]
    amount: Series[float] = pa.Field(ge=0)
    status: Series[str] = pa.Field(isin=["pending", "complete", "cancelled"])

    class Config:
        coerce = True


class ProcessedSalesSchema(SalesSchema):
    amount_tax: Series[float] = pa.Field(ge=0)


@pa.check_types
def process(df: DataFrame[SalesSchema]) -> DataFrame[ProcessedSalesSchema]:
    df = df.copy()
    df["amount_tax"] = df["amount"] * 1.1
    return df
```

## Unit Testing Data Transforms

<!-- skill-lint: ignore -->
```python
import pytest
import pandas as pd
from my_module import normalize_prices


@pytest.fixture
def sample_df():
    return pd.DataFrame({"price": [10.0, 20.0, 30.0]})


def test_normalize_prices_range(sample_df):
    result = normalize_prices(sample_df)
    assert result["price_norm"].min() == 0.0
    assert result["price_norm"].max() == 1.0


def test_normalize_prices_no_mutation(sample_df):
    original = sample_df.copy()
    normalize_prices(sample_df)
    pd.testing.assert_frame_equal(sample_df, original)


def test_normalize_prices_single_value():
    df = pd.DataFrame({"price": [5.0]})
    result = normalize_prices(df)
    # With min==max, result should be 0 or NaN — assert explicitly
    assert result["price_norm"].isna().all() or result["price_norm"].iloc[0] == 0.0
```

## Memory Optimization

| Technique                         | Savings                               | When to use                      |
| --------------------------------- | ------------------------------------- | -------------------------------- |
| `dtype="category"`                | Up to 90% for low-cardinality strings | Status, region, category columns |
| `int32` / `float32` instead of 64 | 50%                                   | When value range allows          |
| `pd.read_csv(chunksize=N)`        | Bounded memory                        | Files too large to fit in RAM    |
| `del df; gc.collect()`            | Immediate release                     | After large intermediate frames  |
| `.select_dtypes()` before joins   | Avoids carrying unused columns        | Before merge operations          |

```python
# Downcast numerics automatically
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, downcast="float")

# Convert string columns to category
for col in ["region", "status", "product_line"]:
    df[col] = df[col].astype("category")
```

## Code Review Checklist

Before merging data transformation code:

- [ ] No `iterrows` or `itertuples` in hot paths — use vectorized operations
- [ ] No `pd.concat` inside a loop — collect, then concat once
- [ ] Explicit `dtype` specified on `read_csv` / `read_parquet`
- [ ] Nulls handled intentionally (not silently propagated)
- [ ] No chained indexing — use `.loc` / `.iloc`
- [ ] Functions return `df.copy()` to avoid mutation of inputs
- [ ] Type hints on all public functions
- [ ] At least one unit test per transform function
- [ ] Schema validated at pipeline entry/exit boundaries
