import re, os, sys, traceback, json
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime,date
from rocketbot import SetVar, GetVar

### LIB WORKFLOW
from workflowlog import set_var, init_log, print_log, get_platform_vars, get_info,conv, gpvars
from workflowlog import DEFAULT, SUCCESS, ERROR, WARNING, INFO

### MODULE DR_WORKFLOW FUNCTIONS
sys.path.append(os.path.join(os.getcwd(),os.path.normpath('modules/dr-workflow')))
from module.business.carriers_manager import  get_regex_for_types,get_carriers_per_client
from module.business import remember as rem, Gspreadsheet as gsheet, alerts

### GET LIB TO MANAGE THE APP
sys.path.append(os.path.join(os.getcwd(),os.path.normpath('modules/ActionsHandler/libs')))
from actionsHandler.PyAutoGui import pyautogui as pg
from actionsHandler.WinAction import WinAction
from actionsHandler.ImgAction import ImgAction
from actionsHandler import utils as ut
from utils import loadJson
global winAction, imgAction, schema, wins
from actionsHandler.uiautomation import uiautomation as ui

sys.path.append(os.path.join(GetVar("base_pathP").replace("/", "\\"), os.path.normpath('bots/scripts')))
from winnavigator import init, openWin
from upload_docs import selectInsuranceType
from insurance_naming import get_group_name, fillNumberWithZero
from dr_api_operations import get_last_record,get_records,post_new_matrix
from client_db_operations import insert_query_consult
import csv
from difflib import SequenceMatcher as SM

import pyautogui

bot_data = init_log("iv_extraction", globals)
bot_data = get_platform_vars([
    ('iv_config',conv),
    ('gsheet_columns',conv),
    ('base_pathP'),
    ('sheet'),
    ('data_supplies',conv),
    ('log')
], bot_data, log=False)

def clean_regex(regex):
    regex = regex.replace('(?i)',"")
    return r'(?i)' + regex

