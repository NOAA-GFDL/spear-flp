import polars as pl
from netCDF4 import Dataset
from pathlib import Path
import argparse

parser=argparse.ArgumentParser(
    description="Generate a CSV catalog from netCDF files stored in the CMIP format within a given input_directory."
)

parser.add_argument(
    "input_directory",
    nargs="?",
    default=None,
    help="Directory to scan for files."
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

default_columns = [
    "activity_id",
    "experiment_id",
    "frequency",
    "grid_label",
    "institution_id",
    "model_id",
    "project_id",
    "realm",
    "source_id",
    "table_id",
    "variable_id",
    "variant_label",
    "standard_name",
    "time_range"
]

filename_properties = [
    "variable_id",
    "table_id",
    "model_id",
    "experiment_id",
    "variant_label",
    "grid_label",
    "time_range"
]

def _load_config(config_file: str) -> dict:
    with open(config_file, 'r') as f:
        yaml_conf = yaml.safe_load(f)
    config_dict = {
        "input_directory": yaml_conf.get("input_directory", None),
        "output_file": yaml_conf.get("output_file", None),
        "columns": yaml_conf.get("columns", default_columns),
        "filename_pattern": yaml_conf.get("filename_pattern", filename_properties)
    }
    return config_dict

def _load_inputs(input_parser: argparse.ArgumentParser):
    args = input_parser.parse_args()
    
    if args.config:
        input_dict = _load_config(args.config)
    else:
        input_dict = {
            "columns": default_columns,
            "filename_pattern": filename_properties
        }

    if args.input_directory:
        input_dict["input_directory"] = args.input_directory

    if args.output_file:
        input_dict["output_file"] = args.output_file

    return input_dict

def generate_catalog(
    input_directory,
    output_file,
    columns=default_columns,
    filename_pattern=filename_properties
):
    df_columns = columns.copy()
    df_columns.append('path')

    rootDir = Path(input_directory).resolve()
    files = list(rootDir.rglob('*.nc'))

    file_props = []

    for f in files:
        with Dataset(f,'r') as ds:
            metadata = {}
            metadata['path'] = str(f)

            filename_props = f.stem.split('_')
            for i,x in enumerate(filename_properties):
                if x in df_columns:
                    metadata[x] = filename_props[i]

            var_id = ds.getncattr('variable_id')

            global_attrs = ds.ncattrs()
            var_attrs = ds[var_id].ncattrs()

            for c in df_columns:
                if c in global_attrs:
                    metadata[c] = ds.getncattr(c)
                elif c in var_attrs:
                    metadata[c] = ds[var_id].getncattr(c)
                else:
                    print(f"Warning: File {str(f)} has no metadata for {c}.")
            
            file_props.append(metadata)
    
    output_df = pl.from_dicts(file_props, schema=headers)
    output_df.write_csv(output_file)
            
if __name__=="__main__":
    input_dict = _load_inputs(parser)
    generate_catalog(
        input_dict["input_directory"],
        input_dict["output_file"],
        columns=input_dict["columns"],
        filename_pattern=input_dict["filename_pattern"]
    )
