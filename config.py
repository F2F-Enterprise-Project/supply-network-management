# config.py
from sqlalchemy import create_engine

engine = create_engine("sqlite:///supplynetwork.db", connect_args={"check_same_thread": False})

is_agnet_up = False
agnet_base_url = "http://146.190.243.241:8303/api/v1"
version = "0.2.1"
API_MAP = ""