def is_number(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

script_vars = get_info(bot_data,'vars',def_value={})
iv_config = get_info(script_vars,"iv_config",def_value={})
base_path = get_info(script_vars,'base_pathP', def_value= "")
data_supplies = get_info(script_vars,'data_supplies',def_value={})
elg_carriers_clinic = clean_regex(get_info(iv_config,'elg_carriers_clinic',def_value={}))
locations = [location.upper() for locations in iv_config['elg_clinic'].values() for location in locations]

exception_text = {
    'Cannot insert duplicate key in object' : 'NOT INSERT INTO DB DUE THE INFO ALREADY EXISTS|',
    'A record with the same key values already exists' : 'INSERT SKIPPED - PLAN ALREADY EXISTS IN DB|',
    'Error converting data type nvarchar to numeric' : 'CAN NOT INSERT INTO API DUE ERROR CONVERTING [VARCHAR TO NUMERIC] REVIEW VALUES IN THE FORM'
}

ELG_PATTERNS = {
    "dual_pattern": r'\bdual\b',
    "nj_family_pattern" : r'\b(nj\s*family|familycare)\b',
    "encore_nj_pattern": {
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
    },

    "geha" : {
        're' : r"(?i)^(Government Employee Health|GEHA.*(Connection)?( Dental)?( Federal)?)$",
        'payor' : "39026"
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

winAction = WinAction()
imgAction = ImgAction()
_client = iv_config['project_name']

### Get selectors dictionary
schema = loadJson(os.path.join(base_path,'DRselectors.json'))
schema = get_info(schema,"DE_V1143",def_value = {})
init(_winAction=winAction, _schema=schema)
wins = get_info(schema,"Dentrix_Enterprise",def_value = {})
carriers_regex = {}

def setLog(log):
    SetVar("log", GetVar("log") + log)


def update_log_wrapper(log):
    return lambda: SetVar("log", GetVar("log") + log)


def fail_writeback_status(status = None):
    if not status:
        SetVar("writeback_status", "Error")
    else:
        SetVar("writeback_status", status)
        gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!T{gpvars('index')}", [[status]])


# This decorator can be placed in utils.py
def handle_exceptions(*error_handlers):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                print_log(ERROR,f"An exception occurred in function '{func.__name__}': {str(e)}")
                for handler in error_handlers:
                    handler()
                raise e
        return wrapper
    return decorator


###### processes for coverage table ######

def exist_click(selector):
    exist = winAction.waitObject(selector)
    if exist == True:
        winAction.click(selector)
    return exist


@handle_exceptions(update_log_wrapper("Exeption in clear payment table|"))
def clear_payment_table():
    iv_config = eval(GetVar("iv_config"))
    service = 'clear_table'
    if service in iv_config['input_wrapper_services']:
        if iv_config['input_wrapper_services'][service]:
            openWin("famFile > insInfo")
            if winAction.windowScope(schema["_WS_family_file"]):
                winAction.click(schema["to_open_payment_table"])
                #winAction.windowScope(schema["_WS_family_file"])
                exist_click(schema["paymant_table_confirm_ok"])
                exist_click(schema["paymant_table_delete_all"])
                exist_click(schema["paymant_table_ok"])


    winAction.closeModals("Edit Updated Insurance|Dentrix Dental Systems",3)


class Window:
    def __init__(self,scope):
        self._scope = schema[scope]
        
    def scope(self):
        return winAction.windowScope(self._scope)

class Element():
    def __init__(self, selector):
        self._selector = schema[selector] if isinstance(selector, str) else selector
        self._state = ''
        self._service_validation = True

    def set_validation(self, value):
        self._service_validation = value
    
    def is_enabled(self):
        import copy
        enabled = winAction.isEnabled(copy.deepcopy(self._selector))
        return enabled

    def click(self):
        winAction.click(self._selector)

    def send_keys(self,*args, **kwargs):
        if len(args) > 0:
            winAction.sendKeys(self._selector,text=args[0]) if len(args) == 1 else winAction.sendKeys(self._selector,*args)
        else:
            winAction.sendKeys(self._selector, **kwargs)
    
    def wait_object(self, *args, **kwargs):
        if len(args) == 0 and len(kwargs) == 0:
            winAction.waitObject(self._selector)
        else:
            winAction.waitObject(self._selector,timeout=args[0]) if len(args) == 1 else winAction.sendKeys(self._selector,**kwargs)
            
    def find_children(self, **kwargs):
        return winAction.findChildren(self._selector,**kwargs)

class Checkbox(Element):
    def update(self,value):
        if self._service_validation:
            self._state = winAction.getCheckBoxState(self._selector)
            if self._state == False and value == True:
                winAction.click(self._selector)
            if self._state == True and value == False:
                winAction.click(self._selector)

class TextBox(Element):
    max_len = 15       

    def set_max_len(self, len):
        self.max_len = len
    
    def clean(self):
        # if winAction.click(self._selector,timeout=0):
        #     pyautogui.press('left', presses = self.max_len)
        #     pyautogui.press('delete', presses = self.max_len)
        winAction.setText(self._selector,text="",clean=True)

    def update(self, value):
        if self._service_validation:
            winAction.setText(self._selector,text=value,clean=True)
    
    def get_text(self, **kwargs):
        return winAction.getText(self._selector, kwargs)
            
class Button(Element):
    pass

class RadioButton(Element):
    pass

class Row(Element):
    pass

class ListControl(Element):
    pass

class ComboBox(Element):
    def update(self, value):
        winAction.sendKeys(self._selector,text=value)

class Table:
    def __init__(self):
        self._data = []
        self._selectors = []
        self._client = ""
        self._data_to_input = []
        self.columns = []
        self.columns_to_update = []
        self.version = 'Default'
        self._template = []
        self._template_columns = []

    def clear_table(self):
        import time
        winAction.windowScope(schema["_WS_family_file"])
        clear = False
        for i in range(3):
            winAction.waitObject(schema["coverage_table_clear_table"])
            clicked = winAction.click(schema["coverage_table_clear_table"])
            if clicked:
                time.sleep(3)
                clear = True if len(self.get_selectors()) == 0 else False
            if clear: break
        return clear

    def set_template(self, config_template):
        self._template = config_template[1:]
    
    def set_data_to_input(self, coverage_list):
        self._data_to_input = [self.get_columns_by_client(fila) for fila in coverage_list]

    def get_selectors(self):
        return ListControl("coverage_table").find_children(dataToFind="ListItemControl", findBy="ctrltype")
    
    def get_values_by_indexes(self, row, indexes):
        return [row[i-1] for i in indexes]

    def get_columns_by_client(self,row):
        try:
            values = self.get_values_by_indexes(row, self.columns_to_update)
            return values
        except Exception as e:
            setLog('get table columns by client')          

    def get_selector_row(self,child):
        import copy
        selector_row = copy.deepcopy(schema["coverage_table"])
        selector_row["children"].append(child)
        return selector_row
    
    def get_row_value(self, selector_row):
        import re
        value = re.split(r'\t+', selector_row["title"])
        value[1] = value[1].lstrip('-')
        value[1] = value[1].replace('.S','')
        value = [re.sub(r' {2,}', ' ', element).strip() for element in value]
        # return self.get_columns_by_client(value)
        return value
        
    def read_table(self):
        self._data, self._selectors = [], []
        selectors = self.get_selectors()
        if len(selectors) > 0:
            for selector in selectors: 
                self._data.append(self.get_row_value(selector))
                self._selectors.append(self.get_selector_row(selector))
    
    def review(self):
        Window("_WS_family_file").scope()
        self.read_table()
        return True if self._data_to_input == [self.get_columns_by_client(fila) for fila in self._data] else False
    
    def review_by_index(self, index):
        self.read_table()
        return True if self._data_to_input[index] == [self.get_columns_by_client(fila) for fila in self._data][index] else False
    
    def compare_template(self):
        Window("_WS_family_file").scope()
        self.read_table()

        matriz1 = self._template
        matriz2 = [self.get_values_by_indexes(row,self._template_columns) for row in self._data]

        # Encontrar las filas que no están en ambas matrices
        filas_no_presentes_en_matriz1 = [fila for fila in matriz1 if fila not in matriz2]
        filas_no_presentes_en_matriz2 = [fila for fila in matriz2 if fila not in matriz1]

        # Imprimir resultados
        if filas_no_presentes_en_matriz1:
            print_log(INFO,"Filas no presentes en la matriz 1:")
            for fila in filas_no_presentes_en_matriz1:
                print(fila)
        if filas_no_presentes_en_matriz2:
            print_log(INFO,"\nFilas no presentes en la matriz 2:")
            for fila in filas_no_presentes_en_matriz2:
                print(fila)
        return True if self._template == [self.get_values_by_indexes(row,self._template_columns) for row in self._data] else False
                
    def update_rows_values(self, row):
        input_row = [
            TextBox("coverage_table_beg_proc"),
            TextBox("coverage_table_end_proc"),
            TextBox("coverage_table_category"),
            TextBox("coverage_table_coverage"),
            ComboBox('coverage_table_deductible'),
            TextBox("coverage_table_copay")
        ]
        #ComboBox('coverage_table_pre_est')
        for i, element in enumerate(self.get_columns_by_client(input_row)):
            element.update(row[i])

    #@handle_exceptions(update_log_wrapper("Exception in upload table|"),fail_writeback_status)  
    def upload(self):
        import time
        error_modals_regex = "Dentrix Dental Systems"
        ins_cov = Window("_WS_family_file")
        Add = Button("coverage_table_add")
        Change = Button("coverage_table_edit")
        OK = Button("coverage_table_save")
        OK_confirm = Button("coverage_table_confirm_save")
        Select_Table = Button("coverage_table_select_table")
        Default_Coverage_Table = Button("coverage_table_default")
        OK_confirm_select_table = Button("coverage_table_select_table_confirm")
        Co_Payment_Calculations = Checkbox("coverage_table_Co-Payment_Calculations")
        Total_Fee_Co_Pay_x_Cov = RadioButton("coverage_table_Total_Fee-Co-Pay_x_Cov_%")

        #exception = eval(GetVar("exception"))
        exception = False
        if not exception:
            if len(self._data_to_input) > 0:
                ins_cov.scope()
                #previous
                prev_validations = False
                if self.version == "Default":
                    prev_validations = self.clear_table()
                elif  self.version == "Custom":
                    prev_validations = select_default_table() and self.compare_template()
                if prev_validations:
                    self.read_table()
                    for i,row in enumerate(self._data_to_input):
                        tries, correct_row  = 1, False 
                        current_row = Row(self._selectors[i]) if self.version == "Custom" else None
                        #input data
                        if self.version == "Default":
                            self.update_rows_values(row)
                            Add.click()

                            for _try in range(3):
                                if self.review_by_index(i):
                                    break
                                else:
                                    winAction.closeModals(error_modals_regex,duration=2)
                                    #retry to input
                                    if self.version == "Default":
                                        self.update_rows_values(row) 
                                        if len(self.get_selectors()) == 0:
                                            Add.click()
                                        else:
                                            Change.click() 
                        elif self.version == "Custom":
                            for _try in range(3):
                                current_row.click()
                                self.update_rows_values(row)
                                Change.click()
                                if self.review_by_index(i):
                                    current_row.send_keys('{DOWN 2}')
                                    break
                                if _try == 2:
                                    SetVar("log", GetVar("log") + "many tries update row table|")
                                
                        
                    if self.review():
                        ins_cov.scope()
                        OK.click()
                        OK_confirm.click()
                        SetVar("log", GetVar("log") + "coverage table updated|")
                    else:
                        setLog('Exception coverage table review does not match|')
                        raise Exception("coverage table review does not match")
                else:
                    setLog('Exception previous validation|')
                    raise Exception("previous validation")
            else:
                setLog('Exception coverage table empty data|')
                raise Exception("coverage table empty data")
        else:
            setLog('coverage table Copay|')
        winAction.closeModals(error_modals_regex,duration=2)

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

planElg = PlanEvaluate(plans)


@handle_exceptions(update_log_wrapper("Exception in select default table|"),fail_writeback_status)
def select_default_table():
    services = iv_config["input_wrapper_services"]["select_default_table"]
    if services["state"]:
        btn_select_table = Button('coverage_table_select_table')
        btn_select_table.click()

        selector = schema["coverage_table_default"]
        selector['children'].pop()

        tables_templates = ListControl(selector)
        tables_templates.wait_object()
        children = tables_templates.find_children(dataToFind="ListItemControl", findBy="ctrltype")

        template_name = re.compile(r'{}'.format(services["table"]))
        for child in children:
            if template_name.match(child['title']):
                t_selector = {'children':selector['children']+[child]}
                btn_template = Button(t_selector)
                btn_template.wait_object()
                btn_template.click()
                btn_confirm = Button('coverage_table_select_table_confirm')
                btn_confirm.click()
                return True
    return False



@handle_exceptions(update_log_wrapper("Exception in review overlap|"))
def review_overlap():
    services = iv_config["input_wrapper_services"]["review_overlap"]
    if services:
        openWin("famFile > insInfo > insCoverage")
        ins_cov = Window("_WS_family_file")
        ins_cov.scope()

        OK = Button("coverage_table_save")
        OK_confirm = Button("coverage_table_confirm_save")
        Add = Button("coverage_table_add")

        OK.click()

        message_confirm = winAction.manageAlert("^Dentrix Dental Systems", "^You have just edited coverage information", "OK", 3)
        if not message_confirm:
            is_overlaping = winAction.manageAlert("^Dentrix Dental Systems", ".*The procedure code ranges overlap", "OK", 3)
            if is_overlaping:
                table = Table()
                table.clear_table()
                table.columns_to_update = [1,2,3,4]
                table.update_rows_values(['D0100','D0101','Overlap','100'])

                Add.click()
                OK.click()
                OK_confirm.click()
                SetVar("log", GetVar("log") + "overlap fix Done|")
        winAction.closeModals("Insurance Coverage.*|Insurance Information",duration=2)
        SetVar("log", GetVar("log") + "overlap reviewed|")
        return True

def generate_table_base_category(template,rule):
    table = []
    template = template[1:]
    for row in template:
        category = row[2].lower()
        if rule == 'ortho_and_implant':
            if 'ortho' in category or 'implant' in category:
                table.append(row + ["0", "S", "Empty"])
            else:
                table.append(row + ["100", "S", "Empty"])
        elif rule == 'zero': 
            table.append(row + ["0", "S", "Empty"])
        elif rule == 'hundred':  
            table.append(row + ["100", "S", "Empty"])
    return table


@handle_exceptions(update_log_wrapper("Exception setting coverage table|"),fail_writeback_status)
def coverage_table():
    import re
    practice = data_supplies['practice']
    template = iv_config['write_back_rules']['template']
    bk = {}
    coverage_table = []
    nomenclature_plan = eval(gpvars("nomenclature_plan"))
    plan_results = planElg.evaluate(
                        data_supplies,
                        iv_config,
                        ELG_PATTERNS
                        )
    if any(plan_results.get(k, False) for k in [
    "dq_matituck_plan",
    "dq_fishkill_plan",
    "dq_catskill_plan"
    ]):
        coverage_table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_3'])
        bk = {'FeeScheduleName': 'Dentaquest'}

    elif any(plan_results.get(k, False) for k in [
    "uhccp_plan",
    "uhccp_dual_plan",
    "uhccp_nj_plan",
    "uhccp_middleisl",
    "caresorce_all_plan"
    ]):
        coverage_table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_1']) 
        bk = {'FeeScheduleName': 'United HealthCare'}

    elif plan_results.get("csea_all_plan", False):
        coverage_table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_3'])
        bk = {'FeeScheduleName': 'Csea'}

    elif plan_results.get("hmo_uhc_plan", False):
        coverage_table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_3'])
        bk = {'FeeScheduleName': 'DHMO'}

    elif nomenclature_plan:
        coverage_table = eval(GetVar("coverage_list"))
        bk = {'FeeScheduleName': 'nomenclature_plan'}

    else:
        bk = eval(GetVar("bk"))
        if ('HMO' in bk['FeeScheduleName'].upper() and re.search(static_regex['re_uhc'],data_supplies['carrier_name'],re.IGNORECASE)):
            coverage_table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_3'])
            bk = eval(GetVar("bk"))
        else:
            coverage_table = eval(GetVar("coverage_list"))

            isNotLivingstonAndOON = True if data_supplies['practice'].lower() != 'livingston' and bk['PatientOON'] == 'n' and bk['OutofNetworkNO'] == 'n' else False
            isLivingstonAndOON = True if data_supplies['practice'].lower() == 'livingston' and bk['PatientOON'] == 'n' else False

            if isNotLivingstonAndOON:
                coverage_table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_2'])
                bk = eval(GetVar("bk"))
            elif isLivingstonAndOON:
                coverage_table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_2'])
                bk = eval(GetVar("bk"))

    if not ('HMO' in bk['FeeScheduleName'].upper() and not re.search(static_regex['re_uhc'],data_supplies['carrier_name'],re.IGNORECASE)):
        if coverage_table != []:
            service = 'update_coverage_table'
            template = iv_config['write_back_rules']['template']
            update_table = iv_config['write_back_rules']['update_table']

            if service in iv_config['input_wrapper_services']:
                if iv_config['input_wrapper_services'][service]:
                    openWin("famFile > insInfo > insCoverage")
                    table = Table()
                    table._client = iv_config['project_name']

                    # config
                    table.columns = update_table['table_columns']
                    if 'version' in update_table:
                        table.version = update_table['version']
                    table.columns_to_update = update_table['columns_to_update']
                    table._template_columns = update_table['template_columns']
                    
                    table.set_data_to_input(coverage_table)
                    table.set_template(template)

                    already_updated = table.review()
                    if already_updated == True:
                        SetVar("log", GetVar("log") + "coverage table already updated|")
                    else:
                        table.upload()
    else:
        SetVar("log", GetVar("log") + "coverage table HMO plan not updated|")
    winAction.closeModals("Insurance Coverage.*|Insurance Information",duration=2)

def is_date_formated(date_str):
    from datetime import datetime
    try:
        datetime.strptime(date_str, "%m/%d/%Y")
        return True
    except ValueError:
        return False

def iso_date_formated(date_str):
    from datetime import datetime
    try:
        if bool(datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")): 
            return True
    except ValueError:
        return False

def iso_simple_formated(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def update_member_and_relationship():
    from difflib import SequenceMatcher as SM
    time_to_exist = 1.25
    bk = eval(GetVar("bk"))
    
    relationship = data_supplies["relationship"]
    if data_supplies['type_of_verification'] == "ELG":
        member_id = data_supplies["member_id"] if data_supplies["member_id"].lower() != "empty" and data_supplies["member_id"].replace("-","").replace(" ","") != "" else False
    elif data_supplies["type_of_verification"] == "FBD":
        flag= eval(GetVar('Amounts'))
        if flag:
            member_id = bk["MemberID"] if bk["MemberID"].lower() != "empty" and bk["MemberID"].replace("-","").replace(" ","") != "" else False
        else:
            member_id = data_supplies["member_id"] if data_supplies["member_id"].lower() != "empty" and data_supplies["member_id"].replace("-","").replace(" ","") != "" else False
    window = ui.WindowControl(RegexName="^Insurance Information")
    member_id_pms = winAction.getText(get_info(schema,"CS_Get_MemberId"), 5 )
    
    if member_id:
        value1 = member_id.replace(" ","").replace("-","") 
        value2 = member_id_pms.replace(" ","").replace("-","") 
        member_id_percentage = int(SM(None,value1,value2).ratio()*100)
        if member_id_percentage < 80:
            # control = ui.EditControl(searchFromControl=window, RegexName="Subscriber Id #")
            # if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(member_id)
            
            if relationship.lower() == "self":
                control = ui.RadioButtonControl(searchFromControl=window,AutomationId="22" ,RegexName='Self')
                if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
            elif relationship.lower() == "spouse":
                control = ui.RadioButtonControl(searchFromControl=window,AutomationId="23" ,RegexName='Spouse')
                if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
            elif relationship.lower() == "child":
                control = ui.RadioButtonControl(searchFromControl=window,AutomationId="24" ,RegexName='Child')
                if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
            elif relationship.lower() == "other":
                control = ui.RadioButtonControl(searchFromControl=window,AutomationId="25" ,RegexName='Other')
                if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
            # setLog(f"Member id was updated from {member_id_pms} to {member_id}|")
    else:
        if not member_id_pms:
            setLog("The patient dont have member id in the PMS")

def last_day_next_month(fecha):
    from datetime import datetime, timedelta
    date_obj = datetime.strptime(fecha, '%Y-%m-%d')
    
    if date_obj.month == 12:
        first_day_next_month = datetime(date_obj.year + 1, 1, 1)
    else:
        first_day_next_month = datetime(date_obj.year, date_obj.month + 1, 1)
    
    last_day_next_month = first_day_next_month + timedelta(days=31)
    last_day_next_month = last_day_next_month.replace(day=1) - timedelta(days=1)
    return last_day_next_month.strftime('%m/%d/%Y')

def is_leap(year):
    return (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))

def february_leap(fecha):
    try:
        fecha = datetime.strptime(fecha,'%m/%d/%Y')
        if fecha.month == 2:
            if fecha.day == 29 and not is_leap(fecha.year):
                return False
            return True
        return False
    
    except ValueError:
        return False

import re
from datetime import datetime

def parse_date(date_str):
    """Convierte varias representaciones de fecha a formato MM/DD/YYYY."""
    formats = [
        "%m/%d/%Y",           # formato americano
        "%Y-%m-%d",           # ISO simple
        "%Y-%m-%dT%H:%M:%S"   # ISO con tiempo
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%m/%d/%Y")
        except ValueError:
            continue
    return ""  # si no coincide con ningún formato válido


def extract_effective_and_term_dates(verification_status):
    regex_date = r"(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|N/A|-|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
    match = re.search(rf"{regex_date}\s*-\s*{regex_date}", verification_status)

    effectivedate, term_date = "", ""

    if match:
        raw_effective = match.group(1).strip()
        raw_term = match.group(2).strip()

        effectivedate = parse_date(raw_effective)
        term_date = parse_date(raw_term)

    print(f"*********effectivedate: {effectivedate}, term_date: {term_date}")
    return effectivedate, term_date

 

def date_validation(date_str) -> bool:
    if not date_str:
        return True   
    try:
        actual_date = datetime.strptime(date_str, "%d/%m/%Y")
        actual_year = datetime.now().year

        return actual_date.year != actual_year

    except ValueError:
        return False



@handle_exceptions(update_log_wrapper("Exception in ELG dates|"),fail_writeback_status)
def elegibility_dates_and_checkboxs2():
    import re 
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    bk = eval(GetVar("bk")) if GetVar("bk") != "" else {}
    # bk = {}
    todays_date = datetime.now()
    Value_last_eligibility_check, Value_eligibility_start, Value_eligibility_end, effectivedate, term_date= '', '', '', '', ''
    verification_status = data_supplies["verification_status"]
    # verification_status = "Inactive | Erie County Individual Plan(plan brochure)| 08/01/2025 - N/A"

    ins_info = Window("_WS_family_file")
    
    if data_supplies["type_of_verification"] == "ELG":
        effectivedate,term_date = extract_effective_and_term_dates(verification_status)

        effectivedate = parse_date(effectivedate)
        term_date = parse_date(term_date)

        print(f"*********effectivedate: {effectivedate} , term_date: {term_date}")
        
    if bk:
        regex_date = r"(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|N/A|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
        if 'EffectiveDate' in bk: 
            get_date = re.search(r"{}".format(regex_date),bk["EffectiveDate"])
            if get_date: 
                effectivedate = get_date.group(1).strip()
            else:
                setLog(f'Exception in EffectiveDate, the value {bk["EffectiveDate"]} is not a date|')
                raise Exception("Exception in EffectiveDates value")

        year_calendar = bk['YearCalendar'].strip()
        year_fiscal = bk['YearFiscal'].strip()
        if year_calendar == 'n' or year_fiscal== 'n':
            if year_calendar == 'n':
                from datetime import datetime
                current_year = datetime.now().year
                term_date = datetime(current_year, 12, 31).strftime('%m/%d/%Y')
            elif year_fiscal== 'n':
                effective_date = bk['EffectiveDate'].strip()
                effective_date_str = effective_date
                effective_date = datetime.strptime(effective_date_str, '%m/%d/%Y')
                next_year = effective_date.year + 1
                is_valid_feb_29 = february_leap(effective_date_str) and effective_date.day == 29
                day = effective_date.day
                month = effective_date.month
                current_year = datetime.now().year
                try:
                    term_date = (datetime(current_year, month, day) + relativedelta(months=12)).strftime('%m/%d/%Y')
                except ValueError:
                    if is_valid_feb_29 and not is_leap(next_year):
                        term_date = datetime(next_year, 2, 28).strftime('%m/%d/%Y')
                    else:
                        raise
        else: 
            setLog('Exception YearCalendar and YearFiscal unchecked|')
            raise Exception("Exception YearCalendar and YearFiscal unchecked")
        print_log(SUCCESS,f"TERM_DATE{term_date}")
    else:

        effectivedate,term_date = extract_effective_and_term_dates(verification_status)

        effectivedate = parse_date(effectivedate)
        term_date = parse_date(term_date)
        print(f"*********effectivedate: {effectivedate} , term_date: {term_date}")


    # Antes: if was_updated == False:
    if not term_date or effectivedate == term_date:
        term_date = last_day_next_month(GetVar("sheet"))
    print_log(INFO,f'term_date last: {term_date}')
    Value_last_eligibility_check, Value_eligibility_start, Value_eligibility_end = todays_date.strftime('%m/%d/%Y'), effectivedate, normalizar_fecha(term_date)

    conf_valid = iv_config['input_wrapper_services']['update_eligibility_dates']
    checkbox_not_elegible = Checkbox("checkbox_not_elegible")
    checkbox_not_elegible.set_validation(conf_valid['not_eligibility_box'])
    last_eligibility_check = TextBox("last_elegibility_check")
    last_eligibility_check.set_validation(conf_valid['last_eligibility_check'])
    plan_effective_date = TextBox("plan_effective_date")
    plan_effective_date.set_validation(conf_valid['plan_effective_date'])
    eligibility_start = TextBox("elegibility_start")
    eligibility_start.set_validation(conf_valid['eligibility_start'])
    eligibility_end = TextBox("elegibility_end")
    eligibility_end.set_validation(conf_valid['eligibility_end'])
    assignment_of_benefits = Checkbox('checkbox_assignment_of_benefits')

    dates_updated = False
    openWin("famFile > insInfo")
    ins_info.scope()

    log = []
    dates_updated = False
    status = verification_status.lower()

    #to review the dates 01/12/2026
    review_date = GetVar("review_date")

    # --- Actualización base ---
    # condition for lastelgdate and review 
    if review_date and date_validation(last_eligibility_check.get_text()):

        last_eligibility_check.update(Value_last_eligibility_check)
        log.append(f"last_check → {Value_last_eligibility_check}")
        dates_updated = True
        
        # --- HMO RULE ---
        set_oon = GetVar("set_oon")
        if not set_oon in ["ERROR_NOT_VAR",""] and set_oon:
            checkbox_not_elegible.update(True)
            log.append(f"chk_not_elg → True (DUE HMO PRACTICE:{data_supplies['practice']} ISNT CLINICS LIST)")
            dates_updated = True

        # --- Estado inactivo ---
        elif 'inactive' in status:
            checkbox_not_elegible.update(False)
            if Value_eligibility_end:
                if eligibility_end.is_enabled():
                    eligibility_end.update(Value_eligibility_end)
                    log.append(f"elig_end → {Value_eligibility_end}")
                dates_updated = True
            checkbox_not_elegible.update(True)
            log.append("chk_not_elg → True (inactive)")

        # --- Otros estados ---
        else:
            checkbox_not_elegible.update(False)
            log.append("chk_not_elg → False")

            if Value_eligibility_start:
                plan_effective_date.update(Value_eligibility_start)
                eligibility_start.update(Value_eligibility_start)
                log.append(f"elig_start → {Value_eligibility_start}")
                dates_updated = True

            if 'active' in status or 'max out' in status:
                if eligibility_end.is_enabled():
                    eligibility_end.update(Value_eligibility_end)
                    log.append(f"elig_end → {Value_eligibility_end}")
                dates_updated = True
            else:
                if eligibility_end.is_enabled():
                    eligibility_end.clean()
                    log.append("elig_end → clr")
                Value_eligibility_end = ''

            if 'not found' in status:
                checkbox_not_elegible.update(True)
                log.append("chk_not_elg → True (not found)")
                dates_updated = True

        # --- Mostrar log final ---
        if dates_updated:
            print("[LOG] Updates:")
            for m in log:
                print(" •", m)
        else:
            print("[LOG] No changes.")

        log_str = " , ".join(log)
        print("log_str: {}".format(log_str))


        
        update_member_relaship = iv_config['input_wrapper_services']['update_member_relationship']
        if update_member_relaship: update_member_and_relationship()

        current_log = GetVar("log")

        if not isinstance(current_log, str):
            current_log = ""

        ins_info.scope()
        winAction.click(schema["insurance_information_ok"])
        warnigng_alert_found = winAction.manageAlert('^Dentrix Family File Module', "The Primary Subscriber's birth month is not|.*will affect all other family members.*", 'Yes|OK', 5)
        winAction.manageAlert('^Dentrix Family File Module', "The Primary Subscriber's birth month is not|.*will affect all other family members.*", 'Yes|OK', 5)
        error_alert_found = winAction.manageAlert('^Dentrix Dental System|^Insurance Information$', "Invalid date|.*must be less than.*", 'OK', 3)
        if error_alert_found:
            # gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!AB{gpvars('index')}", [['Error']]) 
            raise Exception("ELG DATES ERROR")
        else:
            if dates_updated and review_date in ["ERROR_NOT_VAR",""]:
                # gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!AB{gpvars('index')}", [['Uploaded']])
                SetVar("log", current_log  + log_str + " ELG dates updated|")  
                gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!AC{gpvars('index')}", [[current_log  + log_str + " ELG dates updated|"]])
            
            elif review_date != "ERROR_NOT_VAR" and review_date:
                gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!Q{gpvars('index')}", [[log_str + " ELG dates updated in the review|"]])        
            
            else:
                # gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!AB{gpvars('index')}", [['Uploaded|Remains unchanged']])
                SetVar("log", current_log  + "ELG dates Remains unchanged|")   
        
        winAction.closeModals("Dentrix Dental Systems|Insurance Information", duration=1)

        openWin("famFile > insInfo")
        ins_info.scope()
        date_error = False
        if Value_last_eligibility_check:
            if last_eligibility_check.get_text() != Value_last_eligibility_check:
                date_error == True
        if Value_eligibility_start:
            if eligibility_start.get_text() != Value_eligibility_start:
                date_error == True
        if Value_eligibility_end:
            if eligibility_end.get_text() != Value_eligibility_end:
                date_error == True
        
        if date_error:
            # gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!AB{gpvars('index')}", [['Error']]) 
            raise Exception("ELG DATES ERROR")
        else:
            print("**dates review ok")
        winAction.closeModals("Dentrix Dental Systems|Insurance Information", duration=1)
    else:
        log.append(f"last_check → {last_eligibility_check.get_text()}")
        log.append(f"elig_start → {eligibility_start.get_text()}")
        log.append(f"elig_end → {eligibility_end.get_text()}")
        log_str = " , ".join(log)
        gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!Q{gpvars('index')}", [[log_str + " ELG dates already updated|"]])
        winAction.closeModals("Dentrix Dental Systems|Insurance Information", duration=1)
        print("dates already updated: {}".format(log_str))

def normalizar_fecha(fecha_str):
    from datetime import datetime

    if not fecha_str or not isinstance(fecha_str, str) or not fecha_str.strip():
        return None

    fecha_str = fecha_str.strip()
    formatos = ("%m/%d/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S")

    for fmt in formatos:
        try:
            fecha = datetime.strptime(fecha_str, fmt)
            break
        except ValueError:
            fecha = None

    if not fecha:
        return None

    if str(fecha.year).endswith("99"):
        return "12/31/2099"

    return fecha.strftime("%m/%d/%Y")


@handle_exceptions(update_log_wrapper("Exception in ELG dates|"),fail_writeback_status)
def elegibility_dates_and_checkboxs():
    # def NEW_elegibility_dates_and_checkboxs_respetando_no_fecha():
    import re 
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    bk = eval(GetVar("bk")) if GetVar("bk") != "" else {}
    verification_status = data_supplies["verification_status"]
    carrier_name = data_supplies['carrier_name']

    todays_date = datetime.now()
    Value_last_eligibility_check, Value_eligibility_start, Value_eligibility_end, effectivedate, term_date = '', '', '', '', ''

    ins_info = Window("_WS_family_file")    

    # --- Extraer fechas ---
    if bk:
        regex_date = r"(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|N/A|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
        if 'EffectiveDate' in bk: 
            get_date = re.search(r"{}".format(regex_date), bk["EffectiveDate"])
            if get_date: 
                effectivedate = get_date.group(1).strip()
            else:
                setLog(f'Exception in EffectiveDate, the value {bk["EffectiveDate"]} is not a date|')
                raise Exception("Exception in EffectiveDates value")

        year_calendar = bk['YearCalendar'].strip()
        year_fiscal = bk['YearFiscal'].strip()
        if year_calendar == 'n' or year_fiscal == 'n':
            if year_calendar == 'n':
                current_year = datetime.now().year
                term_date = datetime(current_year, 12, 31).strftime('%m/%d/%Y')
            elif year_fiscal == 'n':
                effective_date = bk['EffectiveDate'].strip()
                effective_date_obj = datetime.strptime(effective_date, '%m/%d/%Y')
                next_year = effective_date_obj.year + 1
                is_valid_feb_29 = february_leap(effective_date) and effective_date_obj.day == 29
                day = effective_date_obj.day
                month = effective_date_obj.month
                current_year = datetime.now().year
                try:
                    term_date = (datetime(current_year, month, day) + relativedelta(months=12)).strftime('%m/%d/%Y')
                except ValueError:
                    if is_valid_feb_29 and not is_leap(next_year):
                        term_date = datetime(next_year, 2, 28).strftime('%m/%d/%Y')
                    else:
                        raise
        else: 
            setLog('Exception YearCalendar and YearFiscal unchecked|')
            raise Exception("Exception YearCalendar and YearFiscal unchecked")
        print_log(SUCCESS, f"TERM_DATE {term_date}")
    else:
        # ELG sin bookmarks
        effectivedate, term_date = extract_effective_and_term_dates(verification_status)

    # --- Normalizar fechas solo si son válidas ---
    parsed_effectivedate = parse_date(effectivedate)
    parsed_term_date = parse_date(term_date)

    Value_last_eligibility_check = todays_date.strftime('%m/%d/%Y')
    Value_eligibility_start = parsed_effectivedate if parsed_effectivedate else None
    Value_eligibility_end = normalizar_fecha(parsed_term_date) if parsed_term_date else None

    # CONTROLES UI
    conf_valid = iv_config['input_wrapper_services']['update_eligibility_dates']

    checkbox_not_elegible = Checkbox("checkbox_not_elegible")
    checkbox_not_elegible.set_validation(conf_valid['not_eligibility_box'])

    last_eligibility_check = TextBox("last_elegibility_check")
    last_eligibility_check.set_validation(conf_valid['last_eligibility_check'])

    plan_effective_date = TextBox("plan_effective_date")
    plan_effective_date.set_validation(conf_valid['plan_effective_date'])

    eligibility_start = TextBox("elegibility_start")
    eligibility_start.set_validation(conf_valid['eligibility_start'])

    eligibility_end = TextBox("elegibility_end")
    eligibility_end.set_validation(conf_valid['eligibility_end'])

    start_date = parse_date(Value_eligibility_start) if Value_eligibility_start else None
    end_date = parse_date(Value_eligibility_end) if Value_eligibility_end else None

    # ABRIR VENTANA DE NUEVO
    openWin("famFile > insInfo")
    ins_info = Window("_WS_family_file")
    ins_info.scope()

    # REINICIAR LOG Y FLAGS
    log = []
    dates_updated = False
    status = verification_status.lower()
    inactive_status = 'inactive' in status
    
    regex_types = get_regex_for_types()
    is_fbd_payer = bool(re.search(regex_types["FBD"], carrier_name))

    # --- LÓGICA DE ELEGIBILIDAD ---
    checkbox_not_elegible.update(False)
    log.append("chk_not_elg → False")

    if not inactive_status and is_fbd_payer and last_eligibility_check.is_enabled():
        last_eligibility_check.update(Value_last_eligibility_check)
        log.append(f"last_check → {Value_last_eligibility_check}")

    dates_are_valid = True
    if start_date and end_date and start_date > end_date:
        dates_are_valid = False
        log.append("invalid dates (start > end)")

    # Eligibility start → actualizar solo si hay fecha válida
    if not inactive_status and dates_are_valid and Value_eligibility_start and eligibility_start.is_enabled():
        eligibility_start.update(Value_eligibility_start)
        plan_effective_date.update(Value_eligibility_start)
        dates_updated = True
        log.append(f"elig_start → {Value_eligibility_start}")

    # Eligibility end → actualizar solo si hay fecha válida
    if not inactive_status and dates_are_valid and ('active' in status or 'max out' in status) and Value_eligibility_end:
        if eligibility_end.is_enabled():
            eligibility_end.update(Value_eligibility_end)
            dates_updated = True
            log.append(f"elig_end → {Value_eligibility_end}")
    else:
        # limpiar solo si realmente es campo activo y tenía fecha
        if not inactive_status and eligibility_end.is_enabled() and Value_eligibility_end:
            eligibility_end.clean()
            log.append("elig_end → clr")

    # INACTIVE → marcar checkbox al final
    if inactive_status:
        checkbox_not_elegible.update(True)
        log.append("chk_not_elg → True (inactive)")

    log_str = " , ".join(log)
    print("log_str: {}".format(log_str))

    # Actualizar miembro
    update_member_relaship = iv_config['input_wrapper_services']['update_member_relationship']
    if update_member_relaship:
        update_member_and_relationship()

    current_log = GetVar("log")
    if not isinstance(current_log, str):
        current_log = ""

    # GUARDAR + ALERTAS
    ins_info.scope()
    winAction.click(schema["insurance_information_ok"])
    winAction.manageAlert('^Dentrix Family File Module', "The Primary Subscriber's birth month is not|.*will affect all other family members.*", 'Yes|OK', 5)
    error_alert_found = winAction.manageAlert('^Dentrix Dental System|^Insurance Information$', "Invalid date|A Subscriber ID must|.*must be less than.*", 'OK', 3)

    if error_alert_found:
        raise Exception("ELG DATES ERROR")
    else:
        review_date = GetVar("review_date")
        if dates_updated and review_date in ["ERROR_NOT_VAR", ""]:
            setLog(f" {log_str} ELG dates updated|") 
        elif review_date != "ERROR_NOT_VAR" and review_date:
            setLog(f" {log_str} ELG dates updated in the review|")       
        else:
            setLog(f" ELG dates Remains unchanged|")

    winAction.closeModals("Dentrix Dental Systems|Insurance Information", duration=1)

@handle_exceptions(update_log_wrapper("Exception in verified employer|"),fail_writeback_status)
def verified_employer():
    print_log(SUCCESS,"VERIFIED EMPLOYER")
    global get_info,data_supplies,iv_config,create_employer,ut
    cont = 0
    employer_from_site = ""
    found_employer = False
    flag = iv_config['input_wrapper_services']['employer_process']['verified_employer']
    plan_results = planElg.evaluate(data_supplies, iv_config, ELG_PATTERNS )
    
    if plan_results['hmo_uhc_plan']:
        info = data_supplies["verification_status"].split("|")[1].split('-')
        groupNameSite = '-'.join(info[1:-1]).strip()[:31].strip().replace("*","").replace("`","'").strip()
        employer_from_site = groupNameSite if groupNameSite else False

    elif plan_results['csea_all_plan'] and re.search(static_regex["csea_reg"],data_supplies['carrier_name'],re.IGNORECASE):
        employerCsea = data_supplies['verification_status']
        matchcsea = re.search(r'\b(Dental|Plan)\b', employerCsea,re.IGNORECASE)
        if matchcsea:
            employerCsea = employerCsea[:matchcsea.start()].strip()
            employer_from_site = employerCsea.upper().split("|")[1].strip()
        else:
            return False
        
    elif plan_results['dq_fishkill_plan'] or plan_results['dq_catskill_plan']:
        employer_from_site = data_supplies['verification_status'].split("|")[1].strip()[:31].replace("*","").replace("`","'").strip()
        employer_from_site = employer_from_site if not is_number(employer_from_site) else "EMPTY"
  
    else:
        elg_plan = any(plan_results.get(k, False) for k in [
            "dq_matituck_plan",
            "uhccp_plan",
            "uhccp_dual_plan",
            "uhccp_nj_plan",
            "caresorce_all_plan",
            "uhccp_middleisl",
            "liberty_mattituck_plan",
        ])
      
        employer_from_site = eval(GetVar('general_info'))['Employer'].strip()[:31].strip().replace("*","").replace("`","'").strip() if not elg_plan else "EMPTY"

    if flag and employer_from_site:
        winAction.windowScope(get_info(wins,"_WS_office_manager",def_value= "empty"),10)
        winAction.click(get_info(schema,"verified_employer._CS_maintenance_option"), 5 , 'SIMPLE')
        winAction.click(get_info(schema,"verified_employer._CS_reference_option"), 5 , 'SIMPLE')
        winAction.click(get_info(schema,"verified_employer._CS_employer_option"), 5 , 'SIMPLE')
        winAction.setText(get_info(schema,"verified_employer._CS_txt_search_employer"),5,employer_from_site)
        winAction.click(get_info(schema,"verified_employer._CS_btn_search_employer"),5,"DOUBLE")
        table_selector = get_info(schema,"extract_ins._GT_employer_tbl")
        employers_table = winAction.findChildren(table_selector, 10, "ListItemControl", "ctrltype")
        if len(employers_table)>0:
            while cont < len(employers_table) and not found_employer:
                employer_row = employers_table[cont]
                cont += 1
                if employer_row['title'].lower().strip() == employer_from_site.lower().strip():
                    found_employer = True
            if found_employer:
                winAction.closeModals("Employer Maintenance",3)
            else:
                create_employer(employer_from_site)
                winAction.closeModals("Employer Maintenance",3)
        else:
            winAction.manageAlert('^Dentrix Family File Module', "No matches found.", 'OK', 3)
            create_employer(employer_from_site)
            winAction.closeModals("Employer Maintenance",3)
    else:
        note = f"Employer name it is a empty value review form with QA|"
        setLog(note)
        return False
        raise Exception(f"Employer name it is a empty value review form with QA|")
    return employer_from_site if employer_from_site else None


@handle_exceptions(update_log_wrapper("Exception employer not created|"))
def create_employer(employer_name :str):
    global get_info
    flag = iv_config['input_wrapper_services']['employer_process']['create_employer']
    if flag:
        winAction.click(get_info(schema,"verified_employer._CS_new_employer"),5,"SIMPLE")
        winAction.setText(get_info(schema,"verified_employer._CS_new_name_employer_txt"),5,employer_name)
        winAction.click(get_info(schema,"verified_employer._CS_save_employer"),5,"SIMPLE")
        note = f"|Employer name : {employer_name} was created"
        setLog(note)
        
@handle_exceptions(update_log_wrapper("Exception in no_create_plan_report|"))        
def no_create_plan_report(_employer="Empty"):
    global get_info, data_supplies
    import os
    import pandas as pd
    from datetime import datetime, timedelta

    # Variables del sistema
    sheet = GetVar("sheet")
    base_pathP = GetVar("base_pathP")
    bk = eval(GetVar("bk")) if GetVar("bk") != "" else {}
    fee_schedule = bk['FeeScheduleName'] if bk and bk['FeeScheduleName'] else 'Empty'
    current_log = GetVar("log")

    # Carpeta base de reportes por usuario
    carpeta = os.path.join(base_pathP, 'no_created_plan_reports_by_user')
    os.makedirs(carpeta, exist_ok=True)

    # Usuario actual del sistema
    try:
        usuario = os.getlogin()
    except Exception:
        usuario = "unknown_user"

    # Fecha de hoy
    hoy = datetime.today().strftime('%Y-%m-%d')

    # Crear subcarpeta con la fecha
    carpeta_fecha = os.path.join(carpeta, hoy)
    os.makedirs(carpeta_fecha, exist_ok=True)

    # Ruta del archivo final
    archivo_usuario = os.path.join(carpeta_fecha, f'report_{hoy}__{usuario}.xlsx')

    # Crear dict con datos
    paciente = {
        'practice': data_supplies['practice'],
        'carrier_name': data_supplies['carrier_name'],
        'patient_id': data_supplies['patient_id'],
        'patient_first_name': data_supplies['patient_first_name'],
        'patient_last_name': data_supplies['patient_last_name'],
        'type_of_verification': data_supplies['type_of_verification'],
        'appointment date': sheet,
        'fee_schedule': fee_schedule,
        'employer': _employer,
        'log': current_log
    }

    # Cargar o crear DataFrame
    if os.path.exists(archivo_usuario):
        df_existente = pd.read_excel(archivo_usuario)
    else:
        df_existente = pd.DataFrame()

    nueva_fila = pd.DataFrame([paciente])

    # Eliminar duplicados si ya existe una fila igual
    if not df_existente.empty:
        df_actualizado = pd.concat([df_existente, nueva_fila], ignore_index=True)
        df_actualizado.drop_duplicates(inplace=True)
    else:
        df_actualizado = nueva_fila

    # Guardar archivo con ajuste de columnas
    with pd.ExcelWriter(archivo_usuario, engine='openpyxl') as writer:
        df_actualizado.to_excel(writer, index=False, sheet_name='Report')
        worksheet = writer.sheets['Report']
        
        for column_cells in worksheet.columns:
            max_length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
            col_letter = column_cells[0].column_letter
            worksheet.column_dimensions[col_letter].width = max_length + 2

    print(f"Paciente guardado en {archivo_usuario}")

    # Limpieza de subcarpetas antiguas
    dias_para_guardar = 3
    fecha_limite = datetime.now() - timedelta(days=dias_para_guardar)

    for subcarpeta in os.listdir(carpeta):
        ruta_subcarpeta = os.path.join(carpeta, subcarpeta)
        if os.path.isdir(ruta_subcarpeta):
            try:
                fecha_sub = datetime.strptime(subcarpeta, '%Y-%m-%d')
                if fecha_sub < fecha_limite:
                    # Borrar todos los archivos dentro y luego la carpeta
                    for archivo in os.listdir(ruta_subcarpeta):
                        os.remove(os.path.join(ruta_subcarpeta, archivo))
                    os.rmdir(ruta_subcarpeta)
                    print(f"Carpeta eliminada: {ruta_subcarpeta}")
            except ValueError:
                continue


@handle_exceptions(update_log_wrapper("Exception in merge_user_reports|")) 
def merge_user_reports():
    import os
    import pandas as pd
    from datetime import datetime

    base_pathP = GetVar("base_pathP")
    carpeta_base = os.path.join(base_pathP, 'no_created_plan_reports_by_user')
    hoy = datetime.today().strftime('%Y-%m-%d')

    # Subcarpeta con la fecha del día
    carpeta_fecha = os.path.join(carpeta_base, hoy)

    if not os.path.exists(carpeta_fecha):
        print(f"No existe la carpeta de reportes del día: {carpeta_fecha}")
        return

    archivos = [f for f in os.listdir(carpeta_fecha) if f.startswith(f'report_{hoy}__') and f.endswith('.xlsx')]

    df_combinado = pd.DataFrame()

    for archivo in archivos:
        path = os.path.join(carpeta_fecha, archivo)
        try:
            df = pd.read_excel(path)
            df['source_user'] = archivo.split('__')[1].replace('.xlsx', '')  # Para saber de quién es cada fila
            df_combinado = pd.concat([df_combinado, df], ignore_index=True)
        except Exception as e:
            print(f"Error al leer {archivo}: {e}")

    if not df_combinado.empty:
        archivo_salida = os.path.join(carpeta_base, f'combined_report_{hoy}.xlsx')
        with pd.ExcelWriter(archivo_salida, engine='openpyxl') as writer:
            df_combinado.to_excel(writer, index=False, sheet_name='Combined')
            worksheet = writer.sheets['Combined']
            for column_cells in worksheet.columns:
                max_length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
                col_letter = column_cells[0].column_letter
                worksheet.column_dimensions[col_letter].width = max_length + 2

        print(f"Reporte combinado generado: {archivo_salida}")
    else:
        print("No se encontraron archivos para combinar.")


@handle_exceptions(update_log_wrapper("Exception updating employer|"))
def update_employer(employer :str, nomenclature_plan = None):
    global get_info,data_supplies
    from time import sleep
    employer_name = employer
    app = False
    flag = iv_config['input_wrapper_services']['employer_process']['create_employer']
    cont = 0
    found_employer = False
    if flag:
        openWin("famFile")
        winAction.click(get_info(schema,"update_employer._CS_check_employer"),5,"DOUBLE")
        winAction.click(get_info(schema,"update_employer._CS_select_employer"),5,"SIMPLE")
        winAction.setText(get_info(schema,"update_employer._CS_employer_txt"),10, employer_name)
        winAction.click(get_info(schema,"update_employer._CS_employer_>>"),5,"SIMPLE")
        winAction.click(get_info(schema,"update_employer._CS_exist_employer_update"),5,"DOUBLE")
        winAction.click(get_info(schema,"update_employer._CS_employer_information_ok"),5,"SIMPLE")
        selectInsuranceType(data_supplies["ordinal"])
        winAction.click(get_info(schema,"update_employer._CD_insurance_information"),5,"DOUBLE")

        if iv_config['clinic_settings']['settings'][data_supplies['practice']]['ivf_type'].lower() == "new" and "NOT FOUND" not in data_supplies["verification_status"].upper():
            api_plan  = input_api_and_db(employer_name,nomenclature_plan)
            print_log(SUCCESS,api_plan)
            if api_plan:
                verified_api_dict = ["group_plan_name","plan_employer","plan_group_number"]
                flag_api = all(nodo in api_plan for nodo in verified_api_dict)
                if flag_api:
                    #searching and selecting plan
                    search_and_select_plan(api_plan)
                    btn_save = winAction.click(schema["insurance_information_ok"])
                    warnigng_alert_found = winAction.manageAlert('^Dentrix Family File Module', "The Primary Subscriber's birth month is not|.*will affect all other family members.*", 'Yes|OK')
                    warnigng_alert_found = winAction.manageAlert('^Dentrix Family File Module', "Changes to the Dental (Primary|Secondary) Subscriber information will affect all other family members covered under this subscriber.*", 'Yes|OK', 3)

                else:
                    setLog("Can't create new plan|")
                    no_create_plan_report(employer_name)
            else:
                no_create_plan_report(employer_name)
        else:
            selector_group = get_info(schema,"extract_ins._CS_Insurance_Information_BTN")
            ins_button = winAction.findChildren(selector_group, dataToFind="Insurance Data", findBy="title")
            if len(ins_button) > 0:
                ins_button = {"parent": selector_group['parent'], 'children': selector_group['children']+ins_button}
                winAction.click(ins_button)
                sleep(1)
                winAction.manageAlert('^Dentrix Dental Systems', "^Changes in existing insurance plan will affect existing Payment Plan charges.", 'OK', 3)

            employer_ins = winAction.getText(get_info(schema,"extract_ins._GT_extract_employer"),5)
            fee_schedule = winAction.getText(get_info(schema,"extract_ins._GT_fee_schedule_pms"),5)
            group_name_pms =winAction.getText(get_info(schema,"extract_ins._GT_extract_groupPlan"),5) 

            if employer_ins.lower().strip() != employer_name.lower().strip():
                winAction.click(get_info(schema,"update_employer._CS_employer_update_>>"),5,"SIMPLE")
                winAction.sendKeys(get_info(schema,"update_employer._CS_employer_txt"),10, employer_name)
                winAction.click(get_info(schema,"update_employer._CS_employer_>>"),5,"SIMPLE")
                table_selector = get_info(schema,"extract_ins._GT_employer_tbl")
                employers_table = winAction.findChildren(table_selector, 10, "ListItemControl", "ctrltype")
                if len(employers_table)>0:
                    while cont < len(employers_table) and not found_employer:
                        employer_row = employers_table[cont]
                        cont += 1
                        if employer_row['title'].lower().strip() == employer_name.lower().strip():
                            plan_idx = employer_row['idx']
                            employer_selector = get_info(schema,"update_employer._CS_exist_employer_update")
                            employer_selector["children"][-1]['idx'] = plan_idx
                            winAction.click(employer_selector,5,"DOUBLE")
                            found_employer = True  
                SetVar("log", GetVar("log") + f" employer updated|") 
            else: SetVar("log", GetVar("log") + f" employer already updated|")

            winAction.click(get_info(schema,"update_employer._CS_btn_insurance_information_ok"),5,"SIMPLE")
            warnigng_alert_found = winAction.manageAlert('^Dentrix Family File Module', "Changes to the Dental (Primary|Secondary) Subscriber information will affect all other family members covered under this subscriber.*", 'Yes|OK', 3)

            alert_change_plan = winAction.waitObject(get_info(schema,"update_employer._CS_change_ins_plan"),2)
            if alert_change_plan:
                winAction.click(get_info(schema,"update_employer._CS_change_ins_plan"),5,"SIMPLE")
            winAction.closeModals("Dental Insurance Plan Information",1)
            warnigng_alert_found = winAction.manageAlert('^Dentrix Family File Module', "The Primary Subscriber's birth month is not|.*will affect all other family members.*", 'Yes|OK')
        winAction.closeModals("Insurance Information",1)



@handle_exceptions(update_log_wrapper("Exception ins type|"))
def select_ins_type():
    global get_info
    ordinal = get_info(data_supplies,"ordinal", def_value = "empty")
    winAction.windowScope(get_info(wins,"_WS_Family",def_value= "empty"),10) 
    winAction.click(get_info(schema,"extract_ins._CS_Open_CBox"), 5 , 'SIMPLE')
    if ordinal.lower() == "primary":
        return winAction.click(get_info(schema,"extract_ins._CS_Primary_Option"), 5 , 'SIMPLE')
    elif ordinal.lower() == "secondary":
        return winAction.click(get_info(schema,"extract_ins._CS_Secondary_Option"), 5 , 'SIMPLE')

@handle_exceptions(update_log_wrapper("Exeption setting provider|"))
def set_provider():
    if 'select_default_provider' in iv_config['input_wrapper_services']:
        if iv_config['input_wrapper_services']['select_default_provider']['state']:
            verification_status = data_supplies["verification_status"]
            if 'max out' in verification_status.lower() or 'inactive' in verification_status.lower():
                window = ui.WindowControl(RegexName="^Patient Information")
                window.SetFocus()

                time_to_exist = 1.25

                control = ui.EditControl(searchFromControl=window, RegexName="Prov1")
                if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue("OFFINSISSU")

                prov2 = ui.EditControl(searchFromControl=window, RegexName="Prov2")
                if prov2.Exists(time_to_exist, 0):prov2.Click(simulateMove=False, waitTime=0.5)

                if winAction.manageAlert('^Dentrix Family File Module', "^Unknown Provider.*", 'OK', 3):
                    if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue("")
                    btn_prov = ui.ButtonControl(searchFromControl=window, AutomationId="55", RegexName=">>" )
                    if btn_prov.Exists(time_to_exist, 0):btn_prov.Click(simulateMove=False, waitTime=0.5)

                    selec_provider = ui.WindowControl(RegexName="^Select Provider")
                    selec_provider.SetFocus()

                    last_name = ui.EditControl(searchFromControl=window, RegexName="Last Name")
                    if last_name.Exists(time_to_exist, 0):last_name.GetPattern(ui.PatternId.ValuePattern).SetValue("ISSUE")

                    btn_search = ui.ButtonControl(searchFromControl=selec_provider,  RegexName=">>" )
                    if btn_search.Exists(time_to_exist, 0):btn_search.Click(simulateMove=False, waitTime=0.5)

                    list_item = ui.ListItemControl(searchFromControl=selec_provider, RegexName=".*Issue.*")
                    if list_item.Exists(time_to_exist, 0):list_item.DoubleClick(simulateMove=False, waitTime=0.5)

@handle_exceptions(update_log_wrapper("Exception updating otherId|"))
def update_other_id():
    win = schema["familyFile"]
    otherId = datetime.now().strftime("%m/%d/%Y_DR")
    openWin("famFile > patientInfo")
    winAction.setText(win["txtOtherId"], text=otherId)

    if "contact_info_set_deafault" in iv_config["input_wrapper_services"]:
        set_default_service= iv_config["input_wrapper_services"]["contact_info_set_deafault"]
        if set_default_service['state']:
            txt_mobile = TextBox(win["mobile"])
            txt_home_email = TextBox(win["homeEmail"])
            if txt_mobile.is_enabled():
                if txt_mobile.get_text() == "": txt_mobile.update(set_default_service["mobile_default"])
            
            # if txt_home_email.is_enabled():
            #     if txt_home_email.get_text() == "": txt_home_email.update(set_default_service["home_email_default"])

    set_provider()
    
    winAction.click(win["btnPatientInfoOk"])
    window_title = "^Dentrix Family File Module|^Invalid Email Address"
    alerts = ".*Provider.*is Inactive.*|^The Primary Subscriber's|^\nFollowing fields are required|^The patient's Prov1 must be a primary provider|^Secondary Provider|.*is inactive.|The length of the Chart # must be at least 7 characters long!|^Another|^The email address entered is in an invalid format|^Invalid SS#|^Invalid phone number"
    
    if winAction.manageAlert(window_title, alerts, 'OK', 4):
        winAction.closeModals("Patient Information")
        setLog("otherId not updated due to alert|")
        
    if winAction.manageAlert(window_title, alerts, 'OK', 4):
        winAction.closeModals("Patient Information")
        setLog("otherId not updated due to alert|")
    else:
        winAction.manageAlert('^Dentrix Family File Module', "^The patient's provider is not in the same clinic as the patient", 'Yes', 3)
        winAction.manageAlert("^Email Address Change", '^Change.*', 'OK', 4)
        setLog("otherId updated|")
    
    

@handle_exceptions(update_log_wrapper("Exception in setting coverage table note|"))
def set_coverage_table_note():
    win = schema["familyFile"]
    table_config = iv_config["input_wrapper_services"]["coverage_table_note"]
    if not table_config["state"]: return None

    note = table_config["default_note"] if "default_note" in table_config else ""
    openWin("famFile > insInfo > insCoverage")
    winAction.windowScope(win["appFamFile"])
    winAction.click(win["btnInsInfoNote"])
    winAction.setText(win["txtInsInfoNote"], text=note)
    winAction.click(win["btnInsInfoNoteOk"])
    winAction.click(win["insCoverage"]["btnOk"])
    winAction.manageAlert("^Dentrix Dental Systems", "^You have just edited coverage information", "OK", 3)
    winAction.closeModals("Insurance Information")
    setLog("note done|")

@handle_exceptions(update_log_wrapper("Exception in generate_amounts_dict|"))
def generate_amounts_dict():
    amounts_row = data_supplies['amounts']
   
    if amounts_row and amounts_row.lower() != "empty":
        amounts_values = amounts_row.split('-')
        amounts_dict = {key: ('0' if value == 'None' else
        None if value in ['N/A', '-', '', '$NaN','Not applicable'] else
        re.sub(r'[\$,]', '', value))
        for amount in amounts_values
        for key, value in [amount.split(':')]}

        for key, amount in amounts_dict.items():
            if amount:
                if amount.count('.') == 1:
                    numero = float(amount)
                    if numero.is_integer(): 
                        amounts_dict[key] = str(int(numero))
                    else:
                        amounts_dict[key] = str(numero)
                elif amount.count(".")> 1:
                    cleaned_amount = amount.replace('.', '', amount.count('.') - 1)
                    cleaned_amount = cleaned_amount.replace('.', ',')
                    numero = float(cleaned_amount.replace(',', '.'))
                    if numero.is_integer(): 
                        amounts_dict[key] = str(int(numero))
                    else:
                        amounts_dict[key] = str(numero)
                        
                normalized_amount = str(amount).strip().lower()
    
                # Caso 'unlimited'
                if normalized_amount == "unlimited":
                    amounts_dict[key] = "9999"

                # Caso cuando el valor numérico excede 9999
                else:
                    numeric_amount = float(normalized_amount.replace(',', ''))
                    if numeric_amount > 9999:
                        amounts_dict[key] = "9999"
                    else:
                        amounts_dict[key] = str(numeric_amount)
    return amounts_dict


@handle_exceptions(update_log_wrapper("Exception in setting amounts|"),fail_writeback_status)
def set_amounts(max_value=None):
    amounts = {}
    
    amounts_dict = generate_amounts_dict()
    amounts_form = eval(GetVar("Amounts"))
    win = schema["familyFile"]["insCoverage"]
    services = iv_config["input_wrapper_services"]["update_amounts"]

    if max_value is not None: 
        amounts["AnnualMaximum"] = max_value
    elif amounts_form and data_supplies['type_of_verification'] == 'FBD':
        amounts = amounts_form
    elif amounts_dict and data_supplies['type_of_verification'] == 'ELG':
        plan_results = planElg.evaluate(data_supplies, iv_config, ELG_PATTERNS )

        if re.search(r'(?i)^EMBLEM',data_supplies['carrier_name'],re.IGNORECASE) and data_supplies['type_of_verification'] == 'ELG':
            if amounts_dict['ind_ded']: amounts["Deductible"] = amounts_dict['ind_ded']
            if amounts_dict['ind_max']: amounts["AnnualMaximum"] = amounts_dict['ind_max']  
        elif plan_results["dq_fishkill_plan"] or plan_results["dq_catskill_plan"]:
            amounts["Deductible"] = '0'
            amounts["AnnualMaximum"] = '99999'  
        elif not re.search(r'(?i)^EMBLEM',data_supplies['carrier_name'],re.IGNORECASE) :
            if amounts_dict['ind_ded']: amounts["Deductible"] = amounts_dict['ind_ded']
            if amounts_dict['ind_max']: amounts["AnnualMaximum"] = amounts_dict['ind_max']
            
    def have_number(value):
        return bool(re.match(r"\d", value))

    for key in amounts:
        if not have_number(str(amounts[key]).strip()):
            if amounts[key] == 'Not applicable':
                amounts[key] = '0'
            else:
                setLog(f"THE KEY '{key}' HAS NO NUMERIC VALUE: {amounts[key]}")
                fail_writeback_status()
                raise Exception(f"La clave '{key}' no tiene un valor numérico2: {amounts[key]}")
    if amounts:
        openWin("famFile > insInfo > insCoverage")

        if services["deductible"]["annual_individual"] and 'Deductible' in amounts: 
            winAction.setText(win["txtAnnualIndividual"], text=str(amounts["Deductible"]))
            setLog(f"upd AI: {amounts['Deductible']} ")  # AI = Annual Individual

        if services["deductible"]["annual_family"] and 'Family' in amounts: 
            winAction.setText(win["txtMaxBenFamily"], text=str(amounts["Family"]))
            setLog(f"upd AF: {amounts['Family']} ")  # AF = Annual Family

        if services["maximum"]["individual"] and 'AnnualMaximum' in amounts: 
            winAction.setText(win["txtMaxBenIndividual"], text=str(amounts["AnnualMaximum"]))
            setLog(f"upd AM: {amounts['AnnualMaximum']} ")  # AM = Annual Maximum

        if services["deductible"]["preventive_annual_individual"] and "DeductiblePreventive" in amounts: 
            winAction.setText(win["txtPreventiveAnnualIndividual"], text=str(amounts["DeductiblePreventive"]))
            setLog(f"upd PI: {amounts['DeductiblePreventive']} ")  # PI = Preventive Individual

        winAction.click(win["btnOk"])
        winAction.manageAlert("^Dentrix Dental Systems", "^You have just edited coverage information", "OK", 3)
        winAction.closeModals("Insurance Information")
        setLog("amounts|")
    else:
        setLog("amounts ELG NOT FOUND")


@handle_exceptions(update_log_wrapper("Exception in setting deductibles|"),fail_writeback_status)
def set_deductible(amounts_dict = None):
    win = schema["familyFile"]["editDedBenefits"]
    services = iv_config["input_wrapper_services"]["update_amounts"]["deductibleMet"]
    amounts = {}
    if amounts_dict:
        if amounts_dict['met_ded']: amounts["Met_Deductible"] = amounts_dict['met_ded']
        if amounts_dict['amount_used']: amounts["AmountUsedToDate"] = amounts_dict['amount_used']
    else:  
        amounts = eval(GetVar("Amounts"))

    def safe_number(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0

    if amounts:
        for key, val in amounts.items():
            amounts[key] = safe_number(val)
    
    if amounts:
        openWin("famFile > insInfo")
        dedBtnEnabled = winAction.isEnabled(schema["familyFile"]["btnDedBenefits"])

        if dedBtnEnabled:
            winAction.click(schema["familyFile"]["btnDedBenefits"])
            winAction.manageAlert("^Dentrix Dental Systems", "^Changes in existing insurance plan", "OK", 3)

            if services["annual_individual"] and 'Met_Deductible' in amounts: 
                winAction.setText(win["txtAnnualIndividual"], text=str(amounts["Met_Deductible"]))
                setLog(f"upd MD: {amounts['Met_Deductible']} ")  # MD = Met Deductible

            if services["ben_individual"] and 'AmountUsedToDate' in amounts:
                winAction.setText(win["txtBenApplied"], text=str(amounts["AmountUsedToDate"]))
                setLog(f"upd BU: {amounts['AmountUsedToDate']} ")  # BU = Benefits Used

            winAction.click(win["btnOk"])

            if winAction.manageAlert("^Re-enter", ".*The Benefits Applied must be a pos.*tive number.*", "OK"):
                setLog("deductibles not updated due to alert|")
                raise Exception("upd FAIL: alert - invalid benefits value ")
            
            setLog("deductibles|")
        else:
            setLog("deds not updated btn disabled")

        winAction.closeModals("Insurance Information")


def isCoveraged():
    openWin("patientInfo")
    clinic = winAction.getText(schema["familyFile"]["txtClinic"]).strip()
    data_supplies['practice'] = data_supplies['practice'] if clinic.upper() == data_supplies['practice'] else clinic.upper()
    winAction.closeModals("Patient Information")
    if clinic in iv_config["clinic_settings"]["settings"]:
        return True
    else:
        setLog(f"{clinic} is not coveraged")
        return False


@handle_exceptions(update_log_wrapper("Exception in review benefit_renewall|"))
def review_benefit_renewall():

    def get_month_name(month_number):
        months = {
            1: "JAN",
            2: "FEB",
            3: "MAR",
            4: "APR",
            5: "MAY",
            6: "JUN",
            7: "JUL",
            8: "AUG",
            9: "SEP",
            10: "OCT",
            11: "NOV",
            12: "DEC"
        }
        return months.get(month_number)

    time_to_exist = 1.25
    bk = eval(GetVar("bk"))

    if data_supplies['type_of_verification'] == "FBD" and bk:
        benefit_renewal = ''
        if 'YearCalendar' in bk and 'YearFiscal' in bk:
            if bk['YearCalendar'] == 'n':
                benefit_renewal = 'JAN'
            elif bk['YearFiscal'] == 'n':
                benefit_renewal = get_month_name(datetime.strptime(bk['EffectiveDate'].strip(), '%m/%d/%Y').month)

        if benefit_renewal:
            openWin("famFile > insInfo")
            #open insurance plan information
            window = ui.WindowControl(RegexName="^Insurance Information")
            window.SetFocus()
            control = ui.ButtonControl(searchFromControl=window, RegexName="Insurance Data")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
            winAction.manageAlert("^Dentrix Dental Systems", "^Changes in existing insurance plan", "OK", 3)

            
            window = ui.WindowControl(RegexName="^Dental Insurance Plan Information")
            window.SetFocus()
            control = ui.EditControl(searchFromControl=window, RegexName="Benefit Renewal:")
            if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(benefit_renewal)
            control = ui.ButtonControl(searchFromControl=window, RegexName="^OK$")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)

            winAction.manageAlert("^Insurance...", "^Change Plan for All", "OK", 3)
            setLog("rev_benefit_renewal: {}|".format(benefit_renewal))
            winAction.closeModals("Insurance Information")


def get_all_regex_by_CCC():
  from module.business.carriers_manager import get_regex_for_types,get_carriers_per_client
  practice = GetVar("practice")
  SetVar("practice", iv_config['clinic_settings']['settings'][practice]['clinic_name'])
  carriers = { obj.name: obj.regex for obj in get_carriers_per_client().bots }
  SetVar("practice", practice)
  SetVar('carriers_regex',carriers)
  return practice


def read_json(json_path):
    from json import load
    try:
        with open(json_path) as json_file:
            fee_info_data = load(json_file)
    except Exception as e:
        setLog(e)
        fee_info_data = []
    return fee_info_data

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


def fee_schedule_elg(dental_plan: str, option: str):
    clinic_name = data_supplies['practice']
    route = os.path.dirname(os.path.abspath(__file__))
    # feed_data = f"{route}\\fee_data.json"
    route = os.path.dirname(os.path.abspath(__file__))

    # Usuario actual del sistema
    try:
        usuario = os.getlogin()
    except Exception:
        usuario = "unknown_user"


    feed_data = f"{route}\\fee_data\\fee_data_{usuario}.json"
    data = read_json(feed_data)

    # Diccionario de aliases para normalizar nombres de planes
    plan_name_aliases = {
        "EBF MEMBER PLUS": "EBF",
        "UCS RETIREE" : "UCS RETIRED"
        # Agregá más aliases según sea necesario
    }

    # Función interna para normalizar el nombre del plan
    def normalize_plan(plan_name):
        return plan_name_aliases.get(plan_name.upper(), plan_name).lower()

    normalized_plan = normalize_plan(dental_plan)

    if clinic_name in data:
        option_lower = option.lower()

        if option_lower == "csea":
            if 'CSEA' in data[clinic_name]:
                nodo = data[clinic_name]['CSEA']['Plan Type']

                if normalized_plan:
                    
                    nodo_plan = next(
                        (value for key, value in nodo.items() if normalized_plan and key.lower().startswith(normalized_plan.lower()) ),
                        {}
                    )
            
                    if not nodo_plan:
                        nodo_plan = next(
                        (value for key, value in nodo.items() if normalized_plan.lower() in key.lower()),
                        {}
                    )
                    
                    if nodo_plan:
                        print(nodo_plan,"REVIEW THE NODO PLAN")
                        return nodo_plan
                        
                    else:
                        setLog(f'PLAN DENTAL: {dental_plan} DOES NOT MATCH WITH ANY PLAN IN MASTER')
            else:
                setLog(f'CSEA is not in the clinic {clinic_name}')

        elif option_lower == "uhc":
            if 'United HealthCare' in data[clinic_name]:
                nodo = data[clinic_name]['United HealthCare']['Plan Type']

                nodo_plan = next(
                    (value for key, value in nodo.items() if normalized_plan in key.lower()),
                    {}
                )

                if nodo_plan:
                    return nodo_plan
                else:
                    setLog(f'PLAN DENTAL: {dental_plan} DOES NOT MATCH WITH ANY PLAN IN MASTER')
            else:
                setLog(f'United HealthCare is not in the clinic {clinic_name}')

        elif option_lower == "dq":
            if "Sunlife Dentaquest" in data[clinic_name]:
                nodo = data[clinic_name]['Sunlife Dentaquest']['Plan Type']
                plan_names = [key for key, values in nodo.items() if nodo]
                plan_found = search_dq_fishkill_plan(plan_names, dental_plan)

                if plan_found and nodo:
                    nodo_plan = nodo[plan_found]
                    return nodo_plan
                else:
                    setLog(f'PLAN DENTAL: {dental_plan} DOES NOT MATCH WITH ANY PLAN IN MASTER')
            else:
                setLog(f'Dentaquest is not in the clinic {clinic_name}')
    else:
        setLog(f'The clinic {clinic_name} is not in the master.')

    return None


@handle_exceptions(update_log_wrapper("Exception in get_elg_info|"),fail_writeback_status)
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

    if re.search(static_regex['dentaquest'], data_supplies['carrier_name'],re.IGNORECASE) and data_supplies['practice'].lower() == "catskill":
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
            dq_data = {'Smilist TIN': 1225, 'State': 'NY'}

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

    print("antess*******")
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
        if dental_plan:
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

def unlimited_value(mbi, am):
    def unlimited_(value):
        return all(char == '9' for char in str(value))
    
    if unlimited_(mbi) and unlimited_(am):
        return True
    if mbi == am:
        return True
    return False

@handle_exceptions(update_log_wrapper("Exception in handle_group_plan|"))
def handle_group_plan(new_group_plan,smilist_tin,amounts,general_info,data_response):
    from time import sleep
    fee_shid = new_group_plan.split("-")[-1] if new_group_plan else None
    plan_results = planElg.evaluate(data_supplies, iv_config, ELG_PATTERNS )
    data ={
        'practice': data_supplies['practice'],
        'employer': general_info["Employer"].strip()[:31].strip(),
        'group_number': general_info['GroupID'],
        'annual_max': amounts["AnnualMaximum"],
        'deductible_standar': amounts["Deductible"],
        'feeschedule_id': fee_shid
    }

    if len(data['group_number']) > 31 :
        if "-" in data['group_number']:
            group_id = data['group_number'].split('-')
            primer_segmento = group_id[0].lstrip('0') or '0'  
            otros_segmentos = group_id[1:]
            group_id = f'{primer_segmento}-' + '-'.join(otros_segmentos)
            data['group_number'] = group_id

    data_response = [plan_api for plan_api in data_response["data"] if plan_api["location_id"] == data["practice"]] if not plan_results["caresorce_all_plan"] else [plan_api for plan_api in data_response["data"]]
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
                    bk = eval(GetVar("bk"))
                else:
                    print_log(INFO,"****************************************COVERAGE LIST************************************")
                    coverage_list = eval(GetVar("coverage_list"))
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
                    winAction.closeModals("Insurance Coverage.*|Insurance Information",duration=2)
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
        db_insertion,exception_db = insert_query_consult(query_matrix)
        print("*** db_insertion: {}".format(db_insertion))
        if db_insertion:
            SetVar("log", GetVar("log") + "Matrix input at DB|")
            post_records = post_new_matrix(new_matrix)
            if post_records:
                SetVar("log", GetVar("log") + "Matrix input at api and DB|")
                api_plan = {
                    "carrier_name" : new_matrix['carrier'],
                    "group_plan_name": new_matrix["group_plan_name"],
                    "plan_employer": new_matrix["plan_employer"],
                    "plan_group_number": new_matrix["plan_group_number"],
                    "smilist_tin": smilist_tin
                }
                return api_plan
            else:
                SetVar("log", GetVar("log") + "Can not insert into api|")
                fail_writeback_status("Exception")
                return None

        elif exception_db and  "Cannot insert duplicate key in object" in exception_db:
            setLog(exception_text["Cannot insert duplicate key in object"])
            post_records = post_new_matrix(new_matrix)
            if post_records:
                SetVar("log", GetVar("log") + "Matrix input at api|")
                api_plan = {
                    "carrier_name" : new_matrix['carrier'],
                    "group_plan_name": new_matrix["group_plan_name"],
                    "plan_employer": new_matrix["plan_employer"],
                    "plan_group_number": new_matrix["plan_group_number"],
                    "smilist_tin": smilist_tin
                }
                return api_plan
        else:
            SetVar("log", GetVar("log") + "Can not insert into api and DB|")
            fail_writeback_status("Exception")
            return None
    else:
        return None

def clean_amounts(amounts):
    cleaned = {}
    for key, value in amounts.items():
        try:
            cleaned[key] = int(float(value))
        except (ValueError, TypeError):
            cleaned[key] = '0.00'
    return cleaned

def reorder_response(data_response):
    data_response = {key:val for key, val in data_response.items() if key not in ('createdAt', 'updatedAt', 'id','status')}
    keys = list(data_response.keys())

    carrier = data_response.pop('carrier')
    keys.insert(5, 'carrier')
    data_response = {key: data_response[key] if key != 'carrier' else carrier for key in keys}

    ortho_plan = data_response.pop('ortho_plan')
    keys.insert(93, 'ortho_plan')
    data_response = {key: data_response[key] if key != 'ortho_plan' else ortho_plan for key in keys}

    ortho_coverage = data_response.pop('ortho_coverage')
    keys.insert(94, 'ortho_coverage')
    data_response = {key: data_response[key] if key != 'ortho_coverage' else ortho_coverage for key in keys}

    ortho_max_age= data_response.pop('ortho_max_age')
    keys.insert(95, 'ortho_max_age')
    data_response = {key: data_response[key] if key != 'ortho_max_age' else ortho_max_age for key in keys}

    ortho_max_dollars= data_response.pop('ortho_max_dollars')
    keys.insert(96, 'ortho_max_dollars')
    data_response = {key: data_response[key] if key != 'ortho_max_dollars' else ortho_max_dollars for key in keys}

    data_response['ortho_plan'] = int(float(data_response['ortho_plan']))
    return data_response

def input_api_and_db(employer_name: str,nomenclature_plan = None):
    plan_results = planElg.evaluate(data_supplies, iv_config, ELG_PATTERNS )
    elg_plan = [key for key, value in plan_results.items() if value]
    elg_plan_db = True if data_supplies['type_of_verification'] == "ELG" and elg_plan else False

    if not elg_plan_db and data_supplies['type_of_verification'] == 'FBD':
        bk = eval(GetVar("bk"))
        general_info = eval(GetVar("general_info"))
        if ('HMO' in bk['FeeScheduleName'].upper() and re.search(static_regex['re_uhc'],data_supplies['carrier_name'],re.IGNORECASE)):
            amounts = {
                "AnnualMaximum": "9999",
                "Deductible": "0.00"
            }
        else:
            amounts = eval(GetVar("Amounts"))
        data_response = get_records(employer_name)
        new_group_plan, smilist_tin = get_group_name(data_supplies)
        print_log(SUCCESS,"NEW GROUP PLAN")
        print(new_group_plan)
        if new_group_plan and len(new_group_plan) == 13 and smilist_tin:
            api_plan = handle_group_plan(new_group_plan, smilist_tin, amounts, general_info, data_response)
            if api_plan:
                return api_plan
            else:
                return None
        else: 
            setLog(f'REVIEW THE NEW GROUP PLAN IS {new_group_plan}|')
            return None

    elif elg_plan_db:
        print_log(SUCCESS, "STARTING FOR ELG PLAN")
        data_response = get_records(employer_name)
        information = get_elg_info(data_supplies['carrier_name'], data_supplies['verification_status'])
        print_log(SUCCESS, "INFORMATION ELG PLAN")
        print(information)

        if information:
            new_group_plan = information['group_plan']
            general_info = {
                "Employer": information['employer'],
                "GroupID": information['group_number']
            }
            amounts = {
                "AnnualMaximum": information['annual_max'],
                "Deductible": information['deductible_standar']
            }
            amounts = clean_amounts(amounts)
            fee_shid = information['group_plan'].split("-")[-1] if information['group_plan'] else None
            print(data_response)
            api_plan = handle_group_plan(new_group_plan, fee_shid, amounts, general_info, data_response)

            if api_plan:
                return api_plan
            else:
                return None
        else:
            return None

    # 120725 start
    else:
        def change_to_ppo(plan):
            return re.sub(r'\b(?:TOTAL\s+)?DPPO\b|\bPREMIER\b', 'PPO', plan, flags=re.IGNORECASE)

        #pg.alert('review plan correction')
        print_log(SUCCESS,"NOMENCLATURE PLAN")
        print(normalize_plan)
        data_response_all = get_records(nomenclature_plan['employer_plan'])
        data_response = [plan_api for plan_api in data_response_all["data"] if plan_api["location_id"] == data_supplies['practice']]
        if data_response:
            nomenclature_group_name = "-".join(change_to_ppo(nomenclature_plan['group_name_plan']).split("-")[:3]) 
            #pg.alert(nomenclature_group_name)
            fee_schedule_plan = nomenclature_group_name.split("-")[-1]
            #pg.alert(fee_schedule_plan)
            for value in data_response:
                api_group_name = "-".join(value['group_plan_name'].split("-")[:3])

                if (value["plan_group_number"] == nomenclature_plan['group_number_plan'] 
                    and nomenclature_group_name == api_group_name
                    and value["plan_employer"].lower() == nomenclature_plan['employer_plan'].lower() 
                    and int(value["fee_schedule_id"]) == int(fee_schedule_plan)):
                    #pg.alert("FOUND PLAN IN API")
                    api_plan = {
                        "carrier_name" : value['carrier'],
                        "group_plan_name": value["group_plan_name"],
                        "plan_employer": value["plan_employer"],
                        "plan_group_number": value["plan_group_number"],
                        "smilist_tin": fee_schedule_plan
                    }

                    data_response = reorder_response(value)
                    query_matrix = tuple([value for key, value in data_response.items()])
                    print(query_matrix)
                    print("INSERTING INTO DB CLIENT")
                    #pg.alert(len(query_matrix))
                    #pg.alert(query_matrix)
                    #pg.alert("INSERTING INTO DB")
                    db_insertion,exception_db = insert_query_consult(query_matrix)
                    #pg.alert(db_insertion)
                    #pg.alert(exception_db)
                    #pg.alert("MATRIX INSERTED")
                    if db_insertion and not exception_db:
                        setLog("THE PLAN WAS INSERTED INTO DB|")
                    else:
                        for key,val in exception_text.items():
                            if key.lower() in exception_db.lower():
                                setLog(val)

                    template = iv_config['write_back_rules']['template']
                    tc = [
                        row + [str(int(float(val)*100)), "S", "Empty"]
                        for row in template[1:]
                        for key, val in data_response.items()
                        if key.startswith("D") and key == f"{row[0]}_{row[1]}"
                    ]
                    #pg.alert("tabla de cobertura")
                    #pg.alert(tc)
                    print(tc)
                    #pg.alert("api plan")
                    #pg.alert(api_plan)
                    if tc:set_var('coverage_list',tc)
                    return api_plan

        data_response = [plan_api for plan_api in data_response_all['data'] if plan_api['group_plan_name'] == nomenclature_plan['group_name_plan']]
        #pg.alert("data response ")
        #pg.alert(data_response)
        if data_response:
            data_response = reorder_response(data_response[0])
        else:
            data_response = None
            return None


        new_group_plan = "-".join(data_response["group_plan_name"].split("-")[:3])
        new_group_plan = change_to_ppo(new_group_plan)
        last_secuential_number = get_last_record() 
        last_secuential_number = fillNumberWithZero(last_secuential_number)
        new_group_plan = f"{new_group_plan}-{last_secuential_number}"
        data_response['group_plan_name'] = new_group_plan
        data_response['location_id'] = data_response['location_id'] if data_response['location_id'].upper() == data_supplies['practice'].upper() else data_supplies['practice'].upper()
        query_matrix = tuple([value for key, value in data_response.items()])
        #pg.alert(query_matrix)
        print(query_matrix)
        print("VALUES MATRIX")
        
        #pg.alert(len(query_matrix))
        #pg.alert(query_matrix)
        db_insertion,exception_db = insert_query_consult(query_matrix)
        print("*** db_insertion: {}".format(db_insertion))

        if db_insertion and not exception_db:
            post_records = post_new_matrix(data_response)
            if post_records:
                SetVar("log", GetVar("log") + "Matrix input at api and DB|")
                api_plan = {
                    "carrier_name" : data_response['carrier'],
                    "group_plan_name": data_response["group_plan_name"],
                    "plan_employer": data_response["plan_employer"],
                    "plan_group_number": data_response["plan_group_number"],
                    "smilist_tin": fillNumberWithZero(data_response['fee_schedule_id'])
                }

                template = iv_config['write_back_rules']['template']
                tc = [
                    row + [str(int(float(val)*100)), "S", "Empty"]
                    for row in template[1:]
                    for key, val in data_response.items()
                    if key.startswith("D") and key == f"{row[0]}_{row[1]}"
                ]
                if tc:set_var('coverage_list',tc)

                return api_plan
            else:
                SetVar("log", GetVar("log") + "Can not insert into api|")
                fail_writeback_status()
                return None

        else:
            for key,val in exception_text.items():
                if key.lower() in exception_db.lower():
                    if key.lower() == "Cannot insert duplicate key in object".lower():
                        setLog(val)
                        post_records = post_new_matrix(data_response)
                        if post_records:
                            SetVar("log", GetVar("log") + "INPUT PLAN AT API|")
                            api_plan = {
                                "carrier_name" : data_response['carrier'],
                                "group_plan_name": data_response["group_plan_name"],
                                "plan_employer": data_response["plan_employer"],
                                "plan_group_number": data_response["plan_group_number"],
                                "smilist_tin": fillNumberWithZero(data_response['fee_schedule_id'])
                            }

                            template = iv_config['write_back_rules']['template']
                            tc = [
                                row + [str(int(float(val)*100)), "S", "Empty"]
                                for row in template[1:]
                                for key, val in data_response.items()
                                if key.startswith("D") and key == f"{row[0]}_{row[1]}"
                            ]
                            if tc:set_var('coverage_list',tc)
                            return api_plan 
            # fail_writeback_status()
            return None  

    # 120725 end
            
def search_and_select_plan(api_plan:dict):
    time_to_exist = 1.25
    create_plan = None  
    # api_plan = {
    #     "group_plan_name" : "PPO-INN NJ070 1500-100/080/080",
    #     "employer": "Varonis",
    #     "group_number" : "204475"
    # }
    window = ui.WindowControl(RegexName="^(:?)Insurance Information")
    app= window.SetFocus()
    from time import sleep
    if app:
        abr_exception = ["ppo","enc_","ny-ppo","nj-ppo"]
        if data_supplies['groupname'].lower().strip() in abr_exception:
            # carrier >> 134 group plan 97
            control = ui.ButtonControl(searchFromControl=window, AutomationId="97", RegexName=">>")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
            sleep(90)
            # search by groupname radiobuton 912 , groupnumber 914
            control = ui.RadioButtonControl(searchFromControl=window, AutomationId="912")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
            
            # input search by groupname [Enter Group Plan Name] if you want by number [Enter Group Number]
            control = ui.EditControl(searchFromControl=window, RegexName="Enter Group Plan Name:")
            if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(api_plan['group_plan_name'])
            sleep(4)
            # btn search by groupname 
            control = ui.ButtonControl(searchFromControl=window, AutomationId="905")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
            sleep(70)
        else:
            # carrier >> 134 group plan 97
            control = ui.ButtonControl(searchFromControl=window, AutomationId="97", RegexName=">>")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)

            # search by groupname radiobuton 912 , groupnumber 914
            control = ui.RadioButtonControl(searchFromControl=window, AutomationId="912")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)

            # input search by groupname [Enter Group Plan Name] if you want by number [Enter Group Number]
            control = ui.EditControl(searchFromControl=window, RegexName="Enter Group Plan Name:")
            if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(api_plan['group_plan_name'])
            # btn search by groupname 
            control = ui.ButtonControl(searchFromControl=window, AutomationId="905")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)  
            
        # get len table plan list
        group_plan = get_info(schema,"group_plans.GT_len_group_plan")
        group_len_table = winAction.findChildren(group_plan, 10, "ListItemControl", "ctrltype")

        for idx in group_len_table:
            group_plan = {}
            # get all items in table plan list
            items_group_plan = get_info(schema,"group_plans.GT_items_group_plan")
            items_group_plan["children"][-1]['idx'] = idx['idx']

            # create dict with the info in the table
            all_items_group_plan = winAction.findChildren(items_group_plan,10,"TextControl","ctrltype")
            group_plan['carrier_name'] = all_items_group_plan[0]['title'] if 'title' in all_items_group_plan[0] else None 
            group_plan['group_plan_name'] = all_items_group_plan[1]['title'] if 'title' in all_items_group_plan[1] else None   
            group_plan['employer'] = all_items_group_plan[2]['title'] if 'title' in all_items_group_plan[2] else None
            group_plan['group_number'] = all_items_group_plan[3]['title'] if 'title' in all_items_group_plan[3] else None

            group_carrier = (group_plan.get('carrier_name') or '').lower()
            api_carrier = (api_plan.get('carrier_name') or '').lower()

            carrier_match = (
                not api_carrier
                or group_carrier in api_carrier
                or api_carrier in group_carrier
            )

            # conditional to evaluate create or not the new plan
            if (carrier_match
            and group_plan['group_plan_name'] == api_plan['group_plan_name']
            and group_plan['employer'].lower() == api_plan['plan_employer'].lower()
            and group_plan['group_number'] == api_plan['plan_group_number']):

                create_plan = False
                plan_name_click = get_info(schema,"group_plans.CS_grou_plan_name")
                items_group_plan["children"].append(plan_name_click) 
                winAction.click(items_group_plan, 5 , 'DOUBLE')
                warnigng_alert_found = winAction.manageAlert('^Dentrix Family File Module', "Changes to the Dental (Primary|Secondary) Subscriber information will affect all other family members covered under this subscriber.*", 'Yes|OK', 3)
       
                break
            
            else:
                if int(idx['idx']> 7 and idx['idx']<= len(group_len_table)):
                    # btn to scroll the table down
                    control = ui.ButtonControl(searchFromControl=window, AutomationId="DownButton")
                    if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5) 
                    create_plan = True
        else:
            create_plan = True

        if create_plan:
            # btn to create new plan
            control = ui.ButtonControl(searchFromControl=window, AutomationId="908")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5) 
            #abel's fucntion 
            print_log(SUCCESS,'***************************API DATA**************************')
            print(api_plan)
            create_new_group_plan(api_plan)

