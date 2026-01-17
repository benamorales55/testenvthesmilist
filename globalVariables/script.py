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
values = ['MEDFORD', 'Humana', 'H67912388', '11727', 'Omkar', 'Singh', '01/09/1960', 'Omkar', 'Singh', '01/09/1960', 'self', 'Done by DR', 'Active / Member ID doesnt match | 01/01/2026 - N/A', 'FBD', '0319515', 'EMPTY', 'EMPTY', 'Uploaded,Error', 'Primary', 'DONE', 'https://docs.google.com/document/d/1lM_CPa-5o4_U4qVDuiiO_c7ymuUEeEtx/edit , https://drive.google.com/file/d/12f-my22g7p5DFE244RO66d4GlDQ6jr00/view', 'met_ded:-amount_used:$0-ind_ded:N/A-ind_max:$3,000', '11:30', 'DEN310', 'DIS-000 NY000 0000-100/000/000', '675717', '2026-01-01, 11:01:42', 'HYGPAUTAP', 'BOB Prim uploaded at 2026-01-08 H:10:48|otherId updated|overlap reviewed|note:The fee schedule was selected by PlanType [PlanType: PPO,MasterRow: 3001, SmilistTin: 146]|Matrix input at DB|Matrix input at api and DB|create_new_group_plan [renewall: JAN]|rev_benefit_renewal: JAN|updt_Phone: 800-833-2223|upd AI: 0.00 upd AF: 0.00 upd AM: 3000.00 upd PI: 0.00 amounts|upd MD: 0.0 upd BU: 0.0 deductibles|coverage table updated|note done|last_check → 01/08/2026 , chk_not_elg → False , elig_start → 01/01/2026 , elig_end → 12/31/2026 ELG dates updated| |Process Done By dentalrobot111', '1753-03-02', 'Medford', 'Insurance_verification_form_Humana_Primary_Omkar Singh_01082026.docx,Eligibility_status_Humana_Primary_Omkar Singh_01082026.pdf']
data_supplies = dict(zip(columns,values))
print(data_supplies)
#to create ivconfig from yaml
with open(f"{root_path}{os.sep}PMSconf.yaml", "r", encoding="utf-8") as f:
    iv_config = yaml.safe_load(f)


idSpreedSheet = "1yVdPiyCLcaR_owZg4yjq4Fi8qs-8pfLzRrtlYswGr2Q"
run_config = [{'practice': 'FISHKILL', 'date': '2025-02-19'}, {'practice': 'BELLEROSE', 'date': '2025-02-19'}]
sheet = "2025-02-19"

ELG_PATTERNS = {
    "dual_pattern": r'\bdual\b',
    "nj_family_pattern" : r'\b(nj\s*family|familycare)\b',
    "encore_nj_pattern": {
        "plan_a" :r"^(?!.*ABP).*FamilyCare A(?!.*ABP).*", 
        "plan_b" : r"FamilyCare B",   
        "plan_c" : r"FamilyCare C",   
        "plan_d" : r"FamilyCare D",   
        "plan_abp" : r".*FamilyCare ABP.*",
        "plan_sn" : r".*Special Needs*"
    }
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
    "csea_reg" : r'(?i)^(CSEA).*|^(C\.S\.E\.A\.?).*'
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


