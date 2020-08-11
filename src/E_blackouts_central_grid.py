import pandas as pd
import numpy as np
import logging
import os.path
from copy import deepcopy

from src.constants import (
    OUTPUT_FOLDER,
    INPUT_FOLDER_TIMESERIES,
    RESTORE_BLACKOUTS_IF_EXISTENT,
    TIMESTEP,
    MAX_DATE_TIME_INDEX,
    EXPERIMENT_NAME,
    GRID_TOTAL_BLACKOUT_DURATION,
    GRID_NUMBER_OF_BLACKOUTS,
    GRID_RELIABILITY,
    BLACKOUT_DURATION,
    BLACKOUT_FREQUENCY,
    MAX_EVALUATED_DAYS,
    BLACKOUT_FREQUENCY_STD_DEVIATION,
    NATIONAL_GRID_RELIABILITY_H,
    NATIONAL_GRID_TOTAL_BLACKOUT_DURATION,
    NATIONAL_GRID_NUMBER_OF_BLACKOUTS,
    GRID_AVAILABILITY_CSV,
)

# Check for saved blackout scenarios/grid availability, else continue randomization of backout events
def get_blackouts(settings, blackout_experiment_s):

    blackout_experiments_left = deepcopy(blackout_experiment_s)
    blackout_result_s = {}

    data_complete = False

    # Search, if file is existant (and should be used)

    if (
        os.path.isfile(os.path.join(settings[OUTPUT_FOLDER] + GRID_AVAILABILITY_CSV))
        or os.path.isfile(
            os.path.join(settings[INPUT_FOLDER_TIMESERIES] + GRID_AVAILABILITY_CSV)
        )
    ) and settings[RESTORE_BLACKOUTS_IF_EXISTENT] == True:

        # ? read to csv: timestamp as first row -> not equal column number, date time without index
        if os.path.isfile(
            os.path.join(settings[OUTPUT_FOLDER] + GRID_AVAILABILITY_CSV)
        ):
            data_set = pd.read_csv(settings[OUTPUT_FOLDER] + GRID_AVAILABILITY_CSV)
        elif os.path.isfile(
            os.path(settings[INPUT_FOLDER_TIMESERIES] + GRID_AVAILABILITY_CSV)
        ):
            data_set = pd.read_csv(
                os.path(settings[INPUT_FOLDER_TIMESERIES] + GRID_AVAILABILITY_CSV)
            )

        index = pd.DatetimeIndex(data_set[TIMESTEP].values)
        index = [
            item + pd.DateOffset(year=settings[MAX_DATE_TIME_INDEX][0].year)
            for item in index
        ]
        data_set = data_set.drop(columns=[TIMESTEP])
        grid_availability_df = pd.DataFrame(
            data_set.values, index=index, columns=data_set.columns.values
        )

        all_blackout_experiment_names = [
            blackout_experiment_s[experiment][EXPERIMENT_NAME]
            for experiment in blackout_experiment_s
        ]

        if len(settings[MAX_DATE_TIME_INDEX]) > len(grid_availability_df.index):
            data_complete = False
            logging.WARNING(
                "Saved blackout series can not be used (timestamps not compatible). Auto-generated timeseries will be used."
            )

        else:
            count_of_red_data = 0
            for experiment in blackout_experiment_s:

                if (
                    blackout_experiment_s[experiment][EXPERIMENT_NAME]
                    in grid_availability_df.columns
                ):
                    count_of_red_data = count_of_red_data + 1
                    name_of_experiment_requested_from_file_dataset = blackout_experiment_s[
                        experiment
                    ][
                        EXPERIMENT_NAME
                    ]
                    blackout_result = oemof_extension_for_blackouts(
                        grid_availability_df[
                            name_of_experiment_requested_from_file_dataset
                        ]
                    )
                    logging.info(
                        'Blackout experiment "'
                        + blackout_experiment_s[experiment][EXPERIMENT_NAME]
                        + '": '
                        + "Total blackout duration "
                        + str(blackout_result[GRID_TOTAL_BLACKOUT_DURATION])
                        + " hrs,"
                        + " total number of blackouts "
                        + str(blackout_result[GRID_NUMBER_OF_BLACKOUTS])
                        + " with grid reliability of "
                        + str(blackout_result[GRID_RELIABILITY])
                    )

                    blackout_result_s.update(
                        {
                            blackout_experiment_s[experiment][
                                EXPERIMENT_NAME
                            ]: blackout_result.copy()
                        }
                    )
                    del blackout_experiments_left[experiment]
                    logging.info(
                        "Previous blackout timeseries restored: "
                        + blackout_experiment_s[experiment][EXPERIMENT_NAME]
                    )

                # are all availability timeseries from file?
                if count_of_red_data == len(all_blackout_experiment_names):
                    data_complete = True
                    logging.info("All necessary blackout timeseries restored.\n \n")

    else:
        grid_availability_df = pd.DataFrame(index=settings[MAX_DATE_TIME_INDEX])

    # if data not saved, generate blackouts
    if data_complete == False:
        # from E_blackouts_central_grid import central_grid
        grid_availability_df = availability(
            settings,
            blackout_experiments_left,
            blackout_result_s,
            grid_availability_df,
        )
        logging.info("Missing blackout timeseries added through auto-generation.")

    grid_availability_df.index.name = TIMESTEP
    grid_availability_df.to_csv(settings[OUTPUT_FOLDER] + GRID_AVAILABILITY_CSV)

    return grid_availability_df, blackout_result_s


