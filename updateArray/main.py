import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalVariables.resultIntegration import result_integration
from globalVariables.script import iv_config,columns,clinic_dict,ERROR,SUCCESS,months,data_supplies
from globalVariables.carriersRegex import regex_by_type
from drApiOperations.searchVerification import search_verifications
from findMatch import find_match
from validateElgDate import validate_elgdate
from globalFunctions.script import print_log,gpvars
from datetime import datetime

today_date = gpvars("sheet")
today_date= datetime.strptime(today_date.strip(), '%Y-%m-%d')

regex = regex_by_type
result_integration = [[value if str(value).strip() else 'EMPTY' for value in row] for row in result_integration]
re_mo = '(?i)^(Delta|Delta[l]* Dental)(?!.*(Ak|Or|Moda|Care USA HMO)).*( MO.*| Missouri.*)$'
re_met = '(?i)^Met.*(life).*'
medicaid_re = '(?i)^((United( )?Health( )?Care|UHC|AZUHC)( ?(-?Comm(unity)?)( ?Plan?)?| Delaware)|UHC ?CP.*)$|^(Sun[\s]?Life[\s]?|Denta[\s]?quest)|Horizon(?!.*\bNJ\s*Health\b).*$'

for idx,row in enumerate(result_integration):
    current_row = result_integration[idx]
    clinic = row[0].strip()
    clinicExcluded = clinic in iv_config["no_actions_rules"]['except_clinics']
    hasCarrier = row[1].lower() != "empty"
    carrierIsCoveraged = not re.search(iv_config["no_actions_rules"]['regex_carrier'], row[1], re.IGNORECASE)
    row_data = row.copy()
    # row_data = array_and_dict.convert_array_to_dict(row_data,[])
    row_data = dict(zip(columns,row_data))

    if iv_config['NoVerifyClinic'] and clinic.upper() in clinic_dict['CT'] or clinic.upper() in clinic_dict['DE']:
        if clinic.upper() in clinic_dict['CT']:
            row[11] = 'IN PROGRESS CT'
        else:
            row[11] = 'IN PROGRESS DE' 


    if clinic.lower() == "bridgeton" and  re.search(re_met,row[1],re.IGNORECASE):
        row[2] = "EMPTY"
        row[11] = "NO ACTIONS"
        continue

    # No actions if carrier is Empty
    if not hasCarrier:
        row[2] = "EMPTY"
        row[11] = "NO ACTIONS"
        continue
    
    # No action if the clinic is not excluded and carrier name matches master regex
    if not clinicExcluded and re.search(iv_config["no_actions_rules"]['regex_master'], row[1], re.IGNORECASE):
        row[2] = "EMPTY"
        row[11] = "NO ACTIONS"
        continue

    if re.search(r"^Horizon Federal$",row[1].strip(),re.IGNORECASE):
        row[28] = f"NO ACTIONS DUE RULE OF HORIZON FEDERAL"
        row[2] = "EMPTY"
        row[11] = "NO ACTIONS"
        continue
    
    if row[27].strip().lower() == "norecall":
        row[28] = f"NO ACTIONS BECAUSE HAS NORECALL PROVIDER"
        row[2] = "EMPTY"
        row[11] = "NO ACTIONS"     
        continue       

    if re.search(r"(?i)^blue cross blue shield$",row[1].strip(),re.IGNORECASE) and row[2].startswith("8"):
        row[1] = f"DNOA {row[1]}"

    if re.search(r"(?i)^Delta( Dental( Master)?)?$|(Delta(\sDental)?|DD)? (of\s)?(CA(\sMaster)?$|California)",row[1].strip(),re.IGNORECASE) and row[2].startswith("9"):
        row[1] = 'Delta Dental Federal'

    if carrierIsCoveraged:
        row[9] = row[9].replace("-","/")
        row[6] = row[6].replace("-","/")

        if re.search(medicaid_re, row[1],re.IGNORECASE):
            row[13] = "ELG"
        
        elif re.search(regex['ELG'], row[1],re.IGNORECASE) and row[0].upper() == "DANBURY" and iv_config['extraction_services']['dambury_rule']:
            row[13] = "ELG"

        elif re.search(regex['ELG'], row[1], re.IGNORECASE) or re.search(re_mo,row[1],re.IGNORECASE):
            
            api_results = search_verifications(row_data)
            if re.search(r"(?i)^(Delta Dental( of)?( ky| kentucky))$",row[1],re.IGNORECASE):
                match_patient,result,patient_verified = find_match(api_results,row_data,"FBD")
            else:
                match_patient,result,patient_verified = find_match(api_results,row_data,"ELG")
            print_log(ERROR,"ELSE ELG ")
            if api_results:
                if patient_verified and re.match(r'\bactive\b',x['StatusVerification'],re.IGNORECASE):
                    row[13] = "ELG"
                    row[11] = f"ALREADY VERIFIED"
                    row[12] = f"ALREADY VERIFIED"
                    row[28] = f"ALREADY VERIFIED ON API DR APPTDATE {result['ApptDate']}"
                elif validate_elgdate(row[29]) and match_patient and match_patient >= 95 and patient_verified:
                    row[13] = "ELG"
                    row[11] = f"ALREADY VERIFIED"
                    row[12] = f"ALREADY VERIFIED"
                    row[28] = f"ALREADY VERIFIED ON LAST ELIGIBILITY DATE CHECK {row[29]}"
                else:
                    if result:
                        if result['ApptDate'] and datetime.strptime(result['ApptDate'],'%Y-%m-%d') >= today_date :
                            row[13] = "ELG"
                            row[11] = f"ALREADY VERIFIED"
                            row[12] = f"ALREADY VERIFIED"
                            row[28] = f"ALREADY VERIFIED ON API DR APPTDATE {result['ApptDate']}"

                        elif result['ApptDate'] and datetime.strptime(result['ApptDate'],'%Y-%m-%d') <= today_date and result['audited'] and validate_elgdate(result['ApptDate']):
                            row[13] = "ELG"
                            row[11] = f"ALREADY VERIFIED"
                            row[12] = f"ALREADY VERIFIED"
                            row[28] = f"ALREADY VERIFIED ON API DR APPTDATE {result['ApptDate']}"
                        else:
                            row[13] = "ELG"
                    else:
                        row[13] = "ELG" if not re.search(r"(?i)^(Delta Dental( of)?( ky| kentucky))$",row[1],re.IGNORECASE) else "FBD"
            else:
                row[13] = "ELG" if not re.search(r"(?i)^(Delta Dental( of)?( ky| kentucky))$",row[1],re.IGNORECASE) else "FBD"
        else:
            api_results = search_verifications(row_data)
            if api_results:
                if re.search(r"(?i)^(Sun[\s]?Life[\s]?|Denta[\s]?quest)",row[1],re.IGNORECASE):
                    match_patient,result,patient_verified = find_match(api_results,row_data,"ELG")
                else:
                    match_patient,result,patient_verified = find_match(api_results,row_data,"FBD")                    
                
                print(match_patient,result,patient_verified)
                if validate_elgdate(row[29]) and not (row[0].upper() == "DANBURY" and iv_config['extraction_services']['dambury_rule'])  and match_patient and match_patient >= 95 and patient_verified:
                    row[13] = "FBD"
                    row[11] = f"ALREADY VERIFIED"
                    row[12] = f"ALREADY VERIFIED"
                    row[28] = f"ALREADY VERIFIED ON LAST ELIGIBILITY DATE CHECK {row[29]}"
                elif patient_verified and not (row[0].upper() == "DANBURY" and iv_config['extraction_services']['dambury_rule']):
                    row[13] = "EMPTY"
                    row[11] = f"ALREADY VERIFIED"
                    row[12] = f"ALREADY VERIFIED"
                    row[28] = f"ALREADY VERIFIED ON API DR APPTDATE {result['ApptDate']}"

                elif result and  result['ApptDate'] and datetime.strptime(result['ApptDate'],'%Y-%m-%d') <= today_date and result['audited'] and validate_elgdate(result['ApptDate']) and validate_elgdate(row[29]):
                    row[13] = "EMPTY"
                    row[11] = f"ALREADY VERIFIED"
                    row[12] = f"ALREADY VERIFIED"
                    row[28] = f"ALREADY VERIFIED ON API DR APPTDATE {result['ApptDate']}"
                else:
                    if match_patient and match_patient >= 95 and result:
                        date = result['ApptDate']
                        corrects_date = True
                        renewall = row_data['office'].upper()
                        print_log(SUCCESS,f"RENEWALL {renewall}")
                        current_month = datetime.now().month
                        if months[renewall] == 1:
                            row[13] = "ELG"
                        else:
                            if int(current_month) < months[renewall]:
                                row[13] = "ELG" 
                            else:
                                try:
                                    start_date = datetime.strptime(f"{datetime.now().year}-{months[renewall]:02d}-01","%Y-%m-%d")
                                    date_api = datetime.strptime(date,"%Y-%m-%d")
                                    end_date = datetime.strptime(f"{datetime.now().year}-12-31","%Y-%m-%d")
                                    print_log(SUCCESS,f"start-date={start_date}, end-date{end_date}, renewall = {months[renewall]} date from api= {date_api}")
                                except(ValueError, TypeError):
                                    vtype = "FBD"
                                    corrects_date = False   
                                if corrects_date:
                                    if start_date >= date_api <= end_date:
                                        vtype = "ELG"
                                    else:
                                        vtype = "FBD"
                                    row[13]= vtype
                    else:
                        row[13] = "FBD" if not re.search(r"(?i)^(Sun[\s]?Life[\s]?|Denta[\s]?quest)",row[1],re.IGNORECASE) else "ELG"             
            else:
                row[13] = "FBD" if not re.search(r"(?i)^(Sun[\s]?Life[\s]?|Denta[\s]?quest)",row[1],re.IGNORECASE) else "ELG"     

        row[30] = iv_config['clinic_settings']['settings'][row[0]]['office']    
        if any(vtype in row[13] for vtype in ["FBD", "ELG"]):
            print("creando files name")
            # row[-1] = pf.create_file_name(current_row,script_vars['sheet'],script_vars['iv_config'])[-1]
        else:
            row[-1] = 'EMPTY'
    else:
        row[2] = "EMPTY"
        row[11] = "NO ACTIONS"        
        row[30] = "EMPTY"

