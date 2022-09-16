#!/bin/bash

while getopts i:m:q:s: flag
do
    case "${flag}" in
        i) interval=${OPTARG};;
        m) markettype=${OPTARG};;
        q) quotedasset=${OPTARG};;
        s) streamtype=${OPTARG};;
    esac
done

# set directory. DIFFERENT IN EVERY MACHINE, UNLESS USE DOCKER.
cd /home/llagask/Trading/polaris_beta/capture-data

# activate virtual environment. DIFFERENT IN EVERY MACHINE, UNLESS USE DOCKER, IN THIS CASE IS UNNECESSARY.
source ../.venv/bin/activate

python3 obtain-data-klines.py \
--updatedb \
--interval $interval \
--markettype $markettype \
--quotedasset $quotedasset \
--streamtype $streamtype \
2>> /home/llagask/Trading/polaris_beta/capture-data/errors.txt

# deactivate virtual environment
deactivate