def oemof_extension_for_blackouts(grid_availability):
    # calculating blackout results
    total_grid_availability = sum(grid_availability)
    total_grid_blackout_duration = (
        len(grid_availability.index) - total_grid_availability
    )
    grid_reliability = 1 - total_grid_blackout_duration / len(grid_availability.index)
    # Counting blackouts for blackout results
    number_of_blackouts = 0
    for step in range(0, len(grid_availability.index)):
        if grid_availability.iat[step] == 0:
            if number_of_blackouts == 0:
                number_of_blackouts = number_of_blackouts + 1
            elif number_of_blackouts != 0 and grid_availability.iat[int(step - 1)] != 0:
                number_of_blackouts = number_of_blackouts + 1

    blackout_result = {
        GRID_RELIABILITY: grid_reliability,
        GRID_TOTAL_BLACKOUT_DURATION: total_grid_blackout_duration,
        GRID_NUMBER_OF_BLACKOUTS: number_of_blackouts,
    }

    return blackout_result


def availability(
    settings, blackout_experiment_s, blackout_result_s, grid_availability_df
):

    date_time_index = settings[MAX_DATE_TIME_INDEX]

    # get timestep frequency: timestep = date_time_index.freq()
    timestep = 1
    experiment_count = 0

    for experiment in blackout_experiment_s:
        experiment_count = experiment_count + 1

        logging.info(
            "Blackout experiment "
            + str(experiment_count)
            + ": "
            + "Blackout duration "
            + str(blackout_experiment_s[experiment][BLACKOUT_DURATION])
            + " hrs, "
            "blackout frequency "
            + str(blackout_experiment_s[experiment][BLACKOUT_FREQUENCY])
            + " per month"
        )

        number_of_blackouts = get_number_of_blackouts(
            settings[MAX_EVALUATED_DAYS], blackout_experiment_s[experiment]
        )

        # 0-1-Series for grid availability
        grid_availability = pd.Series(
            [1 for i in range(0, len(date_time_index))], index=date_time_index
        )

        if number_of_blackouts != 0:
            time_of_blackout_events = get_time_of_blackout_events(
                number_of_blackouts, date_time_index
            )

            (
                blackout_event_durations,
                accumulated_blackout_duration,
            ) = get_blackout_event_durations(
                blackout_experiment_s[experiment], timestep, number_of_blackouts
            )

            (
                grid_availability,
                overlapping_blackouts,
                actual_number_of_blackouts,
            ) = availability_series(
                grid_availability,
                time_of_blackout_events,
                timestep,
                blackout_event_durations,
            )
        else:
            accumulated_blackout_duration = 0
            actual_number_of_blackouts = 0

        total_grid_availability = sum(grid_availability)
        total_grid_blackout_duration = len(date_time_index) - total_grid_availability
        # Making sure that grid outage duration is equal to expected accumulated blackout duration
        if total_grid_blackout_duration != accumulated_blackout_duration:
            logging.info(
                "Due to "
                + str(overlapping_blackouts)
                + " overlapping blackouts, the total random blackout duration is not equal with the real grid availability."
            )
        # Simple estimation of reliability
        grid_reliability = 1 - total_grid_blackout_duration / len(date_time_index)

        logging.info(
            "Grid is not operational for "
            + str(round(total_grid_blackout_duration, 2))
            + " hours, with a reliability of "
            + str(round(grid_reliability * 100, 2))
            + " percent. \n"
        )

        blackout_name = blackout_experiment_s[experiment][EXPERIMENT_NAME]
        blackout_result_s.update(
            {
                blackout_name: {
                    GRID_RELIABILITY: grid_reliability,
                    GRID_TOTAL_BLACKOUT_DURATION: total_grid_blackout_duration,
                    GRID_NUMBER_OF_BLACKOUTS: actual_number_of_blackouts,
                }
            }
        )

        grid_availability_df = grid_availability_df.join(
            pd.DataFrame(
                grid_availability.values,
                columns=[blackout_name],
                index=grid_availability.index,
            )
        )

    return grid_availability_df


