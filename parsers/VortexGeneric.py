
from datetime import datetime
import requests
import re
class VortexGeneric():
  def stripTags(self, value):
    return re.compile(r'<[^>]+>').sub('', value)
  def __init__(self):
    print("Created Vortex Motorsport Parser")
  def parse(self, url: str):
    content = requests.get(url).text
    positionTablePattern = r"<fieldset>.*</fieldset>"
    positionTableRaw = re.findall(positionTablePattern, content, re.DOTALL)
    if len(positionTableRaw) == 0:
      return ""
    positionTable = positionTableRaw[0]
    
    sessionInfoPattern = r"<td class=\'sessioninfo\'>(<b>)?(?P<name>([^\<]+))(</b>)?</td><td class=\'sessioninfo\'>(?P<value>(.*?)</td>)"

    sessionInfosRaw = re.findall(sessionInfoPattern, content, re.DOTALL)
    sessionInfos = {}
    replacements = {
      r"Sitzungsstatus": "SessionState",
      r"Streckenstatus": "TrackState",
      r"Sitzung":"Session",
      r"Streckenn.+sse": "TrackWetness",
      r"Windst.+": "TrackWetness",
      r"Temp Luft": "AirTemp",
      r"Temp Strecke": "TrackTemp",
      r"Serverzeit": "ServerTime",
      r"Betriebszeit": "RunTime",
      r"Streckenl.+": "TrackLength",
      r"Runden": "Laps",
      r"Restzeit":"RemainingTime"
    }
    for sessionInfoRaw in sessionInfosRaw:
      
      name = self.stripTags(sessionInfoRaw[1])
      for replacementKey,replacementValue in replacements.items():
        if re.match(replacementKey, name):
          name = replacementValue
          break
      value = self.stripTags(sessionInfoRaw[4])[1:].strip(" ")
      if "slite" in sessionInfoRaw[4]: # sektoreninfo
        if "y" in sessionInfoRaw[4]:
          value = "yellow"
        else:
          value = "green"
        name = name.replace("Sektorstatus","SectorState")
      if "&deg" in value:
        value = value.replace("&deg","").replace(" ;C","")
      if name == "SessionState":
        value = value.lower().replace("flag", "")
      if name == "Laps":
        parts = value.split("/")
        runnedLaps = parts[0]
        allLaps = parts[1]
        if allLaps != "-": # es gibt maximale rundenzahl
          name = "LeftDisplayString" 
          value =  runnedLaps + "/" + allLaps
        else:
          value = None
      if name == "Time Left" and "LeftDisplayString" not in sessionInfos:
        value = re.compile(r" \(.+\)").sub("",value)
        name = "LeftDisplayString" 

      if value is not None:
        sessionInfos[name] = value
    rowPattern = r"(<tr(.*?)</tr>)+"
    rows = re.findall(rowPattern, positionTable)
    columnPattern = r"<t(d|h)[^\>]{0,}>(.*?)</t(d|h)>"

    headers = []
    
    drivers=[]
    for index, row in enumerate(rows):
      driver = {}
      lastLap = None
      bestLap = None
      columns = re.findall(columnPattern, row[1], re.DOTALL)
      for columnIndex, column in enumerate(columns):
        oldValue = column[1]
        value = self.stripTags(column[1])
        if index == 0: #header
          headers.append(value)
        else:
          header = headers[columnIndex]
          # translate the header values
          if header == "Driver":
            nameParts = value.split(" ")
            driver["firstName"] = nameParts[0]
            driver["lastName"] = value.replace(driver["firstName"] +" ","")
          elif header == "Vehicle":
            nameParts = value.split("#")
            driver["teamName"] = nameParts[0]
            driver["numberString"] = nameParts[1]
          elif header == "Abstand":
            if index != 1:
              driver["status"] = value
          elif header == "Intervall":
            if index == 1:
              driver["status"] = value
          elif header == "Pitlane":
            if value == "PIT":
              driver["status"] = "pit"
            elif value != "-":
              driver["status"] = "out"
          elif header == "Status":
              if value != "Running":
                driver["status"] = "dnf"
          elif header == "Best Lap":
            lastLap = value
          elif header == "Last Lap":
            if value != "-":
              bestLap = value
          else:
            driver[header] = value

          print(header)
      if "status" not in driver or driver["status"] is None:
        print(lastLap, bestLap)
        if bestLap is not None:
          driver["status"] = bestLap
        else: 
          driver["status"] = lastLap


      if index != 0:    
        drivers.append(driver)
    return {
      "session": sessionInfos, 
      "drivers":  drivers,
      "currentDriver": drivers[0]}