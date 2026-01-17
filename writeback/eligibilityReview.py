@handle_exceptions(update_log_wrapper("Exception in ELG dates|"),fail_writeback_status)
def elegibility_dates_and_checkboxs():
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


    # Antes: if was_updated == False:
    if not term_date or effectivedate == term_date:
        term_date = last_day_next_month(GetVar("sheet"))
    print_log(INFO,f'term_date last: {term_date}')
    Value_last_eligibility_check, Value_eligibility_start, Value_eligibility_end = todays_date.strftime('%m/%d/%Y'), effectivedate, term_date

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

    # --- Actualización base ---
    # condition for lastelgdate and review 
    pg.alert("review")
    print(last_eligibility_check.get_text())
    print(eligibility_start.get_text())
    print(eligibility_end.get_text())


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

    #to review the dates 01/12/2026
    review_date = GetVar("review_date")

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


import re

result_integration = eval(GetVar("result_integration"))
pattern_date = r"\b(\d/\d{1,2}/\d{4}|\d{1,2}/\d/\d{4}|\d{4}-\d-\d{1,2}|\d{4}-\d{1,2}-\d|\d{4}-\d-\d{1,2}T\d{2}:\d{2}:\d{2}|\d{4}-\d{1,2}-\dT\d{2}:\d{2}:\d{2})\b"

indexs = [
    idx + 2
    for idx, row in enumerate(result_integration)
    if row[17].strip().lower() == "uploaded,success"
    and row[16].strip().lower() == "empty"
    and "not found" not in row[19].lower()

    and re.search(pattern_date, row[12], re.IGNORECASE)
]
print(indexs)
SetVar("indexs",indexs)

