import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalVariables.script import data_supplies,static_regex,ELG_PATTERNS
from globalFunctions.script import fillNumberWithZero,generate_amounts_dict
from feeScheduleElg import fee_schedule_elg

def get_elg_info(carrier_name: str, group_name: str):
    clinic = data_supplies['practice']  

    bots_elg_plan = {
        'Skygen': {
            'regex': "(?i)^(((United( )?Health( )?Care|UHC|AZUHC)( ?(-?Comm(unity)?)( ?Plan?)?| Delaware)|UHC ?CP.*)|(Delta )?(Dental|Delta).*(KY|Kentucky).*)$",
            'fee_schedule': {
                "UHCCPNY": 212,
                "UHCCPDUALNY": 212,
                "UHCCPNJ": 17,
                "UHCCPMIDDLEISLANDDUAL":212,
                "UHCCPMIDDLEISLANDNOTDUAL":212
            },
            'employer': "EMPTY",
            "state": 'NY',
            'plan_logic': {
                'dual': {"fee_schedule_key": "UHCCPDUALNY", "group_number_base": f"UHCCP-DUAL COMPLETE-{clinic}", "annual_max": "9999","deductible":"0.00"},
                'nj familycare': {"fee_schedule_key": "UHCCPNJ", "group_number_base": f"UHCCP-{clinic}", "annual_max": "9999","deductible":"0.00"},
                'default': {"fee_schedule_key": "UHCCPNY", "group_number_base": f"UHCCP-{clinic}", "annual_max": "9999","deductible":"0.00"},
                'uhccpmiddleislandnotdual' : {"fee_schedule_key": "UHCCPMIDDLEISLANDNOTDUAL", "group_number_base": f"UHCCP-MI", "annual_max": "0.00","deductible":"0.00"},
                'uhccpmiddleislanddual' : {"fee_schedule_key": "UHCCPMIDDLEISLANDDUAL", "group_number_base": f"UHCCP-MI-DUAL COMPLETE", "annual_max": "1000","deductible":"0.00"}

            }
        },
        'Dentaquest': {
            'regex': "(?i)^ ?(denta quest|dentaquest)",
            'fee_schedule': {
                'DQ': 247
            },
            'employer': "EMPTY",
            "state": 'NY',
            'plan_logic': {
                'default': {"fee_schedule_key": 'DQ', "group_number_base": "Dentaquest", "annual_max": "0.00","deductible":"0.00"}
            }
        },
        'Caresource':{
            'regex': "(?i)^((Horizon )?(NJ )(health)).*$",
            'fee_schedule': {
                'CS': 457
            },
            'employer': "EMPTY",
            "state": 'NJ',
            'plan_logic':{
                'familycare a' : {"fee_schedule_key": 'CS', "group_number_base": "Plan A", "annual_max": "0.00","deductible":"0.00"},
                'familycare b' : {"fee_schedule_key": 'CS', "group_number_base": "Plan B", "annual_max": "0.00","deductible":"0.00"},
                'familycare c' : {"fee_schedule_key": 'CS', "group_number_base": "Plan C", "annual_max": "0.00","deductible":"0.00"},
                'familycare d' : {"fee_schedule_key": 'CS', "group_number_base": "Plan D", "annual_max": "0.00","deductible":"0.00"},
                'familycare abp' : {"fee_schedule_key": 'CS', "group_number_base": "Plan ABP", "annual_max": "0.00","deductible":"0.00"},
                'special needs' : {"fee_schedule_key": 'CS', "group_number_base": "Plan Special Needs", "annual_max": "0.00","deductible":"0.00"}
            }
        },
        'Liberty': {
            'regex': "(?i)^Liberty.*",
            'fee_schedule': {
                'LB': 1308
            },
            'employer': "EMPTY",
            "state": 'NY',
            'plan_logic': {
                'default': {"fee_schedule_key": 'LB', "group_number_base": "", "annual_max": "99999","deductible":"0.00"}
            }
        },
    }

    if re.search(static_regex['dentaquest'], data_supplies['carrier_name'],re.IGNORECASE) and data_supplies['practice'].lower() == "fishkill":
        def is_number(value):
            try:
                float(value)
                return True
            except ValueError:
                return False
        
        dental_plan = group_name.split("|")[1].strip()
        group_number = group_name.split("|")[2].strip()

        dq_data = None
        dental_plan_number = is_number(dental_plan)
        if not dental_plan_number:
            dq_data = fee_schedule_elg(dental_plan,"dq")

        if dq_data:
            fee_schedule = fillNumberWithZero(dq_data['Smilist TIN'])
            employer = data_supplies['verification_status'].split("|")[1].strip().replace("*","").replace("`","'")
            info = {
                "group_plan" : f"{dq_data['State']}-MCD-{fee_schedule}",
                "employer" : f"{employer}",
                "group_number" : f"{group_number}",
                "annual_max" : "99999",
                "deductible_standar" : '0.00'
            }
            return info
        else:
            return None


    if re.search(static_regex['re_uhc'],data_supplies['carrier_name'],re.IGNORECASE) and "HMO" in data_supplies['verification_status'].upper():
        dental_plan = "DHMO"
        employer = group_name.split("|")[1].split('-')
        employer= '-'.join(employer[1:-1])
        group_number = group_name.split("|")[1].split('-')[-1].strip()
        group_number = group_number if group_number else "EMPTY"

        uhc_data= fee_schedule_elg(dental_plan,"uhc")
        if uhc_data:
            fee_schedule = fillNumberWithZero(uhc_data['Smilist TIN'])
            info = {
                "group_plan" : f"{uhc_data['State']}-HMO-{fee_schedule}",
                "employer" : employer,
                "group_number" : group_number,
                "annual_max" : "9999",
                "deductible_standar" : '0.00'
            }
            return info
        else:
            return None

    if re.search(static_regex['csea_reg'], data_supplies['carrier_name'], re.IGNORECASE):
        print("CSEA regex matched in carrier_name:", data_supplies['carrier_name'])

        matchcsea = re.search(r'\b(Dental|Plan)\b', group_name, re.IGNORECASE)
        print("Match for 'Dental' or 'Plan' in group_name:", matchcsea)

        if matchcsea:
            dental_plan = group_name[:matchcsea.start()].strip()
            print("dental_plan before splitting (matchcsea):", dental_plan)

            dental_plan = dental_plan.upper().split("|")[1].strip()
            print("dental_plan after splitting (matchcsea):", dental_plan)

            employer_plan = dental_plan
            groupnumber = dental_plan
        else:
            dental_plan = group_name.upper().split('|')[1].strip()
            print("dental_plan without matchcsea:", dental_plan)

            employer_plan = dental_plan
            groupnumber = dental_plan

        print("Practice location:", data_supplies['practice'])

        if not data_supplies['practice'] == 'CATSKILL':
            csea_data = fee_schedule_elg(dental_plan, "csea")
            print("csea_data from fee_schedule_elg (not CATSKILL):", csea_data)
        else:
            csea_data = fee_schedule_elg('OON', 'csea')
            print("csea_data from fee_schedule_elg (CATSKILL):", csea_data)

        if csea_data:
            fee_schedule = fillNumberWithZero(csea_data['Smilist TIN'])
            print("fee_schedule (zero-filled):", fee_schedule)

            amounts = generate_amounts_dict()
            print("Generated amounts dict:", amounts)

            info = {
                "group_plan": f"{csea_data['State']}-PPO-{fee_schedule}",
                "employer": employer_plan,
                "group_number": groupnumber,
                "annual_max": amounts['ind_max'],
                "deductible_standar": '0.00'
            }
            print("Final info dict:", info)
            return info
        else:
            print("No csea_data found.")
            return None

        
    if carrier_name.lower() == "dentaquest" and clinic.lower() != "mattituck" and clinic.lower() != "fishkill":
        return None

    if carrier_name.lower() == "dentaquest" and clinic.lower() == "mattituck":
        fee_schedule = bots_elg_plan['Dentaquest']['fee_schedule']['DQ']
        fee_schedule = fillNumberWithZero(fee_schedule)
        group_number = f"{bots_elg_plan['Dentaquest']['plan_logic']['default']['group_number_base']}"
        annual_max = f"{bots_elg_plan['Dentaquest']['plan_logic']['default']['annual_max']}"
        deductible = f"{bots_elg_plan['Dentaquest']['plan_logic']['default']['deductible']}"
        state = f"{bots_elg_plan['Dentaquest']['state']}"
        info = {
            "group_plan": f"{state}-MCD-{fee_schedule}",
            "employer": bots_elg_plan['Dentaquest']['employer'],
            "group_number": group_number,
            "annual_max": annual_max,
            "deductible_standar": deductible
        }
        return info
    
    if (re.search(bots_elg_plan['Skygen']['regex'],data_supplies['carrier_name'],re.IGNORECASE)
        and clinic.lower() == "middleisl"):
        dual_plan = bool(re.search(ELG_PATTERNS['dual_pattern'],data_supplies['verification_status'],re.IGNORECASE))
        plan_moderator = "uhccpmiddleislanddual" if dual_plan else "uhccpmiddleislandnotdual"
        fee_schedule = bots_elg_plan['Skygen']['fee_schedule'][f"{plan_moderator.upper()}"]
        fee_schedule = fillNumberWithZero(fee_schedule)
        group_number = f"{bots_elg_plan['Skygen']['plan_logic'][plan_moderator]['group_number_base']}"
        annual_max = f"{bots_elg_plan['Skygen']['plan_logic'][plan_moderator]['annual_max']}"
        deductible = f"{bots_elg_plan['Skygen']['plan_logic'][plan_moderator]['deductible']}"
        state = f"{bots_elg_plan['Skygen']['state']}"
        info = {
            "group_plan": f"{state}-MCD-{fee_schedule}",
            "employer": bots_elg_plan['Skygen']['employer'],
            "group_number": group_number,
            "annual_max": annual_max,
            "deductible_standar": deductible
        }
        return info

    if re.search(bots_elg_plan['Liberty']['regex'], data_supplies['carrier_name'],re.IGNORECASE) and data_supplies['practice'].lower() == "mattituck":
        dental_plan = group_name.split("|")[1].strip()
        group_number = dental_plan.split('::')[1].strip()
        if group_number:
            fee_schedule = fillNumberWithZero(bots_elg_plan['Liberty']['fee_schedule']['LB'])
            
            info = {
                "group_plan" : f"{bots_elg_plan['Liberty']['state']}-MCD-{fee_schedule}",
                "employer" : bots_elg_plan['Liberty']['employer'],
                "group_number" : f"{group_number}",
                "annual_max" : "99999",
                "deductible_standar" : '0.00'
            }
            return info
        else:
            return None
        

    for key, val in bots_elg_plan.items():
        if re.search(val['regex'], carrier_name, re.IGNORECASE):
            fee_schedule = None
            group_number = None
            annual_max = None
            deductible = None
            state = val['state']

            for group_key, group_val in val['plan_logic'].items():
                if re.search(r'\b' + re.escape(group_key) + r'\b', group_name.lower()):
                    fee_schedule_key = group_val['fee_schedule_key']
                    fee_schedule = val['fee_schedule'][fee_schedule_key]
                    group_number = group_val['group_number_base']
                    fee_schedule = fillNumberWithZero(fee_schedule)
                    annual_max = group_val['annual_max']
                    deductible = group_val['deductible']
                    break  

            if fee_schedule is None:
                if 'default' in val.get('plan_logic', {}):
                    group_val = val['plan_logic']['default']
                    fee_schedule_key = group_val['fee_schedule_key']
                    fee_schedule = val['fee_schedule'][fee_schedule_key]
                    fee_schedule = fillNumberWithZero(fee_schedule)
                    group_number = group_val['group_number_base']
                    annual_max = group_val['annual_max']
                    deductible = group_val['deductible']
                else:
                    return None
            info = {
                "group_plan": f"{state}-MCD-{fee_schedule}",
                "employer": val['employer'],
                "group_number": group_number,
                "annual_max": annual_max,
                "deductible_standar": deductible
            }
            return info
    return None

info= get_elg_info(data_supplies["carrier_name"],data_supplies["verification_status"]) 
print(info)


