import pandas as pd

# read with "read_csv", fields are comma-seperated

all_data = pd.read_csv('input_data_costs.csv', encoding='utf8', index_col='Cost')

print(all_data['Investment'][1:])