@handle_exceptions(update_log_wrapper("Exception in create new group plan|"), fail_writeback_status)
def create_new_group_plan (api_plan:dict):
    
    time_to_exist = 1.25
    
    # 120725 start
    nomenclature_plan = eval(gpvars("nomenclature_plan"))
    if nomenclature_plan and data_supplies['type_of_verification'] == 'ELG':
        new_group_plan = {
            "carrier_name" : nomenclature_plan['carrier_plan'],
            "street_address" : nomenclature_plan['street_address_plan'],
            "city" :  nomenclature_plan['city_plan'],
            "state" : nomenclature_plan['state_plan'],
            "zip" : nomenclature_plan['zip_plan'],
            "phone" : nomenclature_plan['phone_plan'],
            "last_update_date" : datetime.now().strftime("%m/%d/%Y"),
            "benefit_renewal" : nomenclature_plan['renewal_plan'],
            "payor_id" : nomenclature_plan['payor_plan'],
            "alt_code" : "ADA",
            "claim_format" : "DX2019",
            "rvu_schedule" :  "<NONE>",
            "source_of_payment" : "Commercial Insurance Co.",
            "financial_class_types" : "No Financial Class Types"
        }

    else:
        new_group_plan = get_group_plan_dict()
        if new_group_plan == 'guardian_error':
            setLog('plan no created|')
            return None


    print_log(SUCCESS,"REVIEW THE NEW GROUP PLAN")
    print(new_group_plan)
    all_fee_schedule = eval(GetVar("all_fee_schedule"))
    

    for fee in all_fee_schedule:
        if fee[0] == int(api_plan["smilist_tin"]):
            fee_schedule = fee[1].strip()
            break
        else:
            fee_schedule = False

    print_log(SUCCESS,"FEE SCHEDULE")
    print(fee_schedule)
    if new_group_plan:

        window = ui.WindowControl(RegexName="^Dental Insurance Plan Information")
        window.SetFocus()

        control = ui.EditControl(searchFromControl=window, RegexName="Carrier Name:")
        if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(new_group_plan['carrier_name'])

        control = ui.EditControl(searchFromControl=window, RegexName="Group Plan:")
        if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(api_plan['group_plan_name'])

        select_employer(api_plan['plan_employer'])

        control = ui.EditControl(searchFromControl=window, RegexName="Street Address:")
        if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(new_group_plan['street_address'])
        
        control = ui.EditControl(searchFromControl=window, RegexName="Zip:")
        if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(new_group_plan['city'])

        control = ui.EditControl(searchFromControl=window, AutomationId="15")
        if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(new_group_plan['state'])
        
        control = ui.EditControl(searchFromControl=window, AutomationId="17")
        if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(new_group_plan['zip'])
        
        control = ui.EditControl(searchFromControl=window, RegexName="Phone:")
        if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(new_group_plan['phone'])

        control = ui.EditControl(searchFromControl=window, RegexName="Group #:")
        if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(api_plan['plan_group_number'])        

        control = ui.EditControl(searchFromControl=window, RegexName="Last Update:")
        if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(new_group_plan['last_update_date'])
        
        control = ui.EditControl(searchFromControl=window, RegexName="Benefit Renewal:")
        if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(new_group_plan['benefit_renewal'])
        
        control = ui.ButtonControl(searchFromControl=window, AutomationId="61")
        if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
        win_select_alt_code = ui.WindowControl(RegexName="^Select Alt Code")
        win_select_alt_code.SetFocus()
        control = ui.ListItemControl(searchFromControl=win_select_alt_code, RegexName=new_group_plan['alt_code'])
        if control.Exists(time_to_exist, 0):
            control.DoubleClick(simulateMove=False, waitTime=0.5)
        else:
            setLog("Alt code not found|")
            fail_writeback_status("Exception")
            control = ui.ButtonControl(searchFromControl=win_select_alt_code, RegexName="Cancel")
            if control.Exists(time_to_exist, 0):
                control.Click(simulateMove=False, waitTime=0.5)
        
        
        control = ui.ButtonControl(searchFromControl=window, RegexName="Open")
        if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
        control = ui.ListItemControl(searchFromControl=window, RegexName=new_group_plan['claim_format'])
        if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)

        # selecting fee schedule
        if fee_schedule:
            select_fee_schedule(fee_schedule)
        else:
            setLog("Exception in sp fee")
            raise Exception("exception in sp fee schedule")

        control = ui.ButtonControl(searchFromControl=window, AutomationId="1152", RegexName=">>" )
        if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
        win_select_rvu_schedule = ui.WindowControl(RegexName="^Select RVU Schedule")
        win_select_rvu_schedule.SetFocus()
        control = ui.ListItemControl(searchFromControl=win_select_rvu_schedule, RegexName=new_group_plan['rvu_schedule'])
        if control.Exists(time_to_exist, 0):control.DoubleClick(simulateMove=False, waitTime=0.5)

        control = ui.ButtonControl(searchFromControl=window, AutomationId="121", RegexName=">>" )
        if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
        
        win_select_rpayer_id = ui.WindowControl(RegexName="^Select Payer ID")
        win_select_rpayer_id.SetFocus()
        control = ui.ListItemControl(searchFromControl=win_select_rpayer_id, RegexName=f".*{new_group_plan['payor_id']}")
        # control = ui.ListItemControl(searchFromControl=win_select_rpayer_id, RegexName=f".*DXPRT")
        attempts = 0
        exists = False
        import time
        while attempts < 3:
            exists = control.Exists()
            if exists and control.GetClickablePoint()[2]:
                time.sleep(1)
                control.DoubleClick(simulateMove=False)
                break
            attempts += 1
            if not exists: break
            control.WheelDown(2)
        if not exists:
            win_select_rpayer_id.SetFocus()
            btn_cancel = ui.ButtonControl(searchFromControl=win_select_rpayer_id, RegexName=f"Cancel")
            if btn_cancel.Exists(time_to_exist, 0):btn_cancel.Click(simulateMove=False, waitTime=0.5)

            window = ui.WindowControl(RegexName="^Dental Insurance Plan Information")
            window.SetFocus()

            control = ui.EditControl(searchFromControl=window, RegexName="Payor ID:")
            # if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(new_group_plan['payor_id'])
            if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue("06126")


        control = ui.ComboBoxControl(searchFromControl=window, RegexName="Source of Payment:" )
        if control.Exists(time_to_exist, 0):
            control.Click(simulateMove=False, waitTime=0.5)
            control = ui.ListItemControl(searchFromControl=window, RegexName=new_group_plan['source_of_payment'])
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)

        control = ui.RadioButtonControl(searchFromControl=window, RegexName=new_group_plan["financial_class_types"])
        if control.Exists(time_to_exist, 0):control.DoubleClick(simulateMove=False, waitTime=0.5)

        control = ui.ButtonControl(searchFromControl=window, RegexName="OK")
        if control.Exists(time_to_exist, 0):control.DoubleClick(simulateMove=False, waitTime=0.5)
        setLog("create_new_group_plan [renewall: {}]|".format(new_group_plan['benefit_renewal']))


