#!/bin/bash
# This script prompts the user to enter two numbers and outputs their sum.

read -p "Enter first number: " a
read -p "Enter second number: " b
sum=$((a + b))
echo "Sum: $sum"
read -p "Press Enter to continue..." # Waits for Enter key press