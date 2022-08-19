import configparser

config = configparser.ConfigParser()
config.read('config.ini')

BOT_TOKEN = config.get('BOT', 'token')
OWNER_ID = config.getint('BOT', 'owner_id')

