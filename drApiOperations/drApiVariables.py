from dotenv import load_dotenv
import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
from globalFunctions.script import gpvars
from datetime import datetime
from base64 import b64encode
from hmac import new
from hashlib import sha512

conv = ""

env_path = gpvars("env_path")
iv_config = gpvars("iv_config",conv)

dateUTC = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
if not os.path.exists(env_path):
    raise Exception("The file of environment variables not exist")
load_dotenv(dotenv_path = env_path)

keysToSign = 'date host apiKey'
apiKey = os.getenv('apiKey')
hmac_user = os.getenv('hmac_user')
hmac_secret = os.getenv('hmac_secret')
hostString = os.getenv('hostString')
hostGetPatient = os.getenv('hostGetPatient')
hostGetPlan = os.getenv('hostGetPlan')

stringToSign = f"date: {dateUTC}\nhost: {hostString}\napiKey: {apiKey}"
hmac = b64encode(new(bytes(hmac_secret, "UTF-8"),  bytes(stringToSign, "UTF-8"), sha512).digest()).decode()
authorization = "hmac username=\"{hmac_user}\", algorithm=\"hmac-sha512\",headers=\"{keysToSign}\",signature=\"{hmac}\""

headers = {
 "Content-Type": "application/json",
 "apiKey": apiKey,
 "authorization": authorization,
 "date": dateUTC
 }

# print(hmac_secret)
# print(stringToSign)
# print(bytes(hmac_secret,"UTF-8"))
# print(bytes(stringToSign,"UTF-8"))
# print(new(bytes(hmac_secret, "UTF-8"),  bytes(stringToSign, "UTF-8"), sha512).digest())
# print(b64encode(new(bytes(hmac_secret, "UTF-8"),  bytes(stringToSign, "UTF-8"), sha512).digest()).decode())