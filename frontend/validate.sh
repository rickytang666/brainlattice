#!/bin/bash
green='\033[0;32m'
red='\033[0;31m'
yellow='\033[1;33m'
nc='\033[0m'

echo -e "${yellow}validating frontend...${nc}"

echo -e "1. linting..."
if npm run lint; then
    echo -e "${green}lint passed${nc}"
else
    echo -e "${yellow}lint failed${nc}"
    exit 1
fi

echo -e "2. building..."
if npm run build; then
    echo -e "${green}build passed${nc}"
else
    echo -e "${red}build failed${nc}"
    exit 1
fi

echo -e "${green}all checks passed${nc}"
