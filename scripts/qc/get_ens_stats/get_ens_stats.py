import argparse
import json
from pathlib import Path
import ens_stats as es
import polars as pl

parser = argparse.ArgumentParser(description="Calculate summary statistics for datasets found in an intake-esm catalog.")
parser.add_argument(
    "input_catalog",
    nargs="?",
    default=None,
    help="Intake-ESM catalog used to find datasets."
)
parser.add_argument(
    "output_file",
    nargs="?",
    default=None,
    help="CSV file to write outputs to."
)
parser.add_argument(
    "--config",
    help="Config yaml with additional configuration options."
)

def get_ensemble_stats(
    input_catalog,
    output_file,
    group_by=None,
    variable_column="variable_id",
    member_column=None,
    concatenate_by=[],
    ignore_columns=[],
    filter_by={}
):
    catalog_df = pl.read_csv(input_catalog).filter(
        *[pl.col(k).is_in(es._to_list(v)) for k,v in filter_by.items()]
    )
    print(f"Filtered catalog has {catalog_df.shape[0]} entries.")

    skip_columns = es._get_skip_columns(concatenate_by,ignore_columns)
    group_columns = es.get_group_columns(
        catalog_df,
        group_by=group_by,
        variable_column=variable_column,
        member_column=member_column,
        skip_columns=skip_columns
    )

    output_df_schema = es._get_df_schema(group_columns)

    print(f"Writing outputs to {str(Path(output_file).resolve())}")
    if not Path(output_file).exists():
        pl.DataFrame(
            schema=output_df_schema
        ).write_csv(output_file)

    for g,subdf in catalog_df.group_by(group_columns):
        grp = dict(zip(group_columns,g))
        da = es.open_datasets(subdf)[grp[variable_column]]
        stats = es.compute_stats(da)
        output_dict = {k : [v] for k,v in dict(grp,**stats).items()}
        with open(output_file,'a') as f:
            pl.DataFrame(
                output_dict,
                schema=output_df_schema
            ).write_csv(f,include_header=False)

if __name__=="__main__":
    input_dict = es._load_inputs(parser)
    print(input_dict)
    get_ensemble_stats(
        input_dict["input_catalog"],
        input_dict["output_file"],
        group_by=input_dict["group_by"],
        member_column=input_dict["member_column"],
        concatenate_by=input_dict["concatenate_by"],
        ignore_columns=input_dict["ignore_columns"],
        filter_by=input_dict["filter_by"]
    )