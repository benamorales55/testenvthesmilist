import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalFunctions.script import setLog,GetVar,read_json,get_plan_type
from difflib import SequenceMatcher as SM
from pathlib import Path


def search_fee_info(practice : str, carrier : str, fee_schedule: str,group_name :str):
    print(practice,carrier,fee_schedule,group_name)
    # try:
    # route = os.path.dirname(os.path.abspath(__file__))
    # feed_data = f"{route}\\fee_data.json"
    # # # route = os.path.dirname(os.path.abspath(__file__))
    route = Path(__file__).parent.parent

    # Usuario actual del sistema
    try:
        usuario = os.getlogin()
    except Exception:
        usuario = "unknown_user"
    
    print("usuario: {}".format(usuario))


    # feed_data = f"{route}\\fee_data\\fee_data_{usuario}.json"
    feed_data = f"{route}\\fee_data.json"

    data = read_json(feed_data)
    plan_type = get_plan_type(fee_schedule,carrier)  or fee_schedule
    plan_type = "PPO" if plan_type == "PPO|TOTAL DPPO" else plan_type
    plans_list = {
        "PPO" : "PPO",
        "PDP" : "PDP",
        "HMO" : "HMO",
        "MCD" : "MCD",
        "DSC" : "DSC",
        "SM1" : "SM1",
        "LOC" : "LOC",
        "IND" : "IND",
        "MCV" : "MCV",
        "TOTAL DPPO" : "PPO",
        "DPPO" : "PPO",
        "DHMO" : "HMO",
        "PREMIER" : "PREMIER"
    }
    bk = (GetVar("bk"))
    OutofNetworkYES = bk['OutofNetworkYES'] == 'n'
    PatientOON = bk['PatientOON'] == 'n'

    def get_nodo_total(plan,carrier_plan):
        plan_actual = plan
        info_nodo = carrier_plan['Plan Type'][plan]
        nodo_plan = {
            "PPO":carrier_plan['Plan Type'][plan] for plan in carrier_plan['Plan Type']
            if re.fullmatch(plan,plan_actual,re.IGNORECASE)
        }
        setLog(f"note:The fee schedule was selected by PlanType "
            f"[PlanType: {plan_actual},MasterRow: {info_nodo['Row_number']}, SmilistTin: {info_nodo['Smilist TIN']}]|")
        return nodo_plan

    if OutofNetworkYES and PatientOON:
        plan = 'UCR'
        nodo = {
            plan:values[plan]['Plan Type'][plan] for key,values in data.items() 
            if key.lower().strip() == practice.lower()
        }
        setLog(f"note:the fee schedule was selected UCR, "
            f"[MasterRow: {data[practice][plan]['Plan Type'][plan]['Row_number']},"
            f"MasterTIN:{data[practice][plan]['Plan Type'][plan]['Smilist TIN']}]|")
        return nodo
    
    if plan_type:
        clinic_nodo = {
            key:values for key, values in data.items()
            if key.lower().strip() == practice.lower()
        }
        
        carrier_plan = {
            'Plan Type':value['Plan Type'] for key, value in clinic_nodo[practice].items()
            if re.search(value['regex'], carrier, re.IGNORECASE)
            and key.lower() != "empty"
            and clinic_nodo
        }
        
        if not clinic_nodo:
            setLog(f'The clinic {practice} is not in the MASTER DATA|')
            return None
        if not carrier_plan:
            setLog(f'The carrier {carrier} does not match with any regex in the fee data|')
            return None
        no_matching_plans = {
            individual_plan.strip() : plan
            for plan in carrier_plan['Plan Type']
            for individual_plan in plan.split('|')
            if individual_plan.strip() not in plans_list.keys()
        }
        print("carrier plan ", no_matching_plans)
        for plan in no_matching_plans.keys():
            percentage = int(SM(None,plan.lower(), group_name.lower()).ratio() * 100)
            if percentage >= 75:
                original_plan = no_matching_plans[plan]
                info_nodo = carrier_plan['Plan Type'][original_plan]
                nodo_plan = {'PPO':info_nodo}
                setLog(f"note:The fee schedule was selected by GROUP NAME"
                    f"[GroupName: {plan},MasterRow: {info_nodo['Row_number']},SmilistTin: {info_nodo['Smilist TIN']}]")
                return nodo_plan
            else:
                if percentage < 80 and percentage > 70:
                    setLog(f"note:The percentage between Group Name and Master Data is {percentage}"
                        f"review if the name [{plan}] in the Master is correct")
    
        for plan in no_matching_plans.keys():
            actual_plan = plan.lower().strip()
            print("working here")
            actual__fee = fee_schedule.lower().strip()
            if actual_plan == actual__fee:
                original_plan = no_matching_plans[plan]
                info_nodo = carrier_plan['Plan Type'][original_plan]
                nodo_plan = {'PPO':info_nodo}
                setLog(f"note:The fee schedule was selected by FEE SCHEDULE FORM"
                    f"[FeeSchedule: {fee_schedule},MasterRow: {info_nodo['Row_number']},SmilistTin: {info_nodo['Smilist TIN']}]")
                return nodo_plan
        
        for plan in carrier_plan['Plan Type']:
            if re.search(f"^{plan}$",plan_type,re.IGNORECASE):
                plan_actual = re.search(f"{plan}",plan_type,re.IGNORECASE).group() if plan_type != 'TOTAL DPPO' else 'PPO'
                plan_actual = plans_list[plan_actual]
                info_nodo = carrier_plan['Plan Type'][plan]
                nodo_plan = {plan_actual:info_nodo}
                print(type(nodo_plan))
                print(f"PLAN ACTUAL {nodo_plan}")
                if nodo_plan and len(next(iter(nodo_plan.keys()))) > 3:
                    plan_default = "PPO"
                    nodo_plan = {plan_default:info_nodo}

                setLog(f"note:The fee schedule was selected by PlanType "
                f"[PlanType: {plan_actual},MasterRow: {info_nodo['Row_number']}, SmilistTin: {info_nodo['Smilist TIN']}]|")
                return nodo_plan
        
        if plan_type.lower() == 'total dppo':
            plan_actual = 'DPPO'
            if plan_actual in carrier_plan['Plan Type']:
                nodo_plan = get_nodo_total(plan_actual,carrier_plan)
                return nodo_plan
        
        plan_actual = 'PPO'
        if plan_actual in carrier_plan['Plan Type']:
            nodo_plan = get_nodo_total(plan_actual,carrier_plan)
            return nodo_plan
    return None
