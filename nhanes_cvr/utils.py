import functools
import os
from typing import Callable, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from typing import NamedTuple
from nhanes_dl import types
from sklearn.impute import SimpleImputer


def const(x): return x


def getClassName(x) -> str:
    return x.__class__.__name__


def toUpperCase(l):
    return list(map(lambda l: l.upper(), l))


def compose(f, g):
    return lambda x: f(g(x))


def yearToMonths(x): return 12 * x


def labelCauseOfDeathAsCVR(nhanse_dataset: pd.DataFrame) -> pd.Series:
    # Different meanings of ucod_leading - https://www.cdc.gov/nchs/data/datalinkage/public-use-2015-linked-mortality-files-data-dictionary.pdf
    # 1 is Diesease of heart
    # 5 is Cerebrovascular Diseases

    monthsSinceFollowUp = 326 * .5
    return nhanse_dataset.agg(lambda x: 1 if x.PERMTH_EXM <= monthsSinceFollowUp
                              and (x.UCOD_LEADING == 1 or
                                   x.UCOD_LEADING == 5) else 0, axis=1)

    # return nhanse_dataset.agg(lambda x: 1 if (x.UCOD_LEADING == 1 or x.UCOD_LEADING == 5) else 0, axis=1)


def unique(list):
    return functools.reduce(
        lambda l, x: l if x in l else l + [x], list, [])


def ensure_directory_exists(path):
    try:
        os.mkdir(path)
    except:
        pass


def remove_outliers(z_score, df, columns=None):
    columns = columns if columns else df.columns
    scores = np.abs(stats.zscore(df.loc[:, columns]))
    return df.loc[(scores < z_score).all(axis=1), :]


# Need to include this in nhanes-dl
def cache_nhanes(cache_path: str, get_nhanse: Callable[[], types.Codebook]) -> types.Codebook:
    from os.path import exists
    if exists(cache_path):
        return types.Codebook(pd.read_csv(cache_path))

    else:
        res = get_nhanse()
        res.to_csv(cache_path)
        return res
