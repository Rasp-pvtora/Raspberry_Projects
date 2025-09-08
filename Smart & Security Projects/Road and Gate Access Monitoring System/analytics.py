from datetime import datetime

def generate_heatmap(conn, start_date, end_date):
    cur = conn.cursor()
    cur.execute("""
        SELECT strftime('%H', entry_time) as hour, COUNT(*) 
        FROM entries 
        WHERE entry_time BETWEEN ? AND ? 
        GROUP BY hour
    """, (start_date, end_date))
    return {row[0]: row[1] for row in cur.fetchall()}

# Extra Function to add:  export .csv file
