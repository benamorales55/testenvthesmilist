import os
import sys 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
from fuzzywuzzy import fuzz
from globalFunctions.script import gpvars
from elgData import elg_data
import traceback

today_date = gpvars("sheet")
today_date= datetime.strptime(today_date.strip(), '%Y-%m-%d')

def find_match(api_results,row_data,type_verification):
    print(len(api_results))
    search_filters = {
        "with_id":{
            "consult":['carrier_name','member_id','patient_id','ordinal'],
            "api":['CarrierName','MemberID','PatientId','policyType']
        },
        "whithout_id":{
            "consult":['carrier_name','member_id','patient_first_name','patient_last_name','patient_dob'],
            "api":['CarrierName','MemberID','PatientFirstName','PatientLastName','PatientDOB']
        }
    }

    filters = search_filters['with_id'] if row_data["patient_id"].lower() != 'empty' else search_filters['whithout_id']
    try:
        match_patient = 0
        new_filtered_data = []
        results= []
        patient_verified = None
        if api_results:
            for item in api_results:
                consult = [row_data.get(key) for key in filters.get('consult')]
                api = [item.get(key) for key in filters.get('api')]
                similarity = fuzz.token_set_ratio(consult,api)
                
                match_patient = similarity
                if similarity >= 95:
                    new_filtered_data.append(item)
                        
                print(f"There is a {similarity}% match between \n api data and consult")
            current_year = datetime.now().year

            if type_verification == "FBD":

                fbd_items = [
                    item for item in new_filtered_data
                    if item['type'] == 'FBD' and 'ApptDate' in item and
                    datetime.strptime(item['ApptDate'], '%Y-%m-%d').year == current_year
                ]
                
                if fbd_items:
                    fbd_items.sort(key=lambda x: datetime.strptime(x['ApptDate'], '%Y-%m-%d'))
                    already_verified_fbd = any(
                        item.get('ApptDate') and datetime.strptime(item['ApptDate'], '%Y-%m-%d') > today_date
                        for item in fbd_items if 'ApptDate' in item
                    )
                    
                    last_fbd = fbd_items[-1] 
                    last_elg,already_verified_elg = elg_data(new_filtered_data)
            
                    if last_elg :
                        patient_verified = already_verified_elg
                        results =  last_elg
                    else:
                        patient_verified = already_verified_fbd
                        results =  last_fbd
                else:
                    patient_verified = False
                    print("No existe ningun FBD con ApptDate en el ano actual.")
            else:
                last_elg,already_verified_elg = elg_data(new_filtered_data)
                if last_elg:
                    patient_verified = already_verified_elg
                    results = last_elg
        return match_patient,results,patient_verified
    except:
        traceback.print_exc()
        return None, [],None