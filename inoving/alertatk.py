import os
import sys
import tkinter as tk
import _tkinter
import json
import textwrap

FLAG_FILE = f"C:/DentalRobot/Projects/IV/bots/scripts_testing/flagfile/flag_file_{os.getlogin()}.txt"


data_supplies = sys.argv[1]
sheet = sys.argv[2]

root = tk.Tk()
root.title("Information notice ")
root.geometry("300x150")
msg = textwrap.dedent(f"""
    NOTIFICATION DR
    USER: {os.getlogin()}
    DAY OF EXECUTION: {sheet}
    PATIENT ID: {data_supplies['patient_id']}
    PATIENT NAME: {data_supplies['patient_first_name']} {data_supplies['patient_last_name']}
""")

label = tk.Label(root, text=msg)
label.pack(padx=20, pady=20)

root.update_idletasks()

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

window_width = root.winfo_width()
window_height = root.winfo_height()

margin = 120 

x = screen_width - window_width - margin
y = screen_height - window_height - margin

root.geometry(f"{window_width}x{window_height}+{x}+{y}")

def check_flag():
    if os.path.exists(FLAG_FILE):
        root.destroy()
    else:
        root.after(500, check_flag)

root.after(500, check_flag)

root.mainloop()