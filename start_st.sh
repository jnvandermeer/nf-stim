#!/bin/bash

echo "Starting ST Environment"

source /home/nfcontrol/miniconda3/etc/profile.d/conda.sh

conda activate st

cd /home/nfcontrol/nf/nf-stim/src

python FeedbackController.py
