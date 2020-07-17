"""
Collect all functions regarding outputs in this file
"""
import pandas as pd
import pprint as pp
import matplotlib

import matplotlib.pyplot as plt
import logging

import oemof.graph as graph
import networkx as nx


def print_oemof_meta_main_invest(experiment, meta, electricity_bus, case_name):
    if experiment["display_meta"] == True:
        logging.info("********* Meta results *********")
        pp.pprint(meta)

    # print the sums of the flows around the electricity bus
    if experiment["display_main"] == True:
        logging.info("********* Main results *********")
        pp.pprint(electricity_bus[SEQUENCES].sum(axis=0))

    # print the scalars of investment optimization (not equal to capacities!)
    if case_name == "base_oem" or case_name == "base_oem_with_min_loading":
        if experiment["display_invest"] == True:
            logging.info("********* Invest results *********")
            pp.pprint(electricity_bus[SCALARS])
    return

def save_mg_flows(experiment, case_dict, e_flows_df, filename):
    logging.debug("Saving flows MG.")
    flows_connected_to_electricity_mg_bus = [
        "Demand AC",
        "Demand DC",
        DEMAND_SHORTAGE,
        DEMAND_SHORTAGE_AC,
        DEMAND_SHORTAGE_DC,
        DEMAND_SUPPLIED,
        PV_GENERATION,
        PV_GENERATION_AC,
        PV_GENERATION_DC,
        WIND_GENERATION,
        EXCESS_GENERATION,
        CONSUMPTION_MAIN_GRID_MG_SIDE,
        "Feed into main grid (MG side)",
        STORAGE_DISCHARGE,
        "Storage discharge AC",
        STORAGE_DISCHARGE_DC,
        "Storage SOC",
        "Storage charge",
        "Storage charge AC",
        STORAGE_CHARGE_DC,
        GENSET_GENERATION,
        GRID_AVAILABILITY,
    ]

    negative_list = [
        DEMAND_SHORTAGE,
        DEMAND_SHORTAGE_AC,
        DEMAND_SHORTAGE_DC,
        STORAGE_DISCHARGE,
        "Storage discharge AC",
        STORAGE_DISCHARGE_DC,
        "Feed into main grid (MG side)",
    ]

    droplist = [
        "Demand AC",
        "Demand DC",
        DEMAND_SHORTAGE_AC,
        DEMAND_SHORTAGE_DC,
        PV_GENERATION_AC,
        PV_GENERATION_DC,
        "Storage discharge AC",
        STORAGE_DISCHARGE_DC,
        "Storage charge AC",
        STORAGE_CHARGE_DC,
    ]

    mg_flows = pd.DataFrame(
        e_flows_df[DEMAND].values,
        columns=[DEMAND],
        index=e_flows_df[DEMAND].index,
    )
    for entry in flows_connected_to_electricity_mg_bus:
        if entry in e_flows_df.columns:
            # do not add energyflow of shortage/supplied demand, if no shortage occurs
            if not (
                (entry == DEMAND_SUPPLIED or entry == DEMAND_SHORTAGE)
                and (
                    sum(e_flows_df[DEMAND].values)
                    == sum(e_flows_df[DEMAND_SUPPLIED].values)
                )
            ):

                if entry in negative_list:
                    # Display those values as negative in graphs/files
                    if entry == "Feed into main grid (MG side)":
                        new_column = pd.DataFrame(
                            -e_flows_df[entry].values,
                            columns=["Feed into main grid"],
                            index=e_flows_df[entry].index,
                        )
                    else:
                        new_column = pd.DataFrame(
                            -e_flows_df[entry].values,
                            columns=[entry],
                            index=e_flows_df[entry].index,
                        )  # Display those values as negative in graphs/files
                elif entry == CONSUMPTION_MAIN_GRID_MG_SIDE:
                    new_column = pd.DataFrame(
                        e_flows_df[entry].values,
                        columns=["Consumption from main grid"],
                        index=e_flows_df[entry].index,
                    )
                else:
                    new_column = pd.DataFrame(
                        e_flows_df[entry].values,
                        columns=[entry],
                        index=e_flows_df[entry].index,
                    )

                mg_flows = mg_flows.join(new_column)

    if experiment[SAVE_TO_CSV_FLOWS_ELECTRICITY_MG] == True:
        mg_flows.to_csv(
            experiment[OUTPUT_FOLDER]
            + "/electricity_mg/"
            + case_dict[CASE_NAME]
            + filename
            + "_electricity_mg.csv"
        )

    if experiment[SAVE_TO_PNG_FLOWS_ELECTRICITY_MG] == True:
        number_of_subplots = 0

        for item in droplist:
            if item in mg_flows.columns:
                mg_flows = mg_flows.drop([item], axis=1)

        if "Storage SOC" in mg_flows.columns:
            mg_flows = mg_flows.drop(["Storage SOC"], axis=1)
            if case_dict[STORAGE_FIXED_CAPACITY] != None:
                number_of_subplots += 1
        if GRID_AVAILABILITY in mg_flows.columns:
            mg_flows = mg_flows.drop([GRID_AVAILABILITY], axis=1)
            if (case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None) or (
                case_dict[PCC_FEEDIN_FIXED_CAPACITY] != None
            ):
                number_of_subplots += 1

        for timeframe in ["year", "days"]:
            if timeframe == "year":
                plot_flows(
                    case_dict, experiment, mg_flows, e_flows_df, number_of_subplots
                )
                plt.savefig(
                    experiment[OUTPUT_FOLDER]
                    + "/electricity_mg/"
                    + case_dict[CASE_NAME]
                    + filename
                    + "_electricity_mg.png",
                    bbox_inches="tight",
                )

            elif timeframe == "days" and (len(mg_flows[DEMAND]) >= 5 * 24):
                plot_flows(
                    case_dict,
                    experiment,
                    mg_flows[24 : 5 * 24],
                    e_flows_df[24 : 5 * 24],
                    number_of_subplots,
                )
                plt.savefig(
                    experiment[OUTPUT_FOLDER]
                    + "/electricity_mg/"
                    + case_dict[CASE_NAME]
                    + filename
                    + "_electricity_mg_4days.png",
                    bbox_inches="tight",
                )
            plt.close()
            plt.clf()
            plt.cla()

    return

