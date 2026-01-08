import re 

def search_dq_fishkill_plan(master_plan, plan):
    plan_from_site = plan.lower().strip()
    plan_from_site= re.sub(r'^ny\s+', '', plan_from_site)

    best_match = None
    max_coincidence = 0

    key_plan = ["fidelis","hamaspik","mvp","affinity","wellcare"]
    found_key_plan = [kw for kw in key_plan if kw in plan_from_site]

    if found_key_plan:
        for plan_m in master_plan:
            plan_lower = plan_m.lower().strip()
            plan_lower = re.sub(r'^ny\s+', '', plan_lower)

            if plan_lower in plan_from_site or plan_from_site in plan_lower:
                if best_match is None or len(plan_lower) < len(best_match.lower()):
                    best_match = plan_m
                    continue

            key_words = plan_from_site.split()
            coincidence = sum(1 for word in key_words if word in plan_lower)

            if coincidence > max_coincidence:
                best_match = plan_m
                max_coincidence = coincidence

    return best_match if best_match else False