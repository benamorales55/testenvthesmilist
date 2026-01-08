import tkinter as tk
import threading
import time
import os



base_path = GetVar("base_pathP")
sheet = GetVar("sheet")
data_supplies = eval(GetVar("data_supplies"))
base_path_completed = f"{base_path}bots/scripts_testing/flagfile"

FILE_TO_WAIT = f"{base_path_completed}/flag_file_{os.getlogin()}.txt"

if os.path.exists(FILE_TO_WAIT):
    os.remove(FILE_TO_WAIT)
    
msg = f"""
NOTIFICATION DR
USER: {os.getlogin()}
DAY OF EXECUTION: {sheet}
PATIENT ID: {data_supplies['patient_id']}
PATIENT NAME: {data_supplies['patient_first_name']} {data_supplies['patient_last_name']}
"""

def popup_notification():
    root = tk.Tk()
    root.overrideredirect(True)  
    root.attributes("-topmost", True)

    
    width, height = 300, 120
    screen_width = root.winfo_screenwidth()
    x = screen_width - width - 10
    y = 10
    root.geometry(f"{width}x{height}+{x}+{y}")

    label = tk.Label(root, text=msg, bg="yellow", fg="black", font=("Arial", 12))
    label.pack(fill="both", expand=True)


    def check_file():
        if os.path.exists(FILE_TO_WAIT):
            root.destroy()
        else:
            root.after(1000, check_file)  

    root.after(1000, check_file)
    root.mainloop()

def wait_for_notification():
    while True:
        
        if os.path.exists(FILE_TO_WAIT):
            break
        time.sleep(1)

threading.Thread(target=wait_for_notification).start()
popup_notification()