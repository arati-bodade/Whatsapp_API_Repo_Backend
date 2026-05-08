from db.session import SessionLocal
from sqlalchemy import text

def debug_triggers():
    db = SessionLocal()
    try:
        print("--- DEBUGGING GOOGLE SHEET TRIGGERS ---")
        
        # Get all sheets and their devices
        sheets = db.execute(text("SELECT id, sheet_name, device_id FROM google_sheets")).fetchall()
        print(f"\nSheets Found: {len(sheets)}")
        sheet_map = {}
        for s in sheets:
            print(f"Sheet ID: {s[0]} | Name: {s[1]} | Device ID: {s[2]}")
            sheet_map[str(s[0])] = s[2]
            
        # Get all triggers
        triggers = db.execute(text("SELECT trigger_id, sheet_id, device_id, is_enabled, trigger_type, send_time_column, phone_column, status_column, trigger_value FROM google_sheet_triggers")).fetchall()
        print(f"\nTriggers Found: {len(triggers)}")
        for t in triggers:
            tid, sid, did, enabled, ttype, stime_col, pcol, scol, tval = t
            sheet_device = sheet_map.get(str(sid))
            print(f"Trigger {tid}:")
            print(f"  Sheet: {sid}")
            print(f"  Trigger Device ID: {did}")
            print(f"  Sheet Device ID:   {sheet_device}")
            print(f"  Type: {ttype} | Enabled: {enabled}")
            print(f"  Wait until column: {stime_col}")
            print(f"  Phone column: {pcol} | Status column: {scol} | Trigger value: {tval}")
            
            # If device_id is missing in trigger, we should check if we can fallback to sheet device_id
            if not did and not sheet_device:
                print("  !!! ALERT: No device assigned to this trigger or its parent sheet")
                
        # Check active devices
        devices = db.execute(text("SELECT device_id, device_name, is_active FROM devices WHERE is_active = true")).fetchall()
        print(f"\nActive Devices Found: {len(devices)}")
        for d in devices:
            print(f"Device ID: {d[0]} | Name: {d[1]}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_triggers()
