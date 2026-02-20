# import pandas as pd
# import json
# import re
# import os
# import sys

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from globalVariables.carriersRegex import carriers_regex
# from globalVariables.master import MASTER
# from pathlib import Path
# from globalVariables.script import static_regex,data_supplies
# from globalFunctions.script import setLog,read_json,fillNumberWithZero,generate_amounts_dict

# def fee_schedule_elg(dental_plan: str, option: str):
#     clinic_name = data_supplies['practice']
#     route = os.path.dirname(os.path.abspath(__file__))
#     # feed_data = f"{route}\\fee_data.json"
#     route = os.path.dirname(os.path.abspath(__file__))

#     # Usuario actual del sistema
#     try:
#         usuario = os.getlogin()
#     except Exception:
#         usuario = "unknown_user"


#     feed_data = f".\\fee_data.json"
#     data = read_json(feed_data)

#     # Diccionario de aliases para normalizar nombres de planes
#     plan_name_aliases = {
#         "EBF MEMBER PLUS": "EBF",
#         "UCS RETIREE" : "UCS RETIRED"
#         # Agregá más aliases según sea necesario
#     }

#     # Función interna para normalizar el nombre del plan
#     def normalize_plan(plan_name):
#         return plan_name_aliases.get(plan_name.upper(), plan_name).lower()

#     normalized_plan = normalize_plan(dental_plan)
#     print(normalized_plan, "plan normalizado")

#     if clinic_name in data:
#         option_lower = option.lower()

#         if option_lower == "csea":
#             if 'CSEA' in data[clinic_name]:
#                 nodo = data[clinic_name]['CSEA']['Plan Type']

#                 # nodo_plan = next(
#                 #      (value for key, value in nodo.items() if normalized_plan in key.lower()),
#                 #      {}
#                 # )
#                 if normalized_plan:

#                     nodo_plan = next(
#                         (value for key, value in nodo.items() if normalized_plan and key.lower().startswith(normalized_plan.lower()) ),
#                         {}
#                     )
            
#                     if not nodo_plan:
#                         nodo_plan = next(
#                         (value for key, value in nodo.items() if normalized_plan.lower() in key.lower()),
#                         {}
#                     )
                    
#                     if nodo_plan:
#                         print(nodo_plan,"REVIEW THE NODO PLAN")
#                         return nodo_plan
                        
#                     else:
#                         setLog(f'PLAN DENTAL: {dental_plan} DOES NOT MATCH WITH ANY PLAN IN MASTER')
                    
                
#             else:
#                 setLog(f'CSEA is not in the clinic {clinic_name}')

#         elif option_lower == "uhc":
#             if 'United HealthCare' in data[clinic_name]:
#                 nodo = data[clinic_name]['United HealthCare']['Plan Type']

#                 nodo_plan = next(
#                     (value for key, value in nodo.items() if normalized_plan in key.lower()),
#                     {}
#                 )

#                 if nodo_plan:
#                     return nodo_plan
#                 else:
#                     setLog(f'PLAN DENTAL: {dental_plan} DOES NOT MATCH WITH ANY PLAN IN MASTER')
#             else:
#                 setLog(f'United HealthCare is not in the clinic {clinic_name}')

#         # elif option_lower == "dq":
#         #     if "Sunlife Dentaquest" in data[clinic_name]:
#         #         nodo = data[clinic_name]['Sunlife Dentaquest']['Plan Type']
#         #         plan_names = [key for key, values in nodo.items() if nodo]
#         #         plan_found = search_dq_fishkill_plan(plan_names, dental_plan)

#         #         if plan_found and nodo:
#         #             nodo_plan = nodo[plan_found]
#         #             return nodo_plan
#         #         else:
#         #             setLog(f'PLAN DENTAL: {dental_plan} DOES NOT MATCH WITH ANY PLAN IN MASTER')
#         #     else:
#         #         setLog(f'Dentaquest is not in the clinic {clinic_name}')
#     else:
#         setLog(f'The clinic {clinic_name} is not in the master.')

#     return None

# def get_elg_info(carrier_name: str, group_name: str):
#     if re.search(static_regex['csea_reg'], data_supplies['carrier_name'], re.IGNORECASE):
#         # print("CSEA regex matched in carrier_name:", data_supplies['carrier_name'])

