#1785000379
#617161537
from telethon.sync import TelegramClient
from telethon import functions, types
from telethon.tl.types import PeerUser
from dotenv import load_dotenv
import os

load_dotenv()
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
directory = 'sessions'
filename = os.listdir(os.path.join(os.getcwd(), directory))[0]
purefilename = os.path.splitext(os.path.basename(filename))[0]
with TelegramClient(purefilename, api_hash=api_hash, api_id=api_id, system_version="4.16.30-vxCUSTOM") as client:
    result = client.get_entity(PeerUser(617161537))
    print(result.stringify())