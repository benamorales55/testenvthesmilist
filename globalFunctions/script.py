import importlib
import sys
import os
import re
from datetime import datetime
import re
import traceback
import unicodedata
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalVariables.script import data_supplies

class Colors:
    GREEN = '\033[92m'   # Verde
    RED = '\033[91m'     # Rojo
    YELLOW = '\033[93m'  # Amarillo
    BLUE = '\033[94m'    # Azul
    RESET = '\033[0m'    # Resetear color

def print_log(level, message):
    """
    Imprime un mensaje formateado con color según el nivel.
    
    level: tipo de mensaje (str) -> "SUCCESS", "ERROR", "WARNING", "INFO"
    message: el texto a mostrar
    """
    level = level.upper()
    color = Colors.RESET  # default
    
    if level == "SUCCESS":
        color = Colors.GREEN
    elif level == "ERROR":
        color = Colors.RED
    elif level == "WARNING":
        color = Colors.YELLOW
    elif level == "INFO":
        color = Colors.BLUE
    
    print(f"{color}[{level}] {message}{Colors.RESET}")


def setLog(e):
    print(e)


def GetVar(name):
    modules = ["globalVariables.script",
               "globalVariables.master",
               "globalVariables.queryResult",
               "globalVariables.resultIntegration",
               "globalVariables.bk",
               "globalVariables.allFeeSchedule"]

    for module_name in modules:
        module = importlib.import_module(module_name)
        if hasattr(module, name):
            return getattr(module, name)

    raise NameError(f"La variable '{name}' no existe en los módulos definidos.")


def get_info(diccionario, clave):
    return diccionario.get(clave)


def gpvars(name,second = None):
    modules = ["globalVariables.script",
               "globalVariables.master",
               "globalVariables.queryResult",
               "globalVariables.resultIntegration",
               "globalVariables.bk",
               "globalVariables.allFeeSchedule"]

    for module_name in modules:
        module = importlib.import_module(module_name)
        if hasattr(module, name):
            return getattr(module, name)

    raise NameError(f"La variable '{name}' no existe en los módulos definidos.")


def fillNumberWithZero(number: int):
    lenght_scheduleNumber = 6
    formatted_scheduleNumber = str(number).zfill(lenght_scheduleNumber)
    return formatted_scheduleNumber


def read_json(json_path):
    from json import load
    try:
        with open(json_path) as json_file:
            fee_info_data = load(json_file)
    except Exception as e:
        setLog(e)
        fee_info_data = []
    return fee_info_data


def get_plan_type(fee_schedule,carrier):
    plan_type = ""
    if re.compile('PPO|DPPO',re.IGNORECASE).search(fee_schedule):
        plan_type += "PPO|"
    if re.compile('PDP',re.IGNORECASE).search(fee_schedule):
        plan_type += "PDP|"
    if re.compile('HMO|DHMO',re.IGNORECASE).search(fee_schedule):
        plan_type += "DHMO|"
    if re.compile('DMO',re.IGNORECASE).search(fee_schedule):
        plan_type += "DMO|"
    if re.compile('MEDICAID|MCO|NJH|DQ|UHCCP|HPLX|STRAIGHT MEDICAIDS',re.IGNORECASE).search(fee_schedule):
        plan_type += "MCD|"
    if re.compile('DISCOUNT|EDP|AETNA|ACCESS',re.IGNORECASE).search(fee_schedule):
        plan_type += "DSC|"
    if re.compile('SMILIST ONE MEMBERSHIP',re.IGNORECASE).search(fee_schedule):
        plan_type += "SM1|"
    if re.compile('LOCAL & UNION',re.IGNORECASE).search(fee_schedule):
        plan_type += "LOC|"
    if re.compile('INDEMNITY',re.IGNORECASE).search(fee_schedule):
        plan_type += "IND|"
    if re.compile('MEDICARE ADVANTAGE',re.IGNORECASE).search(fee_schedule):
        plan_type += "MCV|"
    if re.compile('ADVANTAGE',re.IGNORECASE).search(fee_schedule) and re.search(r"(?i)^Cigna.*",carrier):
        plan_type += "PPO|"
    if re.compile('TOTAL',re.IGNORECASE).search(fee_schedule) and re.search(r"(?i)^Cigna.*",carrier):
        plan_type += "TOTAL DPPO|"
    if re.compile('DENTALGUARD PREFERRED',re.IGNORECASE).search(fee_schedule) and re.search(r"(?i)^Guardian.*",carrier):
        plan_type += "PPO|"
    if re.compile('Premier',re.IGNORECASE).search(fee_schedule):
        plan_type += 'PREMIER|'
        
    return plan_type[:-1]


def cleanText(text):
    try:
        cleaned_text = re.sub(r"(?:Sr|Ms|Dr)*(\.|\s|,|\/|\\)|[`']|[^\w\s]+|\s+|\xb2", ' ', text).strip()
        cleaned_text = unicodedata.normalize('NFKD', cleaned_text).encode('ascii', 'ignore').decode()
        return cleaned_text
    except:
        traceback.print_exc()

    
