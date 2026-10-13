#!/bin/bash

for i in $(seq 1 30); do
    sbatch ./get_ens_stats_one.sh $1 $i
done