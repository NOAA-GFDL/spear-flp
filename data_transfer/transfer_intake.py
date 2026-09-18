#!/usr/bin/env python

import argparse
import subprocess
from pathlib import Path
import polars as pl
import shutil

gfdl_path_template = [
    'experiment_id',
    'member_id',
    'realm',
    'cell_methods',
    'frequency',
    'chunk_freq'
]

cmip_path_template = [
    'institution_id', 
    'source_id', 
    'experiment_id', 
    'member_id',
    'table_id',
    'variable_id',
    'grid_label',
    'version_id'
]

allowed_filters = [
    'realm',
    'variable_id',
    'experiment_id',
    'frequency',
    'chunk_freq',
    'table_id',
    'member_id'
]

DMGET_RSYNC_SCRIPT = "/work/a3r/Documents/code/spear-flp/data_transfer/dmget_transfer_data.sh"
RSYNC_SCRIPT = "/work/a3r/Documents/code/spear-flp/data_transfer/transfer_data.sh"

parser = argparse.ArgumentParser(
    prog='transfer_intake',
    description='Moves data described by an intake-esm catalog'
)

parser.add_argument('source_catalog')
parser.add_argument('destination')

# Filters:
for x in allowed_filters:
    parser.add_argument(f'--{x}')

# Options:
parser.add_argument(
    '-g',
    '--dmget', 
    action='store_true'
)
parser.add_argument(
    '-n',
    '--dry_run', 
    action='store_true'
)
parser.add_argument(
    '--run_one', 
    action='store_true'
)
parser.add_argument(
    '-o',
    '--output_style', 
    default='gfdl'
)
parser.add_argument(
    '-t',
    '--tmp_dir',
    default=None
)
parser.add_argument(
    '-l',
    '--log_dir', 
    default=None
)
parser.add_argument(
    '-d',
    '--data_dir',
    default=None
)

def _run_transfer(
    sourceDir,
    destDir,
    jobName,
    logPath,
    rsync_flags,
    rsync_filelist,
    dmget_filelist=None
):
    if dmget_filelist is not None:
        subprocess.run([
            "sbatch",
            "-J",
            jobName,
            "--output",
            logPath+'.out',
            "--error",
            logPath+'.err',
            DMGET_RSYNC_SCRIPT,
            dmget_filelist,
            rsync_filelist,
            rsync_flags,
            sourceDir,
            destDir
        ])
    else:
        subprocess.run([
            "sbatch",
            "-J",
            jobName,
            "--output",
            logPath+'.out',
            "--error",
            logPath+'.err',
            RSYNC_SCRIPT,
            rsync_filelist,
            rsync_flags,
            sourceDir,
            destDir
        ])

def transfer_data(
    source_catalog,
    destination,
    filters={},
    data_dir=None,
    tmp_dir=None,
    log_dir=None,
    dry_run=False,
    run_dmget=False,
    run_one=False,
    output_style='gfdl'
):
    if dry_run:
        rsync_flags = '-airnv'
        print(f'-----DRY RUN-----')
    else:
        rsync_flags = '-airv'
    
    baseDir = Path(destination)

    if data_dir:
        dataDir = Path(data_dir)
    else:
        dataDir = baseDir
    if not dry_run:
        dataDir.mkdir(parents=True, exist_ok=True)
    print(f'Saving datasets to {str(dataDir)}')

    if tmp_dir:
        tmpDir = Path(tmp_dir)
    else:
        tmpDir = baseDir / 'tmp'
    if tmpDir.is_dir():
        shutil.rmtree(tmpDir)
    tmpDir.mkdir(parents=True)
    print(f'Saving tmp files to {str(tmpDir)}')

    if log_dir:
        logDir = Path(log_dir)
    else:
        if dry_run:
            logDir = baseDir / 'logs' / 'dry'
        else:
            logDir = baseDir / 'logs'
    logDir.mkdir(parents=True, exist_ok=True)
    print(f'Saving slurm logs to {str(logDir)}')
    
    cat_df = pl.read_csv(source_catalog)
    print(f'Filtering by {filters}')
    subdf = cat_df.filter(*[pl.col(k).is_in(v) for k,v in filters.items()])
    print(f'Filter result shape is {subdf.shape}')

    if output_style.lower() == 'gfdl':
        path_template = gfdl_path_template
    elif output_style.lower() in ['cmip', 'cmip6']:
        path_template = cmip_path_template
    
    for grp,df in subdf.group_by(path_template):
        sourceDir = Path(df['path'][0]).parent

        dest_folder = Path(destination) / '/'.join(grp)
        dest_folder.mkdir(parents=True, exist_ok=True)

        if run_dmget:
            dmget_filelist = tmpDir/('.'.join(grp) + '.dmget.csv')
            df.select('path').write_csv(dmget_filelist, include_header=False)
        else:
            dmget_filelist = None

        rsync_filelist = tmpDir/('.'.join(grp) + '.rsync.csv')
        df.select(pl.col('path').str.split(by='/').list.get(-1)).write_csv(
            rsync_filelist, 
            include_header=False
        )

        jobName = 'trnsfr.'+'.'.join(grp)
        logPath = str(logDir / (jobName+'.%j'))

        print(f'Submitting {jobName} ...')
        _run_transfer(
            sourceDir,
            dest_folder,
            jobName,
            logPath,
            rsync_flags,
            rsync_filelist,
            dmget_filelist=dmget_filelist
        )

        if run_one:
            print('run_one set to True, breaking loop')
            break

if __name__ == '__main__':
    args = parser.parse_args()
    filter_args = {
        k:v.split(',') for k,v in vars(args).items()
        if k in allowed_filters and v is not None
    }
    transfer_data(
        args.source_catalog,
        args.destination,
        log_dir=args.log_dir,
        dry_run=args.dry_run,
        data_dir=args.data_dir,
        run_one=args.run_one,
        tmp_dir=args.tmp_dir,
        run_dmget=args.dmget,
        filters=filter_args,
        output_style=args.output_style
    )
