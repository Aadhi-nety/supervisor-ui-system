# fix.py
import sqlite3
import re

db_file = "salon.db"   # ← your database file name
conn = sqlite3.connect(db_file)
cur = conn.cursor()

# remove anything that looks like {# ... #}
cur.execute("UPDATE help_request SET question = regexp_replace(question, '\\{#.*?#\\}', '', 'g')")
cur.execute("UPDATE help_request SET answer   = regexp_replace(answer,   '\\{#.*?#\\}', '', 'g')")
cur.execute("UPDATE help_request SET context  = regexp_replace(context,  '\\{#.*?#\\}', '', 'g')")

conn.commit()
conn.close()
print("Fixed!")