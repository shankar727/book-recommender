import pandas as pd
import pickle

with open('pt.pkl', 'rb') as f:
    books = pickle.load(f)

print("Columns:", books.columns.tolist())
print("\nFirst 3 rows:")
print(books.head(3))
print("\nSummary:")
print(books.info())