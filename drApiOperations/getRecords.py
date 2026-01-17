import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from requests import get
from json import loads
from drApiVariables import hostGetPlan, headers
import urllib

def get_records(employer_name:str):
    employer_name = urllib.parse.quote(employer_name,safe='')
    url = f"{hostGetPlan}/employer/{employer_name}"
    response = get(url,headers=headers)
    data = loads(response.content)
    return data
            

data_response = get_records("MEDICARE DENTAL")

# data_response = [plan_api for plan_api in data_response["data"] if plan_api["location_id"] == "MEDFORD"]
# print(len(data_response))
# print(data_response)
# for row in data_response:
#     print(f'{row["location_id"]} {row["plan_employer"]} {row["group_plan_name"]} {row["fee_schedule_id"]} \t {row["plan_group_number"]} \t{row["maximum_benefit_individual"]} \t \t{row["deductible_standard_individual_annual"]} \t{row["carrier"] }')