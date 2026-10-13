# Get Ensemble Stats

The main script is `get_ens_stats.py`. It takes two inputs,
```
python get_ens_stats.py $CATALOG $MEMBER_NUMBER
```
- `$CATALOG` : the url or path to the CSV file of the Intake-ESM catalog.
- `$MEMBER_NUMBER` : the member id number that should be run (e.g., to run `pp_ens_02` input `2`)

And outputs, by default, for each `experiment_id`, `realm`, and `variable_id` a csv with the min, max, mean, and standard deviation for each `member_id`, over space and all times. Subsequent runs with different `$MEMBER_NUMBER` will append to the first csv created.

There are also three settings within that script
- `output_path` : base directory where output should be saved.
- `output_path_template` : defines how the folder structure is made from metadata. e.g., `['experiment_id', 'realm']` will result in folder structure like `<output_path>/<experiment_id>/<realm>`
- `output_file_template` : determines the metadata contained in the resulting filename. e.g., `['variable_id']` will result in files that are named `<variable_id>.csv`

In order to run this at GFDL for SPEAR-MED there are two additional scripts
- `get_ens_stats_one.sh` : submits a single job to slurm
- `get_ens_stats_all.sh` : submits all 30 ensemble members at once

`get_ens_stats_one.sh` has the same inputs as `get_ens_stats.py`. `get_ens_stats_all.sh` takes only the catalog path as input.