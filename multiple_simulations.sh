#!/usr/bin/env bash

cd ../../masterthesis_oemof_virt/bin/
source activate
cd ../../Code/simulator_grid-connected_micro_grid

#cd ~/masterthesis_oemof/bin/
#source activate
#cd /mnt/Storage/Documents/Studium/Masterthesis/00_Code/simulator_grid-connected_micro_grid.git/

# Check if working
#python3 A_main_script.py ./inputs/reliable_stage3_mgs.xlsx
#cp ./simulation_results/reliable_stage3_mgs/results_reliable_stage3_mgs.csv /home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_results/results_reliable_stage3_mgs.csv
#cp -r ./simulation_results/reliable_stage3_mgs/electricity_mg/ /home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_results/reliable_graphs

#python3 A_main_script.py ./inputs/unreliable_stage3_mgs.xlsx
#cp ./simulation_results/unreliable_stage3_mgs/results_unreliable_stage3_mgs.csv /home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_results/results_unreliable_stage3_mgs.csv
#cp -r ./simulation_results/unreliable_stage3_mgs/electricity_mg/ /home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_results/unreliable_graphs

# reliable cases
#python3 A_main_script.py ./inputs/reliable_stage1_mgs.xlsx
#cp ./simulation_results/reliable_stage1_mgs/results_reliable_stage1_mgs.csv /home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_results/results_reliable_stage1_mgs.csv

#python3 A_main_script.py ./inputs/reliable_stage2_mgs.xlsx
#cp ./simulation_results/unreliable_stage2_mgs/results_reliable_stage2_mgs.csv /home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_results/results_reliable_stage2_mgs.csv

# Analyse unreliable cases
#python3 A_main_script.py ./inputs/unreliable_stage1_mgs.xlsx
#cp ./simulation_results/reliable_stage1_mgs/results_unreliable_stage1_mgs.csv /home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_results/results_unreliable_stage1_mgs.csv

#python3 A_main_script.py ./inputs/unreliable_stage2_mgs.xlsx
#cp ./simulation_results/unreliable_stage2_mgs/results_unreliable_stage2_mgs.csv /home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_results/results_unreliable_stage2_mgs.csv

# simulating all no mg locations (less important)
#python3 A_main_script.py ./inputs/reliable_no_mgs.xlsx3
#cp ./simulation_results/reliable_no_mgs/results_reliable_no_mgs.csv /home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_results/results_reliable_no_mgs.csv

#python3 A_main_script.py ./inputs/unreliable_no_mgs.xlsx
#cp ./simulation_results/unreliable_no_mgs/results_unreliable_no_mgs.csv /home/local/RL-INSTITUT/martha.hoffmann/Desktop/Nextcloud/Masterthesis/Nigeria_results/results_unreliable_no_mgs.csv
