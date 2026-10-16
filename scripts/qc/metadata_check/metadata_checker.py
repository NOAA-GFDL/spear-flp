import os
import glob
import time
import netCDF4
import numpy as np
import csv
import logging
import yaml
import argparse
import fnmatch
from collections import Counter
import dask
from dask.distributed import Client

# --- ARGUMENT PARSING & CONFIG SETUP ---
parser = argparse.ArgumentParser(description="Run QA Metadata Integrity Check.")
parser.add_argument('--config', type=str, required=True, help="Path to the config YAML file")
args = parser.parse_args()

# Load Configuration
with open(args.config, 'r') as f:
    YAML_CONFIG = yaml.safe_load(f)

VAR_NAME = YAML_CONFIG.get('variable_name', 'pr')
EXPECTED_METADATA = YAML_CONFIG.get('expected_metadata', {})

# Path definitions
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

CONFIG = {
    "input_directory": YAML_CONFIG['input_directory'],
    "output_log": os.path.join(PROJECT_ROOT, "logs", YAML_CONFIG.get('log_file', 'metadata_integrity.log')),
    "output_csv_failures": os.path.join(PROJECT_ROOT, YAML_CONFIG.get('output_directory', 'outputs'), YAML_CONFIG.get('output_filename', 'failed_metadata.csv')),
    "member_search_pattern": YAML_CONFIG.get('member_search_pattern', 'pp_ens_*'),
    "file_search_pattern": YAML_CONFIG.get('file_search_pattern', f"*{VAR_NAME}*.nc")
}

def check_file_integrity(filepath: str) -> dict:
    """Reads ONLY metadata and verifies it against the YAML-defined rules."""
    errors = []
    tracking_id = None
    basename = os.path.basename(filepath)
    
    try:
        with netCDF4.Dataset(filepath, 'r') as ds:
            
            # 1. Check Global Attributes
            if "globals" in EXPECTED_METADATA:
                for key, expected_val in EXPECTED_METADATA["globals"].items():
                    if not hasattr(ds, key):
                        errors.append(f"Missing Global Attr: '{key}'")
                    else:
                        actual_val = getattr(ds, key)
                        if isinstance(expected_val, list):
                            if actual_val not in expected_val:
                                errors.append(f"Global '{key}' is '{actual_val}', expected one of {expected_val}")
                        elif actual_val != expected_val:
                            errors.append(f"Global '{key}' is '{actual_val}', expected '{expected_val}'")

            tracking_id = getattr(ds, 'tracking_id', "MISSING_ID")
            if tracking_id == "MISSING_ID":
                errors.append("Missing Global Attr: 'tracking_id'")

            # 2. Check Dimensions
            if "dimensions" in EXPECTED_METADATA:
                for dim, expected_size in EXPECTED_METADATA["dimensions"].items():
                    if dim not in ds.dimensions:
                        errors.append(f"Missing Dimension: '{dim}'")
                    elif ds.dimensions[dim].size != expected_size:
                        errors.append(f"Dim '{dim}' size is {ds.dimensions[dim].size}, expected {expected_size}")

            # 3. Check Variables
            if "variables" in EXPECTED_METADATA:
                for var_name, expected_attrs in EXPECTED_METADATA["variables"].items():
                    if var_name not in ds.variables:
                        errors.append(f"Missing Variable: '{var_name}'")
                        continue
                    
                    var = ds.variables[var_name]
                    for attr, expected_val in expected_attrs.items():
                        if not hasattr(var, attr):
                            errors.append(f"Var '{var_name}' missing attribute '{attr}'")
                        else:
                            actual_val = getattr(var, attr)
                            if isinstance(expected_val, float):
                                if not np.isclose(actual_val, expected_val):
                                    errors.append(f"Var '{var_name}:{attr}' is {actual_val}, expected {expected_val}")
                            else:
                                if actual_val != expected_val:
                                    errors.append(f"Var '{var_name}:{attr}' is '{actual_val}', expected '{expected_val}'")

            # 4. Dynamic Checks
            if "time" in ds.variables and hasattr(ds.variables["time"], "units"):
                if not getattr(ds.variables["time"], "units").startswith("days since"):
                    errors.append(f"Time units do not start with 'days since'. Found: {ds.variables['time'].units}")

            import re
            match = re.search(r'pp_ens_(\d+)', filepath)
            if match and hasattr(ds, 'realization_index'):
                expected_realization = int(match.group(1))
                actual_realization = int(getattr(ds, 'realization_index'))
                if actual_realization != expected_realization:
                    errors.append(f"Folder is ens_{expected_realization:02d} but file realization_index is {actual_realization}")

    except Exception as e:
        errors.append(f"FILE CORRUPTION or READ ERROR: {e}")

    return {
        "filepath": filepath,
        "basename": basename,
        "status": "PASS" if len(errors) == 0 else "FAIL",
        "errors": " | ".join(errors),
        "tracking_id": tracking_id
    }

def main(client: Client):
    os.makedirs(os.path.dirname(CONFIG["output_log"]), exist_ok=True)
    os.makedirs(os.path.dirname(CONFIG["output_csv_failures"]), exist_ok=True)
    
    member_dirs = glob.glob(os.path.join(CONFIG["input_directory"], CONFIG["member_search_pattern"]))
    file_pattern = CONFIG["file_search_pattern"]
    
    file_list = []
    for m_dir in member_dirs:
        for root, dirs, files in os.walk(m_dir, followlinks=True):
            for filename in fnmatch.filter(files, file_pattern):
                file_list.append(os.path.join(root, filename))
    
    if not file_list:
        print(f"No valid files found matching '{file_pattern}'. Exiting.")
        return
        
    print(f"Found {len(file_list)} files. Starting integrity checks...")
    
    futures = client.map(check_file_integrity, file_list)
    results = client.gather(futures)
    
    failed_files = [r for r in results if r["status"] == "FAIL"]
    passed_count = len(results) - len(failed_files)
    
    tracking_ids = [r["tracking_id"] for r in results if r["tracking_id"] != "MISSING_ID"]
    id_counts = Counter(tracking_ids)
    duplicates = {tid: count for tid, count in id_counts.items() if count > 1}
    
    logging.basicConfig(
        filename=CONFIG["output_log"], level=logging.INFO,
        format='%(asctime)s - %(message)s', filemode='w'
    )
    
    logging.info(f"Total Scanned : {len(results)} | Passed: {passed_count} | Failed: {len(failed_files)}")
    
    if failed_files:
        with open(CONFIG["output_csv_failures"], 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["filepath", "basename", "status", "errors", "tracking_id"])
            writer.writeheader()
            for row in failed_files:
                writer.writerow(row)
        print(f"Wrote {len(failed_files)} failures to {CONFIG['output_csv_failures']}")
    else:
        print("All files passed standard metadata checks!")

if __name__ == "__main__":
    client = Client()
    main(client)
    client.close()