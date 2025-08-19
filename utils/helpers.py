from datetime import datetime

def format_currency(value):
    return f"${value:,}"

def format_date(date_str, input_format="%d-%m-%Y", output_format="%d/%m/%Y"):
    try:
        date = datetime.strptime(date_str, input_format)
        return date.strftime(output_format)
    except ValueError:
        return date_str

def calculate_age(birth_date):
    try:
        today = datetime.now()
        birth_date = datetime.strptime(birth_date, "%d-%m-%Y")
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except ValueError:
        return None