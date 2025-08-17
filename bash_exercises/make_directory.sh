#!/bin/bash
# This script prompts the user to enter a directory name and creates it.

read -p "Enter new directory name: " dirname
mkdir "$dirname"
echo "Directory '$dirname' created."
