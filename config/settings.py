import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

BROWSER_COOKIES = {
    "loginState": "true",
    "menuType": "Admin",
    "abbrCheckCookieFlg": "true",
    "lang": "En",
    "selno": "En",
    "vm": "Html",
    "bv": "Chrome/139.0.0.0",
    "pf": "PC",
    "uatype": "NN",
    "favmode": "false",
    "usr": "",
    "access": "",
    "param": "",
    "key": "",
    "InitialTransitionScreen": "",
    "loginUserName": "",
    "hostChange": "",
    "sourcePage": "1",
    "abbrRedojobingStatus": "allow",
    "logoutIF": "a_user.cgi",
    "notChange": "",
    "webUI": "new",
    "cou": "",
    "adm": ""
}
