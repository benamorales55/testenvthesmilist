import sys 
import os 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalVariables.script import data_supplies,INFO,SUCCESS,iv_config,CARESOURCE_RULES_LAST_RECORD,RULES_VALUES_MAPPING,static_regex
from globalFunctions.script import print_log,GetVar,fillNumberWithZero,unlimited_value,generate_table_base_category,setLog,check_plan_conditions
from drApiOperations.getLastRecord import get_last_record



def handle_group_plan(new_group_plan,smilist_tin,amounts,general_info,data_response):
    from time import sleep
    fee_shid = new_group_plan.split("-")[-1] if new_group_plan else None
    dq_matituck_plan, uhccp_plan, uhccp_dual_plan,uhccp_nj_plan,cs_all_plan,uhccp_middleisl,csea_all_plan,hmo_uhc,dq_fishkill_plan =  check_plan_conditions().values()
    data ={
        'practice': data_supplies['practice'],
        'employer': general_info["Employer"].strip()[:31].strip(),
        'group_number': general_info['GroupID'],
        'annual_max': amounts["AnnualMaximum"],
        'deductible_standar': amounts["Deductible"],
        'feeschedule_id': fee_shid
    }
    data_response = [plan_api for plan_api in data_response["data"] if plan_api["location_id"] == data["practice"]] if not cs_all_plan else [plan_api for plan_api in data_response["data"]]
    api_plan = {}
    print_log(INFO,"HANDLE GROUP PLAN INFORMATION")
    print(data)
    caresource_rule = True if int(data['feeschedule_id']) == 457 and data['group_number'] in CARESOURCE_RULES_LAST_RECORD else False
    print_log(INFO,"DATA RESPONSE LENG **************************************")
    print(len(data_response))
    data_ordered = sorted(data_response,key=lambda x: x['id'], reverse=True)
    print_log(INFO,"DATA ORDERED START **************************************")
    print(data_ordered)
    print_log(INFO,"DATA RESPONSE END **************************************")
    values_evaluate = {}
    for value in data_ordered:
        group_plan_api = "-".join(value["group_plan_name"].split("-")[:3])

        if (value["plan_group_number"] == data['group_number'] 
            and group_plan_api == new_group_plan
            and value["plan_employer"].lower() == data['employer'].lower()
            and unlimited_value(int(float(value["maximum_benefit_individual"])),int(float(data['annual_max']))) 
            and int(float(value["deductible_standard_individual_annual"])) == int(float(data['deductible_standar']))
            and int(value["fee_schedule_id"]) == int(data['feeschedule_id'])):
            print_log(INFO,"****************************************DATE************************************")
            print()
            #table review 
            api_table_dict = {key: int(float(val) * 100) for key,val in value.items() if key.startswith("D")}
            

            coverage_list_table = eval(GetVar("coverage_list"))
            same_coverage_table = None
           
            if data_supplies["type_of_verification"] == "FBD" and coverage_list_table:
                coverage_list = []
                bk = eval(GetVar("bk"))
                template = iv_config['write_back_rules']['template']
                print_log(INFO,"****************************************TEMPLATE************************************")
                print(template)
                if ('HMO' in bk['FeeScheduleName'].upper() and re.search(static_regex['re_uhc'],data_supplies['carrier_name'],re.IGNORECASE)):
                    coverage_list = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_3'])
                    bk = (GetVar("bk"))
                else:
                    print_log(INFO,"****************************************COVERAGE LIST************************************")
                    coverage_list = (GetVar("coverage_list"))
                    print(coverage_list)
                
                coverage_table_dict = {f"{val[0]}_{val[1]}":val[3] for val in coverage_list}
                if len(api_table_dict) == len(coverage_table_dict):
                    differences = {}
                    for key in api_table_dict:
                        if str(api_table_dict[key]) != coverage_table_dict.get(key, None): 
                            differences[key] = (api_table_dict[key], coverage_table_dict.get(key))

                    if not differences:
                        print_log(SUCCESS,"SAME COVERAGE TABLE")
                        same_coverage_table = True

                    else:
                        flag = False
                        print(value["group_plan_name"])
                        print(coverage_table_dict)
                        print(api_table_dict)
                        procedures = []
                        for k, v in differences.items():
                            if int(v[0]) == 0 or int(v[1]) == 0:
                                print(f"{k}: {v[0]} != {v[1]}")
                                procedures.append(f"{k}: {v[0]}__api != {v[1]}__tc")
                            flag = True
                        if flag: 
                            key = f'{value["group_plan_name"]}_{value["createdAt"]}'
                            values_evaluate[key] = procedures        
                        #setLog(f"|new plan created because coverage table was different codes {procedures}")
            else:
                same_coverage_table = True
            
            if values_evaluate:
                # table_confirmation = pg.confirm(f"The plan already exists, but this form has different coverage for procedures {values_evaluate}. Do you want to continue?")
                # continue_proccess = True if table_confirmation == 'OK' else False
                continue_proccess = True
                sleep(2)
                if continue_proccess:
                    same_coverage_table = True
                    #setLog("|new plan created because coverage table was different")
                else: 
                    # # # winAction.closeModals("Insurance Coverage.*|Insurance Information",duration=2)
                    setLog("|Person in charge stop the execution to review the form with QA")
                    raise Exception("Person in charge stop the execution to review the form with QA")            
           
            #table review

            api_plan = {
                "carrier_name" : value['carrier'],
                "group_plan_name": value["group_plan_name"],
                "plan_employer": value["plan_employer"],
                "plan_group_number": value["plan_group_number"],
                "smilist_tin": smilist_tin
            }
            print_log(SUCCESS,'API PLAN INFORMATION FOUND')
            print(api_plan)
            if same_coverage_table: return api_plan
            # return api_plan

    last_secuential_number = get_last_record() if not caresource_rule else CARESOURCE_RULES_LAST_RECORD[data['group_number']]
    last_secuential_number = fillNumberWithZero(last_secuential_number)
    new_group_plan = f"{new_group_plan}-{last_secuential_number}"
    new_matrix = matrix(new_group_plan,data)
    print_log(SUCCESS,new_matrix)
    if new_matrix:
        query_matrix = tuple([value for key, value in new_matrix.items()])
        db_insertion = True
        # # # db_insertion,exception_db = insert_query_consult(query_matrix)
        print("*** db_insertion: {}".format(db_insertion))
        if db_insertion:
            post_records = True
            # # # post_records = post_new_matrix(new_matrix)
            if post_records:
                # # # SetVar("log", GetVar("log") + "Matrix input at api and DB|")
                api_plan = {
                    "carrier_name" : new_matrix['carrier'],
                    "group_plan_name": new_matrix["group_plan_name"],
                    "plan_employer": new_matrix["plan_employer"],
                    "plan_group_number": new_matrix["plan_group_number"],
                    "smilist_tin": smilist_tin
                }
                return api_plan
            else:
                # # # SetVar("log", GetVar("log") + "Can not insert into api|")
                # # # fail_writeback_status()
                return None

        else:
            # # # SetVar("log", GetVar("log") + "Can not insert into api and DB|")
            # # # fail_writeback_status()
            return None
    else:
        return None