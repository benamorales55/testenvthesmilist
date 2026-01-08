import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalFunctions.script import fillNumberWithZero

def create_groupName(fee_data):
    for key,value in fee_data.items():
        schedule_id = value['Smilist TIN']
        if schedule_id != "":
            schedule_number = fillNumberWithZero(schedule_id)
            new_groupName = f"{value['State']}-{key}-{schedule_number}"
        
    return new_groupName

