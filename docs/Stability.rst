==========================================
Stability criteria
==========================================
**to be updated**

A micro grid with PV generation can only be called stable during operation, if a large enough fossil-fuelled generator or storage capacity exists. To ensure, that the micro grids optimized components adhere to this stability criteria, an oemof-constraint was introduced. It...

* Limits PV generation penetration to 50~% in a micro grid without storage
* Defines minimal storage capacities for purely renewable operation (Assuming CAP=0.5*max(demand)/C-Rate)
* Ensures that the estimated minimal storage capacity in micro grids majorly relying on PV generation, adheres to the constrains in the OEM

With micro grids interconnected to a blackout-ridden national grid, additional aspects have to be considered:

* In case of later on grid-interconnected micro grids, the stability criteria has to adhered to the off-grid operation (UNCLEAR)
* In case of grid-tied micro grids, the stability criterion can be fullfilled through the main grid interconnection. With blackouts occuring in it's supply, a micro grid with 100% reliability still needs to adhere to above presented constraints.



First documents to be red:

(1) ABB (2012): Integrating renewables into remote or isolated power networks and microgrids. Innovative solutions to ensure power quality and grid stability. http://www02.abb.com/global/seitp/seitp202.nsf/0/d6f1b0d903edac26c1257c37003153fc/$file/brochure-integrating+renewables+into+microgrids.pdf

(2) S. Bifaretti, S.  Cordiner, V. Mulone, V. Rocco, J. L. Rossi, F. Spagnolo (2017): Grid-connected Microgrids to Support Renewable Energy Sources Penetration. https://www.researchgate.net/publication/317309748_Grid-connected_Microgrids_to_Support_Renewable_Energy_Sources_Penetration

(3) https://cleanenergysolutions.org/sites/default/files/documents/10.abb-micro-grids_and_renewable_energy_integration.pdf

(4) naja: http://www.sustainablepowersystems.com/wp-content/uploads/2016/03/GTM-Whitepaper-Integrating-High-Levels-of-Renewables-into-Microgrids.pdf

-> Spinning reserve

(5) https://www.solarwirtschaft.de/fileadmin/user_upload/Session1_4_Intersolar_ARE_event.pdf