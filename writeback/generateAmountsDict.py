import sys
import os
import re 
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalVariables.script import ELG_PATTERNS,data_supplies,static_regex,iv_config
from globalFunctions.script import clean_regex,get_info,read_json,setLog

def generate_amounts_dict():
    amounts_row = data_supplies['amounts']
   
    if amounts_row and amounts_row.lower() != "empty":
        #amounts_values = amounts_row.split('-')
        amounts_values = re.split(r'--|-', amounts_row)
        amounts_values = [v for v in amounts_values if v]

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

amounts_dict = generate_amounts_dict()
amounts = {}
print(amounts_dict)
if amounts_dict["ind_max"] == None:
    amounts["AnnualMaximum"] = "99999"
if amounts_dict["ind_max"]: amounts["AnnualMaximum"] = amounts_dict['ind_max']
if amounts_dict['ind_ded']: amounts["Deductible"] = amounts_dict['ind_ded']
def have_number(value):
    return bool(re.match(r"\d", value))

for key in amounts:
    if not have_number(str(amounts[key]).strip()):
        if amounts[key] == 'Not applicable':
            amounts[key] = '0'
        else:
            setLog(f"THE KEY '{key}' HAS NO NUMERIC VALUE: {amounts[key]}")
            raise Exception(f"La clave '{key}' no tiene un valor numérico2: {amounts[key]}")
note = f"Amounts updates in the review of emblem:: upd AI: {amounts['Deductible']} , upd AM: {amounts['AnnualMaximum']}|"
print(note)

print(iv_config["clinic_settings"]["settings"])