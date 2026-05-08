from services.google_sheets_service import GoogleSheetsService
import logging

# Mock logger
logging.basicConfig(level=logging.INFO)

def test_eligibility():
    service = GoogleSheetsService()
    
    # User scenario: Status is "Send"
    status = "Send"
    is_eligible = service.is_eligible_for_sending(status)
    print(f"Status '{status}' eligible? {is_eligible}")
    
    if not is_eligible:
        print("❌ FAILED: 'Send' should be eligible based on user requirement, but current logic rejects it.")
    else:
        print("✅ SUCCESS: 'Send' is eligible.")

    # Current logic checks for ["", "pending"]
    print(f"Status 'Pending' eligible? {service.is_eligible_for_sending('Pending')}")

if __name__ == "__main__":
    test_eligibility()
