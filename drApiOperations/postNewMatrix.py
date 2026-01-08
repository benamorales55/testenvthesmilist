import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from requests import post
from drApiVariables import hostGetPlan, headers

def post_new_matrix(matrix:dict):   
    try:
        response = post(hostGetPlan,headers=headers,json=matrix)
        print(response.text)
        return True
    except:
        return None 
        print(e)