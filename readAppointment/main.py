import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalFunctions.script import GetVar
from readAppointmentscript import readAppoinments


try:
    sheet = GetVar("sheet")
    iv_config = (GetVar("iv_config"))
    reportType = iv_config["isExtractionTypeReport"]
    idSpreedSheet =GetVar("idSpreedSheet")
    #anexada
    run_config = (GetVar("run_config"))
    practices = [value['practice'] for value in run_config if iv_config["clinic_settings"]["settings"][value['practice']]["spreadsheet_id"] == idSpreedSheet]
    print(practices)
    query_result = (GetVar('query_result'))
    header = [
        "appointment_id",
        "appointment_db",
        "clinic_name",
        "appointment_datetime",
        "appointment_createddate",
        "patient_last_name",
        "patient_first_name",
        "patient_chart_id",
        "patient_date_of_birth",
        "patient_zip_code",
        "patient_employer_name",
        "patient_id",
        "patient_db",
        "other_id",
        "provider_id",
        "provider_last_name",
        "provider_first_name",
        "guarantor_last_name",
        "guarantor_first_name",
        "guarantor_date_of_birth",
        "subscriber_zip_code",
        "insurance_order",
        "insurance_company_name",
        "insurance_group_name",
        "insurance_group_number",
        "insurance_fee_schedule",
        "subscriber_id",
        "relation_to_subscriber",
        "last_eligibility_check",
        'benefits_renewal',
        "query_run_time"
        ]

    if reportType:
        reportPath = GetVar("appointment_path")
        if not os.path.exists(reportPath): raise FileNotFoundError("The report path does not exist")
        data = pd.read_csv(reportPath, encoding='latin9', sep='\t', dtype = str)
        apptDate = data['Appt_Date'].iloc[0]
        apptDate = datetime.strptime(apptDate, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S').split(" ")[0]
        datesMatch = apptDate == sheet
    else:
        df = pd.DataFrame(query_result, columns=header) 
        data = df[df['clinic_name'].isin(practices)] # the db data in form of dataframe
        print(data)
        data = data[data['appointment_datetime'].str.split(' ').str[0] == sheet]
        datesMatch = (data['appointment_datetime'].str.split(' ').str[0] == sheet).all()

    if datesMatch:
        readAppoinments(data,reportType)
    else:
        raise Exception("Sheet does not match appt date")

except FileNotFoundError as e:
    print(str(e))
    # alerts.start("The report path does not exist", "Alert")
except Exception as e:
    print(str(e))
    # alerts.start("Unexpected error", "Alert")
    # SetVar("result_integration", [])
