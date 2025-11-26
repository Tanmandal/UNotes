

def pick_color():
    import random
    # Color palette for notes
    COLORS = [
        'rgba(255, 0, 0, 0.551)', 
        'rgba(255, 217, 0, 0.573)', 
        '#ed1e78a2', 
        '#FF5F6D', 
        'rgba(210, 105, 30, 0.7)', 
        'rgba(0, 255, 128, 0.629)'
    ]
    return random.choice(COLORS)

def get_date_string():
    from datetime import datetime
    dt = datetime.now()
    return dt.strftime("%B %d, %Y")

def get_uuid():
    import uuid
    import base64
    unique_id = uuid.uuid4()
    unique_id = base64.urlsafe_b64encode(unique_id.bytes).rstrip(b'=').decode('ascii')
    return unique_id