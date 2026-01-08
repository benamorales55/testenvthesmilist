import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalFunctions.script import gpvars
from datetime import datetime

def validate_elgdate(eligibility_date):
    try:
        last_eligibility = datetime.strptime(eligibility_date.strip(), '%Y-%m-%d')
    except ValueError:
        print("Error: The eligibility date is not valid.")
        raise ValueError("The eligibility date must be in this format  'YYYY-MM-DD'.")
    apptDate = gpvars("sheet")
    apptDate  = datetime.strptime(apptDate.strip(), '%Y-%m-%d')
    return last_eligibility.year == apptDate.year and last_eligibility.month == apptDate.month