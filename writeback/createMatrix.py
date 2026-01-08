import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalFunctions.script import check_plan_conditions,GetVar,generate_table_base_category,print_log
from globalVariables.script import data_supplies,iv_config,RULES_VALUES_MAPPING,static_regex,SUCCESS

def matrix(group_plan_name : str, data : dict):
    import re
    matrix = {}
    regex = r'^(.*?)\s*Master'
    practice = data_supplies['practice']
    template = iv_config['write_back_rules']['template']
    dq_matituck_plan, uhccp_plan, uhccp_dual_plan,uhccp_nj_plan,cs_all_plan,uhccp_middleisl,csea_all_plan,hmo_uhc,dq_fishkill_plan=  check_plan_conditions().values()
    elg_plan = any([dq_matituck_plan, uhccp_plan, uhccp_dual_plan, uhccp_nj_plan,cs_all_plan,uhccp_middleisl,csea_all_plan,hmo_uhc,dq_fishkill_plan])

    if dq_matituck_plan:
        bk = {'GroupID':'Dentaquest','Employer':'EMPTY','InsuranceName':'Dentaquest','Deductible':'00','Family':'00','DeductiblePreventive':'00','AnnualMaximum':'00','Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif uhccp_plan or uhccp_nj_plan:
        bk = {'GroupID':f'UHCCP-{practice}','Employer':'EMPTY','InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':'00','Family':'00','DeductiblePreventive':'00','AnnualMaximum':'9999','Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif uhccp_dual_plan:
        bk = {'GroupID':f'UHCCP-DUAL COMPLETE-{practice}','Employer':'EMPTY','InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':'00','Family':'00','DeductiblePreventive':'00','AnnualMaximum':'9999','Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif cs_all_plan:
        bk = {'GroupID':f"{data['group_number']}",'Employer':'EMPTY','InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':'00','Family':'00','DeductiblePreventive':'00','AnnualMaximum':'00','Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif uhccp_middleisl:
        bk = {'GroupID':f"{data['group_number']}",'Employer':'EMPTY','InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':f"{data['deductible_standar']}",'Family':'00','DeductiblePreventive':'00','AnnualMaximum':f"{data['annual_max']}",'Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif csea_all_plan:
        bk = {'GroupID':f"{data['group_number']}",'Employer':f"{data['employer']}",'InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':f"{data['deductible_standar']}",'Family':'00','DeductiblePreventive':'00','AnnualMaximum':f"{data['annual_max']}",'Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif hmo_uhc:
        bk = {'GroupID':f"{data['group_number']}",'Employer':f"{data['employer']}",'InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':f"{data['deductible_standar']}",'Family':'00','DeductiblePreventive':'00','AnnualMaximum':f"{data['annual_max']}",'Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    # elif dq_fishkill_plan:
    #     plan_number = ''
    #     parts = [part.strip() for part in data_supplies["verification_status"].split('|')]
    #     if len(parts) >= 3:
    #         plan_number = parts[2]
    #     bk = {'GroupID':f"{plan_number}",'Employer':'EMPTY','InsuranceName':'Dentaquest','Deductible':f"{data['deductible_standar']}",'Family':'00','DeductiblePreventive':'00','AnnualMaximum':f"{data['annual_max']}",'Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif dq_fishkill_plan:
        bk = {'GroupID':f"{data['group_number']}",'Employer':f"{data['employer']}",'InsuranceName':'Dentaquest','Deductible':f"{data['deductible_standar']}",'Family':'00','DeductiblePreventive':'00','AnnualMaximum':f"{data['annual_max']}",'Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    else:
        bk = eval(GetVar("bk"))
        if ('HMO' in bk['FeeScheduleName'].upper() and re.search(static_regex['re_uhc'],data_supplies['carrier_name'],re.IGNORECASE)):
            bk['AnnualMaximum'] = "9999"
            bk['Deductible'] = "0.00"
        else:
            Amounts = eval(GetVar("Amounts"))
            bk['AnnualMaximum'] = str(Amounts['AnnualMaximum'])

    def format_dec(dec):
        dec = int(dec) / 100
        return f"{float(dec):.2f}"

    def found_number(string):
        return any(int(num_str) > 0 for num_str in re.findall(r'\d+', string))
    
    def get_last_age(s):
        numeros = re.findall(r'\d+', s)
        numeros = [int(num) for num in numeros]
        return max(numeros, default=0)

    
    #################################
    #group_plan_name = "TESTING GROUP"
    fee_schedule_id = group_plan_name.split("-")[2]
    fee_schedule_id = int(fee_schedule_id)
    ##################################
    group_id = ''
    if not elg_plan:
        if len(bk["GroupID"]) > 31:
            if "-" in bk["GroupID"]:
                group_id = bk["GroupID"].split('-')
                primer_segmento = group_id[0].lstrip('0') or '0'  
                otros_segmentos = group_id[1:]
                group_id = f'{primer_segmento}-' + '-'.join(otros_segmentos)
        else:
            group_id = bk["GroupID"]  
    else:
        group_id= bk["GroupID"]


    # if group_plan_name and practice and fee_schedule_id and bk["Employer"]:
    if group_plan_name and practice and fee_schedule_id:

        def process_string(input_string: str) -> str:
            cleaned_string = input_string.strip()
            if cleaned_string in  ["-",'','N/A','None','Not Covered']:
                return "00"
            if cleaned_string in ["Unlimited","UNLIMITED","unlimited"]:
                return "9999"   
            cleaned_string = cleaned_string.replace(",", "").replace("$", "")
            return cleaned_string

        matrix["group_plan_name"] = group_plan_name
        matrix["plan_group_number"] = group_id
        table = []
        if not elg_plan:
            if ('HMO' in bk['FeeScheduleName'].upper() and re.search(static_regex['re_uhc'],data_supplies['carrier_name'],re.IGNORECASE)):
                table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_3'])
            else:
                table = eval(GetVar("coverage_list"))
            matrix["plan_employer"] = bk["Employer"].strip()[:31].strip()
            
        else:
            matrix["plan_employer"] = bk["Employer"]
            if dq_matituck_plan or dq_fishkill_plan:
                table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_3'])
            elif uhccp_plan or uhccp_dual_plan or uhccp_nj_plan or cs_all_plan or uhccp_middleisl:
                table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_1'])
            elif csea_all_plan or hmo_uhc:
                table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_3'])

        matrix["location_id"] = practice
        matrix["fee_schedule_id"] = fee_schedule_id
        if 'see group name' in bk["InsuranceName"].lower():
            bk['InsuranceName'] = data_supplies['carrier_name']

        matrix["carrier"] = re.search(regex,bk["InsuranceName"],re.IGNORECASE).group(1) if bool(re.search(regex,bk["InsuranceName"],re.IGNORECASE)) else bk["InsuranceName"]
        if table:
            for row in table:
                if row[2] == "Ortho":
                    ortho_value= format_dec(row[3])
                matrix[row[0]+"_"+row[1]] = format_dec(row[3])
            matrix["deductible_standard_individual_lifetime"] = "00"
            matrix["deductible_standard_individual_annual"] = process_string(bk["Deductible"])
            matrix["deductible_standard_family_annual"]= process_string(bk["Family"])
            matrix["deductible_preventative_individual_lifetime"]= "00"
            matrix["deductible_preventative_individual_annual"]= process_string(bk["DeductiblePreventive"])
            matrix["deductible_preventative_family_annual"]= "00"
            matrix["deductible_other_individual_lifetime"]= "00"
            matrix["deductible_other_individual_annual"]= "00"
            matrix["deductible_other_family_annual"]= "00"
            matrix["maximum_benefit_individual"]= process_string(bk["AnnualMaximum"])
            matrix["ortho_plan"]= 1 if found_number(bk["Orthodontic"]) else 0
            #matrix["ortho_coverage"] = float(bk["Orthodontic"].strip().replace("%","")) if found_number(bk["Orthodontic"]) else "00"
            matrix["ortho_coverage"] = ortho_value
            matrix["ortho_max_age"] = get_last_age(bk["Orthodontics_AgeLimit"])
            matrix["ortho_max_dollars"] = format(float(process_string(bk["LifetimeMax"])),".2f") if found_number(bk["LifetimeMax"]) else 0.00
            print_log(SUCCESS,"MATRIX CREATED CORRECTLY")
            print(matrix)
            ##pg.alert('review matrix info')
        else:
            return None
    return matrix