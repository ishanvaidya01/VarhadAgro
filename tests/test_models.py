import pytest
import pandas as pd
from cropres.models.train import split_data

def test_split_data():
    df = pd.DataFrame({
        "year": [2017, 2018, 2019, 2020]
    })
    train, test = split_data(df, train_end_year=2018)
    assert len(train) == 2
    assert len(test) == 2
    assert train["year"].max() == 2018
    assert test["year"].min() == 2019
