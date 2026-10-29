"""This script checks for rogue pixels in NetCDF climate outputs 
using Dask for parallel processing. It is driven entirely by a YAML config file."""

import os
import glob
import logging
import time
import netCDF4
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import yaml
import dask
import argparse
import fnmatch
from dask.distributed import Client, progress
from datetime import timedelta

# --- ARGUMENT PARSING & CONFIG SETUP ---
parser = argparse.ArgumentParser(description="Run QA rogue pixel check.")
parser.add_argument('--config', type=str, required=True, help="Path to the config YAML file")
args = parser.parse_args()

# Load Configuration
with open(args.config, 'r') as f:
    CONFIG = yaml.safe_load(f)

# Path definitions
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Update output paths to be absolute
CONFIG['output_directory'] = os.path.join(PROJECT_ROOT, CONFIG.get('output_directory', 'outputs'))
CONFIG['log_file'] = os.path.join(PROJECT_ROOT, 'logs', CONFIG.get('log_file', 'rogue_pixel_qa.log'))


def create_alert_plot(data: np.ndarray, lons: np.ndarray, lats: np.ndarray, date: object, filepath: str, t_index: int) -> None:
    """Generates and saves a plot for a specific timestep when an anomaly is detected."""
    try:
        fig = plt.figure(figsize=CONFIG['plot_settings'].get("figure_size", [8, 5]))
        ax = plt.axes(projection=ccrs.Robinson())
        ax.set_global()
        
        mesh = ax.pcolormesh(
            lons, lats, data, transform=ccrs.PlateCarree(),
            cmap=CONFIG['plot_settings'].get("cmap", "viridis")
        )
        ax.coastlines()
        ax.gridlines(draw_labels=False)
        
        cbar = plt.colorbar(mesh, orientation='vertical', pad=0.02, aspect=30, shrink=0.8)
        cbar.set_label(CONFIG['plot_settings'].get("cbar_label", "Value"))
        
        start_time = date
        end_time = start_time + timedelta(hours=6)
        basename = os.path.basename(filepath)
        
        # Dynamic Title
        alert_title = CONFIG['plot_settings'].get("alert_title", "Anomaly Detected")
        title = f"{alert_title}\nSource: {basename} ({start_time.strftime('%Y-%m-%d %H:%M')}-{end_time.strftime('%H:%M')})"
        ax.set_title(title, pad=20)
        
        sanitized_path = basename.replace('.nc', '')
        plot_filename = f"ALERT_{sanitized_path}_timestep_{t_index:05d}.png"
        save_path = os.path.join(CONFIG["output_directory"], plot_filename)
        
        plt.savefig(save_path, dpi=CONFIG['plot_settings'].get("dpi", 150), bbox_inches='tight')
        
    except Exception as e:
        print(f"Error plotting {filepath} at timestep {t_index}: {e}")
    finally:
        plt.close(fig)

@dask.delayed
def process_single_file(filepath: str) -> str:
    """Processes a single NetCDF file and returns a log message."""
    start_time = time.time()
    anomaly_found = False
    basename = os.path.basename(filepath)
    
    try:
        with netCDF4.Dataset(filepath, 'r') as ds:
            if CONFIG["variable_name"] not in ds.variables:
                return f"SKIPPED: {basename} (Variable '{CONFIG['variable_name']}' not found)"

            var_data = ds.variables[CONFIG["variable_name"]]
            lats = ds.variables[CONFIG["lat_dim"]][:]
            lons = ds.variables[CONFIG["lon_dim"]][:]
            time_var = ds.variables[CONFIG["time_dim"]]
            num_timesteps = len(time_var)

            # Get parameters from config
            conv_factor = CONFIG.get("conversion_factor", 1.0)
            max_thresh = CONFIG.get("max_threshold")
            min_thresh = CONFIG.get("min_threshold")

            for t_index in range(num_timesteps):
                data_slice = var_data[t_index, :, :]
                scaled_data = data_slice * conv_factor
                
                # Check thresholds gracefully (ignores None)
                has_high = (max_thresh is not None) and np.any(scaled_data > max_thresh)
                has_low = (min_thresh is not None) and np.any(scaled_data < min_thresh)
                
                if has_high or has_low:
                    anomaly_found = True
                    date = netCDF4.num2date(time_var[t_index], time_var.units, getattr(time_var, 'calendar', 'standard'))
                    
                    print(f"\nALERT! Anomaly in {basename} at step {t_index}. Plotting...")
                    create_alert_plot(scaled_data, lons, lats, date, filepath, t_index)

        duration = time.time() - start_time
        print(f"COMPLETED: {basename} in {duration:.2f} seconds.")

        if anomaly_found:
            return f"{filepath} processed in {duration:.2f}s, ROGUE PIXELS FOUND (Exceeded bounds)!"
        else:
            return f"{filepath} processed in {duration:.2f}s, no rogue values found."

    except Exception as e:
        duration = time.time() - start_time
        print(f"ERROR: Failed to process {basename} after {duration:.2f}s.")
        return f"ERROR processing {filepath} after {duration:.2f}s. Reason: {e}"

def main() -> None:
    os.makedirs(CONFIG["output_directory"], exist_ok=True)
    os.makedirs(os.path.dirname(CONFIG["log_file"]), exist_ok=True)
    
    # 1. First find all ensemble member directories
    member_pattern = CONFIG.get("member_search_pattern", "pp_ens_*")
    member_dirs = glob.glob(os.path.join(CONFIG["input_directory"], member_pattern))
    
    # 2. Get the target filename pattern (e.g., "*t_ref_max*.nc")
    default_pattern = f'*{CONFIG["variable_name"]}*.nc'
    file_pattern = CONFIG.get("file_search_pattern", default_pattern)
    
    # 3. Bulletproof HPC Search: Walk through every directory, forcing symlinks to be followed
    file_list = []
    for m_dir in member_dirs:
        for root, dirs, files in os.walk(m_dir, followlinks=True):
            for filename in fnmatch.filter(files, file_pattern):
                file_list.append(os.path.join(root, filename))
    
    if not file_list:
        print(f"No valid files found matching '{file_pattern}' inside '{CONFIG['input_directory']}'. Exiting.")
        return
        
    print(f"Found {len(file_list)} files to process for variable '{CONFIG['variable_name']}'.")
    
    tasks = [process_single_file(fp) for fp in file_list]
    
    print("Starting Dask client and processing files in parallel...")
    results = dask.compute(*tasks)
    progress(results)
    
    logging.basicConfig(
        filename=CONFIG["log_file"],
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filemode='w'
    )
    
    print(f"\nAll processing complete. Writing results to '{CONFIG['log_file']}'...")
    for log_message in results:
        logging.info(log_message)

    print("Done.")

if __name__ == "__main__":
    client = Client()
    print(f"Dask client started. Dashboard link: {client.dashboard_link}")
    main()
    client.close()