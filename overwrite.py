import sys, os, re, numpy as np, traceback
from datetime import datetime

sys.path.append(os.path.join(os.getcwd(),os.path.normpath('modules/dr-workflow')))
from module.business import pdf_reader as pdf
from module import set_var, init_log, get_platform_vars, get_info,conv, \
    print_log, set_status, INFO, SUCCESS, WARNING, global_path
    
sys.path.append(os.path.join(global_path,'libs'))
from workflow_lib.business.document_manager import DocumentManager, DocumentManagerDict

DEF_VALUE = 'EMPTY'

overwrite = init_log("overwrite",globals)
overwrite = get_platform_vars([
    ('result_integration',conv),
    ('verification_type'),
    ('status'),
    ('state_verification'),
    ('index',conv),
    ('sheet'),
    ('gsheet_columns',conv),
    ('returned_values',conv),
    ('docx_path'),
    ('base_pathP'),
    ('bot_name'),
], overwrite, log=False)

script_vars = get_info(overwrite,'vars',def_value={})
cc_data = get_info(overwrite,'vars.returned_values',def_value={})
print_log(SUCCESS,"data from returned values")
print(cc_data)

def set_value(column,value):
    global overwrite, script_vars
    row = script_vars['index']
    columns = script_vars['gsheet_columns'][0]
    value = value.replace('\n','').replace("'",'`')
    value = value if value != '' else DEF_VALUE
    script_vars['result_integration'][row][columns.index(column)] = value

