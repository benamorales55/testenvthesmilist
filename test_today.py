import pandas as pd
import json
import re
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from globalVariables.carriersRegex import carriers_regex
from globalVariables.master import MASTER
from pathlib import Path
from globalVariables.script import static_regex,data_supplies
from globalFunctions.script import setLog,read_json,fillNumberWithZero,generate_amounts_dict



plans = ['PREFERRED', 'PREFERRED PLUS', 'PREFERRED PREMIER']
text = "EH PPO  PREFERRED  PLUS"

text_words = set(text.lower().split())

best_match = None
best_length = 0

for plan in plans:
    plan_words = set(plan.lower().split())
    
    if plan_words.issubset(text_words):
        if len(plan_words) > best_length:
            best_match = plan  
            best_length = len(plan_words)

print(best_match)