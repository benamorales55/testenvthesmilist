import tkinter as tk
import threading
import os
import time

FILE_TO_WAIT = "D:/DentalRobotWork/01_DebugClients/TestSmilist/tet.txt"  # archivo que disparará el cierre
msg = "El proceso sigue en ejecución..."

def popup_notification():
    root = tk.Tk()
    root.overrideredirect(True)  
    root.attributes("-topmost", True)

    # tamaño y posición
    width, height = 300, 80
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


threading.Thread(target=popup_notification).start()
