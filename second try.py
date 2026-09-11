import numpy as np
import pandas as pd
bruhhhhhh = 3
print(bruhhhhhh*2)

def age_calculator(year, month, day, name):
    today = pd.Timestamp.now().date()
    birthdate = pd.Timestamp(year=year, month=month, day=day).date()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age