import argparse
import pathlib
import json
import polars as pl
import numpy as np

thisDir = pathlib.Path(__file__).parent.resolve()
default_mappings = thisDir/"spear_mappings.json"

parser = argparse.ArgumentParser(
    description='Verifies FRE CMOR output summary statistics by comparing two CSV files. CSV files are assumed to be created using the get_ens_stats tool from this repository. Output is a copy of the cmorized_stats file with a new column called match that stores boolean values.'
)

parser.add_argument(
    "cmorized_stats",
    help="Path to file containing stats calculated from CMORized datasets."
)
parser.add_argument(
    "original_stats",
    help="Path to file containing stats calculated from pre-CMORized datasets."
)
parser.add_argument(
    "-o",
    "--output_file",
    default=None,
    help="Path to write output to. By default this script will save over the cmorized_stats file."
)
parser.add_argument(
    "--mappings",
    default=default_mappings,
    help="Path to mappings file. See documentation for how to format this."
)
parser.add_argument(
    "--member_column",
    default="member_id",
    help="Name of member id column in the CMORized CSV. This defaults to member_id, though CMORized data could often also use variant_label."
)

stats_columns = ['min', 'max', 'mean', 'std']

def get_member_id(variant_label):
    return "pp_ens_" + variant_label.split("i")[0][1:].zfill(2)

def get_filter(group, mappings):
    orig_filter = {}
    for k,v in mappings.items():
        if "map_from" in v:
            map_from = v["map_from"]
        else:
            map_from = k

        if "map_to" in v:
            map_to = v["map_to"]
        else:
            map_to = k
        
        map_dict = v["mappings"]
        if type(map_from) == list:
            value = map_dict[group[map_from[0]]]
            for mf in map_from[1:]:
                value = value[group[mf]]
            orig_filter[map_to] = value
        else:
            orig_filter[map_to] = map_dict[group[map_from]]
    return orig_filter

def main(
    cmorized_stats,
    original_stats,
    output_file=None,
    mappings_file=default_mappings,
    member_column="member_id"
):
    cmor_df = pl.read_csv(cmorized_stats)
    orig_df = pl.read_csv(original_stats)
    with open(mappings_file,'r') as f:
        mappings = json.load(f)

    group_columns = [
        c for c in cmor_df.columns 
        if c not in stats_columns
        and c != member_column
    ]

    outdf_schema = cmor_df.schema.to_python()
    outdf_schema['match'] = bool
    output_df = pl.DataFrame(schema=outdf_schema)

    for g,subdf in cmor_df.group_by(group_columns):
        grp = dict(zip(group_columns,g))

        orig_filters = get_filter(grp,mappings)

        for cmor_row in subdf.iter_rows(named=True):
            cmor_member = cmor_row[member_column]
            orig_member = get_member_id(cmor_member)

            orig_values = orig_df.filter(
                *[pl.col(k) == v for k,v in orig_filters.items()],
                pl.col("member_id") == orig_member
            ).select(*[pl.col(s) for s in stats_columns]).to_numpy()

            cmor_values = np.array([cmor_row[s] for s in stats_columns])
            cmor_row['match'] = np.isclose(cmor_values, orig_values).all()

            out_row = pl.DataFrame(
                cmor_row,
                schema=outdf_schema
            )
            output_df.extend(out_row)
    
    if output_file:
        output_df.write_csv(output_file)
    else:
        output_df.write_csv(cmorized_stats)

if __name__=='__main__':
    args = parser.parse_args()
    main(
        args.cmorized_stats,
        args.original_stats,
        output_file=args.output_file,
        mappings_file=args.mappings,
        member_column=args.member_column
    )



