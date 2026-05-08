from pydantic import BaseModel, Field, ConfigDict, field_validator, BeforeValidator
from typing import Optional, Dict, List, Any, Union, Annotated
from datetime import datetime
from enum import Enum
from uuid import UUID

class SheetStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"

class TriggerType(str, Enum):
    NEW_ROW = "new_row"
    UPDATE_ROW = "update_row"
    TIME = "time"

class TriggerHistoryStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"

# --- Request Schemas ---

class GoogleSheetConnectRequest(BaseModel):
    sheet_name: str
    spreadsheet_id: str
    worksheet_name: Optional[str] = None

class GoogleSheetRowsRequest(BaseModel):
    worksheet_name: Optional[str] = None
    start_row: Optional[int] = 1
    end_row: Optional[int] = None

class ManualSendRequest(BaseModel):
    model_config = {"populate_by_name": True}
    
    device_id: Union[str, UUID]
    message_template: str
    phone_column: str = Field(..., alias="phone_col")  # Accept both phone_col and phone_column
    selected_rows: Optional[List[Dict[str, Any]]] = None
    send_all: Optional[bool] = False

# ✅ NEW: Official Template Message Request for Google Sheets
class OfficialTemplateSendRequest(BaseModel):
    model_config = {"populate_by_name": True}
    
    device_id: Union[str, UUID]  # Kept for compatibility, but not used in official messaging
    template_name: str
    language_code: str = "en_US"
    phone_column: str = Field(..., alias="phone_col")
    header_param_columns: Optional[List[str]] = None
    body_param_columns: Optional[List[str]] = None
    button_param_columns: Optional[Dict[str, str]] = None
    selected_rows: Optional[List[Dict[str, Any]]] = None
    send_all: Optional[bool] = False

# ✅ NEW: Google Sheet Messaging Request (supports both text and template)
class GoogleSheetMessagingRequest(BaseModel):
    model_config = {"populate_by_name": True}
    
    mode: str = Field(..., description="Message mode: 'text' or 'template'")
    phone_column: str = Field(..., alias="phone_col")
    
    # Text message fields (when mode = "text")
    text_message: Optional[str] = None
    
    # Template message fields (when mode = "template")
    template_name: Optional[str] = None
    language_code: Optional[str] = "en_US"
    header_param_columns: Optional[List[str]] = None
    body_param_columns: Optional[List[str]] = None
    button_param_columns: Optional[Dict[str, str]] = None
    
    # Common fields
    selected_rows: Optional[List[Dict[str, Any]]] = None
    send_all: Optional[bool] = False
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        if v not in ['text', 'template']:
            raise ValueError("Mode must be either 'text' or 'template'")
        return v

class TriggerCreateRequest(BaseModel):
    sheet_id: Optional[Union[UUID, str]] = None
    device_id: Optional[Union[str, UUID]] = None  # Made optional
    trigger_type: str
    is_enabled: Optional[bool] = True
    # Extended fields
    message_template: Optional[str] = None
    phone_column: Optional[str] = None
    trigger_column: Optional[str] = None
    status_column: Optional[str] = None
    trigger_value: Optional[str] = None
    schedule_column: Optional[str] = None
    webhook_url: Optional[str] = None
    execution_interval: Optional[int] = None
    send_time_column: Optional[str] = None
    message_column: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    source_file_url: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    # Round Robin fields
    multi_device_ids: Optional[List[str]] = None
    multi_templates: Optional[List[str]] = None

    @field_validator('sheet_id')
    @classmethod
    def validate_sheet_id(cls, v):
        if v in ["none", "null", "undefined", "file", ""]:
            return None
        return v

# ✅ NEW: Official Template Trigger Request for Google Sheets
class OfficialTemplateTriggerRequest(BaseModel):
    sheet_id: Optional[UUID] = None
    device_id: Optional[Union[str, UUID]] = None  # Made optional
    trigger_type: str
    is_enabled: Optional[bool] = True
    # Official template fields
    template_name: str
    language_code: str = "en_US"
    phone_column: Optional[str] = None
    header_param_columns: Optional[List[str]] = None
    body_param_columns: Optional[List[str]] = None
    button_param_columns: Optional[Dict[str, str]] = None
    # Trigger fields
    trigger_column: Optional[str] = None
    status_column: Optional[str] = None
    trigger_value: Optional[str] = None
    schedule_column: Optional[str] = None
    webhook_url: Optional[str] = None
    execution_interval: Optional[int] = None