def replace_empty(value):
    return value if pd.notna(value) and value != "" else "EMPTY"


def format_datetime(date):
    global pd
    if date != 'EMPTY':
        date_to_format = pd.to_datetime(date)
        date_to_format = date_to_format.strftime('%m/%d/%Y')
    else:
        date_to_format = 'EMPTY'
    return date_to_format


def generate_table_base_category(template,rule):
    table = []
    template = template[1:]
    for row in template:
        category = row[2].lower()
        if rule == 'ortho_and_implant':
            if 'ortho' in category or 'implant' in category:
                table.append(row + ["0", "S", "Empty"])
            else:
                table.append(row + ["100", "S", "Empty"])
        elif rule == 'zero': 
            table.append(row + ["0", "S", "Empty"])
        elif rule == 'hundred':  
            table.append(row + ["100", "S", "Empty"])
    return table


def is_date_formated(date_str):
    from datetime import datetime
    try:
        datetime.strptime(date_str, "%m/%d/%Y")
        return True
    except ValueError:
        return False
    

def iso_date_formated(date_str):
    from datetime import datetime
    try:
        if bool(datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")): 
            return True
    except ValueError:
        return False
    

def iso_simple_formated(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False
    

def last_day_next_month(fecha):
    from datetime import datetime, timedelta
    date_obj = datetime.strptime(fecha, '%Y-%m-%d')
    
    if date_obj.month == 12:
        first_day_next_month = datetime(date_obj.year + 1, 1, 1)
    else:
        first_day_next_month = datetime(date_obj.year, date_obj.month + 1, 1)
    
    last_day_next_month = first_day_next_month + timedelta(days=31)
    last_day_next_month = last_day_next_month.replace(day=1) - timedelta(days=1)
    return last_day_next_month.strftime('%m/%d/%Y')


def is_leap(year):
    return (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))


def february_leap(fecha):
    try:
        fecha = datetime.strptime(fecha,'%m/%d/%Y')
        if fecha.month == 2:
            if fecha.day == 29 and not is_leap(fecha.year):
                return False
            return True
        return False
    
    except ValueError:
        return False


def parse_date(date_str):
    """Convierte varias representaciones de fecha a formato MM/DD/YYYY."""
    formats = [
        "%m/%d/%Y",           # formato americano
        "%Y-%m-%d",           # ISO simple
        "%Y-%m-%dT%H:%M:%S"   # ISO con tiempo
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%m/%d/%Y")
        except ValueError:
            continue
    return ""  # si no coincide con ningún formato válido


def extract_effective_and_term_dates(verification_status):
    regex_date = r"(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}|N/A|-|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
    match = re.search(rf"{regex_date}\s*-\s*{regex_date}", verification_status)

    effectivedate, term_date = "", ""

    if match:
        raw_effective = match.group(1).strip()
        raw_term = match.group(2).strip()

        effectivedate = parse_date(raw_effective)
        term_date = parse_date(raw_term)

    print(f"*********effectivedate: {effectivedate}, term_date: {term_date}")
    return effectivedate, term_date


def generate_amounts_dict():
    amounts_row = data_supplies['amounts']
   
    if amounts_row and amounts_row.lower() != "empty":
        amounts_values = amounts_row.split('-')
        amounts_dict = {key: ('0' if value == 'None' else
        None if value in ['N/A', '-', '', '$NaN','Not applicable'] else
        re.sub(r'[\$,]', '', value))
        for amount in amounts_values
        for key, value in [amount.split(':')]}

        for key, amount in amounts_dict.items():
            if amount:
                if amount.count('.') == 1:
                    numero = float(amount)
                    if numero.is_integer(): 
                        amounts_dict[key] = str(int(numero))
                    else:
                        amounts_dict[key] = str(numero)
                elif amount.count(".")> 1:
                    cleaned_amount = amount.replace('.', '', amount.count('.') - 1)
                    cleaned_amount = cleaned_amount.replace('.', ',')
                    numero = float(cleaned_amount.replace(',', '.'))
                    if numero.is_integer(): 
                        amounts_dict[key] = str(int(numero))
                    else:
                        amounts_dict[key] = str(numero)
                        
                normalized_amount = str(amount).strip().lower()
    
                # Caso 'unlimited'
                if normalized_amount == "unlimited":
                    amounts_dict[key] = "9999"

                # Caso cuando el valor numérico excede 9999
                else:
                    numeric_amount = float(normalized_amount.replace(',', ''))
                    if numeric_amount > 9999:
                        amounts_dict[key] = "9999"
                    else:
                        amounts_dict[key] = str(numeric_amount)
    return amounts_dict


def unlimited_value(mbi, am):
    def unlimited_(value):
        return all(char == '9' for char in str(value))
    
    if unlimited_(mbi) and unlimited_(am):
        return True
    if mbi == am:
        return True
    return False


def clean_regex(regex):
    regex = regex.replace('(?i)',"")
    return r'(?i)' + regex

