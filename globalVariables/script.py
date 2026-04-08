from pathlib import Path
import os
import yaml
import json

#credentiales to file .env
current_dir = Path(__file__)
root_path = current_dir.parent.parent
env_path = f"{root_path}{os.sep}creds.env"
#variables to use with printlog
SUCCESS = "SUCCESS"
ERROR = "ERROR"
WARNING = "WARNING"
INFO = "INFO"
#to create data_supplies
columns = ['practice', 'carrier_name', 'member_id', 'subscriber_zip_code', 'subscriber_first_name', 'subscriber_last_name', 'subscriber_dob', 'patient_first_name', 'patient_last_name', 'patient_dob', 'relationship', 'iv_process_result', 'verification_status', 'type_of_verification', 'patient_id', 'plan_id_in_the_pms', 'subs_id', 'upload_status', 'ordinal', 'final_audit', 'urls', 'amounts', 'appointment_date', 'employer_name_pms', 'groupname', 'group_number', 'extraction_datetime', 'elg_update_status', 'log', 'last_eligibility', 'office', 'docs']
values = ['ALLERTON', 'emblem', '123514809001', '22201', 'Joeseph', 'Martinez', '12/31/1991', 'Cristian', 'Lavao', '07/14/1995', 'spouse', 'Done by DR', 'Active | 1124328 ,1199 SEIU NBF,EH PPO PREFERRED PREMIER  |08/04/2024 - N/A', 'FBD', '027756_Arlin', 'EMPTY', 'EMPTY', 'Uploaded,Success', 'Primary', 'DONE', 'https://docs.google.com/document/d/157jK56A3J6LExq9XcGSMumBTU1sOjC0F/edit , https://drive.google.com/file/d/16I58QQFLg-vo4coEjwGb7A4N8xD9RBsa/view', 'met_ded:-amount_used:-ind_ded:$50.00-ind_max:$2000.00', '09:00', 'EMPTY', 'MASTER United Concordia', 'MASTER', '2026-02-23, 13:05:00', 'HYGSORTO', 'BOB Prim uploaded at 2026-02-24 H:23:45|otherId not updated due to alert|otherId updated|overlap reviewed|REVIEW THE NEW GROUP PLAN IS None|rev_benefit_renewal: JAN|updt_Phone: 800-332-0366|updt_Payer: 89070|upd AI: 50.00 upd AF: 100.00 upd AM: 2000.00 upd PI: 0.00 amounts|upd MD: 0.0 upd BU: 0.0 deductibles|coverage table updated|note done| chk_not_elg → False , last_check → 02/24/2026 , elig_start → 09/14/2024 , elig_end → 12/31/2026 ELG dates updated| |Process Done By Dentalrobot89', '1753-03-02', 'Arlington', 'Insurance_verification_form_United Concordia MASTER Do Not_Primary_Cristian Lavao_03042026.docx,Eligibility_status_United Concordia MASTER Do Not_Primary_Cristian Lavao_03042026.pdf']

# data_supplies = dict(zip(columns,values))
data_supplies= {'practice': 'WANTAGH', 'carrier_name': 'EDP', 'member_id': 'K60781528', 'subscriber_zip_code': '11566', 'subscriber_first_name': 'Vincent', 'subscriber_last_name': 'Olson', 'subscriber_dob': '11/02/1968', 'patient_first_name': 'Denise', 'patient_last_name': 'Mitkish', 'patient_dob': '07/26/1968', 'relationship': 'spouse', 'iv_process_result': 'EMPTY', 'verification_status': 'Active | 1124328 ,1199 SEIU NBF ,EH PPO PREFERRED PREMIER  |01/01/2021 - N/A', 'type_of_verification': 'EMPTY', 'patient_id': 'EMPTY', 'plan_id_in_the_pms': 'EMPTY', 'subs_id': 'EMPTY', 'upload_status': 'EMPTY', 'ordinal': 'Primary', 'final_audit': 'EMPTY', 'urls': 'EMPTY', 'amounts': 'met_ded:-amount_used:-ind_ded:25.00-ind_max:N/A', 'appointment_date': '14:00', 'employer_name_pms': 'EMPTY', 'groupname': 'GHI-PPO NY/NJ 99999-100/100/100', 'group_number': 'DP010297', 'extraction_datetime': '2026-03-17, 22:52:43', 'extraction_logs': 'HYGEDMOND', 'log': 'EMPTY', 'last_eligibility': '2025-10-17', 'office': 'Jan', 'docs': 'EMPTY'}

