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
values = ['MATTITUCK', 'Dentaquest', 'U8409477504', '11772', 'Francis', 'Ruf', '11/15/2005', 'Francis', 'Ruf', '11/15/2005', 'self', 'Done by DR', 'Active / But Group number doesnt match |EXP Adult Female All Ages TLS::SEXADFATS::OK SoonerSelect- Adult |07/01/2022 - 11/30/2031', 'FBD', '0488556', 'EMPTY', 'EMPTY', 'Uploaded,Success', 'Primary', 'DONE', 'https://docs.google.com/document/d/1YJbLcr8SVSV_G6hozyABBhNcqc5onkk9/edit , https://drive.google.com/file/d/17FGRbYqI3C8yGZp_z6B8EL_pJB8EB0u6/view', 'met_ded:-amount_used:-ind_ded:N/A-ind_max:N/A', '14:00', 'EMPTY', 'MASTER Cigna', '2501670', '2026-01-18, 13:07:00', 'INSISSUE', 'BOB Prim uploaded at 2026-01-22 H:21:23|otherId updated|overlap reviewed|note:The fee schedule was selected by PlanType [PlanType: PPO,MasterRow: 3053, SmilistTin: 10]|rev_benefit_renewal: JUL|updt_Phone: (800) 244-6224|updt_Payer: 62308|upd AI: 0.00 upd AF: 0.00 upd AM: 0.00 upd PI: 0.00 amounts|upd MD: 0.0 upd BU: 0.0 deductibles|coverage table already updated|note done|last_check → 01/22/2026 , chk_not_elg → False , elig_start → 07/01/2022 , elig_end → 07/01/2027 ELG dates updated| |Process Done By dentalrobot102', '1753-03-02', 'Medford', 'Insurance_verification_form_Cigna MASTER DO NOT CHANGE_Primary_Francis Ruf_01272026.docx,Eligibility_status_Cigna MASTER DO NOT CHANGE_Primary_Francis Ruf_01272026.pdf']

# data_supplies = dict(zip(columns,values))
data_supplies= {'practice': 'AMITYVILLE', 'carrier_name': 'United Healthcare Community', 'member_id': '931674982', 'subscriber_zip_code': '12148', 'subscriber_first_name': 'Louis', 'subscriber_last_name': 'Ianniello', 'subscriber_dob': '03/25/1961', 'patient_first_name': 'Louis', 'patient_last_name': 'Ianniello', 'patient_dob': '03/25/1961', 'relationship': 'self', 'iv_process_result': 'Done by DR', 'verification_status': 'Active |dual| 03/01/2024 - N/A', 'type_of_verification': 'FBD', 'patient_id': '11008009_LOUDE', 'plan_id_in_the_pms': 'EMPTY', 'subs_id': 'EMPTY', 'upload_status': 'Uploaded,Error', 'ordinal': 'Primary', 'final_audit': 'DONE', 'urls': 'https://docs.google.com/document/d/1xaG--suoYsLQA_pc_hsbp300h6y52EpL/edit , https://drive.google.com/file/d/1CQvDwwh17-dBum1DKtYC--hPWvQvUK7F/view', 'amounts': 'met_ded:$0.00-amount_used:$0.00-ind_ded:$50.00-ind_max:$2000.00', 'appointment_date': '08:30', 'employer_name_pms': 'EMPTY', 'groupname': 'NY-PPO-000000-M00610', 'group_number': 'MASTER', 'extraction_datetime': '2026-02-05, 19:20:26', 'extraction_logs': 'HYGHATALLA', 'log': 'BOB Prim uploaded at 2026-02-12 H:14:28|otherId not updated due to alert|otherId updated|overlap reviewed|REVIEW THE NEW GROUP PLAN IS None|rev_benefit_renewal: JAN|updt_Phone: 800-627-4200|upd AI: 50.00 upd AF: 150.00 upd AM: 2000.00 upd PI: 0.00 amounts|upd MD: 0.0 upd BU: 0.0 deductibles|coverage table updated|note done| chk_not_elg → False , last_check → 02/13/2026 , elig_start → 01/01/2019 , elig_end → 12/31/2026 ELG dates updated| |Process Done By Dentalrobot91', 'last_eligibility': '1753-03-02', 'office': 'Loudonville', 'docs': 'Insurance_verification_form_GUARDIAN MASTER_Primary_Louis Ianniello_02162026.docx,Eligibility_status_GUARDIAN MASTER_Primary_Louis Ianniello_02162026.pdf'}


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
    "liberty" : r'(?i)^Liberty.*'
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


