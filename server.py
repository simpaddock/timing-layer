
from flask import Flask
from collections import OrderedDict
from json import dumps, loads
app = Flask(__name__)
from flask_cors import CORS
import os
import importlib
CORS(app)

CONFIG = None
PARSERS = None

def parseConfig():
  global CONFIG, PARSERS
  parentDir = os.path.dirname(os.path.realpath(__file__))
  configFilePath = os.path.join(parentDir, "config.json")
  parsersConfigFilePath = os.path.join(parentDir, "parsers", "parsers.json")
  with open(configFilePath, "r") as fh:
    CONFIG = loads(fh.read())
  with open(parsersConfigFilePath, "r") as fh:
    PARSERS = loads(fh.read())
    
parseConfig()

selectedParserModule= PARSERS[CONFIG["vendor"]]
module = importlib.import_module("parsers." + selectedParserModule)
parser = getattr(module, selectedParserModule )() 

@app.route("/")
def getData():
  global parser, CONFIG
  result = parser.parse(CONFIG["url"])
  return dumps(result)

app.run(debug=True)