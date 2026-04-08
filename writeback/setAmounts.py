def set_amounts2(max_value=None):
    amounts = {}
    
    ins_info = Window("_WS_family_file") 
    win = schema["familyFile"]["insCoverage"]
    services = iv_config["input_wrapper_services"]["update_amounts"]

    group_name_base = "1199 SEIU NBF"
    group_name = data_supplies.get('verification_status', '')
    group_name_emblem = None

    if isinstance(group_name, str) and '|' in group_name:
        parts = group_name.split("|")
        if len(parts) > 1:
            group_name_emblem = parts[1].strip()

            if ',' in group_name_emblem:
                subparts = group_name_emblem.split(',')
                if len(subparts) > 1:
                    group_name_emblem = subparts[1].strip()
                else:
                    setLog('No group number after comma')
            else:
                setLog('No comma in emblem info')
        else:
            setLog('No second part after "|"')
    else:
        setLog('Invalid or missing key of verification_status')


    if not group_name_base.upper() in group_name_emblem.upper():
        amounts["Deductible"] = "0"
        amounts["AnnualMaximum"] = "3000"

    else:
        amounts_dict = generate_amounts_dict()
        if amounts_dict["ind_max"] == None:
            amounts["AnnualMaximum"] = amounts_dict['ind_max']
        if amounts_dict['ind_ded']: amounts["Deductible"] = amounts_dict['ind_ded']


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
        gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!Q{gpvars('index')}", [["Amounts updates in the review of emblem|"]])       
        setLog("amounts|")
    else:
        gsheet.load_to_sheet(gpvars('idSpreedSheet'), f"{gpvars('sheet')}!Q{gpvars('index')}", [["Amounts failed in the review of emblem|"]])       
        setLog("amounts ELG NOT FOUND")