import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalFunctions.script import gpvars
from datetime import datetime

today_date = gpvars("sheet")
today_date= datetime.strptime(today_date.strip(), '%Y-%m-%d')

def elg_data(filtered_data):
    current_year = datetime.now().year
    elg_items = [
        item for item in filtered_data
        if item['type'] == 'ELG' and 'ApptDate' in item
        ]
    elg_items.sort(key=lambda x: datetime.strptime(x['ApptDate'], '%Y-%m-%d'), reverse=True)
    already_verified_elg = any(
        datetime.strptime(item['ApptDate'], '%Y-%m-%d') > today_date
        for item in elg_items if 'ApptDate' in item
    )
    if elg_items:
        most_recent_elg = elg_items[0]
        print("Resultado (ELG con fecha mas reciente)")
        return most_recent_elg,already_verified_elg
    else:
        print("No hay elementos ELG.")
        return None,None