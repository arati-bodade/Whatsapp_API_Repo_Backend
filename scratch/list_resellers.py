import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_I4dGpkvPi2zw@ep-snowy-mountain-an3w18e6-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

cur.execute("SELECT reseller_id, name, available_credits, used_credits, total_credits FROM resellers;")
rows = cur.fetchall()
for row in rows:
    print(row)

cur.close()
conn.close()
