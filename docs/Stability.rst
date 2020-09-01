==========================================
Stability criteria
==========================================
**to be updated**

A micro grid with PV generation can only be called stable during operation, if a large enough fossil-fuelled generator or storage capacity exists. To ensure, that the micro grids optimized components adhere to this stability criteria, an oemof-constraint was introduced. It...

* Limits PV generation penetration to 50~% in a micro grid without storage
* Defines minimal storage capacities for purely renewable operation (Assuming CAP=0.5*max(demand)/C-Rate)
* Ensures that the estimated minimal storage capacity in micro grids majorly relying on PV generation, adheres to the constrains in the OEM

With micro grids interconnected to a blackout-ridden national grid, additional aspects have to be considered:

* In case of later-on grid-interconnected micro grids, the stability criteria has to adhered to by the during off-grid operation of the MG. 
* In case of grid-tied micro grids, the stability criterion can be fullfilled through the main grid interconnection. With blackouts occuring in it's supply, a micro grid with 100% reliability still needs to adhere to above presented constraints.
