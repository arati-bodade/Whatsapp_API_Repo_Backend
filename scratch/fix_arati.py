import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_I4dGpkvPi2zw@ep-snowy-mountain-an3w18e6-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

# Refund 9 credits to Arati Bodade
cur.execute("""
    UPDATE resellers 
    SET available_credits = available_credits + 9,
        used_credits = used_credits - 9
    WHERE name ILIKE '%Arati%' AND used_credits > 4000;
""")

print(f"Rows updated: {cur.rowcount}")
conn.commit()
cur.close()
conn.close()
