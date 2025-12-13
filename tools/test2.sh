#!/bin/bash
# Description: Interactive greeting script that displays custom messages based on user input
# Author: Test Script
# Version: 1.0.0

set -euo pipefail

# Colors
GREEN='\033[1;32m'
BLUE='\033[1;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Interactive Greeting Script       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Get user's name
read -p "Enter your name: " name

if [ -z "$name" ]; then
  echo -e "${YELLOW}No name provided. Using 'Guest'${NC}"
  name="Guest"
fi

# Get user's mood
echo ""
echo "How are you feeling today?"
echo "1) Happy"
echo "2) Excited"
echo "3) Relaxed"
echo "4) Curious"
echo ""
read -p "Select (1-4): " mood

case $mood in
  1)
    echo -e "\n${GREEN}🎉 Hello $name! Great to see you happy today!${NC}"
    ;;
  2)
    echo -e "\n${GREEN}🚀 Hello $name! Your excitement is contagious!${NC}"
    ;;
  3)
    echo -e "\n${GREEN}😌 Hello $name! Enjoy your relaxed state!${NC}"
    ;;
  4)
    echo -e "\n${GREEN}🔍 Hello $name! Stay curious and keep learning!${NC}"
    ;;
  *)
    echo -e "\n${YELLOW}Hello $name! Have a wonderful day!${NC}"
    ;;
esac

# Show system info
echo ""
echo -e "${BLUE}System Information:${NC}"
echo -e "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "  User: $(whoami)"
echo -e "  Hostname: $(hostname)"
echo -e "  Uptime: $(uptime -p)"
echo ""
