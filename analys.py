import pandas as pd

df = pd.read_csv("patients_model.csv")
print(df['dob'].isna())