#         matchcsea = re.search(r'\b(Dental|Plan)\b', group_name, re.IGNORECASE)
#         # print("Match for 'Dental' or 'Plan' in group_name:", matchcsea)

#         if matchcsea:
#             dental_plan = group_name[:matchcsea.start()].strip()
#             # print("dental_plan before splitting (matchcsea):", dental_plan)

#             dental_plan = dental_plan.upper().split("|")[1].strip()
#             # print("dental_plan after splitting (matchcsea):", dental_plan)

#             employer_plan = dental_plan
#             groupnumber = dental_plan
#         else:
#             dental_plan = group_name.upper().split('|')[1].strip()
#             print("dental_plan without matchcsea:", dental_plan)

#             employer_plan = dental_plan
#             groupnumber = dental_plan

#         # print("Practice location:", data_supplies['practice'])

#         if not data_supplies['practice'] == 'CATSKILL':
#             csea_data = fee_schedule_elg(dental_plan, "csea")
#             print("csea_data from fee_schedule_elg (not CATSKILL):", csea_data)
            
#         else:
#             csea_data = fee_schedule_elg('OON', 'csea')
#             print("csea_data from fee_schedule_elg (CATSKILL):", csea_data)

#         if csea_data:
#             fee_schedule = fillNumberWithZero(csea_data['Smilist TIN'])
#             # print("fee_schedule (zero-filled):", fee_schedule)

#             amounts = generate_amounts_dict()
#             # print("Generated amounts dict:", amounts)

#             info = {
#                 "group_plan": f"{csea_data['State']}-PPO-{fee_schedule}",
#                 "employer": employer_plan,
#                 "group_number": groupnumber,
#                 "annual_max": amounts['ind_max'],
#                 "deductible_standar": '0.00'
#             }
#             # print("Final info dict:", info)
#             return info
#         else:
#             print("No csea_data found.")
#             return None


# # print(data_supplies['verification_status'])
# # information = get_elg_info(data_supplies['carrier_name'], data_supplies['verification_status'])
# # # print(information)


# from datetime import datetime

# f1 = datetime.strptime("1/15/2020", "%m/%d/%Y")
# f2 = datetime.strptime("01/15/2020", "%m/%d/%Y")
# # f2 = datetime.strptime("", "%m/%d/%Y")
# print(f1 == f2)   # True
# print(f1 > f2)  

# def parse_date(date_str):
#     """Convierte varias representaciones de fecha a formato MM/DD/YYYY."""
#     formats = [
#         "%m/%d/%Y",           # formato americano
#         "%Y-%m-%d",           # ISO simple
#         "%Y-%m-%dT%H:%M:%S"   # ISO con tiempo
#     ]
#     for fmt in formats:
#         try:
#             return datetime.strptime(date_str, fmt).strftime("%m/%d/%Y")
#         except ValueError:
#             continue
#     return ""  # si no coincide con ningún formato válido
# fir = parse_date("1/15/2020")
# sec = parse_date("01/15/2020")
# print(fir)
# print(sec)
# print(fir == sec)
import re
from datetime import datetime

regex_date = (
    r"(\d{1,2}/\d{1,2}/\d{4}"
    r"|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"|\d{4}-\d{2}-\d{2}"
    r"|N/A|-)"
    )
def parse_date(date_str):
    if not date_str or date_str in ["N/A", "-"]:
        return None

    formats = [
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%m/%d/%Y")
        except ValueError:
            continue

    print(f"Date '{date_str}' does not match any allowed format: {formats} |")
    raise ValueError(f"Date '{date_str}'")

match = re.search(rf"{regex_date}\s*-\s*{regex_date}", "Active / OON Plan | PPO-UNITED WELFARE FUND-1786486 |2024-10-01 - 12/31/2026")

effectivedate, term_date = None, None

if match:
    raw_effective = match.group(1).strip()
    raw_term = match.group(2).strip()

    effectivedate = parse_date(raw_effective)
    term_date = parse_date(raw_term)


print(effectivedate, term_date)


if re.search("hmo", "the paln is dhmo", re.IGNORECASE):
    print("okkk")