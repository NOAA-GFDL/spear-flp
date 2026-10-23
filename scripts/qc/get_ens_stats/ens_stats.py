import argparse
import polars as pl
import xarray as xr
import dask
import yaml
from pathlib import Path

def _to_list(a):
    if type(a) == str:
        return [a]
    else:
        return list(a)

def get_group_columns(
    df: pl.DataFrame, 
    group_by=None,
    variable_column="variable_id",
    member_column=None,
    skip_columns=[]
) -> list:
    if group_by is None:
        return [c for c in df.columns if c not in skip_columns]
    else:
        groupBy = group_by.copy()
        groupBy.append(variable_column)
        if member_column:
            groupBy.append(member_column)
        return groupBy

def _load_config(config_file: str) -> dict:
    with open(config_file, 'r') as f:
        yaml_conf = yaml.safe_load(f)
    config_dict = {
        "input_catalog": yaml_conf.get("input_catalog", None),
        "output_file": yaml_conf.get("output_file", None),
        "group_by": yaml_conf.get("group_by", None),
        "variable_column": yaml_conf.get("variable_column", "variable_id"),
        "member_column": yaml_conf.get("member_column", "member_id"),
        "concatenate_by": yaml_conf.get("concatenate_by", []),
        "ignore_columns": yaml_conf.get("ignore_columns", []),
        "filter_by": yaml_conf.get("filter_by", {})
    }
    return config_dict

def _load_inputs(input_parser: argparse.ArgumentParser):
    args = input_parser.parse_args()
    
    if args.config:
        input_dict = _load_config(args.config)
    else:
        input_dict = {
            "group_by": None,
            "variable_column": "variable_id",
            "member_column": "member_id",
            "concatenate_by": [],
            "ignore_columns": [],
            "filter_by": {}
        }

    if args.input_catalog:
        input_dict["input_catalog"] = args.input_catalog

    if args.output_file:
        input_dict["output_file"] = args.output_file

    return input_dict

def _get_df_schema(group_columns):
    df_schema = {
            c : str
            for c in group_columns
        }
    for c in ['min','max','mean','std']:
        df_schema[c] = float
    return df_schema

def _get_skip_columns(
    concatenate_by,
    ignore_columns
):
    if type(concatenate_by) != list:
        concatBy = [concatenate_by]
    else:
        concatBy = concatenate_by
    skip_columns = concatBy + ignore_columns
    return skip_columns

def compute_stats(da: xr.DataArray) -> dict:
    """
    Computes min, max, mean, and standard deviation with dask and returns
    them in a dictionary.
    """
    avgval_lazy = da.mean()
    stdval_lazy = da.std()
    minval_lazy = da.min()
    maxval_lazy = da.max()

    avgval, stdval, minval, maxval = dask.compute(
        avgval_lazy, 
        stdval_lazy,
        minval_lazy,
        maxval_lazy
    )

    results = {
        "min" : float(minval),
        "max" : float(maxval),
        "mean" : float(avgval),
        "std" : float(stdval)
    }

    return results

def _cs():
    return {
        "min" : 1.,
        "max" : 10.,
        "mean" : 5.,
        "std" : 2.
    }

def open_datasets(subcatalog: pl.DataFrame) -> xr.Dataset:
    paths = subcatalog.get_column("path").to_list()
    return xr.open_mfdataset(
        paths,
        parallel=True,
        chunks='auto',
        engine='netcdf4'
    )

def _nonunique_warning(df: pl.DataFrame, ignore_columns=[]):
    for c in df.columns:
        if c not in ignore_columns and df.n_unique(pl.col(c)) > 1:
            print("Warning: column {c} has multiple entries.")