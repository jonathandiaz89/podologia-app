import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    return re.match(r'^\+?\d{8,15}$', phone) is not None

def validate_date(date_str, format="%d-%m-%Y"):
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False