try:
    note = ""
    status = "Empty"
    met_ded = get_info(cc_data,"ded_used",def_value = "0.00")
    plan = get_info(cc_data,"other_info.plan",def_value = "0.00")
    amount_used = get_info(cc_data,"max_used",def_value="0.00")
    term_date = get_info(cc_data,"term_date", def_value = "N/A") if get_info(cc_data,"term_date", def_value = "N/A") else "N/A"
    effective_date = get_info(cc_data, "effective_date", def_value = "N/A") if get_info(cc_data,"effective_date", def_value = "N/A") else "N/A"
    if effective_date == "N/A":
        effective_date = get_info(cc_data, "bk.EffectiveDate", def_value="N/A")
    group_name = get_info(cc_data, "group_name", def_value = "EMPTY") if get_info(cc_data,"group_name", def_value = "EMPTY") else "EMPTY"
    group_plan = get_info(cc_data, "network", def_value = "EMPTY") if get_info(cc_data,"network", def_value = "EMPTY") else ""
    ind_ded = "N/A" if cc_data["ind_ded"] == "" else cc_data["ind_ded"]
    ind_max = "N/A" if cc_data["ind_max"] == "" else cc_data["ind_max"]
    amounts = f"met_ded:{met_ded}-amount_used:{amount_used}-ind_ded:{ind_ded}-ind_max:{ind_max}"

    if script_vars['status'].lower() != "check":
        if term_date != "N/A" or effective_date != "N/A":
            status = f"{script_vars['status']} | {effective_date} - {term_date}" 
        else: 
            status = script_vars['status']


        if 'AETNA' in script_vars['bot_name'].upper():
            if term_date != "N/A" or effective_date != "N/A":
                status = f"{script_vars['status']} |{group_plan}| {effective_date} - {term_date}" 
            else:
                status = f"{script_vars['status']} |{group_plan}"            
       
        if 'EMBLEM' in script_vars['bot_name'].upper():
            
            group_name = get_info(cc_data, "group_name", def_value = "EMPTY") if get_info(cc_data,"group_name", def_value = "EMPTY") else ""
            group_id = get_info(cc_data, "group_id", def_value = "EMPTY") if get_info(cc_data,"group_id", def_value = "EMPTY") else ""
            plan_name = get_info(cc_data["other_info"], "plan_name", def_value = "EMPTY") if get_info(cc_data["other_info"],"plan_name", def_value = "EMPTY") else ""
            info = f'{group_id},{group_name},{plan_name}' if group_id and group_name and plan_name else 'no info'
            if term_date != "N/A" or effective_date != "N/A":
                status = f"{script_vars['status']} | {info} |{effective_date} - {term_date}"
            else:
                status = f"{script_vars['status']} | {info}"  

        # if "EMBLEM" in script_vars['bot_name'].upper():
        #     ind_ded = "N/A" if cc_data["ind_ded"] == "" else cc_data["ind_ded"]
        #     ind_max = "N/A" if cc_data["ind_max"] == "" else cc_data["ind_max"]
        #     note = f"|ind_ded:{ind_ded}-ind_max:{ind_max}"
        #     status = status + note 
            
        if 'SKYGEN' in script_vars['bot_name'].upper():
            if term_date != "N/A" or effective_date != "N/A":
                status = f"{script_vars['status']} |{group_name}| {effective_date} - {term_date}" 
            else:
                status = f"{script_vars['status']} |{group_name}"

        if 'CARESOURCE' in script_vars['bot_name'].upper() or 'CSEA' in script_vars['bot_name'].upper():
            if term_date != "N/A" or effective_date != "N/A":
                status = f"{script_vars['status']} |{group_plan}| {effective_date} - {term_date}" 
            else:
                status = f"{script_vars['status']} |{group_plan}"

        if 'SUNLIFE DENTAQUEST' in script_vars['bot_name'].upper():
            plan_number = get_info(cc_data,"group_id", def_value = "0.00")
            if term_date != "N/A" or effective_date != "N/A":
                status = f"{script_vars['status']} | {plan} | {plan_number} |{effective_date} - {term_date}"
            else:
                status = f"{script_vars['status']} |{plan}| {plan_number}"

        if 'UNITED HEALTHCARE' in script_vars['bot_name'].upper():
            plan = get_info(cc_data, "product_plan_type", def_value = "EMPTY") if get_info(cc_data,"product_plan_type", def_value = "EMPTY") else ""
            group_name = get_info(cc_data, "group_name", def_value = "EMPTY") if get_info(cc_data,"group_name", def_value = "EMPTY") else ""
            group_id = get_info(cc_data, "group_id", def_value = "EMPTY") if get_info(cc_data,"group_id", def_value = "EMPTY") else ""

            info = f"{plan}-{group_name}-{group_id}"
            if term_date != "N/A" or effective_date != "N/A":
                status = f"{script_vars['status']} | {info} |{effective_date} - {term_date}"
            else:
                status = f"{script_vars['status']} |{info}"
        
        #rule for anthem 01/14/2026
        if 'NEW BCBS' in script_vars['bot_name'].upper():
            anthemPlanCoverageMap = get_info(cc_data["other_info"], "anthemPlanCoverageMap", def_value = "EMPTY") if get_info(cc_data,"anthemPlanCoverageMap", def_value = "EMPTY") else ""

            info = f"anthemPlanCoverageMap :{anthemPlanCoverageMap}"
            if term_date != "N/A" or effective_date != "N/A":
                status = f"{script_vars['status']} | {info} |{effective_date} - {term_date}"
            else:
                status = f"{script_vars['status']} |{info}"

        #rule for liberty 02/14/2026
        if 'LIBERTY DENTAL PLAN' in script_vars['bot_name'].upper():
            groupName = get_info(cc_data, "group_name", def_value = "EMPTY") if get_info(cc_data, "group_name", def_value = "EMPTY") else ""
            groupNumber = get_info(cc_data, "group_id", def_value = "EMPTY") if get_info(cc_data, "group_id", def_value = "EMPTY") else ""
            planName = get_info(cc_data, "network", def_value = "EMPTY") if get_info(cc_data, "network", def_value = "EMPTY") else ""

            info = f"{groupName}::{groupNumber}::{planName}"
            if term_date != "N/A" or effective_date != "N/A":
                status = f"{script_vars['status']} | {info} |{effective_date} - {term_date}"
            else:
                status = f"{script_vars['status']} |{info}"                


    # set_value('Amounts',note)              
    set_value('Insurance Verification Process Results',script_vars['state_verification'])
    set_value('Insurance Verification Status',status.replace("'",""))
    #set_value('Verification Date',datetime.today().strftime('%m/%d/%Y'))
    set_value('Amounts',amounts)
    # set_value('Employer Name From Site', get_info(cc_data,"group_name"))
    set_var('result_integration', script_vars['result_integration'])
except:
    traceback.print_exc()



                elif(data_supplies['type_of_verification'] == "ELG" and 
                "INACTIVE" not in data_supplies["verification_status"].upper() and  
                "MAX OUT" not in data_supplies["verification_status"].upper()):     
                    plan_results = planElg.evaluate(data_supplies, iv_config, ELG_PATTERNS)
                    print_log(SUCCESS,'PLAN RESULTS')
                    print(plan_results)
                    elg_plan = [key for key, value in plan_results.items() if value]

                    update_payor(found_carrier,elg_plan) 
                    nomenclature_plan = eval(gpvars("nomenclature_plan"))
                    print_log(SUCCESS,'NOMENCLATURE VAR')
                    print(nomenclature_plan)
                    if nomenclature_plan: 
                        update_employer(nomenclature_plan['employer_plan'],nomenclature_plan)
                        coverage_table()
                    if elg_plan:
                        setLog(f"ELG PLAN {elg_plan[0].upper()}|")
                        review_overlap()
                        employer_ = verified_employer()
                        if employer_:update_employer(employer_)  
                        coverage_table()
                        if any(plan_results.get(k, False) for k in [
                            "uhccp_plan",
                            "uhccp_dual_plan",
                            "uhccp_nj_plan"
                            ]):
                            max_value = '9999'
                            set_amounts(max_value)
                    
                    set_amounts()
                    set_deductible(generate_amounts_dict())