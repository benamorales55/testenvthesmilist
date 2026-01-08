import sys
import os
import re 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalVariables.script import ELG_PATTERNS,data_supplies,static_regex,iv_config
from globalFunctions.script import clean_regex,get_info

elg_carriers_clinic = clean_regex(get_info(iv_config,'elg_carriers_clinic'))

def is_elg_plan(clinics_bot):
    if clinics_bot in iv_config['elg_clinic']['All_Clinics']:
        return True
    else:
        return(data_supplies['type_of_verification'] == 'ELG' and
        data_supplies['practice'] in iv_config['elg_clinic'][clinics_bot] and 
        bool(re.search(elg_carriers_clinic,data_supplies['carrier_name'])))

def check_plan_conditions():
    sky_reg = r'^(((United( )?Health( )?Care|UHC|AZUHC)( ?(-?Comm(unity)?)( ?Plan?)?| Delaware)|UHC ?CP.*)|(Delta )?(Dental|Delta).*(KY|Kentucky).*)$'
    cs_reg = r'^((Horizon )?(NJ )(health)).*$'
    csea_reg = r'(?i)^(CSEA).*|^(C\.S\.E\.A\.?).*'
    def check_encore_nj_plan():
        for plan_key, plan_pattern in ELG_PATTERNS['encore_nj_pattern'].items():
            if re.search(plan_pattern, data_supplies['verification_status'], re.IGNORECASE):
                return plan_key  
        return None 
    
    dq_matituck_plan = (is_elg_plan("Dentaquest") and 
    bool(re.search(r'(denta quest|dentaquest)',data_supplies['carrier_name'],re.IGNORECASE))
    and data_supplies['practice'].lower() == 'mattituck')

    uhccp_middleisland = (bool(re.search(sky_reg,data_supplies['carrier_name'],re.IGNORECASE)) and 
    data_supplies['practice'].lower() == 'middleisl')

    uhccp_plan = (is_elg_plan("Skygen_NY") and 
    not bool(re.search(ELG_PATTERNS['dual_pattern'],data_supplies['verification_status'],re.IGNORECASE)) and 
    not bool(re.search(ELG_PATTERNS['nj_family_pattern'],data_supplies['verification_status'],re.IGNORECASE)) and 
    bool(re.search(sky_reg,data_supplies['carrier_name'],re.IGNORECASE)))

    uhccp_dual_plan = (is_elg_plan("Skygen_DUALNY") and
    bool(re.search(ELG_PATTERNS['dual_pattern'], data_supplies['verification_status'], re.IGNORECASE)) and
    bool(re.search(sky_reg,data_supplies['carrier_name'],re.IGNORECASE)))

    uhccp_nj_plan = (is_elg_plan("Skygen_NJ") and
    bool(re.search(ELG_PATTERNS['nj_family_pattern'], data_supplies['verification_status'], re.IGNORECASE)) and
    bool(re.search(sky_reg,data_supplies['carrier_name'],re.IGNORECASE)))

    encore_nj_plan = (is_elg_plan("Caresource") and check_encore_nj_plan() and
    bool(re.search(cs_reg,data_supplies['carrier_name'],re.IGNORECASE)))
    print(encore_nj_plan,"ENCORE NJ PLAN")

    cs_all_plan = check_encore_nj_plan() if encore_nj_plan else False
    csea_all_plan = (bool(re.search(csea_reg,data_supplies['carrier_name'],re.IGNORECASE)))
    
    hmo_uhc = True if ("HMO" in data_supplies["verification_status"].upper() and re.search(static_regex["re_uhc"],data_supplies['carrier_name'],re.IGNORECASE) and "view" in data_supplies['urls']) else False

    dq_fishkill_plan = (bool(re.search(static_regex['dentaquest'],data_supplies['carrier_name'],re.IGNORECASE)) and data_supplies['practice'].lower() == 'fishkill')

    elg_plans_flags = {
        "dq_matituck_plan":dq_matituck_plan,
        "uhccp_plan":uhccp_plan,
        "uhccp_dual_plan":uhccp_dual_plan,
        "uhccp_nj_plan":uhccp_nj_plan,
        "cs_all_plan": cs_all_plan,
        'uhc_middleisland_plan' : uhccp_middleisland,
        'csea_all_plan' : csea_all_plan,
        'hmo_uhc' : hmo_uhc,
        'dq_fishkill_plan' : dq_fishkill_plan
        }
    print(elg_plans_flags)
    return elg_plans_flags


