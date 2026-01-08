import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalVariables.script import data_supplies
from globalFunctions.script import read_json,setLog
from searchDQfishkillPlan import search_dq_fishkill_plan
from pathlib import Path

def fee_schedule_elg(dental_plan: str, option: str):
    clinic_name = data_supplies['practice']
    route = Path(__file__).parent.parent
    # feed_data = f"{route}\\fee_data.json"
    # route = os.path.dirname(os.path.abspath(__file__))

    # Usuario actual del sistema
    try:
        usuario = os.getlogin()
    except Exception:
        usuario = "unknown_user"

    feed_data = f"{route}\\fee_data.json"
    # feed_data = f"{route}\\fee_data\\fee_data_{usuario}.json"
    data = read_json(feed_data)
    print(data)
    # Diccionario de aliases para normalizar nombres de planes
    plan_name_aliases = {
        "EBF MEMBER PLUS": "EBF",
        "UCS RETIREE" : "UCS RETIRED"
        # Agregá más aliases según sea necesario
    }

    # Función interna para normalizar el nombre del plan
    def normalize_plan(plan_name):
        return plan_name_aliases.get(plan_name.upper(), plan_name).lower()

    normalized_plan = normalize_plan(dental_plan)

    if clinic_name in data:
        option_lower = option.lower()

        if option_lower == "csea":
            if 'CSEA' in data[clinic_name]:
                nodo = data[clinic_name]['CSEA']['Plan Type']

                nodo_plan = next(
                     (value for key, value in nodo.items() if normalized_plan in key.lower()),
                     {}
                )

                # nodo_plan = next(
                #     (value for key, value in nodo.items() 
                #     if int(SM(None,normalized_plan.lower(), key.lower()).ratio() * 100) >= 90),
                #     {}
                # )

                if nodo_plan:
                    return nodo_plan
                else:
                    setLog(f'PLAN DENTAL: {dental_plan} DOES NOT MATCH WITH ANY PLAN IN MASTER')
            else:
                setLog(f'CSEA is not in the clinic {clinic_name}')

        elif option_lower == "uhc":
            if 'United HealthCare' in data[clinic_name]:
                nodo = data[clinic_name]['United HealthCare']['Plan Type']

                nodo_plan = next(
                    (value for key, value in nodo.items() if normalized_plan in key.lower()),
                    {}
                )

                if nodo_plan:
                    return nodo_plan
                else:
                    setLog(f'PLAN DENTAL: {dental_plan} DOES NOT MATCH WITH ANY PLAN IN MASTER')
            else:
                setLog(f'United HealthCare is not in the clinic {clinic_name}')

        elif option_lower == "dq":
            if "Sunlife Dentaquest" in data[clinic_name]:
                nodo = data[clinic_name]['Sunlife Dentaquest']['Plan Type']
                plan_names = [key for key, values in nodo.items() if nodo]
                plan_found = search_dq_fishkill_plan(plan_names, dental_plan)

                if plan_found and nodo:
                    nodo_plan = nodo[plan_found]
                    return nodo_plan
                else:
                    setLog(f'PLAN DENTAL: {dental_plan} DOES NOT MATCH WITH ANY PLAN IN MASTER')
            else:
                setLog(f'Dentaquest is not in the clinic {clinic_name}')
    else:
        setLog(f'The clinic {clinic_name} is not in the master.')

    return None

