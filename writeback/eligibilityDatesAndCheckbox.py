import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalFunctions.script import setLog, print_log
from globalVariables.bk import bk
from dateutil.relativedelta import relativedelta

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
    
if bk:
    regex_date = r"(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}|N/A|-|\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
    if 'EffectiveDate' in bk: 
        get_date = re.search(r"{}".format(regex_date),bk["EffectiveDate"])
        if get_date: effectivedate = get_date.group(1).strip()

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
    
    print_log("SUCCESS",f"TERM_DATE{term_date}")
    print_log("SUCCESS",f"TERM_DATE{effectivedate}")