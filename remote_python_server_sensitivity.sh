#!/usr/bin/env bash

#ssh rl-institut.local\\martha.hoffmann@192.168.11.220
#sudo mount.cifs -o user=martha.hoffmann,dom=rl-institut,uid=RL-INSTITUT\\martha.hoffmann //192.168.10.14/UserShares ~/user_shares/

cd ./master_thesis_simulation_mgs/simulator_grid-connected_micro_grid/ma_tool/bin/
source activate
cd ../../

python3 A_main_script.py ./inputs/electricity_price_sensitivity.xlsx
cp ~/master_thesis_simulation_mgs/simulator_grid-connected_micro_grid/simulation_results/electricity_price_sensitivity/results_electricity_price_sensitivity.csv ~/user_shares/Martha.Hoffmann/Nigeria_results_sync

python3 A_main_script.py ./inputs/blackout_sensitivity.xlsx
cp ~/master_thesis_simulation_mgs/simulator_grid-connected_micro_grid/simulation_results/blackout_sensitivity/results_blackout_sensitivity.csv ~/user_shares/Martha.Hoffmann/Nigeria_results_sync

exit
cp -r /home/local/RL-INSTITUT/martha.hoffmann/user_shares/Martha.Hoffmann/Nigeria_results_sync/ /home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_results/