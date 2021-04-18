import pandas as pd
pd.set_option('display.max_columns', 200)

df_origin = pd.read_csv('./log.csv')
char_int = df_origin.columns[4:]
char = [chr(int(i)) for i in char_int]
df = df_origin.rename(columns=dict(zip(char_int, char)))
