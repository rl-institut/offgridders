import pandas as pd
import numpy as np
import logging

class national_grid:

    def availability(blackout_experiments):
        from config import date_time_index
        # get timestep frequency: timestep = date_time_index.freq()
        timestep = 1
        experiment_count = 0

        sensitivity_grid_availability = {}

        for experiment in blackout_experiments:

            experiment_count = experiment_count + 1

            logging.info("Experiment "+ str(experiment_count) + ": " +
                  "Blackout duration " + str(experiment['blackout_duration']) + " hrs, "
                  "blackout frequency " + str(experiment['blackout_frequency'])+ " per month")

            number_of_blackouts =  national_grid.number_of_blackouts(experiment['blackout_frequency'])

            # 0-1-Series for grid availability
            grid_availability = pd.Series([1 for i in range(0, len(date_time_index))], index=date_time_index)

            if number_of_blackouts != 0:
                time_of_blackout_events =  national_grid.get_time_of_blackout_events(number_of_blackouts)

                blackout_event_durations, accumulated_blackout_duration = \
                    national_grid.get_blackout_event_durations(experiment['blackout_duration'], timestep, number_of_blackouts)

                grid_availability = national_grid.availability_series(grid_availability, time_of_blackout_events,
                                                                      timestep, blackout_event_durations)
            else:
                accumulated_blackout_duration   = 0

            total_grid_availability = sum(grid_availability)
            total_grid_blackout_duration = len(date_time_index) - total_grid_availability
            # Making sure that grid outage duration is equal to expected accumulated blackout duration
            if total_grid_blackout_duration != accumulated_blackout_duration:
                logging.info("Random blackout duration not equal with grid_availability vector!")
            # Simple estimation of reliability
            grid_reliability = 1 - total_grid_blackout_duration / len(date_time_index)

            logging.info("Grid is not operational for " + str(round(total_grid_blackout_duration, 2))
                  + " hours, with an reliability of " + str(round(grid_reliability * 100, 2)) + " percent.")

            logging.info(experiment['experiment_name'])
            sensitivity_grid_availability.update({experiment['experiment_name']:
                                                      {'grid_availability': grid_availability,
                                                       'grid_reliability': grid_reliability,
                                                       'grid_total_blackout_duration': total_grid_blackout_duration,
                                                       'grid_number_of_blackouts': number_of_blackouts
                                                       }})

        return sensitivity_grid_availability

    def number_of_blackouts(blackout_frequency):
        from config import evaluated_days
        # Calculation of expected blackouts per analysed timeframe
        blackout_events_per_timeframe = int(round(12 * blackout_frequency / 365 * evaluated_days))
        return blackout_events_per_timeframe

    def get_time_of_blackout_events(blackout_events_per_timeframe):
        from config import date_time_index
        # Choosing blackout event starts randomly from whole duration
        # (probability set by data_time_index and blackout_events_per_timeframe)
        time_of_blackout_events = pd.Series(date_time_index).sample(n=blackout_events_per_timeframe, # number of events
                                                                    replace=False) # no replacements
        # Chronological order
        time_of_blackout_events.sort_index(inplace=True)
        # Display all events
        string_blackout_events = ""
        for item in time_of_blackout_events.index:
            string_blackout_events = string_blackout_events + str(time_of_blackout_events[item]) + ", "
        logging.info("Blackouts events occur on following dates: " + string_blackout_events[:-2])

        number_of_blackouts = len(time_of_blackout_events)
        logging.info("Number of blackouts in simulated timeframe: " + str(number_of_blackouts))

        # blackouts are in index
        time_of_blackout_events = pd.Series([0 for i in range(0, len(time_of_blackout_events))],
                                            index=time_of_blackout_events.values)
        time_of_blackout_events.reindex(date_time_index)
        print(len(time_of_blackout_events))
        #print(time_of_blackout_events)

        return time_of_blackout_events, number_of_blackouts

    def get_blackout_event_durations(blackout_duration, timestep, number_of_blackouts):
        # Generating blackout durations for the number of events
        blackout_event_durations = np.random.normal(loc=blackout_duration,  # median value: blackout duration
                                                    scale=0.15 * blackout_duration,  # sigma (as far as I remember)
                                                    size=number_of_blackouts)  # randum values for number of blackouts

        logging.info("Accumulated blackout duration: " + str(round(float(sum(blackout_event_durations)), 3)))

        # Round so that blackout durations fit simulation timestep => here, it would make sense to simulate for small timesteps
        for item in range(0, len(blackout_event_durations)):
            blackout_event_durations[item] = round(blackout_event_durations[item] / timestep) * timestep

        accumulated_blackout_duration = float(sum(blackout_event_durations))
        logging.info("Accumulated blackout duration (rounded): " + str(round(accumulated_blackout_duration, 3)))

        return blackout_event_durations, accumulated_blackout_duration

    def availability_series(grid_availability, time_of_blackout_events, timestep, blackout_event_durations):
        from config import date_time_index
        ## Create 0-1-series that determines grid_availability
        blackout_started = 0
        overlapping_blackouts = 0
        blackout_count = 0

        for step in date_time_index:
            if any(step == time_of_blackout_events):
                # Timestep analysed is a timestep, in which a blackout event takes place
                if blackout_started != 0:
                    logging.info('A blackout event overlaps with another!')
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
        return grid_availability

    def get_blackout_experiment_name(blackout_duration, blackout_frequency):
        blackout_experiment_name = 'blackout_duration'+ '_' + str(round(blackout_duration,2))+"_" \
                              +'blackout_frequency'+ '_' + str(round(blackout_frequency,2))
        return blackout_experiment_name

    def extend_oemof_results(oemof_results, sensitivity_grid_availability):
        oemof_results.update({'national_grid_reliability': sensitivity_grid_availability['grid_reliability'],
                              'national_grid_total_blackout_duration': sensitivity_grid_availability['grid_total_blackout_duration'],
                              'national_grid_number_of_blackouts': sensitivity_grid_availability['grid_number_of_blackouts']})
        return oemof_results