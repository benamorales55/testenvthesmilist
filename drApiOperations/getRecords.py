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
            

data_response = get_records("THE STATE OF NEW YORK")

data_response = [plan_api for plan_api in data_response["data"] if plan_api["location_id"] == "AMHERST"]
print(data_response)