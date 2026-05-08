import psycopg2

conn = psycopg2.connect("postgresql://neondb_owner:npg_I4dGpkvPi2zw@ep-snowy-mountain-an3w18e6-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require")
cur = conn.cursor()

# Arati: ba57b395-4e43-4e78-9690-710dcfe2cad2
# Bodade Construction: 87624568-107c-43cc-ac83-a060f4395e9c

arati_id = 'ba57b395-4e43-4e78-9690-710dcfe2cad2'
bodade_id = '87624568-107c-43cc-ac83-a060f4395e9c'

# Find leaked messages
cur.execute("""
    SELECT usage_id, message_id, credits_deducted 
    FROM message_usage_credit_logs 
    WHERE busi_user_id = %s AND source != 'distribution' AND credits_deducted > 0;
""", (arati_id,))

leaked = cur.fetchall()
print(f"Leaked messages for Arati: {len(leaked)}")
for l in leaked:
    print(l)

# Fix them: Move to Bodade Construction
if len(leaked) > 0:
    print("Moving leaked messages to Bodade Construction...")
    cur.execute("""
        UPDATE message_usage_credit_logs 
        SET busi_user_id = %s 
        WHERE busi_user_id = %s AND source != 'distribution' AND credits_deducted > 0;
    """, (bodade_id, arati_id))
    print(f"Updated {cur.rowcount} logs.")
    
    # Also need to update the credits_used and credits_remaining for the sub-user
    # 9 messages = 9 credits
    total_leaked = sum(l[2] for l in leaked)
    print(f"Total credits to adjust: {total_leaked}")
    
    cur.execute("""
        UPDATE businesses 
        SET credits_used = credits_used + %s,
            credits_remaining = credits_remaining - %s
        WHERE busi_user_id = %s;
    """, (total_leaked, total_leaked, bodade_id))
    print("Updated sub-user wallet.")

conn.commit()
cur.close()
conn.close()
