import pandas as pd
import json
import re
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalVariables.carriersRegex import carriers_regex
from globalVariables.master import MASTER
from pathlib import Path

def fee_data():
    # from module.business.carriers_manager import get_regex_for_types,get_carriers_per_client



    titles = ['Location', 'Payer', '', 'Plan Type/ Plan Name', 'Legacy Tin', 'Smilist Tin', 'State', 'matches']
    rename_clinics = {
    'HAMILTONSQUARE':'HAMILTONSQ',
    'LAWRENCEVILLE':'LAWRENCEVI',
    'BRINTONLAKE':'BRINTONLAK',
    'SPRINGFIELD':'SPRINGFIEL',
    'WESTSENECA':'WESTSENEC',
    'SMITHTOWNOS':'SMITHTO_OS',
    'BROOKLYNHEIGHTS': 'BRKHEIGHTS', 
    'COMMACKENDO': 'ENDOCOMMAC', 
    'ENGLISHTOWN': 'ENGLISHTOW', 
    'HERALDSQUARE': 'HERALDSQ', 
    'NORTHBABYLON': 'NORTHBABYL', 
    'MIDDLEISLAND': 'MIDDLEISL', 
    'PORTWASHINGTON': 'PORTWASH', 
    'MOUNTAINSIDE': 'MOUNTAINSD', 
    'N.FLUSHING': 'NFLUSHING', 
    'N.FLUSHING2': 'NFLUSHING2', 
    'VALLEYSTREAM': 'VALLEYSTRM', 
    'SOUDERTON': 'SOUDERTON1', 
    'SOUDERTON': 'SOUDERTOLD',
    'STATENISLAND': 'STATENISLD', 
    'TDCMIDDLEISLAND': 'TDCMIDDLEI', 
    'WADINGRIVER': 'WADINGRVR', 
    'WASHINGTONSQUAREPARK': 'WASHSQPARK', 
    'WESTHARTFORD': 'WHARTFORD', 
    'WESTCHESTER': 'WESTCHESTE', 
    'WHITEPLAINS': 'WHITEPLAIN',
    'TOMSRIVER':'ENC_TOMS',
    'WADINGRIVER':'WADINGRVR',
    "SHILLINGTON":"SHILLINGTO",
    "HADDONHEIGHTS":"HADDONHEIG",
    "SBS-MEDFORD" : "MEDFORDNJ",
    "BALDWINSVILLE" : "BALDWINSVI",
    "POUGHKEEPSIE" : "POUGHKEEPS",
    "WAPPINGERFALLS" : "WAPPNGRFLL",
    "PINEBUSH" : "PINEBUSH",
    "LOUDONVILLE" : "LOUDONVILL",
    "CENTRALSQUARE" : "CENTRALSQ",
    "REDHOOK" : "REDHOOK",
    "CLIFTONPARK" : "CLIFTONPRK",
    "HURLEYAVE" : "HURLEYAVE"
    }

    # # # spreed_fee_data = (GetVar("MASTER"))
    spreed_fee_data = MASTER

