#!/bin/bash
DRIVES=(
/dev/sdf
/dev/sdh
/dev/sdk
/dev/sdm
/dev/sdi
/dev/sdl
/dev/sdn
/dev/sdo
/dev/sdg
/dev/sdj
/dev/sda
/dev/sde
/dev/sdb
/dev/sdc
/dev/sdd
)

for drive in "${DRIVES[@]}"; do
  hours=$(sudo smartctl -A "$drive" 2>/dev/null | awk '$2 == "Power_On_Hours" {print $10}')
  if [[ -n "$hours" ]]; then
    echo "$drive : $hours hours"
  else
    echo "$drive : Power_On_Hours not found"
  fi
done

