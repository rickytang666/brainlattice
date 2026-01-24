#!/bin/bash
green='\033[0;32m'
blue='\033[0;34m'
nc='\033[0m'

cd "$(dirname "$0")"

echo -e "${blue}installing deps...${nc}"
npm install --silent

echo -e "${green}starting frontend...${nc}"
npm run dev
