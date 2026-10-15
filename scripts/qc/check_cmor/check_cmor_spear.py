import argparse
import pathlib
import json
import polars as pl
import numpy as np
import xarray as xr 
import dask

thisDir = pathlib.Path(__file__).parent.resolve()

parser = argparse.ArgumentParser(
                description='Verifies FRE CMOR output of SPEAR data using catalogs to search for datasets'
            )

parser.add_argument(
    'catalog_path',
    help="Path to input csv catalog that describes the CMORized data. This could be the CSV of an intake-esm catalog, output by CatalogBuilder."
)

parser.add_argument(
    'stats_dir',
    help="Same as the base_path in get_ens_stats.py, tells this script where to look for the precomputed pre-CMORization stats."
)

parser.add_argument(
    '--table_id',
    help='Allows to filter the catalog by a specific table_id.'
)

parser.add_argument(
    '--variable_id',
    help='Allows to filter the catalog by a specific variable_id.'
)

parser.add_argument(
    '--experiment_id',
    help='Allows to filter the catalog by a specific experiment_id.'
)

parser.add_argument(
    '--mappings',
    default=thisDir / 'spear_mappings.json',
    help="Describes how to map the experiment_id, table_id, and variable_id to the precomputed stats directory structure. See the default file spear_mappings.json for an example of how to format this."
)

columns = ['min', 'max', 'mean', 'std']

def get_member_id(variant_label):
    return "pp_ens_" + variant_label.split("i")[0][1:].zfill(2)

def main(
    catalog_path,
    stats_dir,
    table_id=None,
    experiment_id=None,
    variable_id=None,
    mappings=thisDir/'spear_mappings.json'
):

    cmor_out_catalog = catalog_path
    csv_base_path = stats_dir

    cat_df = pl.read_csv(cmor_out_catalog)

    # use cmorized values
    filters = []
    for k,v in {
        "table_id" : table_id,
        "experiment_id" : experiment_id,
        "variable_id" : variable_id
    }.items():
        if v is not None:
            filters.append(pl.col(k) == v)
    subcat = cat_df.filter(*filters)

    mapping_dict = json.load(mappings)

    for grp,subdf in subcat.group_by([
        "experiment_id", 
        "table_id", 
        "variable_id"
    ]):
        exp_id,tab_id,var_id = grp

        print(f"Checking {grp}...")

        in_csv = (csv_base_path +
            mapping_dict["experiment_id"][exp_id] + '/' +
            mapping_dict["table_id"][var_id][tab_id] + '/' +
            mapping_dict["variable_id"][var_id] + '.csv')

        out_csv = (csv_base_path +
            mapping_dict["experiment_id"][exp_id] + '/' +
            mapping_dict["table_id"][var_id][tab_id] + '/' +
            mapping_dict["variable_id"][var_id] + '_cmor' + '.csv')
        
        print(f"Getting pre-cmor stats from {in_csv}")
        print(f"Outputting post-cmor stats and results to {out_csv}")

        correct_values = pl.read_csv(in_csv)

        are_values_correct = []

        for subgrp,df in subcat.group_by("member_id"):
            variant_id = subgrp[0]
            # calculate min,max,mean,std

            if len(df['path']) == 1:
                ds = xr.open_dataset(
                    df['path'][0], 
                    chunks='auto',
                    engine='netcdf4'
                )[var_id]
            else:
                ds = xr.open_mfdataset(
                    df['path'], 
                    parallel=True, 
                    chunks='auto',
                    engine='netcdf4'
                )[var_id]

            # test with just one time slice:
            # ds = xr.open_dataset(
            #     df['path'][0], 
            #     chunks='auto',
            #     engine='netcdf4'
            # )[var_id].isel(time=0)

            weights = np.cos(np.deg2rad(ds.lat))
            weights.name = "weights"
            avgval_lazy = ds.weighted(weights).mean()
            stdval_lazy = ds.weighted(weights).std()

            minval_lazy = ds.min()
            maxval_lazy = ds.max()

            cmor_values = np.array(dask.compute(
                minval_lazy,
                maxval_lazy,
                avgval_lazy,
                stdval_lazy
            ))

            expected_values = correct_values.filter(
                pl.col('member_id') == get_member_id(variant_id)
            ).select(pl.exclude('member_id')).to_numpy()

            # res = {i : j for i,j in zip(columns, (cmor_values == expected_values)[0])}
            res = {i : j for i,j in zip(columns, cmor_values)}
            res['match'] = np.isclose(cmor_values, expected_values).all()
            res['member_id'] = variant_id

            are_values_correct.append(res)

            # break

        is_correct_df = pl.DataFrame(
            are_values_correct, 
            {
                'member_id' : str, 
                'min' : float, 
                'max' : float, 
                'mean' : float, 
                'std': float,
                'match': bool
            }
        ).select(correct_values.columns + ['match'])
        is_correct_df.sort("member_id").write_csv(out_csv)

if __name__=='__main__':
    args = parser.parse_args()
    main(
        args.catalog_path,
        args.stats_dir,
        table_id=args.table_id,
        experiment_id=args.experiment_id,
        variable_id=args.variable_id,
        mappings=args.mappings
    )