def read_payer_json(json_file):
    with open(json_file, 'r') as f:
        payers = json.load(f)
    return payers

@handle_exceptions("Exception in get group plan dict|")
def get_group_plan_dict():
    import re
    from datetime import datetime

    def getBkInsPlanInfo(claimAddress:str)->dict:
        bkStreetAddress = None
        bkCity = None
        bkState = None
        bkZipCode = None
        
        cityNames = iv_config['city_names']
        carrierRegex = re.compile(r'\b(?:delta\s)?dental\b|Cigna|UHC(?:\sARRO)?|Met(?:life|Life\sDental|life\sdental)\b', flags=re.IGNORECASE)
        

        #Remove carrier name
        match = carrierRegex.search(claimAddress)
        if match:
            claimAddress = re.sub(carrierRegex,'',claimAddress).strip()   

        for city in cityNames:
            #get city
            if city.lower() in claimAddress.lower():
                bkCity = city
                #get street address
                bkStreetAddress = re.split(rf'\b{re.escape(city.lower())}\b', claimAddress, flags=re.IGNORECASE)[0].strip()

        states_dictionary = {
        'Alabama' : 'AL',
        'Alaska' : 'AK',
        'Arizona' : 'AZ',
        'Arkansas' : 'AR',
        'California' : 'CA',
        'Colorado' : 'CO',
        'Missouri' : 'MO',
        'Nebraska' : 'MI',
        'New Jersey' : 'AR',
        'New Mexico' : 'NM',
        'North Carolina' : 'MI',
        'North Dakota' : 'MI',
        'Connecticut' : 'AR',
        'Georgia' : 'GA',
        'Hawaii' : 'HI',
        'Idaho' : 'ID',
        'Illinois' : 'IL',
        'Maine' : 'NH',
        'New Hampshire': 'NH',
        'Vermont' : 'NH',
        'Ohio' : 'MI',
        'Oklahoma' : 'OK',
        'Oregon' : 'OR',
        'Pennsylvania' : 'PA',
        'Puerto Rico' : 'PR',
        'Rhode Island' : 'RI',
        'South Carolina' : 'MO',
        'South Dakota' : 'SD',
        'Indiana' : 'MI',
        'Iowa' : 'IA',
        'Kansas' : 'KY',
        'Kentucky' : 'KY',
        'Massachusetts' : 'WI',
        'Michigan' : 'MI',
        'Maryland' : 'MD',
        'Minnesota' : 'MI',
        'Tennessee' : 'TN',
        'Virginia' : 'VA',
        'Washington' : 'WA',
        'Wisconsin' : 'WI',
        'Wyoming' : 'WY',
        'Nevada' : 'NV',
        'Utah' : 'UT',
        'Texas' : 'TX',
        }
        
        def get_state_zipcode(claimAddress):
            #get state and zip
            pattern = re.compile(r'\b([A-Z]{2})[.,\s]*(\d{5}(?:-\d{4,5})?)\b')
            match = pattern.search(claimAddress)
            if match:
                bkState = match.group(1)
                bkZipCode = match.group(2)
            else:
                bkState = None
                bkZipCode = None
            return bkState, bkZipCode

        def replace_state_with_abbreviation(text):
            for state, state_code in states_dictionary.items():
                text = re.sub(r'\b' + re.escape(state) + r'\b', state_code, text)
            return text

        bkState, bkZipCode = get_state_zipcode(claimAddress)
        if not bkState and not bkZipCode:
            address_info = [re.split(rf'\b{re.escape(city.lower())}\b', claimAddress, flags=re.IGNORECASE)[0].strip()
            for city in cityNames
            if city.lower() in claimAddress.lower()][0].strip()

            state_info = [re.split(rf'\b{re.escape(city.lower())}\b', claimAddress, flags=re.IGNORECASE)[1].strip()
            for city in cityNames
            if city.lower() in claimAddress.lower()][0]
            
            rename_state = replace_state_with_abbreviation(state_info)
            claimAddress = address_info + rename_state
            bkState, bkZipCode = get_state_zipcode(claimAddress)

        bkStreetAddress = "-" if bkStreetAddress is None else bkStreetAddress
        bkCity = "-" if bkCity is None else bkCity
        bkState = "-" if bkState is None else bkState
        bkZipCode = "-" if bkZipCode is None else bkZipCode

        return {
            "Street Address": bkStreetAddress,
            "City": bkCity,
            "State": bkState,
            "Zip Code": bkZipCode
        }   

    def get_month_name(month_number):
        months = {
            1: "JAN",
            2: "FEB",
            3: "MAR",
            4: "APR",
            5: "MAY",
            6: "JUN",
            7: "JUL",
            8: "AUG",
            9: "SEP",
            10: "OCT",
            11: "NOV",
            12: "DEC"
        }
        return months.get(month_number)

    new_group_plan_dict = {}
    practice = data_supplies['practice']

    plan_results = planElg.evaluate(data_supplies, iv_config, ELG_PATTERNS)
    print_log(SUCCESS, "PLANS ELG REVIEWS")
        
    if any(plan_results.get(k, False) for k in [
        "dq_matituck_plan",
        "dq_fishkill_plan"
    ]):
        bk = {'ClaimsAddress':'PO Box 2906 Milwaukee, WI 53201','InsuranceName':'Dentaquest','CallReference':'(800)341-8478','PayerID':'CX014','YearCalendar':'n','YearFiscal':''}
    elif ['dq_catskill_plan']:
        bk = {'ClaimsAddress':'PO Box 2906 Milwaukee, WI 53201','InsuranceName':'Dentaquest','CallReference':'(800)417-7140','PayerID':'CX014','YearCalendar':'n','YearFiscal':''}
    elif any(plan_results.get(k, False) for k in [
        "uhccp_plan",
        "uhccp_dual_plan",
        "uhccp_nj_plan",
        "uhccp_middleisl"
    ]):
        bk = {'ClaimsAddress':'PO Box 2061 Milwaukee, WI 53201','InsuranceName':f"{data_supplies['carrier_name']}",'CallReference':'(800)341-8478','PayerID':'GP133','YearCalendar':'n','YearFiscal':''}
    elif plan_results['csea_all_plan']:
        bk = {'ClaimsAddress':'PO Box 489 Latham, NY 12110','InsuranceName':f"{data_supplies['carrier_name']}",'CallReference':'(800)323-2732','PayerID':'CX054','YearCalendar':'n','YearFiscal':''}
    elif plan_results['caresorce_all_plan']:
        bk = {'ClaimsAddress':'PO Box 299 Milwaukee, WI 53201','InsuranceName':f"{data_supplies['carrier_name']}",'CallReference':'(800)341-8478','PayerID':'HNJ01','YearCalendar':'n','YearFiscal':''}
    elif plan_results['hmo_uhc_plan']:
        bk = {'ClaimsAddress':'PO Box 30567 Salt Lake City, UT 84130-0567','InsuranceName':f"{data_supplies['carrier_name']}",'CallReference':'(800)822-5353','PayerID':'521337971','YearCalendar':'n','YearFiscal':''}   
    elif plan_results['liberty_mattituck_plan']:
        bk = {'ClaimsAddress':'PO Box 15149 Tampa, FL 33684','InsuranceName':f"{data_supplies['carrier_name']}",'CallReference':'(888)352-7924','PayerID':'CX083','YearCalendar':'n','YearFiscal':''}          
    else:
        bk = eval(GetVar("bk"))


    street_address = getBkInsPlanInfo(bk["ClaimsAddress"])
    print("street_address: {}".format(street_address))
    if "-" in street_address.values():
        # if any(element == '-' for element in street_address.values()):
        setLog("Exception in get street address|")
        fail_writeback_status("Exception")
    else:
        regex = r'^(.*?)\s*Master'
        new_group_plan_dict["carrier_name"] = re.search(regex,bk["InsuranceName"],re.IGNORECASE).group(1) if bool(re.search(regex,bk["InsuranceName"],re.IGNORECASE)) else bk["InsuranceName"]
        new_group_plan_dict["street_address"] = street_address["Street Address"]
        new_group_plan_dict["city"] = street_address["City"]
        new_group_plan_dict["state"] = street_address["State"]
        new_group_plan_dict["zip"] = street_address["Zip Code"]

        new_group_plan_dict["last_update_date"] = datetime.now().strftime("%m/%d/%Y")
        new_group_plan_dict["phone"] = bk["CallReference"].replace('.', '')

        benefit_renewal = ''
        if 'YearCalendar' in bk and 'YearFiscal' in bk:
            if bk['YearCalendar'] == 'n':
                benefit_renewal = 'JAN'
            elif bk['YearFiscal'] == 'n':
                benefit_renewal = get_month_name(datetime.strptime(bk['EffectiveDate'].strip(), '%m/%d/%Y').month)


        # new_group_plan_dict["benefit_renewal"] = get_month_name(datetime.strptime(general_info["EffectiveDate"].strip(), '%m/%d/%Y').month)

        new_group_plan_dict["benefit_renewal"] = benefit_renewal

        new_group_plan_dict["alt_code"] = "ADA"
        new_group_plan_dict["claim_format"] = "DX2019"
        new_group_plan_dict["rvu_schedule"] = "<NONE>"
        
        # bk = {'PayerID':'GI813'}
        # data_supplies = {'carrier_name':'UHC','member_id':'abc123456'}

        # json_file = 'C:/DentalRobot/Projects/IV/bots/scripts/global_payers.json'  # Ruta a tu archivo JSON
        # payers = read_payer_json(json_file)

        payor_id = bk["PayerID"].strip()

        guardian_error = False
        if re.search(r'(?i)^Guardian.*',data_supplies['carrier_name']):
            def get_payer_id_guardian(subscriber_id: str) -> str:
                subscriber_id = subscriber_id.replace("-","")
                if len(subscriber_id) == 8 or len(subscriber_id) == 9 or len(subscriber_id) == 10 and subscriber_id.isdigit():
                    setLog("payor Guardian 64246|")
                    return "64246"
                elif len(subscriber_id) == 10 or any(char.isalpha() for char in subscriber_id):
                    setLog("payor Guardian GI813|")
                    return "GI813"
                else:
                    setLog("payor Guardian error|")
                    guardian_error = True
                    gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!T{gpvars('index')}", [[f"REVIEW ISSUE GUARDIAN PAYOR ERROR"]])
                    #raise Exception("get_payer_id_guardian error")

            payor_id = get_payer_id_guardian(data_supplies['member_id'].strip())
        # else:
        #     searched_payor = payers.get(payor_id)
        #     if searched_payor:
        #         setLog("payor found {}|".format(payor_id))
        #     else:
        #         setLog("payor default DXPRT|")
        #         payor_id = 'DXPRT'
        if guardian_error: return 'guardian_error'
        
        new_group_plan_dict["payor_id"] = payor_id[:5] if len(payor_id) > 5 else payor_id
        new_group_plan_dict["source_of_payment"] = "Commercial Insurance Co."
        new_group_plan_dict["financial_class_types"] = "No Financial Class Types"
        print_log(INFO,"NEW GROUP PLAN DICT INFORMATION")
        print(new_group_plan_dict)
    return new_group_plan_dict


