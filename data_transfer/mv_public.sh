#!/bin/bash

eval $(ssh-agent)
ssh-add /home/pcmdi/.ssh/id_rsa_spear-flp
cd /mnt/data/spear/aria/spear-flp

export PATH="$PATH:/mnt/data/spear/aria/julia-1.11.5/bin"
export JULIA_DEPOT_PATH="/mnt/data/spear/aria/.julia"

julia data_transfer/mv_public.jl