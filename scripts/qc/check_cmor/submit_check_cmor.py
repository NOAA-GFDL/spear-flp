import argparse
import subprocess
import pathlib
import polars as pl

thisDir = pathlib.Path(__file__).parent.resolve()
SCRIPT=thisDir/'check_cmor_spear_one.sh'

parser = argparse.ArgumentParser(
                description='Submits fremor checker as slurm jobs, running a separate job for each experiment_id, table_id, and variable_id set. Check docs for necessary edits to the slurm script.'
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
    '--mappings',
    default=thisDir / 'spear_mappings.json',
    help="Describes how to map the experiment_id, table_id, and variable_id to the precomputed stats directory structure. See the default file spear_mappings.json for an example of how to format this."
)

def main(catPath, statsDir, mappings=thisDir/'spear_mappings.json'):
    cat_df = pl.read_csv(catPath)
    for grp,subdf in cat_df.group_by([
        "experiment_id", 
        "table_id", 
        "variable_id"
    ]):
        exp_id,tab_id,var_id = grp
        print(f"Submitting job {grp}...")
        subprocess.run([
            "sbatch",
            SCRIPT,
            catPath,
            statsDir,
            tab_id,
            var_id,
            exp_id,
            str(mappings)
        ])

if __name__=='__main__':
    args = parser.parse_args()
    main(
        args.catalog_path,
        args.stats_dir,
        mappings=args.mappings
    )