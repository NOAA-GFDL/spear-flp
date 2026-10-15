#!/bin/bash
# note this is an example for running on analysis nodes at GFDL

#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=256G
#SBATCH --partition=analysis
#SBATCH --constraint=avx2

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

###############################################
# Parse args
###############################################

CATURL=$1
STATSDIR=$2
TABLEID=$3
VARID=$4
EXPID=$5
MAPPINGS=$6

###############################################
# Load conda + activate environment
###############################################
module load miniforge
conda activate /work/a3r/conda/envs/aria/ # replace with path to your env

###############################################
# Run python script
###############################################
python $SCRIPTPATH/check_cmor_spear.py \
    $CATURL \
    $STATSDIR \
    --table_id $TABLEID \
    --variable_id $VARID \
    --experiment_id $EXPID \
    --mappings $MAPPINGS