import pandas as pd
import numpy as np
import logging
import os.path

from sensitivity import sensitivity

class national_grid:

    # Check for saved blackout scenarios/grid availability, else continue randomization of backout events
    def get_blackouts(blackout_experiments):
        from config import restore_blackouts_if_existant, output_folder, date_time_index
        # Search, if file is existant (and should be used)
        if os.path.isfile(output_folder + "/grid_availability.csv") and restore_blackouts_if_existant == True:
            # todo read to csv: timestamp as first row -> not equal column number, date time without index
            data_set = pd.read_csv(output_folder + '/grid_availability.csv')
            index = pd.DatetimeIndex(data_set['timestep'].values)
            index = [item + pd.DateOffset(year=date_time_index[0].year) for item in index]
            data_set = data_set.drop(columns=['timestep'])
            sensitivity_grid_availability = pd.DataFrame(data_set.values, index = index, columns = data_set.columns.values)

            # todo this is very lazy and not "clean" - same number doesnt mean same entries. check for ENTRIES!!
            if len(sensitivity_grid_availability.columns) != len(blackout_experiments):
                data_complete = False
                logging.info("Saved blackout file not compatible (number of columns not conform).")

            else:
                # calculate result vector
                blackout_results = {}
                for experiment in blackout_experiments:
                    grid_availability = sensitivity_grid_availability[experiment['experiment_name']]
                    # calculating blackout results
                    total_grid_availability = sum(grid_availability)
                    total_grid_blackout_duration = len(grid_availability.index) - total_grid_availability
                    grid_reliability = 1 - total_grid_blackout_duration / len(grid_availability.index)
                    # Counting blackouts for blackout results
                    number_of_blackouts = 0
                    for step in range(0, len(sensitivity_grid_availability.index)):
                        if grid_availability.iat[step] == 0:
                            if number_of_blackouts == 0:
                                number_of_blackouts = number_of_blackouts + 1
                            elif number_of_blackouts != 0 \
                                    and grid_availability.iat[int(step - 1)] != 0:
                                number_of_blackouts = number_of_blackouts + 1

                    blackout_results.update({experiment['experiment_name']:
                                                 {'grid_reliability': grid_reliability,
                                                  'grid_total_blackout_duration': total_grid_blackout_duration,
                                                  'grid_number_of_blackouts': number_of_blackouts
                                                  }})

                    data_complete = True
                    logging.info("Previous blackouts restored (column: " + experiment['experiment_name'] + ")")

        else:
            data_complete = False

        # if data not saved, generate blackouts
        if data_complete == False:
            from national_grid import national_grid
            sensitivity_grid_availability, blackout_results = national_grid.availability(blackout_experiments)
            sensitivity_grid_availability.index.name = 'timestep'
            sensitivity_grid_availability.to_csv(output_folder + '/grid_availability.csv')

        return sensitivity_grid_availability, blackout_results

    def availability(blackout_experiments):
        from config import date_time_index
        # get timestep frequency: timestep = date_time_index.freq()
        timestep = 1
        experiment_count = 0

        blackout_results = {}

        for experiment in blackout_experiments:
            experiment_count = experiment_count + 1

            logging.info("Experiment "+ str(experiment_count) + ": " +
                  "Blackout duration " + str(experiment['blackout_duration']) + " hrs, "
                  "blackout frequency " + str(experiment['blackout_frequency'])+ " per month")

            number_of_blackouts =  national_grid.number_of_blackouts(experiment)

            # 0-1-Series for grid availability
            grid_availability = pd.Series([1 for i in range(0, len(date_time_index))], index=date_time_index)

            if number_of_blackouts != 0:
                time_of_blackout_events = national_grid.get_time_of_blackout_events(number_of_blackouts)

                blackout_event_durations, accumulated_blackout_duration = \
                    national_grid.get_blackout_event_durations(experiment, timestep, number_of_blackouts)

                grid_availability, overlapping_blackouts, actual_number_of_blackouts = national_grid.availability_series(
                    grid_availability, time_of_blackout_events, timestep, blackout_event_durations)
            else:
                accumulated_blackout_duration  = 0
                actual_number_of_blackouts     = 0

            total_grid_availability = sum(grid_availability)
            total_grid_blackout_duration = len(date_time_index) - total_grid_availability
            # Making sure that grid outage duration is equal to expected accumulated blackout duration
            if total_grid_blackout_duration != accumulated_blackout_duration:
                logging.info("Due to " + str(overlapping_blackouts) + " overlapping blackouts, the total random blackout duration is not equal with the real grid availability.")
            # Simple estimation of reliability
            grid_reliability = 1 - total_grid_blackout_duration / len(date_time_index)

            logging.info("Grid is not operational for " + str(round(total_grid_blackout_duration, 2))
                  + " hours, with a reliability of " + str(round(grid_reliability * 100, 2)) + " percent. \n")

            blackout_results.update({experiment['experiment_name']:
                                                      {'grid_reliability': grid_reliability,
                                                       'grid_total_blackout_duration': total_grid_blackout_duration,
                                                       'grid_number_of_blackouts': actual_number_of_blackouts
                                                       }})
            if experiment_count == 1:
                # initial entries
                sensitivity_grid_availability = pd.DataFrame(grid_availability, index=date_time_index, columns=[experiment['experiment_name']])
            else:
                # add columns with headers = experiment_name
                sensitivity_grid_availability = sensitivity_grid_availability.join(pd.DataFrame({experiment['experiment_name']: grid_availability.values}))

        return sensitivity_grid_availability, blackout_results

    def number_of_blackouts(experiment):
        from config import evaluated_days
        # Calculation of expected blackouts per analysed timeframe
        blackout_events_per_month = np.random.normal(loc=experiment['blackout_frequency'],  # median value: blackout duration
                                                    scale=experiment['blackout_frequency_std_deviation'] * experiment['blackout_frequency'],  # Standard deviation
                                                    size=12)  # random values for number of blackouts
        blackout_events_per_timeframe = int(round(sum(blackout_events_per_month) / 365 * evaluated_days))
        logging.info("Number of blackouts in simulated timeframe: " + str(blackout_events_per_timeframe))
        return blackout_events_per_timeframe

    def get_time_of_blackout_events(blackout_events_per_timeframe):
        from config import date_time_index
        # Choosing blackout event starts randomly from whole duration
        # (probability set by data_time_index and blackout_events_per_timeframe)
        time_of_blackout_events = pd.Series([1 for i in range(0, len(date_time_index))],
                                            index=date_time_index).sample(n=blackout_events_per_timeframe, # number of events
                                                                    replace=False) # no replacements
        # Chronological order
        time_of_blackout_events.sort_index(inplace=True)

        # Display all events
        string_blackout_events = ""
        for item in time_of_blackout_events.index:
            string_blackout_events = string_blackout_events + str(item) + ", "
        logging.info("Blackouts events occur on following dates: " + string_blackout_events[:-2])

        time_of_blackout_events = time_of_blackout_events.reindex(index=date_time_index, fill_value=0)
        return time_of_blackout_events

    def get_blackout_event_durations(experiment, timestep, number_of_blackouts):
        # Generating blackout durations for the number of events
        blackout_event_durations = np.random.normal(loc=experiment['blackout_duration'],  # median value: blackout duration
                                                    scale= experiment['blackout_frequency_std_deviation']* experiment['blackout_duration'], # Standard deviation
                                                    size=number_of_blackouts)  # random values for number of blackouts

        logging.info("Accumulated blackout duration: " + str(round(float(sum(blackout_event_durations)), 3)))

        # Round so that blackout durations fit simulation timestep => here, it would make sense to simulate for small timesteps
        for item in range(0, len(blackout_event_durations)):
            blackout_event_durations[item] = round(blackout_event_durations[item] / timestep) * timestep

        accumulated_blackout_duration = float(sum(blackout_event_durations))
        logging.info("Accumulated blackout duration (rounded): " + str(round(accumulated_blackout_duration, 3)))

        return blackout_event_durations, accumulated_blackout_duration

    def availability_series(grid_availability, time_of_blackout_events, timestep, blackout_event_durations):
        ## Create 0-1-series that determines grid_availability
        blackout_started = 0
        overlapping_blackouts = 0
        blackout_count = 0

        for step in grid_availability.index:
            if time_of_blackout_events.loc[step] == 1:
                # Timestep analysed is a timestep, in which a blackout event starts
                if blackout_started != 0:
                    logging.debug('A blackout event overlaps with another!')
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
        oemof_results.update({'national_grid_reliability': blackout_results['grid_reliability'],
                              'national_grid_total_blackout_duration': blackout_results['grid_total_blackout_duration'],
                              'national_grid_number_of_blackouts': blackout_results['grid_number_of_blackouts']})
        return oemof_results