def select_employer(employer_name_api:str):
    cont = 0
    found_employer = None   
    time_to_exist = 1.25
    window = ui.WindowControl(RegexName="^Dental Insurance Plan Information")
    window.SetFocus()

    control = ui.ButtonControl(searchFromControl=window, AutomationId="6472", RegexName=">>")
    if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)

    control = ui.EditControl(searchFromControl=window,AutomationId="5002", RegexName="Enter Employer Name:")
    if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(employer_name_api)

    control = ui.ButtonControl(searchFromControl=window, AutomationId="5903", RegexName=">>")
    if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)

    table_selector = get_info(schema,"extract_ins._GT_employer_tbl")
    employers_table = winAction.findChildren(table_selector, 10, "ListItemControl", "ctrltype")

    while cont < len(employers_table) and not found_employer:
        employer_row = employers_table[cont]
        cont += 1
        
        if employer_row['title'].lower().strip() == employer_name_api.lower().strip():
            plan_idx = employer_row['idx']
            employer_selector = get_info(schema,"update_employer._CS_exist_employer_update2")
            employer_selector["children"][-1]['idx'] = plan_idx
            winAction.click(employer_selector,5,"SIMPLE")
            found_employer = True  
            control = ui.ButtonControl(searchFromControl=window, AutomationId="1", RegexName="OK")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)


