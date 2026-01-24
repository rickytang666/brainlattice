#!/bin/bash
venv=".venv"
green='\033[0;32m'
nc='\033[0m'

cd "$(dirname "$0")"

# ensure venv exists
[ ! -d "$venv" ] && python3 -m venv $venv

# activate
source $venv/bin/activate

# quiet dep check
pip install -r requirements.txt -q

# start
echo -e "${green}starting server...${nc}"
uvicorn main:app --reload
