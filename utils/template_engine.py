import re
from typing import Dict, Any

def render_template(template: str, data: Dict[str, Any]) -> str:
    """
    Render a message template by replacing {{variable}} with values from data.
    
    Example:
        template: "Hello {{name}}, your ID is {{id}}"
        data: {"name": "Vikas", "id": 101}
        Result: "Hello Vikas, your ID is 101"
    """
    if not template:
        return ""
    
    # Use regex to find all matches of {{variable}}
    # This pattern matches anything inside {{ }} including whitespace
    matches = re.findall(r"{{(.*?)}}", template)
    
    rendered_text = template
    for match in matches:
        key = match.strip()
        # Get value from data, default to empty string if missing
        value = data.get(key, "")
        # Replace the literal {{match}} with the string value
        # We use f"{{{{{match}}}}}" to match the original literal including its own whitespace
        rendered_text = rendered_text.replace(f"{{{{{match}}}}}", str(value))
        
    return rendered_text
