import pandas as pd
from sqlalchemy import create_engine, text

file_path = 'C:/Users/nmx/Desktop/case2/das.xlsx'

df = pd.read_excel(file_path)

engine = create_engine('sqlite:///case2giga.db')

df.to_sql('giga', con=engine, index=False, if_exists='replace')

with engine.connect() as connection:
    result = connection.execute(text("SELECT * FROM giga")).fetchall()
    for row in result:
        print(row)