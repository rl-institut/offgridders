import pandas as pd
import logging

class national_grid():

    def avail(blackoutduration, blackoutfrequency):

        print("blackout duration (hrs): " + str(blackoutduration) + " blackout frequency (per month): " + str(blackoutfrequency))
        return

    def availability():
        # this is given by blackoutexperiments
        blackout_duration = 2
        blackout_frequency = 5
        from config import date_time_index
        # get timestep frequency: timestep = date_time_index.freq()
        timestep = 1
        blackout_events_per_year = 12 * blackout_frequency

        # Generating blackout events in dataframe (boolean)
        blackout_event = pd.DataFrame(index=date_time_index)
        for step in blackout_event:
            np.

        # print ("total number of blackouts in simulated timeframe: sum(boolean)")

        # Generating blackout durations for the number of events

        # make that the blackout duration fits chosen timestep

        blackout_started        = 0
        overlapping_blackouts   = 0
        total_blackout_duration = 0

        grid_availability = pd.DataFrame(index=date_time_index)

        for step in date_time_index:
            if blackout_event == True:
                if blackout_started != 0:
                    logging.info('A blackout event overlaps with another!')
                    overlapping_blackouts = overlapping_blackouts + 1
                grid_availability[step] = 0
                blackout_started=timestep

            else:
                if blackout_started == 0:
                    grid_availability[step]=1
                else:
                    if blackout_started == blackout_duration(event)-timestep:
                        grid_availability[step] = 0
                        total_blackout_duration = total_blackout_duration + blackout_started
                        blackout_started = 0
                    else:
                        grid_availability[step] = 0
                        blackout_started = blackout_started + timestep








    def blackout_starts(blackout_events_per_year):
        return blackout_starts

