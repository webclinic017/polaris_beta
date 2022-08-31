#!/bin/bash

# e.g:
# updater-manager.sh 1d 

while getopts i:m: flag
do
    case "${flag}" in
        i) interval=${OPTARG};;
        m) markettype=${OPTARG};;
    esac
done

# set directory. DIFFERENT IN EVERY MACHINE, UNLESS USE DOCKER.
cd /home/llagask/Trading/polaris_beta/capture-data

# activate virtual environment. DIFFERENT IN EVERY MACHINE, UNLESS USE DOCKER, IN THIS CASE IS UNNECESSARY.
source ../.venv-p39/bin/activate

# For testing purpose.
# python3 obtain-data-klines.py --updatedb --markettype spot_margin --interval 15m --symbol BTCUSDT --symbol ETHUSDT --streamtype klines 2>> errors.txt

python3 obtain-data-klines.py --updatedb --markettype spot_margin --interval $interval --portfoliosymbols --streamtype klines 2>> errors.txt

# deactivate virtual environment
deactivate

