#!/usr/bin/env bash

cd ../../masterthesis_oemof_virt/bin/
source activate
cd ../../Code/simulator_grid-connected_micro_grid

python3 A_main_script.py ./inputs/reliable_stage1_mgs.xlsx
python3 A_main_script.py ./inputs/reliable_stage2_mgs.xlsx
python3 A_main_script.py ./inputs/reliable_stage3_mgs.xlsx

#python3 A_main_script.py ./inputs/shs_stage1_mgs.xlsx
#python3 A_main_script.py ./inputs/shs_stage2_mgs.xlsx
#python3 A_main_script.py ./inputs/shs_stage3_mgs.xlsx

#python3 A_main_script.py ./inputs/unreliable_stage1_mgs.xlsx
#python3 A_main_script.py ./inputs/unreliable_stage2_mgs.xlsx
#python3 A_main_script.py ./inputs/unreliable_stage3_mgs.xlsx


#python3 A_main_script.py ./inputs/shs_shortage_stage1_mgs.xlsx
#python3 A_main_script.py ./inputs/shs_shortage_stage2_mgs.xlsx
#python3 A_main_script.py ./inputs/shs_shortage_stage3_mgs.xlsx

python3 A_main_script.py ./inputs/reliable_no_mgs.xlsx
#python3 A_main_script.py ./inputs/shs_shortage_no_mgs.xlsx
python3 A_main_script.py ./inputs/shs_no_mgs.xlsx
#python3 A_main_script.py ./inputs/unreliable_no_mgs.xlsx