@handle_exceptions(update_log_wrapper("Exeption in select_fee_schedule|"))
def select_fee_schedule(fee_schedule:str):
    import time
    time_to_exist = 1.25

    window = ui.WindowControl(RegexName="^(:?)Dental Insurance Plan Information")
    app = window.SetFocus() 
    # fee = "NY- Cigna PPO-23"

    if app:
        control = ui.ButtonControl(searchFromControl=window, AutomationId="4021", RegexName=">>")
        if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
        
        control = ui.EditControl(searchFromControl=window, RegexName="Find Fee Schedule:")
        if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(fee_schedule)

        win_select_fee = ui.WindowControl(RegexName="^Select Fee Schedule")
        win_select_fee.SetFocus()
        control = ui.DataItemControl(searchFromControl=win_select_fee,RegexName=f"Name")
        currentValue = control.GetLegacyIAccessiblePattern().Value
        currentValue = currentValue.strip()
        
        print(f"currentValue ({currentValue}) == fee_schedule ({fee_schedule})")
        if currentValue == fee_schedule:
            if control.GetClickablePoint()[2]:
                time.sleep(1)
                control.DoubleClick(simulateMove=False)
            # control = ui.ButtonControl(searchFromControl=window, AutomationId="okButton", RegexName="OK")
            # if control.Exists(time_to_exist, 0) and control.IsEnabled == 1: 
            #     control.Click(simulateMove=False, waitTime=0.5)
        else:
            control = ui.ButtonControl(searchFromControl=window, AutomationId="cancelButton", RegexName="Cancel")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
            setLog("Fee Schedule doesn't exits|")

