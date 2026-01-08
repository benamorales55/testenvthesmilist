import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalFunctions.script import GetVar,cleanText,format_datetime,replace_empty

def readAppoinments(data, reportType):
    clinic = GetVar("practice")
    iv_config = eval(GetVar("iv_config"))
    

    empty = "EMPTY"
    print("************************ DATA IN THE FUCN", len(data))
    df = pd.DataFrame()
    
    cols = iv_config["columns"]
    src = "src" if reportType else "dbsrc"
    for col in cols: df[col["column"]] = data[col[src]] if src in col else empty

    #df.fillna(empty, inplace=True)
    #data.fillna(empty, inplace=True)
    df = df.applymap(replace_empty)
    data = data.applymap(replace_empty)


    # Complete data
    if reportType:
        df["Practice"] = clinic
        df["Primary"] = "Primary"
        df["SecData"] = data["SIns_Name"] + "," + data["SecSubID"].astype(str).str.split(".").str[0]

    df["Extraction Datetime"] = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

    # Clean data
    df["Carrier Name"] = df["Carrier Name"].apply(cleanText)
    df["Subscriber Zip Code"] = df["Subscriber Zip Code"].apply(lambda value: str(value).split(".")[0]).apply(cleanText)
    df["Patient First Name"] = df["Patient First Name"].apply(cleanText)
    df["Patient Last Name"] = df["Patient Last Name"].apply(cleanText)
    df["Subscriber First Name"] = df["Subscriber First Name"].apply(cleanText)
    df["Subscriber Last Name"] = df["Subscriber Last Name"].apply(cleanText)
    df["Employer Name PMS"] = df["Employer Name PMS"].apply(lambda x: x.replace("\\", "/").replace('"', "").replace("'", ""))
    df["GroupName"] = df["GroupName"].apply(lambda x: x.replace("\\", "/"))
    df["MemberID"] = df["MemberID"].apply(lambda x: x.replace("\\", ""))

    #formating dates news
    df['Subscriber DOB'] = df['Subscriber DOB'].apply(format_datetime)
    df['Patient DOB'] = df['Patient DOB'].apply(format_datetime)

    df['Appointment Date'] = pd.to_datetime(df['Appointment Date'])
    df['Appointment Date'] = df['Appointment Date'].dt.strftime('%H:%M')

    #test because it was eraesing the empty values
    df_with_id = df[df['Patient ID in the PMS'] != 'EMPTY']
    df_empty_id = df[df['Patient ID in the PMS'] == 'EMPTY']
    df_with_id = df_with_id.drop_duplicates(subset=['Patient ID in the PMS', 'Primary'])
    df = pd.concat([df_with_id, df_empty_id], ignore_index=True)

    #print(df[['Subscriber DOB','Patient DOB', 'Appointment Date']])
    # df = df.drop_duplicates(subset=['Patient ID in the PMS','Primary'])
    df = df.sort_values(by=['Practice','Carrier Name'])
    
    apptsList = []

    # Fill appointments list
    if reportType:
        for row in df.to_dict(orient='records'):
            if not reportType:
                secData =  row.pop("SecData")
                carrierNameSec, memberIdSec = secData.split(",")
        
            primRow = row.copy()
            apptsList.append(list(primRow.values())) # add primary
            
            if carrierNameSec != empty: # add secondary if exists
                secRow = row.copy()
                secRow["Carrier Name"], secRow["MemberID"], secRow["Primary"] = cleanText(carrierNameSec), memberIdSec, "Secondary"
                apptsList.append(list(secRow.values()))

        apptsList = [[value.strip() if isinstance(value, str) else value for value in row] for row in apptsList]
        
    else:
        apptsList = []
        for row in df.to_dict(orient='records'):
            apptsList.append(list(row.values()))

        apptsList = [[value.strip() if isinstance(value, str) else value for value in row] for row in apptsList]

        for row in apptsList:
            for col in row:
                if col == None:
                    print("row", row)
        # import time 
        # start = time.time()
        # df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        # print_log(SUCCESS, f"df len {len(df)}")



        # apptsList = df.values.tolist()
        # while (len(apptsList) < len (df)):
        #     time.sleep(0.1)
        #     apptsList = df.value.tolist()
        
        # tiempo = time.time() - start
        
        # print_log(SUCCESS, f"termino la coversion {tiempo}")

    #SetVar("result_integration", apptsList)  
    #print("******************** FUNCTION reads appts =>", apptsList, "ROWSSSS ")
    print("******************** FUNCTION reads appts =>", len(apptsList), "ROWSSSS ")
    print(apptsList)