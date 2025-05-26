import sqlite3

conn = sqlite3.connect("stocks.db")
cursor = conn.cursor()

for row in cursor.execute("SELECT * FROM daily_prices ORDER BY date DESC LIMIT 5"):
    print(row)

conn.close()
