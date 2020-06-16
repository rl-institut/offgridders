Multicriteria Analysis
=======================

Definition and goals
---------------------
A multicriteria analysis (MCA) is used to evaluate solutions considering multiple criteria, usually grouped in different dimensions: economic, technical, social, institutional and environmental. Studies have proved that selecting solutions based exclusively in technical and economic issues is not enough to ensure a long-term sustainability of the project. In that line, multicriteria analysis provide a holistic approach for the decision process.
The solutions evaluated come from the optimization of different electrification scenarios (that can consider different technologies of electricity generation or different values of the technical parameters through the sensitiviy analysis). The outputs of the optimization process (optimal power capacities, optimal dispatch, initial investment costs, etc.) are used to evaluate the solutions in the different criteria of the MCA. Therefore, a perfect integration between optimization and evaluation can be achieved.

Input files
-----------
Initial considerations
_______________________
The MCA can be activated or deactivated in the settings tab: perform_multicriteria_analysis = True. Also, to display the results correctly, sensivity_all_combinations must be also True

Input parameters
__________________
The MCA needs:
* Weights of the dimensions and criteria. The user might want to give a different importance rating (weight) to each criterion and dimension, considering the particular features and context of the project. When filling the weights, two rules must be considered: the sum of the weights of all dimensions must equal 1, and the sum of the weights of all criteria inside each dimension must equal 1.
* Punctuations on the different technologies of electricity generation (PV, wind, diesel, and the national grid). Some of the criteria are closely related to the performance of each technology. For example, diesel generators can be very well accepted by the end users, but might be against of the national governments plans.
The user of the tool can use the default values given in the test_input_template.

Moreover, the MCA allows to choose which parameters included in the sensitivity analysis are also included and displayed in the MCA. Finally, it can be useful to see plotted the evaluations of all electrification solutions regarding one specific criterion.


Code structure
_______________
Two files of the code folder are used for the MCA: H0_multicriteria_analysis.py and H1_multicriteria_functions.py.
Each important section of the code has been commented to allow full understanding.

Output files
_____________
The MCA creates one file (MCA_evaluations.xlsx) and one folder (MCA_plots) to store the plots required. The excel file follows the next structure to present the results:
1. The solutions analysed are displayed. A different number of solutions are analysed depending on the number of case scenarios and the parameters selected from the sensitivity analysis.
2. The main outputs of the optimizations (optimal power capacities) are displayed.
3. Evaluations of the criteria
4. Normalized evaluations of the criteria. If a criterion does not make any difference between the solutions, and therefore every solution has the same value for that criterion, these evaluations cannot be normalized. In that case, the text "None" will be displayed and the weight of this criterion is turned into 0, and modifying the weights of the other criteria of that dimension accordingly.
5. The distance from each solution to an ideal utopian solution (L) is calculated. The lower the L value for one alternative, the better the alternative is. A ranking is also displayed.
6. Finally, the same ranking procedure is repeated for each combination of parameters displayed from the sensitivity analysis. Thus, an analysis within each particular combination is allowed.