def plot_flows(case_dict, experiment, mg_flows, e_flows_df, number_of_subplots):
    if number_of_subplots < 1:
        fig, axes = plt.subplots(nrows=1, figsize=(16 / 2.54, 10 / 2.54 / 2))
        axes_mg = axes
    else:
        fig, axes = plt.subplots(nrows=2, figsize=(16 / 2.54, 10 / 2.54))
        axes_mg = axes[0]

    # website with websafe hexacolours: https://www.colorhexa.com/web-safe-colors
    color_dict = {
        DEMAND: "#33ff00",  # dark green
        DEMAND_SUPPLIED: "#66cc33",  # grass green
        PV_GENERATION: "#ffcc00",  # orange
        WIND_GENERATION: "#33ccff",  # light blue
        GENSET_GENERATION: "#000000",  # black
        "Consumption from main grid": "#990099",  # violet
        "Storage charge": "#0033cc",  # light green
        EXCESS_GENERATION: "#996600",  # brown
        "Feed into main grid": "#ff33cc",  # pink
        STORAGE_DISCHARGE: "#ccccff",  # pidgeon blue
        DEMAND_SHORTAGE: "#ff3300",  # bright red
        "Storage SOC": "#0033cc",  # blue
        GRID_AVAILABILITY: "#cc0000",  # red
    }

    mg_flows.plot(
        title="MG Operation of case "
        + case_dict[CASE_NAME]
        + " in "
        + experiment[PROJECT_SITE_NAME],
        color=[color_dict.get(x, "#333333") for x in mg_flows.columns],
        ax=axes_mg,
        drawstyle="steps-mid",
    )
    axes_mg.set(xlabel="Time", ylabel="Electricity flow in kWh")
    axes_mg.legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)

    if number_of_subplots >= 1:
        ylabel = ""
        if (
            (case_dict[PCC_CONSUMPTION_FIXED_CAPACITY] != None)
            or (case_dict[PCC_FEEDIN_FIXED_CAPACITY] != None)
        ) and (GRID_AVAILABILITY in e_flows_df.columns):
            e_flows_df[GRID_AVAILABILITY].plot(
                ax=axes[1],
                color=color_dict.get(GRID_AVAILABILITY, "#333333"),
                drawstyle="steps-mid",
            )
            ylabel += GRID_AVAILABILITY

        if number_of_subplots > 1:
            ylabel += ",\n "

        if (case_dict[STORAGE_FIXED_CAPACITY] != None) and (
            "Storage SOC" in e_flows_df.columns
        ):
            e_flows_df["Storage SOC"].plot(
                ax=axes[1],
                color=color_dict.get("Storage SOC", "#333333"),
                drawstyle="steps-mid",
            )
            ylabel += "Storage SOC"

        axes[1].set(xlabel="Time", ylabel=ylabel)
        if number_of_subplots > 1:
            axes[1].legend(
                loc="center left", bbox_to_anchor=(1, 0.5), frameon=False
            )

    return

