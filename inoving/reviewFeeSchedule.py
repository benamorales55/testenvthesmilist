@handle_exceptions(update_log_wrapper("Exeption in review fee shedule|"))
def review_fee_schedule():
    print('review fee schedule')
    if "review_fee_schedule" in iv_config["input_wrapper_services"]:
        if iv_config["input_wrapper_services"]["review_fee_schedule"]:

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