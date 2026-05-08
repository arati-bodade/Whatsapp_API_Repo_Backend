
# DYNAMIC DEVICE SELECTION FUNCTIONS
# Add these to your services/google_sheets_automation_unofficial_only.py

def get_active_device_for_trigger(db: Session, trigger: GoogleSheetTrigger) -> Device:
    """Dynamically get an active device for a trigger"""
    # First try to use trigger's assigned device if it's active
    if trigger.device_id:
        device = db.query(Device).filter(
            Device.device_id == trigger.device_id,
            Device.session_status == SessionStatus.connected
        ).first()
        if device:
            return device
    
    # Fallback to any active device
    return db.query(Device).filter(
        Device.session_status == SessionStatus.connected
    ).first()

def validate_and_fix_trigger_device(db: Session, trigger: GoogleSheetTrigger) -> bool:
    """Validate trigger device and fix if needed"""
    if not trigger.device_id:
        # Assign to first active device
        active_device = db.query(Device).filter(
            Device.session_status == SessionStatus.connected
        ).first()
        if active_device:
            trigger.device_id = active_device.device_id
            db.commit()
            return True
    return False

def get_active_sheets_with_valid_devices(db: Session) -> List[GoogleSheet]:
    """Get only active sheets that have valid device assignments"""
    active_sheets = db.query(GoogleSheet).filter(
        GoogleSheet.status == SheetStatus.ACTIVE
    ).all()
    
    valid_sheets = []
    for sheet in active_sheets:
        if sheet.device_id:
            device = db.query(Device).filter(
                Device.device_id == sheet.device_id,
                Device.session_status == SessionStatus.connected
            ).first()
            if device:
                valid_sheets.append(sheet)
    
    return valid_sheets
