#!/usr/bin/env bash

#ssh rl-institut.local\\martha.hoffmann@192.168.11.220
#sudo mount.cifs -o user=martha.hoffmann,dom=rl-institut,uid=RL-INSTITUT\\martha.hoffmann //192.168.10.14/UserShares ~/user_shares/

cd ./master_thesis_simulation_mgs/simulator_grid-connected_micro_grid/ma_tool/bin/
source activate
cd ../../

python3 A_main_script.py ./inputs/reliable_stage3_mgs.xlsx
cp -r ~/master_thesis_simulation_mgs/simulator_grid-connected_micro_grid/simulation_results/reliable_stage3_mgs ~/user_shares/Martha.Hoffmann/Nigeria_results_sync
cp ~/master_thesis_simulation_mgs/simulator_grid-connected_micro_grid/simulation_results/reliable_stage3_mgs/results_reliable_stage3_mgs.csv ~/user_shares/Martha.Hoffmann/Nigeria_results_sync

python3 A_main_script.py ./inputs/unreliable_stage3_mgs.xlsx
cp -r ~/master_thesis_simulation_mgs/simulator_grid-connected_micro_grid/simulation_results/unreliable_stage3_mgs ~/user_shares/Martha.Hoffmann/Nigeria_results_sync
cp ~/master_thesis_simulation_mgs/simulator_grid-connected_micro_grid/simulation_results/unreliable_stage3_mgs/results_unreliable_stage3_mgs.csv ~/user_shares/Martha.Hoffmann/Nigeria_results_sync

python3 A_main_script.py ./inputs/reliable_feedin.xlsx
cp ~/master_thesis_simulation_mgs/simulator_grid-connected_micro_grid/simulation_results/reliable_feedin/results_reliable_feedin.csv ~/user_shares/Martha.Hoffmann/Nigeria_results_sync

python3 A_main_script.py ./inputs/unreliable_feedin.xlsx
cp ~/master_thesis_simulation_mgs/simulator_grid-connected_micro_grid/simulation_results/unreliable_feedin/results_unreliable_feedin.csv ~/user_shares/Martha.Hoffmann/Nigeria_results_sync

exit
cp -r /home/local/RL-INSTITUT/martha.hoffmann/user_shares/Martha.Hoffmann/Nigeria_results_sync/ /home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_results/