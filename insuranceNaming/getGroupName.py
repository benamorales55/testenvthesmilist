import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalFunctions.script import fillNumberWithZero,GetVar,setLog,print_log
from globalVariables.script import SUCCESS,data_supplies
from createGroupName import create_groupName 
from searchFeeInfo import search_fee_info
anthem_re = r"(?i)^((Anthem.*)|((Bcbs|Bc bs(?!$)|Blue Cross|Blue shield|Blue Cross Blue Shield|Bluecross Blueshield)( (Of )?(Alabama|Arkansas|California|- Kansas|Massachu(s?setts)?|Michigan|Minnesota|Pennsylvania|South Carolina|AL|Ar|CA|KS|MA(SS?)?|Mi|MN|PA|SC|Kc|indemnit))?))$"

def get_group_name(data_supplies):
    global create_groupName,fillNumberWithZero,search_fee_info
    try:
        if data_supplies['type_of_verification'] == 'FBD' and 'INACTIVE' not in data_supplies['verification_status'].upper():
            # patient_insurance = eval(GetVar("patient_insurance_info"))
            general_info = (GetVar("bk")) if GetVar("bk") != "" else {}

            #rule for anthem
            if re.match(anthem_re, data_supplies["carrier_name"]):
                anthem_plan_num = data_supplies["verification_status"].split("|")[-2].strip()
                anthem_plan_numeric = r'\b(10|20|30)\b'
                match_anthem = re.search(anthem_plan_numeric, anthem_plan_num)
                if match_anthem:
                    fee_schedule = str(int(match_anthem.group(1)) * 10)
            #end of rule     
            else:
                fee_schedule = general_info['FeeScheduleName']
                
            
            group_name = general_info["GroupName"]
            practice = data_supplies['practice']
            carrier_name = data_supplies['carrier_name']
            smilist_tin = None
            new_name_group_name = None
            if fee_schedule.strip() != "" and fee_schedule.upper().strip() not in ["EMPTY", "NONE"]:
                new_fee_info = search_fee_info(practice,carrier_name,fee_schedule,group_name)
                print_log(SUCCESS,"INFO ABOUT THE NEW FEE")
                print(new_fee_info)
                
            if new_fee_info:
                for key,value in new_fee_info.items():
                    smilist_tin = value["Smilist TIN"]
                new_name_group_name = create_groupName(new_fee_info)
                if new_name_group_name:
                    new_name_group_name = new_name_group_name.upper()
                else:
                    return None,None
            return new_name_group_name,smilist_tin
    except Exception as e :
        print(e,"tesss")
        setLog("[ERROR GENERATING NEW GROUP NAME]")
        print("------[ERROR GENERATING NEW GROUP NAME]--------\n")
        return None,None
        

val = get_group_name(data_supplies)
print(val)
