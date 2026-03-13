import sys
import os
import re 
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalVariables.script import ELG_PATTERNS,data_supplies,static_regex,iv_config
from globalFunctions.script import clean_regex,get_info,read_json



class PlanRule:

    def __init__(
            self,
            name,
            carrier_regex = None,
            verification_include = None,
            verification_exclude = None
        ):
        
        self.name = name
        self.carrier_regex = (
            re.compile(carrier_regex,re.IGNORECASE)
            if carrier_regex else None
        )
        
        self.verification_include = verification_include or []
        self.verification_exclude = verification_exclude or []



    
    def found_plan(self,data_supplies,iv_config,ELG_PATTERNS):

        practice = data_supplies['practice'].lower()
        allowed_practice = [p.lower() for p in iv_config['elg_clinics'].get(self.name) or []]
        
        if "all" not in allowed_practice and practice not in allowed_practice:
            return False
        
        if self.carrier_regex:
            if not self.carrier_regex.search(data_supplies['carrier_name']):
                return False
            

        if self.name == "ghi_emblem_ny_nj" and data:
            nodo_practice = data.get(data_supplies["practice"], {})
            emblem_node = nodo_practice.get("Emblem")
            if not emblem_node:
                return False
            
            #despues se podria aplicar la validacion directa del plan
            plan_types = emblem_node.get("Plan Type",{})

            states = {plan_info.get("State") for plan_info in plan_types.values() }

            if not states.intersection({"NY", "NJ"}):
                return False
            


        for key in self.verification_include:
            pattern_or_dict = ELG_PATTERNS.get(key)
            if isinstance(pattern_or_dict, dict):
                if not any(re.search(pat, data_supplies['verification_status'], re.IGNORECASE)
                        for pat in pattern_or_dict.values()):
                    return False
            else:        
                if not re.search(pattern_or_dict, data_supplies['verification_status'], re.IGNORECASE):
                    return False

        
        for key in self.verification_exclude:
            pattern_or_dict = ELG_PATTERNS.get(key)
            if isinstance(pattern_or_dict, dict):
                if any(re.search(pat, data_supplies['verification_status'], re.IGNORECASE)
                    for pat in pattern_or_dict.values()):
                    return False
            else:
                if re.search(pattern_or_dict, data_supplies['verification_status'], re.IGNORECASE):
                    return False
       
        return True


class PlanEvaluate:

    def __init__(self,plans):
        self.plans = plans
    
    def evaluate(self, data_supplies, iv_config, ELG_PATTERNS):
        results = {}
        for plan in self.plans:
            results[plan.name] = plan.found_plan(
                data_supplies,
                iv_config,
                ELG_PATTERNS

            ) 
        return results
    

plans = [
    PlanRule(
        name = 'dq_mattituck_plan',
        carrier_regex = static_regex['dentaquest'],
    ),
    PlanRule(
        name = 'uhccp_plan',
        carrier_regex = static_regex['skygen_reg'],
        verification_exclude=['dual_pattern','nj_family_pattern']
    ),
    PlanRule(
        name = 'uhccp_dual_plan',
        carrier_regex = static_regex['skygen_reg'],
        verification_include=['dual_pattern']
    ),
    PlanRule(
        name = 'uhccp_nj_plan',
        carrier_regex = static_regex['skygen_reg'],
        verification_include=['nj_family_pattern']
    ),
    PlanRule(
        name = 'caresorce_all_plan',
        carrier_regex = static_regex['caresorce_reg'],
        verification_include=["caresource_nj_pattern"]
    ),
    PlanRule(
        name = 'uhccp_middleisland',
        carrier_regex = static_regex['skygen_reg']     
    ),
    PlanRule(
        name = 'csea_all_plan',
        carrier_regex = static_regex['csea_reg']     
    ),
    PlanRule(
        name = 'hmo_uhc_plan',
        carrier_regex = static_regex['re_uhc'],
        verification_include=["hmo"]     
    ),
    PlanRule(
        name = 'dq_fishkill_plan',
        carrier_regex = static_regex['dentaquest']
    ),
    PlanRule(
        name = 'dq_catskill_plan',
        carrier_regex = static_regex['dentaquest']
    ),
    PlanRule(
        name = 'liberty_mattituck_plan',
        carrier_regex = static_regex['liberty']
    ),
    PlanRule(
        name = 'ghi_emblem_ny_nj',
        carrier_regex = static_regex['emblem']
    )                                                     
]    


engine = PlanEvaluate(plans)
route = Path(__file__).parent.parent
feed_data = f"{route}\\fee_data.json"
data = read_json(feed_data)

plan_results = engine.evaluate(
    data_supplies,
    iv_config,
    ELG_PATTERNS
    
)

print(plan_results)
true_keys = [key for key, value in plan_results.items() if value]



# try:
#     usuario = os.getlogin()
# except Exception:
#     usuario = "unknown_user"

# route = os.path.dirname(os.path.abspath(__file__))
# feed_data = f"{route}\\fee_data\\fee_data_{usuario}.json"
# data = read_json(feed_data)