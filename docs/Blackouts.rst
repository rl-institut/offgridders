==========================================
Randomized Blackouts
==========================================
For many countries, The World Bank provides the average monthly blackout frequency and average individual duration in it's online data source (1). It has to be mentioned, that the enterprises surveyed may, due to their here assumed aggregated location in cities, have a better grid reliability than the average off-grid consumer. Still, the global data availability encourages to use both values as input parameters characterizing blackout behaviour of unreliable in subsequent simulations and optimizations.

Grid availability plays a role when analyzing the performance of an off-grid micro interconnecting to a national grid as well as during optimization of a grid-tied micro grid intended to increase local supply reliability.

Randomizing blackout events
-----------------------------------
To randomize the blackout events that a grid is subjected to, both average monthly blackout frequency and average individual blackout duration are submitted to white noise. The deviation of both values has to be defined as a percentage of the subsequent parameter:::

        'blackout_duration':                2  # hrs per blackout
        'blackout_duration_std_deviation'   0  # While programming
        'blackout_frequency':               7  # blackouts per month
        'blackout_frequency_std_deviation'  0  # While programming

As always, each parameter can be part of the sensitivity analysis.

++++++++++++++++++++++++++++++++++++++++
Creating a grid availability timeseries
++++++++++++++++++++++++++++++++++++++++
First, the number of blackouts during each month of the year is randomized utilizing the numpy normal distribution:::

        blackout_events_per_month = np.random.normal(
            loc=experiment['blackout_frequency'],  # median value: blackout duration
            scale=experiment['blackout_frequency_std_deviation'] * experiment['blackout_frequency'],  # Standard deviation
            size=12)  # random values for number of blackouts

If necessary, the number of events is adjusted to the time frame analyzed.::

        blackout_events_per_timeframe = int(round(sum(blackout_events_per_month) / 365 * evaluated_days))

Each blackout event is then assigned a specific blackout duration. Knowing the total number of expected blackouts, their duration is defined utilizing the numpy normal distribution:::

        blackout_event_durations = np.random.normal(
            loc=experiment['blackout_duration'],  # median value: blackout duration
            scale= experiment['blackout_frequency_std_deviation']* experiment['blackout_duration'],  # sigma (as far as I remember)
            size=number_of_blackouts)  # random values for number of blackouts

To fit the time step resolution of the simulation, the blackout duration is rounded. It could be advisable to integrate eg. a 15-Minute resolution to properly analyse blackout events during the simulation.

From the time frame analyzed, a random set of items equaling the number of blackouts is generated from it's data time index utilizing the pandas sampling function:::

        time_of_blackout_events = pd.Series([1 for i in range(0, len(date_time_index))],
                                            index=date_time_index).sample(
            n=blackout_events_per_timeframe, # number of events
            replace=False) # no replacements!

The grid availability Series is then created, covering the whole simulated time frame. It's values are 0 (grid not available) and 1 (grid available). A new blackout starts when the timestamp of grid availability equals timestamp of occurring blackout event. It stops when its duration is met.

If blackouts overlap, this event will be displayed in the command line, but no additional blackout added. That way, the real number of blackouts experienced might be lower that the randomized expected value, while the mean duration could increase. Both values, real number of blackouts and total blackout duration, will be saved in the simulation results.

+++++++++++++++++++++++++++++++++++++++++++++++
Loading previous grid availability timeseries
+++++++++++++++++++++++++++++++++++++++++++++++

To enable the recalculation of a set of experiments, all grid availability time series are saved to an csv-file. Enabeling the option _restore_blackouts_if_existant_ will load previously generated series.

**Currently this is performed lazily**, meaning that if the number of column heads of the data frame that reloaded the csv values equals the number of blackout events due to the sensitivity bounds defined in the current simulation, the tool assumes that the loaded grid availabilities fit the simulation. If, however, a blackout experiment can not be read from the data frame through its name (column header), the tool will abort the simulation.

=> Analyze performance of grid extension WITHOUT local generation/storage, but keep in mind that allowed shortage has to be >0 to allow blackouts

=> If allowing blackouts, its variable costs have to be substracted from the annuity calculated in the optimization to allow calculation!!

(1) The World Bank (2018): http://www.enterprisesurveys.org/data/exploretopics/infrastructure