# version antigua at 12/04/2025    
#     spreed_fee_data = [
#     row for row in spreed_fee_data
#     if len(row) >= 7
#     and not str(row[1]).strip().lower().startswith("dental")
#     and all(str(row[i]).strip() != "" for i in (0, 1, 3, 5, 6))
# ]

    # new version at 12/04/2025
    spreed_fee_data = [
    row for row in spreed_fee_data
    if not str(row[1]).strip().lower().startswith("dental")
    and (
        str(row[1]).strip().lower() == "ucr"
        or (
            len(row) >= 7
            and all(str(row[i]).strip() != "" for i in (0, 1, 3, 5, 6))
        )
    )
]

    #rename differents clinics to be equal like config.yaml
    for row in spreed_fee_data:
        if bool(row) == True:
            clinic = row[0].upper().replace(' ','')
            if clinic in rename_clinics: clinic = rename_clinics[clinic]
            row[0] = clinic
    fee_data = pd.DataFrame(spreed_fee_data, columns=titles)
    fee_data['Row_number'] = range(4, 4 + len(fee_data))
    
    fee_data = fee_data.applymap(lambda x: x.upper().strip() if isinstance(x, str) else x)

    # # # practice = GetVar("practice")
    # # SetVar("practice", iv_config['clinic_settings']['settings'][practice]['clinic_name'])
    # carriers = { obj.name: obj.regex for obj in get_carriers_per_client().bots }
    carriers = carriers_regex
    carriers.update({'UCR':"^UCR$"})
    # # # SetVar("practice", practice)
    regular_expresions = carriers


    def get_carrier_name(value):
        if value:
            if re.match(r"^(Delta Dental|Delta PPO|Delta Premier)",value,re.IGNORECASE):
                return 'Delta Dental' 
            for carrier_name, regx in regular_expresions.items():
                if re.compile(regx).search(value):
                    return carrier_name
        return "EMPTY"

    def get_regex(value):
        if value:
            if value.lower().startswith("delta"):
                return '^(Delta Dental|Delta|DD).*'
            for carrier_name, regx in regular_expresions.items():
                reg = regx
                if re.compile(regx).search(value):
                    return regx
        return "EMPTY"

    fee_data['Payer'] = fee_data['Payer'].fillna('EMPTY')
    fee_data['Carrier'] = fee_data['Payer'].fillna('EMPTY')
    fee_data['State'] = fee_data['State'].fillna('')
    fee_data['Plan Type'] = fee_data['Plan Type/ Plan Name'].fillna('')
    fee_data['Smilist TIN'] = fee_data['Smilist Tin'].fillna('')
    fee_data['Location'] = fee_data['Location'].fillna('')
    fee_data['regex'] = fee_data['Payer'].apply(get_regex)
    fee_data['Carrier'] = fee_data['Payer'].apply(get_carrier_name)
    fee_data['PreAffiliation TIN'] = fee_data['Legacy Tin'].fillna('')
    fee_data.loc[fee_data['Payer'] == 'UCR', 'Plan Type'] = 'UCR'
    
    # delete rows by value ('EMPTY' or '')
    fee_data = fee_data.loc[fee_data['regex'] != 'EMPTY']
    fee_data = fee_data.loc[fee_data['Plan Type'] != '']
    fee_data = fee_data.loc[fee_data['Smilist TIN'] != '']
    
    fee_data_by_location = fee_data.groupby('Location').apply(lambda x: x[['Row_number','Payer','Carrier','regex','Plan Type','State','Smilist TIN','PreAffiliation TIN']].drop_duplicates().to_dict('records')).to_dict()
    
    master_fee = {}

    def get_plan_type(name):
        plan_type = ""
        patterns = [
            'PPO',
            'DPPO',
            'PDP',
            'HMO',
            'DHMO',
            'DMO',
            'MEDICAID',
            'MCO',
            'NJH',
            'DQ',
            'UHCCP',
            'HPLX',
            'STRAIGHT MEDICAIDS',
            'DISCOUNT',
            'EDP',
            'AETNA',
            'ACCESS',
            'SMILIST ONE MEMBERSHIP',
            'LOCAL & UNION',
            'INDEMNITY',
            'MEDICARE ADVANTAGE'
            ]
        if name == "TOTAL":
            plan_type = "TOTAL DPPO|"
        else:
            pattern_dict = {pattern: rf'^{pattern}(\s|$)' for pattern in patterns}
            matching_patterns = [pattern for pattern, regex in pattern_dict.items() if re.search(regex, name)]
            plan_type = '|'.join(matching_patterns) + '|'
        if plan_type == "|":
            plan_type = name + '|'
        return plan_type[:-1]

    def get_plan_type_by_payer(payer):
        plan_type = ""
        if re.compile('PPO|&DPPO').search(payer):
            plan_type += "PPO|"
        if re.compile('PDP').search(payer):
            plan_type += "PDP|"
        if re.compile('HMO|DHMO|DMO').search(payer):
            plan_type += "HMO|"
        if re.compile('MEDICAID|MCO|NJH|DQ|UHCCP|HPLX|STRAIGHT MEDICAIDS').search(payer):
            plan_type += "MCD|"
        if re.compile('DISCOUNT|EDP|AETNA|ACCESS').search(payer):
            plan_type += "DSC|"
        if re.compile('SMILIST ONE MEMBERSHIP').search(payer):
            plan_type += "SM1|"
        if re.compile('LOCAL & UNION').search(payer):
            plan_type += "LOC|"
        if re.compile('INDEMNITY').search(payer):
            plan_type += "IND|"
        if re.compile('MEDICARE ADVANTAGE').search(payer):
            plan_type += "MCV|"
        
        return plan_type[:-1]

    def combinar_sin_duplicados(str1, str2):
        if str2 == "": return str1
        # Dividir las cadenas por el delimitador '|'
        conjunto1 = set(str1.split('|'))
        conjunto2 = set(str2.split('|'))
        
        # Unir ambos conjuntos para eliminar duplicados
        conjunto_unido = conjunto1.union(conjunto2)
        
        # Convertir el conjunto de nuevo a una cadena separada por '|'
        resultado = '|'.join(sorted(conjunto_unido))
        
        return resultado

    for i, location in enumerate(fee_data_by_location):
        for element in fee_data_by_location[location]:
            if location not in master_fee:
                master_fee[location]={}
            
            if element["Carrier"] not in master_fee[location]:
                master_fee[location][element["Carrier"]] = {'regex': element["regex"], 'Plan Type': {}}

            plan_type = get_plan_type(element["Plan Type"])
            plan_type_by_payer = get_plan_type_by_payer(element["Payer"])
            plan_type = combinar_sin_duplicados(plan_type,plan_type_by_payer)
            pre_afi = element["PreAffiliation TIN"]
            smi_tin = element["Smilist TIN"]
            if not bool(re.search(r'\d', pre_afi)):
                pre_afi = ''
            
            if not bool(re.search(r'\d', smi_tin)):
                smi_tin = ''

            if plan_type and plan_type not in master_fee[location][element["Carrier"]]["Plan Type"]:
                master_fee[location][element["Carrier"]]["Plan Type"][plan_type] = {"Row_number":element["Row_number"],"State": element["State"],"Smilist TIN": smi_tin, "PreAffiliation TIN": pre_afi}

    # multiclinic master fee
    master_fee['SOUDERTON1'] = master_fee['SOUDERTOLD']
    master_fee['ENC_BRICK'] = master_fee['BRICK']
    master_fee['ENC_SHREWS'] = master_fee['SHREWSBURY']
    master_fee['ENC_LACEY'] = master_fee['LACEY']
    master_fee['ENC_JACKS'] = master_fee['JACKSON']
    master_fee['OLD_SHERRY'] = master_fee['CHERRYHILL']
    master_fee['OLD_MARLTO'] = master_fee['MARLTON']
    master_fee['OLD_GIBBS'] = master_fee['GIBBSBORO']
    master_fee['OLD_HADDON'] = master_fee['HADDONHEIG']


    # path_file = f"{GetVar('base_pathP')}\\bots\\scripts\\fee_data.json"
    # # # route = os.path.dirname(os.path.abspath(__file__))
    route = Path(__file__).parent.parent

    # Usuario actual del sistema
    try:
        usuario = os.getlogin()
    except Exception:
        usuario = "unknown_user"


    # # # path_file = f"{route}\\fee_data\\fee_data_{usuario}.json"
    path_file = f"{route}\\fee_data.json"
    with open(path_file, 'w') as file:
        json.dump(master_fee, file, indent=4)

    print(f"JSON has been write in the path: '{path_file}'.")

fee_data()