# print(data_supplies)
#to create ivconfig from yaml
with open(f"{root_path}{os.sep}PMSconf.yaml", "r", encoding="utf-8") as f:
    iv_config = yaml.safe_load(f)


idSpreedSheet = "1yVdPiyCLcaR_owZg4yjq4Fi8qs-8pfLzRrtlYswGr2Q"
run_config = [{'practice': 'FISHKILL', 'date': '2025-02-19'}, {'practice': 'BELLEROSE', 'date': '2025-02-19'}]
sheet = "2025-02-19"

ELG_PATTERNS = {
    "dual_pattern": r'\bdual\b',
    "nj_family_pattern" : r'\b(nj\s*family|familycare)\b',
    "caresource_nj_pattern": {
        "plan_a" :r"^(?!.*ABP).*FamilyCare A(?!.*ABP).*", 
        "plan_b" : r"FamilyCare B",   
        "plan_c" : r"FamilyCare C",   
        "plan_d" : r"FamilyCare D",   
        "plan_abp" : r".*FamilyCare ABP.*",
        "plan_sn" : r".*Special Needs*"
    },
    "hmo":"hmo"
}

RULES_VALUES_MAPPING = {
    'rule_1': 'ortho_and_implant',
    'rule_2':'zero',
    'rule_3':'hundred'
    }

CARESOURCE_RULES_LAST_RECORD = {
    'Plan A' : 'D00005',
    'Plan B' : 'D00006',
    'Plan C' : 'D00007',
    'Plan D' : 'D00008',
    'Plan ABP' : 'D00009',
    'Plan Special Needs' : 'D00010'
}

DEFAULT_PAYERS ={
    'aetna': {
        're' : r"(?i)^Aet?nt?a.*",
        'payor' : "60054"
    },
    'cigna': {
        're' : r"(?i)^Cigna.*",
        'payor' : "62308"
    },
    'unitedconcordia': {
        're' : r"(?i)^((Florida )?Combined Life|United Conco*rd?id?a(\sADDP Claims$)?|tricare|(FEP )?UCCI?|HIGHMARK\s(of\s)?(WNY FEDERAL|BCBS|MASTER|United Concordia)$)",
        'payor' : "89070"
    }
}

static_regex = {
    "re_uhc" : r'(?i)^((((ENC5_)?(United\s?Heal(t)?h\s?(Care( Dental)?|Medicare\sComplete)))|UHC|((AARP Medicare)( UHC| Complete)))(?!-| ?CP| Community| Plan| Comm| Delaware)(?! ?CP MASTER DO NOT CHAN(GE)?$).*)$',
    "medicaid_re" :  r'(?i)^((United( )?Health( )?Care|UHC|AZUHC)( ?(-?Comm(unity)?)( ?Plan?)?| Delaware)|UHC ?CP.*)$|^(Sun[\s]?Life[\s]?|Denta[\s]?quest)|Horizon(?!.*\bNJ\s*Health\b).*$',
    "dentaquest" : r'(?i)^(Sun[\s]?Life[\s]?|Denta[\s]?quest)',
    "csea_reg" : r'(?i)^(CSEA).*|^(C\.S\.E\.A\.?).*',
    "liberty_reg" : r'(?i)^Liberty.*',
    "skygen_reg":r'(((United( )?Health( )?Care|UHC|AZUHC)( ?(-?Comm(unity)?)( ?Plan?)?| Delaware)|UHC ?CP.*)|(Delta )?(Dental|Delta).*(KY|Kentucky).*)$',
    "caresorce_reg" : r'^((Horizon )?(NJ )(health)).*$',
    "liberty" : r'(?i)^Liberty.*',
    "emblem" : r'(?i)^(G\s?H\s?I.*)?(EMBLEM.*)?$',
    "edp" : r'(?i)^EDP$'
}


clinic_dict = {
    'CT':['WHARTFORD','DANBURY','CROMWELL'],
    'DE':['WILMINGTON']
}

months = {
    "JAN" : 1, 
    "FEB" : 2, 
    "MAR" : 3, 
    "APR" : 4, 
    "MAY" : 5, 
    "JUN" : 6, 
    "JUL" : 7, 
    "AUG" : 8, 
    "SEP" : 9, 
    "OCT" : 10, 
    "NOV" : 11, 
    "DEC" : 12, 
    "NULL" : 1
    }