def save_storage(experiment, case_dict, e_flows_df, filename):
    logging.debug("Saving flows storage.")
    if case_dict[STORAGE_FIXED_CAPACITY] != None:

        flows_connected_to_electricity_mg_bus = [
            STORAGE_DISCHARGE,
            "Storage charge",
            "Storage SOC",
        ]
        storage_flows = pd.DataFrame(
            e_flows_df[STORED_CAPACITY].values,
            columns=[STORED_CAPACITY],
            index=e_flows_df[STORED_CAPACITY].index,
        )

        for entry in flows_connected_to_electricity_mg_bus:
            if entry in e_flows_df.columns:
                if entry == STORAGE_DISCHARGE:
                    new_column = pd.DataFrame(
                        -e_flows_df[entry].values,
                        columns=[entry],
                        index=e_flows_df[entry].index,
                    )
                else:
                    new_column = pd.DataFrame(
                        e_flows_df[entry].values,
                        columns=[entry],
                        index=e_flows_df[entry].index,
                    )
                storage_flows = storage_flows.join(new_column)

        if experiment[SAVE_TO_CSV_FLOWS_STORAGE] == True:
            storage_flows.to_csv(
                experiment[OUTPUT_FOLDER]
                + "/storage/"
                + case_dict[CASE_NAME]
                + filename
                + "_storage.csv"
            )

        if experiment[SAVE_TO_PNG_FLOWS_STORAGE] == True:
            fig = storage_flows.plot(
                title="Storage flows of case "
                + case_dict[CASE_NAME]
                + " in "
                + experiment[PROJECT_SITE_NAME]
            )
            fig.set(xlabel="Time", ylabel="Electricity flow/stored in kWh")
            fig.legend(loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)
            plt.savefig(
                experiment[OUTPUT_FOLDER]
                + "/storage/"
                + case_dict[CASE_NAME]
                + filename
                + "_storage.png",
                bbox_inches="tight",
            )
            plt.close()
            plt.clf()
            plt.cla()
            if len(storage_flows[STORED_CAPACITY]) >= 5 * 24:
                fig = storage_flows[24 : 5 * 24].plot(
                    title="Storage flows of case "
                    + case_dict[CASE_NAME]
                    + " in "
                    + experiment[PROJECT_SITE_NAME]
                )
                fig.set(xlabel="Time", ylabel="Electricity flow/stored in kWh")
                fig.legend(
                    loc="center left", bbox_to_anchor=(1, 0.5), frameon=False
                )
                plt.savefig(
                    experiment[OUTPUT_FOLDER]
                    + "/storage/"
                    + case_dict[CASE_NAME]
                    + filename
                    + "_storage_4days.png",
                    bbox_inches="tight",
                )
                plt.close()
                plt.clf()
                plt.cla()
    return

def save_network_graph(energysystem, case_name):
    logging.debug("Generate networkx diagram")
    energysystem_graph = graph.create_nx_graph(energysystem)
    graph_file_name = case_name + "_graph"
    graph_path = "./simulation_results/" + graph_file_name
    nx.readwrite.write_gpickle(G=energysystem_graph, path=graph_path)
    energysystem_graph = nx.readwrite.read_gpickle(graph_path)
    matplotlib.rcParams["figure.figsize"] = [20.0, 15.0]

    draw_graph(
        energysystem_graph,
        case_name,
        node_size=5500,
        node_color={
            "coal": "#0f2e2e",
            "gas": "#c76c56",
            "oil": "#494a19",
            "lignite": "#56201d",
            "bel": "#9a9da1",
            "bth": "#cd3333",
            WIND: "#4ca7c3",
            PV: "#ffde32",
            "demand_el": "#9a9da1",
            "excess_el": "#9a9da1",
            "demand_th": "#cd3333",
            "pp_coal": "#0f2e2e",
            "pp_lig": "#56201d",
            "pp_gas": "#c76c56",
            "pp_oil": "#494a19",
            "pp_chp": "#eeac7e",
            "b_heat_source": "#cd3333",
            "heat_source": "#cd3333",
            "heat_pump": "#42c77a",
        },
        edge_color="#eeac7e",
    )

def draw_graph(
    grph,
    case_name,
    edge_labels=True,
    node_color="#AFAFAF",
    edge_color="#CFCFCF",
    plot=True,
    node_size=2000,
    with_labels=True,
    arrows=True,
    layout="neato",
):
    """
    Draw a graph. This function will be removed in future versions.

    Parameters
    ----------
    grph : networkxGraph
        A graph to draw.
    edge_labels : boolean
        Use nominal values of flow as edge label
    node_color : dict or string
        Hex color code oder matplotlib color for each node. If string, all
        colors are the same.

    edge_color : string
        Hex color code oder matplotlib color for edge color.

    plot : boolean
        Show matplotlib plot.

    node_size : integer
        Size of nodes.

    with_labels : boolean
        Draw node labels.

    arrows : boolean
        Draw arrows on directed edges. Works only if an optimization_model has
        been passed.
    layout : string
        networkx graph layout, one of: neato, dot, twopi, circo, fdp, sfdp.
    """
    if type(node_color) is dict:
        node_color = [node_color.get(g, "#AFAFAF") for g in grph.nodes()]

    # set drawing options
    options = {
        "prog": "dot",
        "with_labels": with_labels,
        #'node_color': node_color,
        "edge_color": edge_color,
        "node_size": node_size,
        "arrows": arrows,
    }

    # draw graph
    pos = nx.drawing.nx_agraph.graphviz_layout(grph, prog=layout)

    nx.draw(grph, pos=pos, **options)

    # add edge labels for all edges
    if edge_labels is True and plt:
        labels = nx.get_edge_attributes(grph, "weight")
        nx.draw_networkx_edge_labels(grph, pos=pos, edge_labels=labels)

    # show output
    if plot is True:
        plt.show()

    return
