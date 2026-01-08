import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalFunctions.script import fillNumberWithZero,GetVar,setLog,print_log
from globalVariables.script import SUCCESS,data_supplies
from createGroupName import create_groupName 
from searchFeeInfo import search_fee_info


def get_group_name(data_supplies):
    global create_groupName,fillNumberWithZero,search_fee_info
    try:
        if data_supplies['type_of_verification'] == 'FBD' and 'INACTIVE' not in data_supplies['verification_status'].upper():
            # patient_insurance = eval(GetVar("patient_insurance_info"))
            general_info = (GetVar("bk")) if GetVar("bk") != "" else {}
            
            group_name = general_info["GroupName"]
            fee_schedule = general_info['FeeScheduleName']
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
