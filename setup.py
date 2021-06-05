# -*- coding: utf-8 -*-
from decouple import config


TOKEN = config("TOKEN", default="TOKEN")
PROXY = config("PROXY", default="PROXY")

# for htmlcsstoimage
HCTI_API_USER_ID = config("HCTI_API_USER_ID", default="HCTI_API_USER_ID")
HCTI_API_KEY = config("HCTI_API_KEY", default="HCTI_API_KEY")
