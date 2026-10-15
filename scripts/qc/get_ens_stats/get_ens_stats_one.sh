#!/bin/bash 
# note this is an example for running on analysis nodes at GFDL

#SBATCH --partition=analysis
#SBATCH --time=72:00:00
#SBATCH --nodes=1

#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=128GB
#SBATCH --constraint=avx2

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

module load miniforge
conda activate /work/a3r/conda/envs/aria/ # replace with path to your env
python $SCRIPTPATH/get_ens_stats.py $1 $2