def get_number_of_blackouts(evaluated_days, experiment):
    # Calculation of expected blackouts per analysed timeframe
    blackout_events_per_month = np.random.normal(
        loc=experiment[BLACKOUT_FREQUENCY],  # median value: blackout duration
        scale=experiment[BLACKOUT_FREQUENCY_STD_DEVIATION]
        * experiment[BLACKOUT_FREQUENCY],  # Standard deviation
        size=12,
    )  # random values for number of blackouts
    blackout_events_per_timeframe = int(
        round(sum(blackout_events_per_month) / 365 * evaluated_days)
    )
    logging.info(
        "Number of blackouts in simulated timeframe: "
        + str(blackout_events_per_timeframe)
    )
    return blackout_events_per_timeframe


def get_time_of_blackout_events(blackout_events_per_timeframe, date_time_index):
    # Choosing blackout event starts randomly from whole duration
    # (probability set by data_time_index and blackout_events_per_timeframe)
    time_of_blackout_events = pd.Series(
        [1 for i in range(0, len(date_time_index))], index=date_time_index
    ).sample(
        n=blackout_events_per_timeframe, replace=False  # number of events
    )  # no replacements
    # Chronological order
    time_of_blackout_events.sort_index(inplace=True)

    # Display all events
    string_blackout_events = ""
    for item in time_of_blackout_events.index:
        string_blackout_events = string_blackout_events + str(item) + ", "
    logging.debug(
        "Blackouts events occur on following dates: " + string_blackout_events[:-2]
    )

    time_of_blackout_events = time_of_blackout_events.reindex(
        index=date_time_index, fill_value=0
    )
    return time_of_blackout_events


def get_blackout_event_durations(experiment, timestep, number_of_blackouts):
    # Generating blackout durations for the number of events
    blackout_event_durations = np.random.normal(
        loc=experiment[BLACKOUT_DURATION],  # median value: blackout duration
        scale=experiment[BLACKOUT_FREQUENCY_STD_DEVIATION]
        * experiment[BLACKOUT_DURATION],  # Standard deviation
        size=number_of_blackouts,
    )  # random values for number of blackouts

    logging.info(
        "Accumulated blackout duration: "
        + str(round(float(sum(blackout_event_durations)), 3))
    )

    # Round so that blackout durations fit simulation timestep => here, it would make sense to simulate for small timesteps
    for item in range(0, len(blackout_event_durations)):
        blackout_event_durations[item] = (
            round(blackout_event_durations[item] / timestep) * timestep
        )

    accumulated_blackout_duration = float(sum(blackout_event_durations))
    logging.info(
        "Accumulated blackout duration (rounded to timestep): "
        + str(round(accumulated_blackout_duration, 3))
    )

    return blackout_event_durations, accumulated_blackout_duration


def availability_series(
    grid_availability, time_of_blackout_events, timestep, blackout_event_durations
):
    ## Create 0-1-series that determines grid_availability
    blackout_started = 0
    overlapping_blackouts = 0
    blackout_count = 0

    for step in grid_availability.index:
        if time_of_blackout_events.loc[step] == 1:
            # Timestep analysed is a timestep, in which a blackout event starts
            if blackout_started != 0:
                logging.debug("A blackout event overlaps with another!")
                overlapping_blackouts = overlapping_blackouts + 1

            grid_availability.loc[step] = 0
            blackout_started = timestep

        else:
            if blackout_started != 0:
                if blackout_started != blackout_event_durations[blackout_count]:
                    # Above started blackout event continues
                    grid_availability.loc[step] = 0
                    blackout_started = blackout_started + timestep
                else:
                    # Blackoutevent reached its duration, grid is already operational in this timestep
                    grid_availability.loc[step] = 1
                    blackout_started = 0
                    blackout_count = blackout_count + 1
            else:
                # No blackout in timestep analysed
                grid_availability.loc[step] = 1

    return grid_availability, overlapping_blackouts, blackout_count


def extend_oemof_results(oemof_results, blackout_results):
    oemof_results.update(
        {
            NATIONAL_GRID_RELIABILITY_H: blackout_results[GRID_RELIABILITY],
            NATIONAL_GRID_TOTAL_BLACKOUT_DURATION: blackout_results[
                GRID_TOTAL_BLACKOUT_DURATION
            ],
            NATIONAL_GRID_NUMBER_OF_BLACKOUTS: blackout_results[
                GRID_NUMBER_OF_BLACKOUTS
            ],
        }
    )
    return oemof_results
