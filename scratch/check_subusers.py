import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_I4dGpkvPi2zw@ep-snowy-mountain-an3w18e6-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

# Find Arati
rid = 'ba57b395-4e43-4e78-9690-710dcfe2cad2'

# Sub-users
cur.execute("SELECT busi_user_id, business_name, credits_allocated, credits_remaining FROM businesses WHERE parent_reseller_id = %s;", (rid,))
users = cur.fetchall()
print(f"Sub-users: {len(users)}")
for u in users:
    print(u)

cur.close()
conn.close()
