import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")
SMB_USER = os.getenv("SMB_USER")
SMB_PASS = os.getenv("SMB_PASS")
SMB_IP = os.getenv("SMB_IP")

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

LOGIN_PAYLOAD = {
    "func": "PSL_LP1_LOG",
    "AuthType": "None",
    "TrackType": "",
    "ExtSvType": "0",
    "PswcForm": "",
    "Mode": "",
    "publicuser": "",
    "username": None,   # <-- placeholder
    "password": None,   # <-- placeholder
    "AuthorityType": "",
    "R_ADM": "AdminAdmin",
    "ExtServ": "0",
    "ViewMode": "",
    "BrowserMode": "",
    "Lang": "",
    "trackname": "",
    "trackpassword": ""
}

EXPORT_PAYLOAD = {
    "func": "PSL_AS_ADD_ADD",
    "AS_ADD_H_BUT": "Export",
    "AS_ADD_H_DUM": "",
    "AS_AB_R_EX": "on",
    "AS_ADD_R_FILE_TYPE": "CSV",
    "AS_ADD_T_PSS": "",
    "AS_ADD_R_SEL": "Abbrev",
    "AS_ADD_H_FILE_TYPE": "",
    "SMB_H_CHOOSE_TYPE": "",
    "SMB_H_HOST_NAME": "",
    "SMB_H_USER_NAME": "",
    "SMB_H_FILE_PATH": "",
    "SMB_H_FILE_TITLE": "",
}

IMPORT_PAYLOAD = {
    "func": "PSL_AS_ADD_ADD",
    "AS_ADD_H_BUT": "Import",
    "AS_ADD_H_DUM": "",
    "AS_ADD_T_PSS": "",
    "AS_ADD_R_IMP": "AddrImportType1",
    "AS_ADD_IMP_R_SEL": "IndividualAbbrev",
    "AS_ADD_R_TYPE": "",
    "SMB_H_CHOOSE_TYPE": "SMB",
    "SMB_H_HOST_NAME": None,      # <-- placeholders
    "SMB_H_USER_NAME": None,
    "SMB_H_FILE_PATH": None,
    "SMB_H_FILE_TITLE": None,
    "AS_ADD_F_FIL": "",
}
