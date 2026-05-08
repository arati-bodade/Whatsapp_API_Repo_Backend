
from sqlalchemy import text
from db.session import SessionLocal

def inspect_latest_campaign_sql():
    db = SessionLocal()
    try:
        # Get latest campaign
        campaign_query = text("SELECT id, name, status, created_at FROM campaigns ORDER BY created_at DESC LIMIT 1")
        result = db.execute(campaign_query).fetchone()
        
        if not result:
            print("No campaigns found.")
            return

        campaign_id = result[0]
        print(f"Latest Campaign ID: {campaign_id}")
        print(f"Name: {result[1]}")
        print(f"Status: {result[2]}")
        
        # Get templates for this campaign
        template_query = text("SELECT id, content, media_url, media_type FROM message_templates WHERE campaign_id = :cid")
        templates = db.execute(template_query, {"cid": campaign_id}).fetchall()
        
        print(f"\nFound {len(templates)} templates:")
        for t in templates:
            print(f"- ID: {t[0]}")
            print(f"  Content: {t[1]}")
            print(f"  Media URL: {t[2]}")
            print(f"  Media Type: {t[3]}")
            print("-" * 20)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_latest_campaign_sql()
