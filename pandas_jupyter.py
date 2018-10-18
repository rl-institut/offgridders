# to display plots in line:
# %matplotlib inline

import pandas as pd
import matplotlib.pyplot as plt

# read with "read_csv", fields are comma-seperated

all_data=pd.read_csv('input_data_costs.csv', encoding='utf9', sep=';', parse_dates=['Date'], dayfirst=True, index_col='Date')

    # change the column separator to a ;
    # Set the encoding to 'latin1' (the default is 'utf8')
    # Parse the dates in the 'Date' column
    # Tell it that our dates have the day first instead of the month first
    # Set the index to be the 'Date' column

# all_data is a DataFrame, made up from all rows and columns. you can get columns by asking for the columntitle

all_data['columntitle']

# you can directly plot the data

all_data['columntitle'].plot()
# with .plot(figsize=(17, 10)) the plot can appear smaller or bigger

#opening multiple colums until row 10
all_data[['columntitle', 'columntitle2']][:10]
