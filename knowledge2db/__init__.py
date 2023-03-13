from knowledge2db import config
import configparser
import os

# try to load config from file
try:
    config_parser = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), "config.ini")
    # print(config_path)
    config_parser.read(config_path)
    config.naming = config_parser.get("DBGenerator", "naming")
    config.translate = config_parser.getboolean("Translator", "translate")
    config.translator = config_parser.get("Translator", "translator")
    config.db_prefix = config_parser.get("DBGenerator", "db_prefix")
    config.table_prefix = config_parser.get("DBGenerator", "table_prefix")
    config.debug = config_parser.getboolean("Debug", "debug")
    config.YOUDAO_URL = config_parser.get("Translator.Youdao", "YOUDAO_URL")
    config.APP_KEY = config_parser.get("Translator.Youdao", "APP_KEY")
    config.APP_SECRET = config_parser.get("Translator.Youdao", "APP_SECRET")
    config.CAIYUN_KEY = config_parser.get("Translator.Caiyun", "CAIYUN_KEY")
except Exception as e:
    # print("Error", e)
    print("Error when loading config file, please check again")

from knowledge2db import mindmap_loader, sql_generator, tree_utilities