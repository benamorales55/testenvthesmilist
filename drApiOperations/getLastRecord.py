import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from requests import get
from drApiVariables import hostGetPlan, headers
from json import loads

def get_last_record():
    response = get(hostGetPlan, headers=headers)
    data = loads(response.content)

    if len(data['data']) > 0:
        last_record = data['data'][-1]['group_plan_name'].split("-")[-1]
        
        while last_record[0].isalpha():
            data['data'].pop() 
            if len(data['data']) == 0:  
                return 1 
            last_record = data['data'][-1]['group_plan_name'].split("-")[-1]
        last_record = int(last_record)
        print(last_record)
        last_record += 1
    else:
        last_record = 0

    return last_record

latst= get_last_record()
print(latst)