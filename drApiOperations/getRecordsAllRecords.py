import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from requests import get
from json import loads
from drApiVariables import hostGetPlan, headers
import urllib

def get_all_records():
    
    url = f"{hostGetPlan}"
    response = get(url,headers=headers)
    data = loads(response.content)
    return data
            

data_response = get_all_records()


print(len(data_response))
for row in data_response["data"]:
    if  row["plan_employer"] == "EMPTY" and row["location_id"] == "MATTITUCK":
        print(f'{row["location_id"]} {row["plan_employer"]} {row["group_plan_name"]} {row["fee_schedule_id"]} \t {row["plan_group_number"]} \t{row["maximum_benefit_individual"]} \t \t{row["deductible_standard_individual_annual"]} \t{row["carrier"] }')
        #print(row)

