==========================================
Validity test
==========================================

Cases currently analysed:

* **base_oem**: Base case off-grid OEM -> dispatch of same capacities doesn't work out
* **oem_grid_tied_mg**: OEM of grid-tied MG
* **interconnected_buy**: Base OEM interconnected with MG, buy (fix PCC)
* **interconnected_buysell**:  Base OEM interconnected with MG, buy and sell (fix PCC)
* **sole_maingrid**: Supply only by national grid (no stability criterion)

-> But I need to adjust stability constraint again, as this locks pcc consumption directly to constraint, <->  it only HAS TO BE POSSIBLE to consume from grid. Assuming this is the definition.
=> expr += pcc_cap * grid availability

Costs
--------------------------------
* Distribution grid costs are included in all cases
* Main grid interconnection costs are included in all cases with interconnection
* Slight difference in PCC capacity (oem_grid_tied, sole_maingrid), as capacity not batch capacities are

+++++++++++++++++++++++
base_oem
+++++++++++++++++++++++

+++++++++++++++++++++++
interconnected_buy
+++++++++++++++++++++++

+++++++++++++++++++++++
interconnected_sell
+++++++++++++++++++++++

+++++++++++++++++++++++
sole_maingrid
+++++++++++++++++++++++

+++++++++++++++++++++++
oem_grid_tied_mg
+++++++++++++++++++++++