def matrix(group_plan_name : str, data : dict):
    import re
    matrix = {}
    regex = r'^(.*?)\s*Master'
    practice = data_supplies['practice']
    template = iv_config['write_back_rules']['template']
    plan_results = planElg.evaluate(data_supplies, iv_config, ELG_PATTERNS )
    elg_plan = [key for key, value in plan_results.items() if value]
  
    if plan_results["dq_matituck_plan"]:
        bk = {'GroupID':'Dentaquest','Employer':'EMPTY','InsuranceName':'Dentaquest','Deductible':'00','Family':'00','DeductiblePreventive':'00','AnnualMaximum':'00','Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif plan_results["uhccp_plan"] or plan_results["uhccp_nj_plan"]:
        bk = {'GroupID':f'UHCCP-{practice}','Employer':'EMPTY','InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':'00','Family':'00','DeductiblePreventive':'00','AnnualMaximum':'9999','Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif plan_results["uhccp_dual_plan"]:
        bk = {'GroupID':f'UHCCP-DUAL COMPLETE-{practice}','Employer':'EMPTY','InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':'00','Family':'00','DeductiblePreventive':'00','AnnualMaximum':'9999','Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif plan_results["caresorce_all_plan"]:
        bk = {'GroupID':f"{data['group_number']}",'Employer':'EMPTY','InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':'00','Family':'00','DeductiblePreventive':'00','AnnualMaximum':'00','Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif plan_results["uhccp_middleisl"]:
        bk = {'GroupID':f"{data['group_number']}",'Employer':'EMPTY','InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':f"{data['deductible_standar']}",'Family':'00','DeductiblePreventive':'00','AnnualMaximum':f"{data['annual_max']}",'Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif plan_results["csea_all_plan"]:
        bk = {'GroupID':f"{data['group_number']}",'Employer':f"{data['employer']}",'InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':f"{data['deductible_standar']}",'Family':'00','DeductiblePreventive':'00','AnnualMaximum':f"{data['annual_max']}",'Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif plan_results["hmo_uhc_plan"]:
        bk = {'GroupID':f"{data['group_number']}",'Employer':f"{data['employer']}",'InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':f"{data['deductible_standar']}",'Family':'00','DeductiblePreventive':'00','AnnualMaximum':f"{data['annual_max']}",'Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif plan_results["dq_fishkill_plan"]:
        bk = {'GroupID':f"{data['group_number']}",'Employer':f"{data['employer']}",'InsuranceName':'Dentaquest','Deductible':f"{data['deductible_standar']}",'Family':'00','DeductiblePreventive':'00','AnnualMaximum':f"{data['annual_max']}",'Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif plan_results["dq_catskill_plan"]:
        bk = {'GroupID':f"{data['group_number']}",'Employer':f"{data['employer']}",'InsuranceName':'Dentaquest','Deductible':'00','Family':'00','DeductiblePreventive':'00','AnnualMaximum':'9999','Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}
    elif plan_results["liberty_mattituck_plan"]:
        bk = {'GroupID':f"{data['group_number']}",'Employer':f"{data['employer']}",'InsuranceName':f"{data_supplies['carrier_name']}",'Deductible':f"{data['deductible_standar']}",'Family':'00','DeductiblePreventive':'00','AnnualMaximum':f"{data['annual_max']}",'Orthodontic':'00','Orthodontics_AgeLimit':'00','LifetimeMax':'00'}        
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
            if cleaned_string in  ["-",'','N/A','None','Not Covered','3 per family']:
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
            if any(plan_results.get(k, False) for k in [
                "dq_matituck_plan",
                "dq_fishkill_plan",
                "dq_catskill_plan",
            ]):
                table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_3'])
            elif any(plan_results.get(k, False) for k in [
                "uhccp_plan",
                "uhccp_dual_plan",
                "uhccp_nj_plan",
                "caresorce_all_plan",
                "uhccp_middleisland"
            ]):
                table = generate_table_base_category(template,RULES_VALUES_MAPPING['rule_1'])
            elif any(plan_results.get(k, False) for k in [
                "csea_all_plan",
                "hmo_uhc_plan"
                ]):
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

@handle_exceptions(update_log_wrapper("Exception in Fee data Json creation|"), fail_writeback_status)
def fee_data():
    from module.business.carriers_manager import get_regex_for_types,get_carriers_per_client

    import pandas as pd
    import json
    import re
    import os

    titles = ['Location', 'Payer', 'Payer ID', 'Plan Type/ Plan Name', 'Legacy Tin', 'Smilist Tin', 'State']
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
    "HURLEYAVE" : "HURLEYAVE",
    'SOUTHPLAINFIELD' : 'SPLNFIELD',
    'EGREENBUSH' : 'EASTGREEN',
    'CLIFTONPARKOMS' : 'OMSCLIFPRK'
    }

    spreed_fee_data = eval(GetVar("MASTER"))
    
    spreed_fee_data = [
    row for row in spreed_fee_data
    if row and not str(row[1]).strip().lower().startswith("dental")
    and (
        str(row[1]).strip().lower() == "ucr"
        or (
            len(row) >= 7
            and all(str(row[i]).strip() != "" for i in (0, 1, 3, 5, 6))
        )
    )
]

    #rename differents clinics to be equal like config.yaml
    for i,row in enumerate(spreed_fee_data):
        if bool(row) == True:
            row = row[:7]
            clinic = row[0].upper().replace(' ','')
            if clinic in rename_clinics: clinic = rename_clinics[clinic]
            row[0] = clinic
            spreed_fee_data[i] = row

    #rule for anthem 100,200,300 it came in the first o third position 
    anthem_re = r"(?i)anthem"
    def transform_plan(row):
        if row:
            anthem_plan_numeric = r'\b(100|200|300)\b'
            first = re.search(anthem_plan_numeric, row[1])
            second = re.search(anthem_plan_numeric, row[3])
            if first:
                value = first.group(1)
                row[3] = value
                
            elif second:
                value = second.group(1)
                row[3] = value
            return row
        else:
            return row
        
    new_data = []

    for row in spreed_fee_data:
        if row and re.match(anthem_re, row[1], re.IGNORECASE):
            row = transform_plan(row)  
        new_data.append(row)

    spreed_fee_data = new_data
    ## end of the new rule 


    fee_data = pd.DataFrame(spreed_fee_data, columns=titles)
    fee_data['Row_number'] = range(4, 4 + len(fee_data))
    
    fee_data = fee_data.applymap(lambda x: x.upper().strip() if isinstance(x, str) else x)

    practice = GetVar("practice")
    SetVar("practice", iv_config['clinic_settings']['settings'][practice]['clinic_name'])
    carriers = { obj.name: obj.regex for obj in get_carriers_per_client().bots }
    carriers.update({'UCR':"^UCR$"})
    SetVar("practice", practice)
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
    route = os.path.dirname(os.path.abspath(__file__))

    # Usuario actual del sistema
    try:
        usuario = os.getlogin()
    except Exception:
        usuario = "unknown_user"


    path_file = f"{route}\\fee_data\\fee_data_{usuario}.json"
    with open(path_file, 'w') as file:
        json.dump(master_fee, file, indent=4)

    print(f"JSON has been write in the path: '{path_file}'.")


def update_group_plan(group_plan_name_api:str,group_plan_pms:str):
    if group_plan_name_api.upper() != group_plan_pms.upper():
        winAction.setText(get_info(schema,"extract_ins._GT_extract_groupPlan"),10, group_plan_name_api)
        SetVar("log", GetVar("log") + "group name updated|")


@handle_exceptions(update_log_wrapper("Exeption in validate_check_date|"))
def validate_check_date(eligibility_date):
    try:
        last_eligibility = datetime.strptime(eligibility_date.strip(), '%Y-%m-%d')
    except ValueError:
        print("Error: The eligibility date is not valid.")
        raise ValueError("The eligibility date must be in this format  'YYYY-MM-DD'.")
    todayDate = date.today()
    formatted_date = todayDate.strftime("%Y-%m-%d")
    apptDate = datetime.strptime(formatted_date, '%Y-%m-%d')
    return last_eligibility.year == apptDate.year and last_eligibility.month == apptDate.month

@handle_exceptions(update_log_wrapper("Exeption in update phone|"))
def update_phone():
    print('update phone!')
    if "update_phone_in_insurance_plan_information" in iv_config["input_wrapper_services"]:
        if iv_config["input_wrapper_services"]["update_phone_in_insurance_plan_information"]:

            bk = eval(GetVar("bk"))
            phone = bk["CallReference"].replace('.', '').replace('Phone: ', '')
            openWin("famFile > insInfo")
            time_to_exist = 1.25
            
            #open insurance plan information
            window = ui.WindowControl(RegexName="^Insurance Information")
            window.SetFocus()
            control = ui.ButtonControl(searchFromControl=window, RegexName="Insurance Data")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
            winAction.manageAlert("^Dentrix Dental Systems", "^Changes in existing insurance plan", "OK", 3)

            
            window = ui.WindowControl(RegexName="^Dental Insurance Plan Information")
            window.SetFocus()

            control = ui.EditControl(searchFromControl=window, RegexName="Phone:")
            if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(phone)

            control = ui.ButtonControl(searchFromControl=window, RegexName="^OK$")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)

            winAction.manageAlert("^Insurance...", "^Change Plan for All", "OK", 3)
            setLog("updt_Phone: {}|".format(phone))
            winAction.closeModals("Insurance Information")

    print("done update phone")


def validar_groupname(groupname):
    partes = groupname.split('-')

    if len(partes) != 4:
        return False

    if len(partes[0]) != 2:
        return False
    
    if len(partes[2]) != 6:
        return False

    if len(partes[3]) != 6:
        return False

    return True

@handle_exceptions(update_log_wrapper("Exeption in update payor|"))
def update_payor(found_carrier,elg_plan = None):
    print('update payer!')
    if "update_payer_default" in iv_config["input_wrapper_services"]:
        if iv_config["input_wrapper_services"]["update_payer_default"]:

            openWin("famFile > insInfo")
            time_to_exist = 1.25
            
            #open insurance plan information
            window = ui.WindowControl(RegexName="^Insurance Information")
            window.SetFocus()
            control = ui.ButtonControl(searchFromControl=window, RegexName="Insurance Data")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
            winAction.manageAlert("^Dentrix Dental Systems", "^Changes in existing insurance plan", "OK", 3)

            
            window = ui.WindowControl(RegexName="^Dental Insurance Plan Information")
            window.SetFocus()
            
            # 120725 star
            
            if not elg_plan and data_supplies['type_of_verification'] == 'ELG':
                nomenclature_plan = {}
                control = ui.EditControl(searchFromControl=window, RegexName="Group Plan:")
                if control.Exists(time_to_exist, 0):group_name_plan = control.GetValuePattern().Value

                group_name_val = group_name_plan.split("-")
                if validar_groupname(group_name_plan):
                    if len(group_name_val[1]) > 3 and group_name_val[1].lower() in ["premier","dppo","total dppo"]:
                        state_plan = ''
                        zip_plan = ''
                        time_to_exist = 1.25

                        control = ui.EditControl(searchFromControl=window, RegexName="Carrier Name:")
                        if control.Exists(time_to_exist, 0):carrier_plan = control.GetValuePattern().Value

                        control = ui.EditControl(searchFromControl=window, RegexName="Group #:")
                        if control.Exists(time_to_exist, 0):group_number_plan = control.GetValuePattern().Value                        
                        
                        control = ui.EditControl(searchFromControl=window, RegexName="Employer:")
                        if control.Exists(time_to_exist, 0):employer_plan = control.GetValuePattern().Value

                        control = ui.EditControl(searchFromControl=window, RegexName="Benefit Renewal:")
                        if control.Exists(time_to_exist, 0):renewal_plan = control.GetValuePattern().Value

                        control = ui.EditControl(searchFromControl=window, RegexName="Street Address:")
                        if control.Exists(time_to_exist, 0):street_address_plan = control.GetValuePattern().Value

                        control =  ui.TextControl(searchFromControl=window, RegexName="Phone:")
                        previous_sibling = control.GetPreviousSiblingControl()
                        if previous_sibling:
                            zip_plan = previous_sibling.GetValuePattern().Value

                        control = ui.EditControl(searchFromControl=window, RegexName="Phone:")
                        if control.Exists(time_to_exist, 0):phone_plan = control.GetValuePattern().Value

                        control = ui.EditControl(searchFromControl=window, RegexName="Payor ID:")
                        if control.Exists(time_to_exist, 0):payor_plan = control.GetValuePattern().Value

                        control = ui.EditControl(searchFromControl=window, RegexName="Zip:")
                        if control.Exists(time_to_exist, 0):city_plan = control.GetValuePattern().Value

                        netx_sibling = control.GetNextSiblingControl()
                        if netx_sibling:
                            state_plan = netx_sibling.GetValuePattern().Value

                        nomenclature_plan = {
                            "carrier_plan" : carrier_plan,
                            "group_number_plan" : group_number_plan,
                            "employer_plan" : employer_plan,
                            "group_name_plan" :group_name_plan,
                            "street_address_plan" :street_address_plan,
                            "phone_plan" : phone_plan,
                            "payor_plan" : payor_plan,
                            "city_plan" : city_plan,
                            "state_plan": state_plan,
                            "zip_plan" : zip_plan,
                            "renewal_plan" :renewal_plan
                        }
                        if all(nomenclature_plan.values()): 
                            set_var("nomenclature_plan",nomenclature_plan)
                        else:
                            nomenclature_plan = {}
                            set_var("nomenclature_plan",{})
                            setLog(f"Revie the info plan, data missing to update the plan {group_name_plan}") 
                            
          
            # 120725 end

            # control = ui.EditControl(searchFromControl=window, RegexName="Carrier Name:")
            # if control.Exists(time_to_exist, 0):carrier_n = control.GetValuePattern().Value

            carrier_n = winAction.getText(get_info(schema,"extract_ins._GT_Extract_carrierName"),5)
            carrier_pms = [key for key,values in DEFAULT_PAYERS.items() if re.match(values['re'],carrier_n,re.IGNORECASE)]

            if found_carrier and carrier_pms and found_carrier[0].lower().strip() == carrier_pms[0].lower().strip():
                payor = DEFAULT_PAYERS[carrier_pms[0]]['payor']
                control = ui.EditControl(searchFromControl=window, RegexName="Payor ID:")
                if control.Exists(time_to_exist, 0):control.GetPattern(ui.PatternId.ValuePattern).SetValue(payor)
                setLog("updt_Payer: {}|".format(payor))

            control = ui.ButtonControl(searchFromControl=window, RegexName="^OK$")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)

            winAction.manageAlert("^Insurance...", "^Change Plan for All", "OK", 3)
            winAction.closeModals("Insurance Information")
            
    print("done update payor")

def review_fee():
    print("*****review_fee")
    is_ready_to_upload = False
    is_ready_to_upload = eval(GetVar('is_ready_to_upload'))
    if is_ready_to_upload:
        log =  data_supplies['log']
        match = re.search(r"SmilistTin:\s*(\d+)", log)
        smilist_tin = ''
        if match:
            smilist_tin = match.group(1)
            print(smilist_tin) 

        all_fee_schedule = eval(GetVar("all_fee_schedule"))
        for fee in all_fee_schedule:
            if fee[0] == int(smilist_tin):
                fee_schedule = fee[1].strip()
                break
            else:
                fee_schedule = False

        print_log(SUCCESS,"FEE SCHEDULE")
        print(fee_schedule)

        openWin("famFile > insInfo")
        time_to_exist = 1.25
        
        #open insurance plan information
        window = ui.WindowControl(RegexName="^Insurance Information")
        window.SetFocus()
        control = ui.ButtonControl(searchFromControl=window, RegexName="Insurance Data")
        if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
        winAction.manageAlert("^Dentrix Dental Systems", "^Changes in existing insurance plan", "OK", 3)

        window = ui.WindowControl(RegexName="^Dental Insurance Plan Information")
        window.SetFocus()

        select_fee_schedule(fee_schedule)


        control = ui.ButtonControl(searchFromControl=window, RegexName="^OK$")
        if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)

        winAction.manageAlert("^Insurance...", "^Change Plan for All", "OK", 3)
        winAction.closeModals("Insurance Information")


def review_fee_schedule():
    if "review_fee_schedule" in iv_config["input_wrapper_services"]:
        if iv_config["input_wrapper_services"]["review_fee_schedule"]:
            openWin("famFile > insInfo")
            time_to_exist = 1.25
            
            #open insurance plan information
            window = ui.WindowControl(RegexName="^Insurance Information")
            window.SetFocus()
            control = ui.ButtonControl(searchFromControl=window, RegexName="Insurance Data")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)
            winAction.manageAlert("^Dentrix Dental Systems", "^Changes in existing insurance plan", "OK", 3)

            window = ui.WindowControl(RegexName="^Dental Insurance Plan Information")
            window.SetFocus()

            control = ui.EditControl(searchFromControl=window, RegexName="Group Plan:")
            if control.Exists(time_to_exist, 0):group_name_plan = control.GetValuePattern().Value

            control = ui.EditControl(searchFromControl=window, RegexName="Fee Schedule:")
            if control.Exists(time_to_exist, 0):fee_schedule_pms = control.GetValuePattern().Value

            if not fee_schedule_pms or fee_schedule_pms.lower() == "<none>" and validar_groupname(group_name_plan):
                all_fee_schedule = eval(GetVar("all_fee_schedule"))
                fee_group = int(group_name_plan.split("-")[2])

                for fee in all_fee_schedule:
                    if fee[0] == int(fee_group):
                        fee_schedule = fee[1].strip()
                        break
                    else:
                        fee_schedule = False
                        fail_writeback_status()
                        
                setLog(f"Fee Schedule update to {fee_group}")

                select_fee_schedule(fee_schedule)

            control = ui.ButtonControl(searchFromControl=window, RegexName="^OK$")
            if control.Exists(time_to_exist, 0):control.Click(simulateMove=False, waitTime=0.5)

            winAction.manageAlert("^Insurance...", "^Change Plan for All", "OK", 3)
            winAction.closeModals("Insurance Information")


@handle_exceptions(update_log_wrapper("Exception in input data|"), fail_writeback_status)
def input_data():
    import time,re
    from reports_logs import log_file_insertion,log_file_creation
    s = time.time()
    is_coveraged = False
    is_ready_to_upload = False

    try:
        timestart= datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        is_ready_to_upload = eval(GetVar('is_ready_to_upload'))
        is_coveraged = isCoveraged()
        log_file_creation()
        practice = data_supplies['practice']
        print('is_ready_to_upload: {}'.format(is_ready_to_upload))
        print('is_coveraged: {}'.format(is_coveraged))
        print("******data_supplies: {}".format(data_supplies))
        #if not (validate_check_date(data_supplies['last_eligibility']) and not (re.search(static_regex["medicaid_re"],data_supplies['carrier_name'],re.IGNORECASE))):
        if is_ready_to_upload and is_coveraged:
            patient_insurance_info = eval(GetVar("patient_insurance_info"))
            found_carrier = [key for key,values in DEFAULT_PAYERS.items() if re.match(values['re'],data_supplies['carrier_name'],re.IGNORECASE)]
            FeeScheduleName =  patient_insurance_info["FeeScheduleName"].upper() if "FeeScheduleName" in patient_insurance_info else ""
            if ("HMO" in data_supplies["verification_status"].upper() and re.search(static_regex["re_uhc"],data_supplies['carrier_name'],re.IGNORECASE) and len(data_supplies['urls'].split(",")) == 1 and "view" in data_supplies['urls']):
                data_supplies['type_of_verification'] = 'ELG'

            if not("HMO" in FeeScheduleName and re.compile('(?i)^Aetna.*|^Foreign.*').search(data_supplies['carrier_name'])):
                update_other_id()

                if (data_supplies['type_of_verification'] == "FBD" and 
                "INACTIVE" not in data_supplies["verification_status"].upper()):   
                    flag= eval(GetVar('Amounts'))
                    if flag:
                        review_overlap()
                        fee_data()
                        employer_ = verified_employer()
                        if employer_:update_employer(employer_)
                        review_benefit_renewall()
                        update_phone()
                        if found_carrier: update_payor(found_carrier) 
                        set_amounts()
                        set_deductible()
                        coverage_table()
                        set_coverage_table_note()
                        
                elif(data_supplies['type_of_verification'] == "ELG" and 
                "INACTIVE" not in data_supplies["verification_status"].upper() and  
                "MAX OUT" not in data_supplies["verification_status"].upper()):     
                    plan_results = planElg.evaluate(data_supplies, iv_config, ELG_PATTERNS)
                    elg_plan = [key for key, value in plan_results.items() if value]

                    update_payor(found_carrier,elg_plan) 
                    nomenclature_plan = eval(gpvars("nomenclature_plan"))
                    print_log(SUCCESS,'NOMENCLATURE VAR')
                    print(nomenclature_plan)
                    if nomenclature_plan: 
                        update_employer(nomenclature_plan['employer_plan'],nomenclature_plan)
                        coverage_table()
                    if elg_plan:
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
            review_fee_schedule()
            elegibility_dates_and_checkboxs()
        #else:
        #   setLog("WRITTEBACK PROCESS DOES NOT EXECUTE DUE THE ELIGIBILITY CHECK DATE IT IS IN THE ACTUAL MONTH")
    except:
        setLog("Exception in input data process with error")
        fail_writeback_status()
    finally:
        try:
            usuario = os.getlogin()
        except Exception:
            usuario = "unknown_user"
        if not is_ready_to_upload: 
            fail_writeback_status()
            log = GetVar('log')
            log = f"{log} |Process Done By {usuario}" if len(log) > 0 else 'Empty'
            gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!AC{gpvars('index')}", [[log]])
            return -1
        writeBackStatus = GetVar("writeback_status")
        uploadStatus = GetVar("upload_status")
        # if writeBackStatus.lower() == "error" or uploadStatus.lower() == "error":
        #     gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!T{gpvars('index')}", [["REVIEW BUG"]])
        gsheet.load_to_sheet(gpvars('idSpreedSheet'),f"{gpvars('sheet')}!R{gpvars('index')}",[[f'{uploadStatus},{writeBackStatus}']])
    
    log = GetVar('log')
    log = f"{log} |Process Done By {usuario}" if len(log) > 0 else 'Empty'
    gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!AC{gpvars('index')}", [[log]])

    e = time.time() 
    r = (e-s)
    upload_status = f'{uploadStatus},{writeBackStatus}'
    print_log(SUCCESS, f'INPUT TIME WAS {r}')
    log_file_insertion(r,timestart,upload_status,data_supplies)
