import sys
import os
import re 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalVariables.script import ELG_PATTERNS,data_supplies,static_regex,iv_config
from globalFunctions.script import clean_regex,get_info


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
    )                                            
]    


engine = PlanEvaluate(plans)

plan_results = engine.evaluate(
    data_supplies,
    iv_config,
    ELG_PATTERNS
)

print(plan_results)
true_keys = [key for key, value in plan_results.items() if value]

print(plan_results.get("uhccp_nj_plan", False),"ajflaj")

if any(plan_results.get(k, False) for k in [
    "uhccp_plan",
    "uhccp_dual_plan",
    "uhccp_nj_plan"
]):
    print("Hay coincidencia UHCCP")