class TriggerUpdateRequest(BaseModel):
    device_id: Optional[str] = None
    trigger_type: Optional[str] = None  # Changed from Enum to String to match DB
    is_enabled: Optional[bool] = None
    phone_column: Optional[str] = None
    trigger_column: Optional[str] = None
    status_column: Optional[str] = None
    trigger_value: Optional[str] = None
    message_template: Optional[str] = None
    send_time_column: Optional[str] = None
    message_column: Optional[str] = None
    webhook_url: Optional[str] = None
    execution_interval: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    # Round Robin fields
    multi_device_ids: Optional[List[str]] = None
    multi_templates: Optional[List[str]] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None

# --- Response Schemas ---

class GoogleSheetResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)]
    user_id: Optional[Annotated[str, BeforeValidator(str)]] = None
    sheet_name: str
    spreadsheet_id: str
    worksheet_name: Optional[str] = None
    status: str  # Changed from Enum to String to match DB
    total_rows: int
    trigger_enabled: bool
    device_id: Optional[Annotated[str, BeforeValidator(str)]] = None
    message_template: Optional[str] = None
    trigger_config: Optional[Dict[str, Any]] = None
    connected_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    available_sheets: Optional[List[str]] = []

    model_config = ConfigDict(from_attributes=True)

class GoogleSheetDataResponse(BaseModel):
    headers: List[str]
    rows: List[Dict[str, Any]]

class GoogleSheetRowResponse(BaseModel):
    row_number: int
    data: Dict[str, Any]
    phone_number: Optional[str] = None

class ManualSendResponse(BaseModel):
    total: int
    sent: int
    failed: int
    errors: List[str] = []

# ✅ NEW: Official Template Send Response
class OfficialTemplateSendResponse(BaseModel):
    total: int
    sent: int
    failed: int
    errors: List[str] = []
    message_ids: List[str] = []  # wamid values from Meta API

# ✅ NEW: Google Sheet Messaging Response (supports both text and template)
class GoogleSheetMessagingResponse(BaseModel):
    total: int
    sent: int
    failed: int
    errors: List[str] = []
    message_ids: List[str] = []  # wamid values from Meta API
    mode: str  # "text" or "template"

class TriggerResponse(BaseModel):
    trigger_id: Annotated[str, BeforeValidator(str)]  # Robust cast
    sheet_id: Optional[Annotated[str, BeforeValidator(str)]] = None  # Robust cast
    device_id: Optional[Annotated[str, BeforeValidator(str)]] = None  # Robust cast
    trigger_type: str  # Changed from Enum to String to match DB
    is_enabled: bool
    last_triggered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    device_name: Optional[str] = None
    sheet_name: Optional[str] = None
    phone_column: Optional[str] = None
    status_column: Optional[str] = None
    trigger_column: Optional[str] = None
    trigger_value: Optional[str] = None
    message_template: Optional[str] = None
    send_time_column: Optional[str] = None
    message_column: Optional[str] = None
    webhook_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    # Round Robin fields
    multi_device_ids: Optional[List[str]] = None
    multi_templates: Optional[List[str]] = None
    trigger_config: Optional[Dict[str, Any]] = None
    # 🔥 NEW: Trigger statistics for UI
    total_rows: Optional[int] = None
    processed_rows: Optional[int] = None
    completion_status: Optional[str] = None  # "pending", "running", "completed"

    model_config = ConfigDict(from_attributes=True)

class TriggerHistoryResponse(BaseModel):
    history_id: Annotated[str, BeforeValidator(str)]  # ✅ String UUID from database id field
    sheet_id: Annotated[str, BeforeValidator(str)]  # This references google_sheets.id
    status: str  # ✅ String from database
    executed_at: Optional[datetime] = None  # ✅ Maps to triggered_at in database
    phone: Optional[str] = None  # ✅ Maps to phone_number in database
    message: Optional[str] = None  # ✅ Maps to message_content in database
    error_message: Optional[str] = None
    sheet_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class TriggerHistoryListResponse(BaseModel):
    history: List[TriggerHistoryResponse]
    total_count: int
    page: int
    per_page: int

class WebhookRequest(BaseModel):
    spreadsheet_id: str
    worksheet_name: str
    row_data: Dict[str, Any]
    row_index: int
    event_type: str = "EDIT"  # EDIT, CHANGE

# --- Internal/Utility Schemas ---

class GoogleSheetWithTriggers(GoogleSheetResponse):
    triggers: List[TriggerResponse] = []

class DeviceValidationResult(BaseModel):
    is_valid: bool
    device: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class RowProcessingResult(BaseModel):
    row_number: int
    phone: str
    message: str
    status: TriggerHistoryStatus
    error: Optional[str] = None

