import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
from json import loads
from requests import get
from globalVariables.script import iv_config,SUCCESS,WARNING,data_supplies
from globalFunctions.script import print_log,get_info,gpvars
from drApiOperations.drApiVariables import hostGetPatient, headers
import traceback


def search_verifications(row_data:dict = {}):
    #practice  = get_info(iv_config, f"clinic_settings.settings.{gpvars('practice')}.clinic_name")
    try:
        results = []
        params = {}
        practice = get_info(row_data,'practice')
        
        # Default params
        default_params = {
            "clientId": os.getenv('clientID'),
            "appointmentDateStart": f"{datetime.now().year}-01-01",
            "appointmentDateEnd": f"{datetime.now().year}-12-31"
        }
        
        # By # By current clinic and patient_id
        if get_info(row_data, "patient_id").lower() != 'empty':
            params = {**default_params, **{
                "practiceId": iv_config["clinic_settings"]["settings"][row_data["practice"]]["practice_id"],
                "patientId":get_info(row_data, "patient_id"),
                "policyType":get_info(row_data, "Primary")
            }}

            response = get(hostGetPatient, headers=headers, params = params)
            data = loads(response.content)
            if data["data"]: results += data["data"]
            print_log(SUCCESS,"FOUND DATA BY PATIENT")
            # # # print(data)
            
        else:
            # By current clinic and full patient data
            params = {**default_params, **{
                "practiceId": iv_config["clinic_settings"]["settings"][row_data["practice"]]["practice_id"],
                "patientFirstName":get_info(row_data, "patient_first_name"),
                "patientLastName": get_info(row_data, "patient_last_name"),
                "patientDOB": get_info(row_data, "patient_dob")            
            }}
            response = get(hostGetPatient, headers=headers, params = params)
            data = loads(response.content)
            if data["data"]: results+= data["data"]
        
            # # # print(results)
            # By full patient data
            if not results:
                params = {**default_params, **{
                    "patientFirstName":get_info(row_data, "patient_first_name"),
                    "patientLastName": get_info(row_data, "patient_last_name"),
                    "patientDOB": get_info(row_data, "patient_dob")            
                }}
                response = get(hostGetPatient, headers=headers, params = params)
                data = loads(response.content)
                if data["data"]: results+= data["data"]
        
            # By patient name
            if not results:
                params = {**default_params, **{
                    "patientFirstName":get_info(row_data, "patient_first_name"),
                    "patientLastName": get_info(row_data, "patient_last_name")       
                }}
                response = get(hostGetPatient, headers=headers, params = params)
                data = loads(response.content)
                if data["data"]: results+= data["data"]

        if results:
            filtered_data = [item for item in results if item.get('driveFiles')]
            results = filtered_data
        else:
            print_log(WARNING, "No results were found with the criteria")  
            print(row_data)       
        return results
    except:
        traceback.print_exc()


values = search_verifications(data_supplies)
print(len(values))
print(values)

for row in values:
    print(row["CarrierName"],row["type"],row["MemberID"],row["driveFiles"],row["audited"],row["policyType"])
    print()