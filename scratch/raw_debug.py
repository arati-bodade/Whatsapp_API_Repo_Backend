import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_I4dGpkvPi2zw@ep-snowy-mountain-an3w18e6-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

# Find Arati
cur.execute("SELECT reseller_id, name FROM resellers WHERE name ILIKE '%Arati%';")
reseller = cur.fetchone()

if reseller:
    rid = reseller[0]
    print(f"Reseller: {reseller[1]} ({rid})")
    
    # Distributions
    cur.execute("SELECT to_business_user_id, credits_shared, shared_at FROM credit_distributions WHERE from_reseller_id = %s;", (rid,))
    rows = cur.fetchall()
    print(f"Distributions: {len(rows)}")
    for r in rows:
        print(r)
        
    # Sub-users
    cur.execute("SELECT busi_user_id, business_name, credits_allocated FROM busi_users WHERE parent_reseller_id = %s;", (rid,))
    users = cur.fetchall()
    print(f"Sub-users: {len(users)}")
    for u in users:
        print(u)
else:
    print("Not found")

cur.close()
conn.close()
