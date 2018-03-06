import requests
import csv

rows = [r for r in csv.reader(open('/app/data/dpu_data.csv','r'))]
cols = rows[0]
data = [dict(zip(cols, r)) for r in rows[1:]]

for d in data:
    requests.post('http://127.0.0.1:5000/send', json=d)
