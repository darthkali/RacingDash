# coding=utf-8
##################################################
# RacingDash by Danny Steinbrecher
# Version - v1.0
#
# based on RaceEssentials by Filip Topuzovic (Topuz)
# 
# Credits:
# Erwin Schmidt - Accurate delta calculation
# Jorge Alves - Inspiration and some app logic
# Rombik - Shared memory Sim Info code
# Minolin, Neys - Thanks for your contributions and inspiration to always do
# more and better
# Yachanay - TC/ABS/DRS performance optimization
# Wally Masterson - some changes
#
# None of the code below is to be redistributed
# or reused without the permission of the
# author(s).
##################################################
import ac
import acsys
import sys
import os.path
import platform
import datetime
import pickle
import bisect
import configparser
import threading
import raceessentials_lib.win32con
import codecs
import json
import re
import traceback

#from dash_lib import main

#sys.path.append("C:\\Users\\dannysteinbrecher\\AppData\\Local\\Programs\\Python\\Python37\\Lib\\site-packages")
#ac.log(str(sys.path))
#import discord




if platform.architecture()[0] == "64bit":
    sysdir = os.path.dirname(__file__) + '/stdlib64'
else:
    sysdir = os.path.dirname(__file__) + '/stdlib'

sys.path.insert(0, sysdir)
os.environ['PATH'] = os.environ['PATH'] + ";."

import ctypes
from ctypes import wintypes

from raceessentials_lib.sim_info import info

updateConfig = False

configPath = "apps/python/RacingDash/config.ini"

config = configparser.ConfigParser()
config.read(configPath)

if not config.has_section("RacingDash"):
    config.add_section("RacingDash")
    updateConfig = True


def getOrSetDefaultBoolean(config, key, default):
    global updateConfig
    try:
        return config.getboolean("RacingDash", key)
    except:
        config.set("RacingDash", key, str(default))
        updateConfig = True
        return default


def getOrSetDefaultFloat(config, key, default):
    global updateConfig
    try:
        return config.getfloat("RacingDash", key)
    except:
        config.set("RacingDash", key, str(default))
        updateConfig = True
        return default


speedInKPH = getOrSetDefaultBoolean(config, "speedInKPH", True)
backgroundOpacity = getOrSetDefaultBoolean(config, "backgroundopacity", True)
minimumWear = getOrSetDefaultFloat(config, "minimumWear", 0)
tyreWearScale = getOrSetDefaultFloat(config, "tyreWearScale", 16.66)
deltaResolution = getOrSetDefaultFloat(config, "deltaResolution", 0.05)
updateDelta = getOrSetDefaultFloat(config, "updateDelta", 0.05)
centralGear = getOrSetDefaultBoolean(config, "centralGear", False)
startClearsValidity = getOrSetDefaultBoolean(config, "startClearsValidity", True)
orangeLimitEnabled = getOrSetDefaultBoolean(config, "orangeLimitEnabled", True)
orangeLimitPercentage = getOrSetDefaultFloat(config, "orangeLimitPercentage", 0.9)
redLimitEnabled = getOrSetDefaultBoolean(config, "redLimitEnabled", True)
redLimitPercentage = getOrSetDefaultFloat(config, "redLimitPercentage", 0.94)
maxPowerRpmLights = getOrSetDefaultBoolean(config, "maxPowerRpmLights", True)
orangeLimitPowerPercentage = getOrSetDefaultFloat(config, "orangeLimitPowerPercentage", 0.94)
redLimitPowerPercentage = getOrSetDefaultFloat(config, "redLimitPowerPercentage", 1)

if updateConfig:
    with open(configPath, 'w') as fileConfig:
        config.write(fileConfig)

centralOffset = 0

###START GLOBAL VARIABLES

# Status helpers
oldStatusValue = 0
appActiveValue = 0

# Reset trigger
resetTrigger = 1

# Outlap helper
outLap = 0

# Pit check helper
carWasInPit = 0

# Timers
timerData = 1
timerDisplay = 0
timerDelay = 0

# Previous lap counter
previousLapValue = 0

# Fuel needed switcher
switcher = 0

# Needed because of references before assignments
rpmMaxValue = 0
trackGripValue = 0
tyreTemperatureValue = 0
tyrePressureValue = 0
tyreWearValue = 0
tyreCompoundValue = 0
tyreCompoundShort = 0
tyreCompoundCleaned = ""
previousTyreCompoundValue = 0
positionBoardValue = 0
positionValue = 0
totalCarsValue = 0
occupiedSlotsValue = 0
totalLapsValue = 0
sessionTimeValue = 0
sessionTypeValue = 0
systemClockValue = 0
fuelAmountValue = 0
airTemperatureValue = 0
roadTemperatureValue = 0
carInPitValue = 0
serverIPValue = 0
hasERS = 0
hasKERS = 0
turboPercentageValue = 0

personalBestLapValue = 0

compoundButtonValue = 0
pedalButtonValue = 0
tempColorButtonValue = 0
pressColorButtonValue = 0
wearColorButtonValue = 0
flagValue = 0

rpmPercentageValue = 0
turboMaxValue = 0
lapValidityValue = 0
lastLapValue = 0
previousBestLapValue = 0
bestLapValue = 0
previousPersonalBestLapValue = 0
previousLastLapValue = 0
fuelStartValue = 0
fuelEndValue = 0
relevantLapsNumber = 0
fuelSpentValue = 0
fuelPerLapValue = 0

idealPressureFront = 0
idealPressureRear = 0
minimumOptimalTemperature = 0
maximumOptimalTemperature = 0

# Delta related
deltaTimer = 0
timer = 0
previousLapProgressValue = 0
posList = []
timeList = []
lastPosList = []
lastTimeList = []
bestPosList = []
bestTimeList = []
personalBestPosList = []
personalBestTimeList = []
deltaButtonValue = 0
prevt = 0
prevt2 = 0
ttb = 0
ttb_old = 0
ttpb = 0
ttpb_old = 0

# Max power rpm
maxPowerRpm = 0
maxPower = 0
maxPowerRpmPercentageValue = 0

# Cache variables
absOldValue = -1
tcOldValue = -1

# Listen key loop helper
listenKeyActive = True

###END GLOBAL VARIABLES

# Set file and folder locations
personalBestDir = "apps/python/RacingDash/personal_best/"
compoundsPath = "apps/python/RacingDash/compounds/"
configDir = "apps/python/RacingDash/config/"

template = "apps/python/RacingDash/images/template.png"
template_opacity = "apps/python/RacingDash/images/template_opacity.png"
drs_available = "apps/python/RacingDash/images/drs_available.png"
drs_enabled = "apps/python/RacingDash/images/drs_enabled.png"


def acMain(ac_version):
    global maxPowerRpmLights, maxPowerRpm, maxPower
    global appWindow, PossibleNewLaptimLable, gearLabel, speedLabel, TestLable, PitTimeCounter, rpmLabel, currentLapLabel, trackGripLabel, lastLapLabel, bestLapLabel, personalBestLapLabel, tyreLabelWearFL, tyreLabelWearFR, tyreLabelWearRL, tyreLabelWearRR, tyreLabelTempFL, tyreLabelTempFR, tyreLabelTempRL, tyreLabelTempRR, tyreLabelPresFL, tyreLabelPresFR, tyreLabelPresRL, tyreLabelPresRR, deltaLabel, positionLabel, lapLabel, sessionTimeLabel, systemClockLabel, fuelAmountLabel, fuelPerLapLabel, fuelForLapsLabel, fuelNeededLabel, temperatureLabel
    global carValue, tyreCompoundLabel, drsLabel
    global filePersonalBest, personalBestLapValue
    global filePersonalBestPosList, filePersonalBestTimeList, personalBestPosList, personalBestTimeList
    global fileCompoundButton, compoundButtonValue
    global filePedalButton, pedalButtonValue, tempColorButtonValue, pressColorButtonValue, wearColorButtonValue
    global filetempColorButton, filepressColorButton, filewearColorButton
    global flagValue
    global fileDeltaButton, deltaButtonValue, deltaButton
    global fileAppActive, appActiveValue
    global compounds, modCompound
    global trackConfigValue, YTempPressWear
    global XTempPressWearCol_1, XTempPressWearCol_2, XTempPressWearCol_3
    global widthWindow, heightWindow, widthDRSLabel

    # Create file names
    carValue = ac.getCarName(0)
    trackValue = ac.getTrackName(0)
    trackConfigValue = ac.getTrackConfiguration(0)

    filePersonalBest = personalBestDir + carValue + "_" + trackValue + trackConfigValue + "_pb.ini"
    filePersonalBestPosList = personalBestDir + carValue + "_" + trackValue + trackConfigValue + "_pbposlist.ini"
    filePersonalBestTimeList = personalBestDir + carValue + "_" + trackValue + trackConfigValue + "_pbtimelist.ini"
    fileCompoundButton = configDir + "compoundButton.ini"
    filePedalButton = configDir + "pedalButton.ini"
    filetempColorButton = configDir + "tempColorButton.ini"
    filepressColorButton = configDir + "pressColorButton.ini"
    filewearColorButton = configDir + "wearColorButton.ini"
    fileDeltaButton = configDir + "deltaButton.ini"
    fileAppActive = configDir + "appActive.ini"

    # Load data from files
    personalBestLapValue = loadFile(filePersonalBest, personalBestLapValue)
    personalBestPosList = loadFile(filePersonalBestPosList, personalBestPosList)
    personalBestTimeList = loadFile(filePersonalBestTimeList, personalBestTimeList)
    compoundButtonValue = loadFile(fileCompoundButton, compoundButtonValue)
    pedalButtonValue = loadFile(filePedalButton, pedalButtonValue)
    tempColorButtonValue = loadFile(filetempColorButton, tempColorButtonValue)
    pressColorButtonValue = loadFile(filepressColorButton, pressColorButtonValue)
    wearColorButtonValue = loadFile(filewearColorButton, wearColorButtonValue)
    deltaButtonValue = loadFile(fileDeltaButton, deltaButtonValue)
    appActiveValue = loadFile(fileAppActive, appActiveValue)

    # Figure out what is the max power rpm
    if maxPowerRpmLights:
        try:
            with codecs.open("content/cars/" + carValue + "/ui/ui_car.json", "r", "utf-8-sig") as uiFile:
                uiDataString = uiFile.read().replace('\r', '').replace('\n', '').replace('\t', '')
            uiDataJson = json.loads(uiDataString)
            for step in uiDataJson["powerCurve"]:
                if int(step[1]) >= maxPower:
                    maxPower = int(step[1])
                    maxPowerRpm = int(step[0])
        except:
            ac.console("RacingDash: UTF ui_car.json failed to load")
            try:
                with codecs.open("content/cars/" + carValue + "/ui/ui_car.json", "r", "latin-1") as uiFile:
                    uiDataString = uiFile.read().replace('\r', '').replace('\n', '').replace('\t', '')
                uiDataJson = json.loads(uiDataString)
                for step in uiDataJson["powerCurve"]:
                    if int(step[1]) >= maxPower:
                        maxPower = int(step[1])
                        maxPowerRpm = int(step[0])
            except:
                ac.console("RacingDash: ANSI ui_car.json failed to load")
                maxPowerRpmLights = False

    # Initialize font
    ac.initFont(0, "Consolas", 1, 1)

    # Initialize configparsers
    compounds = configparser.ConfigParser()
    compounds.read(compoundsPath + "compounds.ini")
    modCompound = configparser.ConfigParser()
    modCompound.read(compoundsPath + carValue + ".ini")

    # App window
    widthWindow = 735
    heightWindow = 134
    appWindow = ac.newApp("RacingDash")
    ac.setTitle(appWindow, "")
    ac.drawBorder(appWindow, 0)
    ac.setIconPosition(appWindow, 0, -10000)
    ac.setSize(appWindow, widthWindow, heightWindow)
    ac.setVisible(appWindow, appActiveValue)

    if backgroundOpacity:
        ac.setBackgroundTexture(appWindow, template_opacity)
    else:
        ac.setBackgroundTexture(appWindow, template)

    ###START CREATING LABELS

    # TestLable
    TestLable = ac.addLabel(appWindow, "")
    ac.setPosition(TestLable, 0, -40)
    ac.setFontSize(TestLable, 13)
    ac.setCustomFont(TestLable, "Consolas", 0, 1)

    # VersionLable
    VersionLable = ac.addLabel(appWindow, "v1.2")
    ac.setPosition(VersionLable, 690, 118)
    ac.setFontSize(VersionLable, 10)
    ac.setCustomFont(VersionLable, "Consolas", 0, 1)
    ac.setFontAlignment(VersionLable, "right")

    # Gear
    gearLabel = ac.addLabel(appWindow, "-")
    ac.setPosition(gearLabel, 7, -9)
    ac.setFontSize(gearLabel, 96)
    ac.setCustomFont(gearLabel, "Consolas", 0, 1)

    # Speed
    speedLabel = ac.addLabel(appWindow, "---")
    ac.setPosition(speedLabel, 65, 8)
    ac.setFontSize(speedLabel, 36)
    ac.setCustomFont(speedLabel, "Consolas", 0, 1)
    ac.setFontAlignment(speedLabel, "left")

    # RPM
    rpmLabel = ac.addLabel(appWindow, "---- rpm")
    ac.setPosition(rpmLabel, 140, 15)
    ac.setFontSize(rpmLabel, 13)
    ac.setCustomFont(rpmLabel, "Consolas", 0, 1)

    # DRS
    widthDRSLabel = 200
    drsLabel = ac.addLabel(appWindow, "")
    ac.setPosition(drsLabel, widthWindow / 2 - widthDRSLabel / 2, -20)
    ac.setSize(drsLabel, widthDRSLabel, 20)

    # Current lap
    currentLapLabel = ac.addLabel(appWindow, "-:--.---")
    ac.setPosition(currentLapLabel, 217, 6)
    ac.setFontSize(currentLapLabel, 24)
    ac.setCustomFont(currentLapLabel, "Consolas", 0, 1)

    # Last lap
    lastLapLabel = ac.addLabel(appWindow, "L: -:--.---")
    ac.setPosition(lastLapLabel, 217, 35)
    ac.setFontSize(lastLapLabel, 18)
    ac.setCustomFont(lastLapLabel, "Consolas", 0, 1)

    # Best lap
    bestLapLabel = ac.addLabel(appWindow, "B: -:--.---")
    ac.setPosition(bestLapLabel, 217, 55)
    ac.setFontSize(bestLapLabel, 18)
    ac.setCustomFont(bestLapLabel, "Consolas", 0, 1)

    # Personal best lap
    personalBestLapLabel = ac.addLabel(appWindow, "P: -:--.---")
    ac.setPosition(personalBestLapLabel, 217, 75)
    ac.setFontSize(personalBestLapLabel, 18)
    ac.setCustomFont(personalBestLapLabel, "Consolas", 0, 1)

    ############ Tyre Temperatur, Pressure, Wear ############
    XTempPressWearCol_1 = 635
    XTempPressWearCol_2 = XTempPressWearCol_1 + 16
    XTempPressWearCol_3 = XTempPressWearCol_2 + 30
    YTempPressWear = 5  # Höhe der Labels für Temperatur, Pressure, Wear	 -	1. Reihe
    # Tyre temperature	--------------------------------------
    tyreLabelWear = ac.addLabel(appWindow, "Temp:")
    ac.setPosition(tyreLabelWear, XTempPressWearCol_1, YTempPressWear)
    ac.setFontSize(tyreLabelWear, 15)
    ac.setCustomFont(tyreLabelWear, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelWear, "right")

    # Tyre FL temperature
    tyreLabelTempFL = ac.addLabel(appWindow, "--")
    ac.setPosition(tyreLabelTempFL, XTempPressWearCol_2, YTempPressWear)
    ac.setFontSize(tyreLabelTempFL, 15)
    ac.setCustomFont(tyreLabelTempFL, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelTempFL, "center")

    # Tyre FR temperature
    tyreLabelTempFR = ac.addLabel(appWindow, "--")
    ac.setPosition(tyreLabelTempFR, XTempPressWearCol_3, YTempPressWear)
    ac.setFontSize(tyreLabelTempFR, 15)
    ac.setCustomFont(tyreLabelTempFR, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelTempFR, "center")

    YTempPressWear += 15  # 2. Reihe
    # Tyre RL temperature
    tyreLabelTempRL = ac.addLabel(appWindow, "--")
    ac.setPosition(tyreLabelTempRL, XTempPressWearCol_2, YTempPressWear)
    ac.setFontSize(tyreLabelTempRL, 15)
    ac.setCustomFont(tyreLabelTempRL, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelTempRL, "center")

    # Tyre RR temperature
    tyreLabelTempRR = ac.addLabel(appWindow, "--")
    ac.setPosition(tyreLabelTempRR, XTempPressWearCol_3, YTempPressWear)
    ac.setFontSize(tyreLabelTempRR, 15)
    ac.setCustomFont(tyreLabelTempRR, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelTempRR, "center")

    YTempPressWear += 20  # 3. Reihe
    # Tyre pressure	--------------------------------------
    tyreLabelWear = ac.addLabel(appWindow, "Press:")
    ac.setPosition(tyreLabelWear, XTempPressWearCol_1, YTempPressWear)
    ac.setFontSize(tyreLabelWear, 15)
    ac.setCustomFont(tyreLabelWear, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelWear, "right")

    # Tyre FL pressure
    tyreLabelPresFL = ac.addLabel(appWindow, "--")
    ac.setPosition(tyreLabelPresFL, XTempPressWearCol_2, YTempPressWear)
    ac.setFontSize(tyreLabelPresFL, 15)
    ac.setCustomFont(tyreLabelPresFL, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelPresFL, "center")

    # Tyre FR pressure
    tyreLabelPresFR = ac.addLabel(appWindow, "--")
    ac.setPosition(tyreLabelPresFR, XTempPressWearCol_3, YTempPressWear)
    ac.setFontSize(tyreLabelPresFR, 15)
    ac.setCustomFont(tyreLabelPresFR, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelPresFR, "center")

    YTempPressWear += 16  # 4. Reihe
    # Tyre RL pressure
    tyreLabelPresRL = ac.addLabel(appWindow, "--")
    ac.setPosition(tyreLabelPresRL, XTempPressWearCol_2, YTempPressWear)
    ac.setFontSize(tyreLabelPresRL, 15)
    ac.setCustomFont(tyreLabelPresRL, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelPresRL, "center")

    # Tyre RR pressure
    tyreLabelPresRR = ac.addLabel(appWindow, "--")
    ac.setPosition(tyreLabelPresRR, XTempPressWearCol_3, YTempPressWear)
    ac.setFontSize(tyreLabelPresRR, 15)
    ac.setCustomFont(tyreLabelPresRR, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelPresRR, "center")

    YTempPressWear += 20  # 5. Reihe
    # Tyre Wear	--------------------------------------
    tyreLabelWear = ac.addLabel(appWindow, "Wear:")
    ac.setPosition(tyreLabelWear, XTempPressWearCol_1, YTempPressWear)
    ac.setFontSize(tyreLabelWear, 15)
    ac.setCustomFont(tyreLabelWear, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelWear, "right")

    # Tyre FL wear
    tyreLabelWearFL = ac.addLabel(appWindow, "")
    ac.setPosition(tyreLabelWearFL, XTempPressWearCol_2, YTempPressWear)
    ac.setFontSize(tyreLabelWearFL, 15)
    ac.setCustomFont(tyreLabelWearFL, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelWearFL, "center")

    # Tyre FR wear
    tyreLabelWearFR = ac.addLabel(appWindow, "")
    ac.setPosition(tyreLabelWearFR, XTempPressWearCol_3, YTempPressWear)
    ac.setFontSize(tyreLabelWearFR, 15)
    ac.setCustomFont(tyreLabelWearFR, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelWearFR, "center")

    YTempPressWear += 16  # 6. Reihe
    # Tyre RL wear
    tyreLabelWearRL = ac.addLabel(appWindow, "")
    ac.setPosition(tyreLabelWearRL, XTempPressWearCol_2, YTempPressWear)
    ac.setFontSize(tyreLabelWearRL, 15)
    ac.setCustomFont(tyreLabelWearRL, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelWearRL, "center")

    # Tyre RR wear
    tyreLabelWearRR = ac.addLabel(appWindow, "")
    ac.setPosition(tyreLabelWearRR, XTempPressWearCol_3, YTempPressWear)
    ac.setFontSize(tyreLabelWearRR, 15)
    ac.setCustomFont(tyreLabelWearRR, "Consolas", 0, 1)
    ac.setFontAlignment(tyreLabelWearRR, "center")

    # DeltaButton
    deltaButton = ac.addButton(appWindow, "")
    ac.setPosition(deltaButton, 355, 39)
    ac.setSize(deltaButton, 93, 52)
    ac.setFontSize(deltaButton, 13)
    ac.setCustomFont(deltaButton, "Consolas", 0, 1)
    ac.drawBorder(deltaButton, 0)
    ac.setBackgroundOpacity(deltaButton, 0)
    ac.addOnClickedListener(deltaButton, deltaButtonClicked)

    # Delta
    deltaLabel = ac.addLabel(appWindow, "--.--")
    ac.setPosition(deltaLabel, 399, 53)
    ac.setFontSize(deltaLabel, 24)
    ac.setCustomFont(deltaLabel, "Consolas", 0, 1)
    ac.setFontAlignment(deltaLabel, "center")

    # Position
    positionLabel = ac.addLabel(appWindow, "Pos: -/-")
    ac.setPosition(positionLabel, 11, 89)
    ac.setFontSize(positionLabel, 18)
    ac.setCustomFont(positionLabel, "Consolas", 0, 1)

    # Lap
    lapLabel = ac.addLabel(appWindow, "Lap: -/-")
    ac.setPosition(lapLabel, 11, 107)
    ac.setFontSize(lapLabel, 18)
    ac.setCustomFont(lapLabel, "Consolas", 0, 1)

    # System clock
    systemClockLabel = ac.addLabel(appWindow, "Time: --:--")
    ac.setPosition(systemClockLabel, 496, 6)
    ac.setFontSize(systemClockLabel, 13)
    ac.setCustomFont(systemClockLabel, "Consolas", 0, 1)

    # Session time
    sessionTimeLabel = ac.addLabel(appWindow, "Rem: --:--")
    ac.setPosition(sessionTimeLabel, 503, 21)
    ac.setFontSize(sessionTimeLabel, 13)
    ac.setCustomFont(sessionTimeLabel, "Consolas", 0, 1)

    # Fuel amount
    fuelAmountLabel = ac.addLabel(appWindow, "--.- L")
    ac.setPosition(fuelAmountLabel, 517, 66)
    ac.setFontSize(fuelAmountLabel, 13)
    ac.setCustomFont(fuelAmountLabel, "Consolas", 0, 1)

    # Fuel per lap
    fuelPerLapLabel = ac.addLabel(appWindow, "Usage: --.-")
    ac.setPosition(fuelPerLapLabel, 494, 81)
    ac.setFontSize(fuelPerLapLabel, 13)
    ac.setCustomFont(fuelPerLapLabel, "Consolas", 0, 1)

    # Fuel for laps
    fuelForLapsLabel = ac.addLabel(appWindow, "Laps Left: --.-")
    ac.setPosition(fuelForLapsLabel, 467, 95)
    ac.setFontSize(fuelForLapsLabel, 13)
    ac.setCustomFont(fuelForLapsLabel, "Consolas", 0, 1)

    # Fuel needed
    fuelNeededLabel = ac.addLabel(appWindow, "Required: --.-")
    ac.setPosition(fuelNeededLabel, 473, 111)
    ac.setFontSize(fuelNeededLabel, 13)
    ac.setCustomFont(fuelNeededLabel, "Consolas", 0, 1)

    # Ambient temperature
    temperatureLabel = ac.addLabel(appWindow, "Tmp: --C/--C")
    ac.setPosition(temperatureLabel, 140, 97)
    ac.setFontSize(temperatureLabel, 13)
    ac.setCustomFont(temperatureLabel, "Consolas", 0, 1)

    # Track grip
    trackGripLabel = ac.addLabel(appWindow, "Track: --%")
    ac.setPosition(trackGripLabel, 125, 111)
    ac.setFontSize(trackGripLabel, 13)
    ac.setCustomFont(trackGripLabel, "Consolas", 0, 1)

    # Tyre compound
    tyreCompoundLabel = ac.addLabel(appWindow, "--")
    ac.setPosition(tyreCompoundLabel, 240, 111)
    ac.setFontSize(tyreCompoundLabel, 13)
    ac.setCustomFont(tyreCompoundLabel, "Consolas", 0, 1)

    # PitTimeCounter
    PitTimeCounter = ac.addLabel(appWindow, "Pit Time: 0.00")
    ac.setPosition(PitTimeCounter, 240, 97)
    ac.setFontSize(PitTimeCounter, 13)
    ac.setCustomFont(PitTimeCounter, "Consolas", 0, 1)
    ac.setFontAlignment(PitTimeCounter, "left")

    # Possible New Laptime
    PossibleNewLaptimLable = ac.addLabel(appWindow, "-:--.---")
    ac.setPosition(PossibleNewLaptimLable, 369, 93)
    ac.setFontSize(PossibleNewLaptimLable, 13)
    ac.setCustomFont(PossibleNewLaptimLable, "Consolas", 0, 1)
    ###END CREATING LABELS

    ###START CREATING BUTTONS
    # PedalButton
    pedalButton = ac.addButton(appWindow, "")
    ac.setPosition(pedalButton, 142, 33)
    ac.setSize(pedalButton, 50, 40)
    ac.drawBorder(pedalButton, 0)
    ac.setBackgroundOpacity(pedalButton, 0)
    ac.addOnClickedListener(pedalButton, pedalButtonClicked)

    # Temperatur, Pressure, Wear - Buttons
    XTempPressWearButtons = XTempPressWearCol_1 - 50
    YTempPressWear = 5  # Höhe der Labels für Temperatur, Pressure, Wear	 -	1. Reihe

    # TempColorButton
    tempColorButton = ac.addButton(appWindow, "")
    ac.setPosition(tempColorButton, XTempPressWearButtons, YTempPressWear)
    ac.setSize(tempColorButton, 110, 30)
    ac.drawBorder(tempColorButton, 0)
    ac.setBackgroundOpacity(tempColorButton, 0)
    ac.addOnClickedListener(tempColorButton, tempColorButtonClicked)

    # PressColorButton
    YTempPressWear += 43
    pressColorButton = ac.addButton(appWindow, "")
    ac.setPosition(pressColorButton, XTempPressWearButtons, YTempPressWear)
    ac.setSize(pressColorButton, 110, 30)
    ac.drawBorder(pressColorButton, 0)
    ac.setBackgroundOpacity(pressColorButton, 0)
    ac.addOnClickedListener(pressColorButton, pressColorButtonClicked)

    # WearColorButton
    YTempPressWear += 43
    wearColorButton = ac.addButton(appWindow, "")
    ac.setPosition(wearColorButton, XTempPressWearButtons, YTempPressWear)
    ac.setSize(wearColorButton, 110, 30)
    ac.drawBorder(wearColorButton, 0)
    ac.setBackgroundOpacity(wearColorButton, 0)
    ac.addOnClickedListener(wearColorButton, wearColorButtonClicked)
    ###END CREATING BUTTONS

    # App visibility listeners
    ac.addOnAppActivatedListener(appWindow, appActivated)
    ac.addOnAppDismissedListener(appWindow, appDismissed)

    ###START UPDATE LABELS WITH LOADED DATA

    # Personal best lap
    if personalBestLapValue > 0:
        personalBestLapValueSeconds = (personalBestLapValue / 1000) % 60
        personalBestLapValueMinutes = (personalBestLapValue // 1000) // 60
        ac.setText(personalBestLapLabel,
                   "P: {:.0f}:{:06.3f}".format(personalBestLapValueMinutes, personalBestLapValueSeconds))

    # Delta
    if deltaButtonValue == 0:
        ac.setText(deltaButton, "Delta B:")
    elif deltaButtonValue == 1:
        ac.setText(deltaButton, "Delta P:")

    ###END UPDATE LABELS WITH LOADED DATA

    # Render callback for drawing bars
    ac.addRenderCallback(appWindow, onFormRender)

    return "RacingDash"




def acUpdate(deltaT):
    global appWindow, PossibleNewLaptimLable, gearLabel, speedLabel, rpmLabel, currentLapLabel, trackGripLabel, lastLapLabel, bestLapLabel, personalBestLapLabel
    global tyreLabelWearFL, tyreLabelWearFR, tyreLabelWearRL, tyreLabelWearRR, tyreLabelTempFL, tyreLabelTempFR, tyreLabelTempRL, tyreLabelTempRR, tyreLabelPresFL, tyreLabelPresFR, tyreLabelPresRL
    global tyreLabelPresRR, deltaLabel, positionLabel, lapLabel, sessionTimeLabel, systemClockLabel, fuelAmountLabel, fuelPerLapLabel, fuelForLapsLabel, fuelNeededLabel, temperatureLabel

    global carValue
    global personalBestLapValue
    global personalBestPosList, personalBestTimeList
    global compoundButtonValue, pedalButtonValue, tempColorButtonValue, pressColorButtonValue, wearColorButtonValue
    global flagValue
    global trackConfigValue

    global oldStatusValue, resetTrigger, outLap, carWasInPit, timerData, timerDisplay, timerDelay, previousLapValue, switcher
    global deltaResolution, updateDelta, deltaTimer, timer, previousLapProgressValue, posList, timeList, lastPosList, lastTimeList, bestPosList, bestTimeList, prevt, prevt2, ttb, ttb_old, ttpb, ttpb_old
    global turboMaxValue, lapValidityValue, lastLapValue, previousBestLapValue, previousLastLapValue, bestLapValue, previousPersonalBestLapValue, previousLastLapValue, fuelStartValue, relevantLapsNumber
    global fuelSpentValue, fuelPerLapValue
    global compounds, modCompound, idealPressureFront, idealPressureRear, minimumOptimalTemperature, maximumOptimalTemperature

    global speedValueKPH, rpmPercentageValue, maxPowerRpmPercentageValue, turboPercentageValue, kersChargeValue, kersInputValue, tyreWearValue, slipRatioValue, ttpb, clutchValue, brakeValue, throttleValue
    global ffbValue, ersCurrentKJValue, ersMaxJValue
    global rpmMaxValue, trackGripValue, tyreTemperatureValue, tyrePressureValue, tyreWearValue, tyreCompoundValue, tyreCompoundShort, tyreCompoundCleaned, previousTyreCompoundValue, positionBoardValue
    global positionValue, totalCarsValue, occupiedSlotsValue, totalLapsValue, sessionTimeValue, sessionTypeValue, systemClockValue, fuelAmountValue, airTemperatureValue, roadTemperatureValue, carInPitValue
    global serverIPValue, hasERS, hasKERS
    global carDamageValue
    global maxPowerRpmLights, maxPowerRpm
    global absOldValue, tcOldValue
    global tyreWearValueFL, tyreWearValueFR, tyreWearValueRL, tyreWearValueRR
    global rFL, gFL, bFL, rFR, gFR, bFR, rRL, gRL, bRL, rRR, gRR, bRR
    global midWear, drsLabel
    global TempColorRange, pessureRange
    global carDamageValueFront, carDamageValueBack, carDamageValueLeft, carDamageValueRight
    global maxColorRangeBlue, maxColorRangeGreen, rColor, gColor, bcolor
    global pitCounter

    ###START RUN THIS INDENTATION WITH EACH FRAME

    try:
        ac.setBackgroundOpacity(appWindow, 0)

        # Check if the game is replay mode
        statusValue = info.graphics.status

        if statusValue == 1:
            oldStatusValue = 1
            ac.setVisible(appWindow, 0)
        if statusValue != 1 and oldStatusValue and appActiveValue:
            oldStatusValue = 0
            ac.setVisible(appWindow, 1)

        if statusValue != 1:

            # Fetch data once per frame
            gearValue = ac.getCarState(0, acsys.CS.Gear)
            speedValueKPH = ac.getCarState(0, acsys.CS.SpeedKMH)
            speedValueMPH = ac.getCarState(0, acsys.CS.SpeedMPH)
            rpmValue = ac.getCarState(0, acsys.CS.RPM)
            kersChargeValue = ac.getCarState(0, acsys.CS.KersCharge)
            kersInputValue = ac.getCarState(0, acsys.CS.KersInput)
            currentLapValue = info.graphics.iCurrentTime
            tiresOutValue = info.physics.numberOfTyresOut
            slipRatioValue = ac.getCarState(0, acsys.CS.SlipRatio)
            lapValue = ac.getCarState(0, acsys.CS.LapCount)
            if trackConfigValue == "touristenfahrten":  # A dirty hack for Nordschleife Tourist
                lapProgressValue = (ac.getCarState(0, acsys.CS.NormalizedSplinePosition) + 0.0480) % 1
            else:
                lapProgressValue = ac.getCarState(0, acsys.CS.NormalizedSplinePosition)
            clutchValue = ac.getCarState(0, acsys.CS.Clutch)
            brakeValue = ac.getCarState(0, acsys.CS.Brake)
            throttleValue = ac.getCarState(0, acsys.CS.Gas)
            ffbValue = ac.getCarState(0, acsys.CS.LastFF)
            if hasERS or hasKERS:
                ersCurrentKJValue = ac.getCarState(0, acsys.CS.ERSCurrentKJ)
                ersMaxJValue = ac.getCarState(0, acsys.CS.ERSMaxJ)
                if carValue == "ks_ferrari_sf15t":
                    ersMaxJValue = 4000000

            # Fetch data once per second
            timerData += deltaT

            if timerData > 1:
                timerData = 0

                if info.static.maxRpm:
                    rpmMaxValue = info.static.maxRpm
                if info.static.maxTurboBoost > turboMaxValue:
                    turboMaxValue = info.static.maxTurboBoost
                trackGripValue = info.graphics.surfaceGrip
                tyreTemperatureValue = ac.getCarState(0, acsys.CS.CurrentTyresCoreTemp)
                tyrePressureValue = ac.getCarState(0, acsys.CS.DynamicPressure)
                tyreWearValue = info.physics.tyreWear
                carDamageValue = info.physics.carDamage
                flagValue = info.graphics.flag
                tyreCompoundValue = info.graphics.tyreCompound
                tyreCompoundShort = tyreCompoundValue[tyreCompoundValue.find("(") + 1:tyreCompoundValue.find(")")]
                tyreCompoundCleaned = re.sub('\_+$', '', re.sub(r'[^\w]+', '_', tyreCompoundValue)).lower()
                positionBoardValue = ac.getCarLeaderboardPosition(0)
                positionValue = ac.getCarRealTimeLeaderboardPosition(0)
                totalCarsValue = ac.getCarsCount()
                occupiedSlotsValue = ac.getServerSlotsCount()
                totalLapsValue = info.graphics.numberOfLaps
                sessionTimeValue = info.graphics.sessionTimeLeft
                sessionTypeValue = info.graphics.session
                systemClockValue = datetime.datetime.now()
                fuelAmountValue = info.physics.fuel
                airTemperatureValue = info.physics.airTemp
                roadTemperatureValue = info.physics.roadTemp
                carInPitValue = ac.isCarInPitline(0)
                serverIPValue = ac.getServerIP()
                hasERS = info.static.hasERS
                hasKERS = info.static.hasKERS

            # Reset session check
            if resetTrigger == 1 and currentLapValue < 500 and lapValue == 0 and speedValueKPH < 1:
                resetTrigger = 0
                outLap = 1
                previousLapValue = 0
                lapValidityValue = 0
                ac.setFontColor(lastLapLabel, 1, 1, 1, 1)
                lastLapValue = 0
                previousLastLapValue = 0
                ac.setText(lastLapLabel, "L: -:--.---")
                previousBestLapValue = 0
                bestLapValue = 0
                ac.setText(bestLapLabel, "B: -:--.---")
                previousPersonalBestLapValue = 0
                relevantLapsNumber = 0
                fuelSpentValue = 0
                fuelPerLapValue = 0
                ac.setText(fuelPerLapLabel, "Usage: --.-")
                ac.setFontColor(deltaLabel, 1, 1, 1, 1)
                prevt = 0
                prevt2 = 0
                ac.setText(deltaLabel, "--.--")
                lastPosList = []
                lastTimeList = []
                bestPosList = []
                bestTimeList = []
                pitCounter = 0
            elif resetTrigger == 0 and currentLapValue > 500:
                resetTrigger = 1
            if (currentLapValue < 1000 and lapValue == 0 and (
                    speedValueKPH > 10 or speedValueMPH > 10)) or sessionTypeValue == 2:
                outLap = 0

            ###START DATA DISPLAY

            # Gear
            if gearValue == 0:
                ac.setText(gearLabel, "R")
            elif gearValue == 1:
                ac.setText(gearLabel, "N")
            else:
                ac.setText(gearLabel, "{}".format(gearValue - 1))

            if rpmValue > rpmMaxValue:
                rpmMaxValue = rpmValue
            if rpmMaxValue:
                rpmPercentageValue = rpmValue / rpmMaxValue
            if rpmMaxValue and (not maxPowerRpmLights or maxPowerRpm >= rpmMaxValue):
                if orangeLimitEnabled and rpmPercentageValue > orangeLimitPercentage and rpmPercentageValue < redLimitPercentage:
                    ac.setFontColor(gearLabel, 1, 0.46, 0.18, 1)
                elif redLimitEnabled and rpmPercentageValue >= redLimitPercentage:
                    ac.setFontColor(gearLabel, 1, 0.18, 0.18, 1)
                else:
                    ac.setFontColor(gearLabel, 1, 1, 1, 1)
            elif maxPowerRpm and maxPowerRpm < rpmMaxValue and maxPowerRpmLights:
                maxPowerRpmPercentageValue = rpmValue / maxPowerRpm
                if orangeLimitEnabled and maxPowerRpmPercentageValue > orangeLimitPowerPercentage and maxPowerRpmPercentageValue < redLimitPowerPercentage:
                    ac.setFontColor(gearLabel, 1, 0.46, 0.18, 1)
                elif redLimitEnabled and maxPowerRpmPercentageValue >= redLimitPowerPercentage:
                    ac.setFontColor(gearLabel, 1, 0.18, 0.18, 1)
                else:
                    ac.setFontColor(gearLabel, 1, 1, 1, 1)

            # Speed
            if speedInKPH:
                ac.setText(speedLabel, "{:.0f}".format(speedValueKPH))
            else:
                ac.setText(speedLabel, "{:.0f}".format(speedValueMPH))

            # RPM
            ac.setText(rpmLabel, "RPM: {:.0f}".format(rpmValue))

            if carInPitValue:
                pitCounter += deltaT
                ac.setText(PitTimeCounter, "Pit Time: {:.2f} ".format(pitCounter))
            else:
                pitCounter = 0

            # Current lap
            currentLapValueSeconds = (currentLapValue / 1000) % 60
            currentLapValueMinutes = (currentLapValue // 1000) // 60
            ac.setText(currentLapLabel, "{:.0f}:{:06.3f}".format(currentLapValueMinutes, currentLapValueSeconds))

            # Lap validity
            if tiresOutValue > 2 or carWasInPit:
                lapValidityValue = 1
            if lapValidityValue:
                ac.setFontColor(currentLapLabel, 1, 0.18, 0.18, 1)
            else:
                ac.setFontColor(currentLapLabel, 1, 1, 1, 1)

            # Tyre compound
            # if compoundButtonValue:
            # ac.setText(tyreCompoundLabel, "TEas")
            # else:
            #	ac.setText(tyreCompoundLabel, "{}: {}psi/{}psi".format(tyreCompoundShort,
            #	idealPressureFront, idealPressureRear))

            ac.setText(tyreCompoundLabel, "TyreCompound: {}".format(tyreCompoundShort))

            # Delta
            deltaTimer += deltaT
            timer += deltaT

            if deltaTimer > deltaResolution:
                deltaTimer = 0
                if lapProgressValue > previousLapProgressValue and lapProgressValue < 1:
                    timeList.append(currentLapValue)
                    posList.append(lapProgressValue)
                previousLapProgressValue = lapProgressValue

            if timer > updateDelta and currentLapValue > 4000 and lapProgressValue > 0.005 and lapProgressValue < 0.995 and carWasInPit == 0:
                timer = 0
                if bestLapValue and deltaButtonValue == 0:
                    i = bisect.bisect_right(bestPosList, lapProgressValue) - 1
                    c = (bestTimeList[i + 1] - bestTimeList[i]) / (bestPosList[i + 1] - bestPosList[i])
                    interpolatedLapValue = bestTimeList[i] + c * (lapProgressValue - bestPosList[i])
                    t = (currentLapValue - interpolatedLapValue) / 1000

                    if t == 0:
                        ac.setText(deltaLabel, "--.--")
                        ac.setFontColor(deltaLabel, 1, 1, 1, 1)
                    elif t > 0:
                        ac.setText(deltaLabel, "{:+.2f}".format(t))
                        ac.setFontColor(deltaLabel, 1, 0.18, 0.18, 1)
                    else:
                        ac.setText(deltaLabel, "{:+.2f}".format(t))
                        ac.setFontColor(deltaLabel, 0.18, 1, 0.18, 1)

                    if prevt2:
                        ttb_old = ttb
                        ttb = 2 * t - prevt - prevt2

                    prevt2 = float(prevt)
                    prevt = float(t)

                elif bestLapValue == 0 and deltaButtonValue == 0:
                    ac.setText(deltaLabel, "--.--")
                    ac.setFontColor(deltaLabel, 1, 1, 1, 1)

                if personalBestLapValue and deltaButtonValue == 1 and outLap != 1:
                    i = bisect.bisect_right(personalBestPosList, lapProgressValue) - 1
                    c = (personalBestTimeList[i + 1] - personalBestTimeList[i]) / (
                            personalBestPosList[i + 1] - personalBestPosList[i])
                    interpolatedLapValue = personalBestTimeList[i] + c * (lapProgressValue - personalBestPosList[i])
                    t = (currentLapValue - interpolatedLapValue) / 1000

                    if t == 0:
                        ac.setText(deltaLabel, "--.--")
                        ac.setFontColor(deltaLabel, 1, 1, 1, 1)
                    elif t > 0:
                        ac.setText(deltaLabel, "{:+.2f}".format(t))
                        ac.setFontColor(deltaLabel, 1, 0.18, 0.18, 1)
                    else:
                        ac.setText(deltaLabel, "{:+.2f}".format(t))
                        ac.setFontColor(deltaLabel, 0.18, 1, 0.18, 1)

                    if prevt2:
                        ttpb_old = ttpb
                        ttpb = 2 * t - prevt - prevt2

                    prevt2 = float(prevt)
                    prevt = float(t)

                elif personalBestLapValue == 0 and deltaButtonValue == 1:
                    ac.setText(deltaLabel, "--.--")
                    ac.setFontColor(deltaLabel, 1, 1, 1, 1)

                if lastLapValue and deltaButtonValue == 2:
                    i = bisect.bisect_right(lastPosList, lapProgressValue) - 1
                    c = (lastTimeList[i + 1] - lastTimeList[i]) / (lastPosList[i + 1] - lastPosList[i])
                    interpolatedLapValue = lastTimeList[i] + c * (lapProgressValue - lastPosList[i])
                    t = (currentLapValue - interpolatedLapValue) / 1000
                elif lastLapValue == 0 and deltaButtonValue == 2:
                    ac.setText(deltaLabel, "--.--")
                    ac.setFontColor(deltaLabel, 1, 1, 1, 1)

            elif timer > updateDelta and currentLapValue > 4000 and carWasInPit:
                timer = 0
                ac.setText(deltaLabel, "--.--")
                ac.setFontColor(deltaLabel, 1, 1, 1, 1)

            elif timer > updateDelta and currentLapValue > 1000 and currentLapValue < 4000 and timerDelay == 0:
                timer = 0

                if bestLapValue and deltaButtonValue == 0 and lapValue > 1:
                    if previousBestLapValue and previousBestLapValue > bestLapValue:
                        t = (lastLapValue - previousBestLapValue) / 1000
                    else:
                        t = (lastLapValue - bestLapValue) / 1000
                    if t == 0:
                        ac.setText(deltaLabel, "--.--")
                        ac.setFontColor(deltaLabel, 1, 1, 1, 1)
                    elif t > 0:
                        ac.setText(deltaLabel, "{:+.3f}".format(t))
                        ac.setFontColor(deltaLabel, 1, 0.18, 0.18, 1)
                    else:
                        ac.setText(deltaLabel, "{:+.3f}".format(t))
                        ac.setFontColor(deltaLabel, 0.18, 1, 0.18, 1)

                if personalBestLapValue and deltaButtonValue == 1 and lapValue > 0:
                    if previousPersonalBestLapValue and previousPersonalBestLapValue > personalBestLapValue:
                        t = (lastLapValue - previousPersonalBestLapValue) / 1000
                    else:
                        t = (lastLapValue - personalBestLapValue) / 1000
                    if t == 0:
                        ac.setText(deltaLabel, "--.--")
                        ac.setFontColor(deltaLabel, 1, 1, 1, 1)
                    elif t > 0:
                        ac.setText(deltaLabel, "{:+.3f}".format(t))
                        ac.setFontColor(deltaLabel, 1, 0.18, 0.18, 1)
                    else:
                        ac.setText(deltaLabel, "{:+.3f}".format(t))
                        ac.setFontColor(deltaLabel, 0.18, 1, 0.18, 1)

            # Possible New Laptime
            if bestLapValue and deltaButtonValue == 0 and lapValue > 0:
                PossibleNewPersonalBestLap = bestLapValue + (prevt * 1000)
                PossibleNewLaptimSeconds = ((PossibleNewPersonalBestLap / 1000) % 60)
                PossibleNewLaptimMinutes = ((PossibleNewPersonalBestLap // 1000) // 60)
                ac.setText(PossibleNewLaptimLable,
                           "{:.0f}:{:06.3f}".format(PossibleNewLaptimMinutes, PossibleNewLaptimSeconds))

            if personalBestLapValue and deltaButtonValue == 1 and lapValue > 0:
                PossibleNewPersonalBestLap = personalBestLapValue + (prevt * 1000)
                PossibleNewLaptimSeconds = ((PossibleNewPersonalBestLap / 1000) % 60)
                PossibleNewLaptimMinutes = ((PossibleNewPersonalBestLap // 1000) // 60)
                ac.setText(PossibleNewLaptimLable,
                           "{:.0f}:{:06.3f}".format(PossibleNewLaptimMinutes, PossibleNewLaptimSeconds))

            # Display data once per second
            timerDisplay += deltaT

            if timerDisplay > 1:
                timerDisplay = 0

                # Reset previous laps helper
                if currentLapValue > 4000 and (
                        previousBestLapValue > 0 or previousPersonalBestLapValue > 0 or previousLastLapValue > 0):
                    previousBestLapValue = 0
                    previousPersonalBestLapValue = 0
                    previousLastLapValue = 0

                # Car in pit check
                if carInPitValue:
                    carWasInPit = 1

                # Set ideal tyre temperatures and pressures
                if previousTyreCompoundValue != tyreCompoundValue:
                    previousTyreCompoundValue = tyreCompoundValue
                    compounds.read(compoundsPath)
                    if compounds.has_section(carValue + "_" + tyreCompoundCleaned):
                        idealPressureFront = int(
                            compounds.get(carValue + "_" + tyreCompoundCleaned, "IDEAL_PRESSURE_F"))
                        idealPressureRear = int(compounds.get(carValue + "_" + tyreCompoundCleaned, "IDEAL_PRESSURE_R"))
                        minimumOptimalTemperature = int(
                            compounds.get(carValue + "_" + tyreCompoundCleaned, "MIN_OPTIMAL_TEMP"))
                        maximumOptimalTemperature = int(
                            compounds.get(carValue + "_" + tyreCompoundCleaned, "MAX_OPTIMAL_TEMP"))
                    elif modCompound.has_section(carValue + "_" + tyreCompoundShort.lower()):
                        idealPressureFront = int(
                            modCompound.get(carValue + "_" + tyreCompoundCleaned, "IDEAL_PRESSURE_F"))
                        idealPressureRear = int(
                            modCompound.get(carValue + "_" + tyreCompoundCleaned, "IDEAL_PRESSURE_R"))
                        minimumOptimalTemperature = int(
                            modCompound.get(carValue + "_" + tyreCompoundCleaned, "MIN_OPTIMAL_TEMP"))
                        maximumOptimalTemperature = int(
                            modCompound.get(carValue + "_" + tyreCompoundCleaned, "MAX_OPTIMAL_TEMP"))
                    else:
                        idealPressureFront = False
                        idealPressureRear = False
                        minimumOptimalTemperature = False
                        maximumOptimalTemperature = False

                # Track grip
                ac.setText(trackGripLabel, "Track: {:.1f}%".format(trackGripValue * 100))

                # Tyre wear
                tyreWearValueFL = round(max(100 - (100 - tyreWearValue[0]) * tyreWearScale, 0))
                tyreWearValueFR = round(max(100 - (100 - tyreWearValue[1]) * tyreWearScale, 0))
                tyreWearValueRL = round(max(100 - (100 - tyreWearValue[2]) * tyreWearScale, 0))
                tyreWearValueRR = round(max(100 - (100 - tyreWearValue[3]) * tyreWearScale, 0))
                midWear = (100 + minimumWear) / 2  # Middle Tyre Waer calculatet from the min TyreWear to max (100%)

                # Calulate TyreWear Color
                # FL
                if tyreWearValueFL <= midWear:
                    rFL = 1
                    gFL = (tyreWearValueFL - minimumWear) / (midWear - minimumWear)
                else:
                    rFL = (100 - tyreWearValueFL) / (100 - midWear)
                    gFL = 1

                # FR
                if tyreWearValueFR <= midWear:
                    rFR = 1
                    gFR = (tyreWearValueFR - minimumWear) / (midWear - minimumWear)
                else:
                    rFR = (100 - tyreWearValueFR) / (100 - midWear)
                    gFR = 1

                # RL
                if tyreWearValueRL <= midWear:
                    rRL = 1
                    gRL = (tyreWearValueRL - minimumWear) / (midWear - minimumWear)
                else:
                    rRL = (100 - tyreWearValueRL) / (100 - midWear)
                    gRL = 1

                # RR
                if tyreWearValueRR <= midWear:
                    rRR = 1
                    gRR = (tyreWearValueRR - minimumWear) / (midWear - minimumWear)
                else:
                    rRR = (100 - tyreWearValueRR) / (100 - midWear)
                    gRR = 1

                if wearColorButtonValue == 0:
                    ac.setFontColor(tyreLabelWearFL, 1, 1, 1, 1)
                    ac.setFontColor(tyreLabelWearFR, 1, 1, 1, 1)
                    ac.setFontColor(tyreLabelWearRL, 1, 1, 1, 1)
                    ac.setFontColor(tyreLabelWearRR, 1, 1, 1, 1)
                else:
                    ac.setFontColor(tyreLabelWearFL, rFL, gFL, 0, 1)
                    ac.setFontColor(tyreLabelWearFR, rFR, gFR, 0, 1)
                    ac.setFontColor(tyreLabelWearRL, rRL, gRL, 0, 1)
                    ac.setFontColor(tyreLabelWearRR, rRR, gRR, 0, 1)

                ac.setText(tyreLabelWearFL, "{:.0f}".format(tyreWearValueFL))
                ac.setText(tyreLabelWearFR, "{:.0f}".format(tyreWearValueFR))
                ac.setText(tyreLabelWearRL, "{:.0f}".format(tyreWearValueRL))
                ac.setText(tyreLabelWearRR, "{:.0f}".format(tyreWearValueRR))

                # Tyre temperatures
                TempColorRange = 10
                tyreTemperatureValueRoundFL = round(tyreTemperatureValue[0], 0)
                tyreTemperatureValueRoundFR = round(tyreTemperatureValue[1], 0)
                tyreTemperatureValueRoundRL = round(tyreTemperatureValue[2], 0)
                tyreTemperatureValueRoundRR = round(tyreTemperatureValue[3], 0)

                ac.setText(tyreLabelTempFL, "{:.0f}".format(tyreTemperatureValueRoundFL))
                ac.setText(tyreLabelTempFR, "{:.0f}".format(tyreTemperatureValueRoundFR))
                ac.setText(tyreLabelTempRL, "{:.0f}".format(tyreTemperatureValueRoundRL))
                ac.setText(tyreLabelTempRR, "{:.0f}".format(tyreTemperatureValueRoundRR))

                if tempColorButtonValue == 0 or minimumOptimalTemperature == False or maximumOptimalTemperature == False:
                    ac.setFontColor(tyreLabelTempFL, 1, 1, 1, 1)
                    ac.setFontColor(tyreLabelTempFR, 1, 1, 1, 1)
                    ac.setFontColor(tyreLabelTempRL, 1, 1, 1, 1)
                    ac.setFontColor(tyreLabelTempRR, 1, 1, 1, 1)
                else:
                    # FL Set Colors
                    rFL = (tyreTemperatureValueRoundFL - minimumOptimalTemperature) / (
                            maximumOptimalTemperature - minimumOptimalTemperature) * 0.8
                    bFL = (maximumOptimalTemperature - tyreTemperatureValueRoundFL) / (
                            maximumOptimalTemperature - minimumOptimalTemperature) * 0.8
                    if int(tyreTemperatureValueRoundFL) < minimumOptimalTemperature:
                        gFL = (tyreTemperatureValueRoundFL - (
                                minimumOptimalTemperature - TempColorRange)) / TempColorRange * 0.95
                    elif int(tyreTemperatureValueRoundFL) > maximumOptimalTemperature:
                        gFL = (maximumOptimalTemperature + (
                                TempColorRange - tyreTemperatureValueRoundFL)) / TempColorRange * 0.95

                    # FR Set Colors
                    rFR = (tyreTemperatureValueRoundFR - minimumOptimalTemperature) / (
                            maximumOptimalTemperature - minimumOptimalTemperature) * 0.8
                    bFR = (maximumOptimalTemperature - tyreTemperatureValueRoundFR) / (
                            maximumOptimalTemperature - minimumOptimalTemperature) * 0.8
                    if int(tyreTemperatureValueRoundFR) < minimumOptimalTemperature:
                        gFR = (tyreTemperatureValueRoundFR - (
                                minimumOptimalTemperature - TempColorRange)) / TempColorRange * 0.95
                    elif int(tyreTemperatureValueRoundFR) > maximumOptimalTemperature:
                        gFR = (maximumOptimalTemperature + (
                                TempColorRange - tyreTemperatureValueRoundFR)) / TempColorRange * 0.95

                    # RL Set Colors
                    rRL = (tyreTemperatureValueRoundRL - minimumOptimalTemperature) / (
                            maximumOptimalTemperature - minimumOptimalTemperature) * 0.8
                    bRL = (maximumOptimalTemperature - tyreTemperatureValueRoundRL) / (
                            maximumOptimalTemperature - minimumOptimalTemperature) * 0.8
                    if int(tyreTemperatureValueRoundRL) < minimumOptimalTemperature:
                        gRL = (tyreTemperatureValueRoundRL - (
                                minimumOptimalTemperature - TempColorRange)) / TempColorRange * 0.95
                    elif int(tyreTemperatureValueRoundRL) > maximumOptimalTemperature:
                        gRL = (maximumOptimalTemperature + (
                                TempColorRange - tyreTemperatureValueRoundRL)) / TempColorRange * 0.95

                    # RR Set Colors
                    rRR = (tyreTemperatureValueRoundRR - minimumOptimalTemperature) / (
                            maximumOptimalTemperature - minimumOptimalTemperature) * 0.8
                    bRR = (maximumOptimalTemperature - tyreTemperatureValueRoundRR) / (
                            maximumOptimalTemperature - minimumOptimalTemperature) * 0.8
                    if int(tyreTemperatureValueRoundRR) < minimumOptimalTemperature:
                        gRR = (tyreTemperatureValueRoundRR - (
                                minimumOptimalTemperature - TempColorRange)) / TempColorRange * 0.95
                    elif int(tyreTemperatureValueRoundRR) > maximumOptimalTemperature:
                        gRR = (maximumOptimalTemperature + (
                                TempColorRange - tyreTemperatureValueRoundRR)) / TempColorRange * 0.95

                    # FL Set Color to Dash
                    if minimumOptimalTemperature and maximumOptimalTemperature:
                        if int(tyreTemperatureValueRoundFL) >= minimumOptimalTemperature and int(
                                tyreTemperatureValueRoundFL) <= maximumOptimalTemperature:
                            ac.setFontColor(tyreLabelTempFL, rFL, 1, bFL, 1)
                        elif int(tyreTemperatureValueRoundFL) < minimumOptimalTemperature:
                            if tyreTemperatureValueRoundFL < minimumOptimalTemperature - TempColorRange:
                                ac.setFontColor(tyreLabelTempFL, 0, 0, 1, 1)
                            else:
                                ac.setFontColor(tyreLabelTempFL, 0, gFL, 1, 1)
                        elif int(tyreTemperatureValueRoundFL) > maximumOptimalTemperature:
                            if tyreTemperatureValueRoundFL > maximumOptimalTemperature + TempColorRange:
                                ac.setFontColor(tyreLabelTempFL, 1, 0, 0, 1)
                            else:
                                ac.setFontColor(tyreLabelTempFL, 1, gFL, 0, 1)

                    # FR Set Color to Dash
                    if minimumOptimalTemperature and maximumOptimalTemperature:
                        if int(tyreTemperatureValueRoundFR) >= minimumOptimalTemperature and int(
                                tyreTemperatureValueRoundFR) <= maximumOptimalTemperature:
                            ac.setFontColor(tyreLabelTempFR, rFR, 1, bFR, 1)
                        elif int(tyreTemperatureValueRoundFR) < minimumOptimalTemperature:
                            if tyreTemperatureValueRoundFR < minimumOptimalTemperature - TempColorRange:
                                ac.setFontColor(tyreLabelTempFR, 0, 0, 1, 1)
                            else:
                                ac.setFontColor(tyreLabelTempFR, 0, gFR, 1, 1)
                        elif int(tyreTemperatureValueRoundFR) > maximumOptimalTemperature:
                            if tyreTemperatureValueRoundFR > maximumOptimalTemperature + TempColorRange:
                                ac.setFontColor(tyreLabelTempFR, 1, 0, 0, 1)
                            else:
                                ac.setFontColor(tyreLabelTempFR, 1, gFR, 0, 1)

                    # RL Set Color to Dash
                    if minimumOptimalTemperature and maximumOptimalTemperature:
                        if int(tyreTemperatureValueRoundRL) >= minimumOptimalTemperature and int(
                                tyreTemperatureValueRoundRL) <= maximumOptimalTemperature:
                            ac.setFontColor(tyreLabelTempRL, rRL, 1, bRL, 1)
                        elif int(tyreTemperatureValueRoundRL) < minimumOptimalTemperature:
                            if tyreTemperatureValueRoundRL < minimumOptimalTemperature - TempColorRange:
                                ac.setFontColor(tyreLabelTempRL, 0, 0, 1, 1)
                            else:
                                ac.setFontColor(tyreLabelTempRL, 0, gRL, 1, 1)
                        elif int(tyreTemperatureValueRoundRL) > maximumOptimalTemperature:
                            if tyreTemperatureValueRoundRL > maximumOptimalTemperature + TempColorRange:
                                ac.setFontColor(tyreLabelTempRL, 1, 0, 0, 1)
                            else:
                                ac.setFontColor(tyreLabelTempRL, 1, gRL, 0, 1)

                    # RR Set Color to Dash
                    if minimumOptimalTemperature and maximumOptimalTemperature:
                        if int(tyreTemperatureValueRoundRR) >= minimumOptimalTemperature and int(
                                tyreTemperatureValueRoundRR) <= maximumOptimalTemperature:
                            ac.setFontColor(tyreLabelTempRR, rRR, 1, bRR, 1)
                        elif int(tyreTemperatureValueRoundRR) < minimumOptimalTemperature:
                            if tyreTemperatureValueRoundRR < minimumOptimalTemperature - TempColorRange:
                                ac.setFontColor(tyreLabelTempRR, 0, 0, 1, 1)
                            else:
                                ac.setFontColor(tyreLabelTempRR, 0, gRR, 1, 1)
                        elif int(tyreTemperatureValueRoundRR) > maximumOptimalTemperature:
                            if tyreTemperatureValueRoundRR > maximumOptimalTemperature + TempColorRange:
                                ac.setFontColor(tyreLabelTempRR, 1, 0, 0, 1)
                            else:
                                ac.setFontColor(tyreLabelTempRR, 1, gRR, 0, 1)

                # Tyre pressures
                pessureRange = 8

                tyrePressureValueRoundFL = round(tyrePressureValue[0], 0)
                tyrePressureValueRoundFR = round(tyrePressureValue[1], 0)
                tyrePressureValueRoundRL = round(tyrePressureValue[2], 0)
                tyrePressureValueRoundRR = round(tyrePressureValue[3], 0)

                ac.setText(tyreLabelPresFL, "{:.0f}".format(tyrePressureValue[0]))
                ac.setText(tyreLabelPresFR, "{:.0f}".format(tyrePressureValue[1]))
                ac.setText(tyreLabelPresRL, "{:.0f}".format(tyrePressureValue[2]))
                ac.setText(tyreLabelPresRR, "{:.0f}".format(tyrePressureValue[3]))

                if pressColorButtonValue == 0 or idealPressureFront == False or idealPressureRear == False:
                    ac.setFontColor(tyreLabelPresFL, 1, 1, 1, 1)
                    ac.setFontColor(tyreLabelPresFR, 1, 1, 1, 1)
                    ac.setFontColor(tyreLabelPresRL, 1, 1, 1, 1)
                    ac.setFontColor(tyreLabelPresRR, 1, 1, 1, 1)
                else:
                    if idealPressureFront and idealPressureRear:

                        # FL Pressure
                        if tyrePressureValueRoundFL < idealPressureFront:
                            if tyrePressureValueRoundFL < idealPressureFront - pessureRange:
                                rRL = 0
                                gRL = 0
                                bRL = 1
                            else:
                                rRL = 0
                                gRL = (tyrePressureValueRoundFL - (
                                        idealPressureFront - pessureRange)) / pessureRange * 1
                                bRL = (idealPressureFront - tyrePressureValueRoundFL) / pessureRange * 1
                        else:
                            if tyrePressureValueRoundFL > idealPressureFront + pessureRange:
                                rRL = 1
                                gRL = 0
                                bRL = 0
                            else:
                                rRL = (tyrePressureValueRoundFL - idealPressureFront) / pessureRange * 1
                                gRL = ((
                                               idealPressureFront + pessureRange) - tyrePressureValueRoundFL) / pessureRange * 1
                                bRL = 0
                        ac.setFontColor(tyreLabelPresFL, rRL, gRL, bRL, 1)

                        # FR Pressure
                        if tyrePressureValueRoundFR < idealPressureFront:
                            if tyrePressureValueRoundFR < idealPressureFront - pessureRange:
                                rRL = 0
                                gRL = 0
                                bRL = 1
                            else:
                                rRL = 0
                                gRL = (tyrePressureValueRoundFR - (
                                        idealPressureFront - pessureRange)) / pessureRange * 1
                                bRL = (idealPressureFront - tyrePressureValueRoundFR) / pessureRange * 1
                        else:
                            if tyrePressureValueRoundFR > idealPressureFront + pessureRange:
                                rRL = 1
                                gRL = 0
                                bRL = 0
                            else:
                                rRL = (tyrePressureValueRoundFR - idealPressureFront) / pessureRange * 1
                                gRL = ((
                                               idealPressureFront + pessureRange) - tyrePressureValueRoundFR) / pessureRange * 1
                                bRL = 0
                        ac.setFontColor(tyreLabelPresFR, rRL, gRL, bRL, 1)

                        # RL Pressure
                        if tyrePressureValueRoundRL < idealPressureFront:
                            if tyrePressureValueRoundRL < idealPressureFront - pessureRange:
                                rRL = 0
                                gRL = 0
                                bRL = 1
                            else:
                                rRL = 0
                                gRL = (tyrePressureValueRoundRL - (
                                        idealPressureFront - pessureRange)) / pessureRange * 1
                                bRL = (idealPressureFront - tyrePressureValueRoundRL) / pessureRange * 1
                        else:
                            if tyrePressureValueRoundRL > idealPressureFront + pessureRange:
                                rRL = 1
                                gRL = 0
                                bRL = 0
                            else:
                                rRL = (tyrePressureValueRoundRL - idealPressureFront) / pessureRange * 1
                                gRL = ((
                                               idealPressureFront + pessureRange) - tyrePressureValueRoundRL) / pessureRange * 1
                                bRL = 0
                        ac.setFontColor(tyreLabelPresRL, rRL, gRL, bRL, 1)

                        # RR Pressure
                        if tyrePressureValueRoundRR < idealPressureFront:
                            if tyrePressureValueRoundRR < idealPressureFront - pessureRange:
                                rRL = 0
                                gRL = 0
                                bRL = 1
                            else:
                                rRL = 0
                                gRL = (tyrePressureValueRoundRR - (
                                        idealPressureFront - pessureRange)) / pessureRange * 1
                                bRL = (idealPressureFront - tyrePressureValueRoundRR) / pessureRange * 1
                        else:
                            if tyrePressureValueRoundRR > idealPressureFront + pessureRange:
                                rRL = 1
                                gRL = 0
                                bRL = 0
                            else:
                                rRL = (tyrePressureValueRoundRR - idealPressureFront) / pessureRange * 1
                                gRL = ((
                                               idealPressureFront + pessureRange) - tyrePressureValueRoundRR) / pessureRange * 1
                                bRL = 0
                        ac.setFontColor(tyreLabelPresRR, rRL, gRL, bRL, 1)

                # Lap
                if totalLapsValue:
                    if lapValue == totalLapsValue:
                        ac.setText(lapLabel, "Lap: {}/{}".format(totalLapsValue, totalLapsValue))
                    elif lapValue < totalLapsValue:
                        ac.setText(lapLabel, "Lap: {}/{}".format(lapValue + 1, totalLapsValue))
                else:
                    ac.setText(lapLabel, "Lap: {}/-".format(lapValue + 1))

                # Position
                if sessionTypeValue == 3:
                    ac.setText(positionLabel, "Pos: -/-")
                elif sessionTypeValue == 2:
                    if serverIPValue:
                        ac.setText(positionLabel, "Pos: {}/{}".format(positionValue + 1, occupiedSlotsValue))
                    else:
                        ac.setText(positionLabel, "Pos: {}/{}".format(positionValue + 1, totalCarsValue))
                else:
                    if serverIPValue:
                        ac.setText(positionLabel, "Pos: {}/{}".format(positionBoardValue, occupiedSlotsValue))
                    else:
                        ac.setText(positionLabel, "Pos: {}/{}".format(positionBoardValue, totalCarsValue))

                # Session time
                sessionTimeValueSeconds = (sessionTimeValue / 1000) % 60
                sessionTimeValueMinutes = (sessionTimeValue // 1000) // 60
                if (
                        sessionTypeValue == 2 and info.static.isTimedRace == 0) or sessionTypeValue > 2 or sessionTimeValue < 0:
                    ac.setFontColor(sessionTimeLabel, 1, 1, 1, 1)
                    ac.setText(sessionTimeLabel, "Rem: --:--")
                else:
                    if sessionTimeValueMinutes < 5:
                        ac.setFontColor(sessionTimeLabel, 1, 0.18, 0.18, 1)
                        ac.setText(sessionTimeLabel,
                                   "Rem: {:02.0f}:{:02.0f}".format(sessionTimeValueMinutes, sessionTimeValueSeconds))
                    elif sessionTimeValueMinutes >= 60:
                        ac.setFontColor(sessionTimeLabel, 1, 1, 1, 1)
                        ac.setText(sessionTimeLabel, "Rem: >1h")
                    else:
                        ac.setFontColor(sessionTimeLabel, 1, 1, 1, 1)
                        ac.setText(sessionTimeLabel,
                                   "Rem: {:02.0f}:{:02.0f}".format(sessionTimeValueMinutes, sessionTimeValueSeconds))

                # System clock
                ac.setText(systemClockLabel,
                           "Time: {:02.0f}:{:02.0f}".format(systemClockValue.hour, systemClockValue.minute))

                # Fuel amount
                ac.setText(fuelAmountLabel, "{:.1f} L".format(fuelAmountValue))

                # Fuel for laps
                if fuelPerLapValue:
                    LapsLeft = fuelAmountValue / fuelPerLapValue
                    if LapsLeft < 2:
                        ac.setFontColor(fuelForLapsLabel, 1, 0.18, 0.18, 1)
                        ac.setText(fuelForLapsLabel, "Laps Left: {:.1f}".format(LapsLeft))
                    else:
                        ac.setFontColor(fuelForLapsLabel, 1, 1, 1, 1)
                        ac.setText(fuelForLapsLabel, "Laps Left: {:.1f}".format(LapsLeft))
                else:
                    ac.setText(fuelForLapsLabel, "Laps Left: --.-")

                # Fuel needed
                if lapValue > 0 and sessionTypeValue == 2:
                    fuelNeededValue = (totalLapsValue - lapValue - lapProgressValue) * fuelPerLapValue
                    if fuelAmountValue < fuelNeededValue and switcher:
                        ac.setFontColor(fuelNeededLabel, 1, 0.18, 0.18, 1)
                        ac.setText(fuelNeededLabel, "Required: {:.1f}".format(fuelNeededValue))
                        switcher = 0
                    elif fuelAmountValue < fuelNeededValue and not switcher:
                        ac.setFontColor(fuelNeededLabel, 1, 0.18, 0.18, 1)
                        ac.setText(fuelNeededLabel, "Required: {:.1f}".format(fuelNeededValue - fuelAmountValue))
                        switcher = 1
                    else:
                        ac.setFontColor(fuelNeededLabel, 1, 1, 1, 1)
                        ac.setText(fuelNeededLabel, "Required: {:.1f}".format(fuelNeededValue))
                else:
                    ac.setFontColor(fuelNeededLabel, 1, 1, 1, 1)
                    ac.setText(fuelNeededLabel, "Required: --.-")

                # Ambient temperature
                ac.setText(temperatureLabel, "Tmp: {:.0f}C/{:.0f}C".format(airTemperatureValue, roadTemperatureValue))

            # Display data once per lap
            # Run on lap start
            if currentLapValue > 500 and currentLapValue < 1000:
                carWasInPit = 0
                fuelStartValue = fuelAmountValue
                timeList = []
                posList = []
                prevt = 0
                prevt2 = 0
                ttb = 0
                ttpb = 0
                if startClearsValidity:
                    lapValidityValue = 0

            # Run on lap finish
            if previousLapValue < lapValue:
                timerDelay += deltaT

                # Reset helpers
                outLap = 0  # Just in case the first condition misfired

                if timerDelay > 0.46:
                    timerDelay = 0
                    previousLapValue = lapValue

                    # Last lap
                    lastLapValue = info.graphics.iLastTime
                    previousLastLapValue = lastLapValue
                    lastLapValueSeconds = (lastLapValue / 1000) % 60
                    lastLapValueMinutes = (lastLapValue // 1000) // 60
                    if lapValidityValue:
                        ac.setFontColor(lastLapLabel, 1, 0.18, 0.18, 1)
                    else:
                        ac.setFontColor(lastLapLabel, 1, 1, 1, 1)
                        ac.setText(lastLapLabel, "L: {:.0f}:{:06.3f}".format(lastLapValueMinutes, lastLapValueSeconds))
                        lastPosList = list(posList)  # LastLapChange
                        lastTimeList = list(timeList)  # LastLapChange

                    # Best lap
                    if lapValidityValue != 1:
                        previousBestLapValue = bestLapValue
                        if not bestLapValue:
                            bestLapValue = lastLapValue
                        if lastLapValue < bestLapValue:
                            bestLapValue = lastLapValue
                        bestLapValueSeconds = (bestLapValue / 1000) % 60
                        bestLapValueMinutes = (bestLapValue // 1000) // 60
                        ac.setText(bestLapLabel, "B: {:.0f}:{:06.3f}".format(bestLapValueMinutes, bestLapValueSeconds))
                        if bestLapValue < previousBestLapValue or previousBestLapValue == 0:
                            bestPosList = list(posList)
                            bestTimeList = list(timeList)

                    # Personal best lap
                    if (bestLapValue < personalBestLapValue or personalBestLapValue == 0) and bestLapValue:
                        previousPersonalBestLapValue = personalBestLapValue
                        personalBestLapValue = bestLapValue
                        personalBestLapValueSeconds = (personalBestLapValue / 1000) % 60
                        personalBestLapValueMinutes = (personalBestLapValue // 1000) // 60
                        ac.setText(personalBestLapLabel, "P: {:.0f}:{:06.3f}".format(personalBestLapValueMinutes,
                                                                                     personalBestLapValueSeconds))
                        personalBestPosList = list(posList)
                        personalBestTimeList = list(timeList)

                    # Fuel per lap
                    if fuelAmountValue < fuelStartValue and not carWasInPit:
                        fuelEndValue = fuelAmountValue
                        relevantLapsNumber += 1
                        fuelSpentValue += (fuelStartValue - fuelEndValue) + (fuelStartValue - fuelEndValue) * (
                                540 / lastLapValue)
                        fuelPerLapValue = fuelSpentValue / relevantLapsNumber
                        ac.setText(fuelPerLapLabel, "Usage: {:.1f}".format(fuelPerLapValue))

                    # Reset helper
                    lapValidityValue = 0
        ###END DATA DISPLAY
        ###END RUN THIS INDENTATION WITH EVERY FRAME

    except:
        ac.log(traceback.format_exc())


# Draw bars
def onFormRender(deltaT):
    global ffbValue
    drsAvailableValue = ac.getCarState(0, acsys.CS.DrsAvailable)
    drsEnabledValue = ac.getCarState(0, acsys.CS.DrsEnabled)

    # RPM
    ac.glColor4f(1, 1, 1, 0.3)
    ac.glQuad(10, 7, 196, 6)
    if not maxPowerRpmLights or maxPowerRpm >= rpmMaxValue:
        if orangeLimitEnabled and rpmPercentageValue > orangeLimitPercentage and rpmPercentageValue < redLimitPercentage:
            ac.glColor4f(1, 0.46, 0.18, 1)
            ac.glQuad(10, 7, (rpmPercentageValue * 196), 6)
        elif redLimitEnabled and rpmPercentageValue >= redLimitPercentage:
            ac.glColor4f(1, 0.18, 0.18, 1)
            ac.glQuad(10, 7, (rpmPercentageValue * 196), 6)
        else:
            ac.glColor4f(1, 1, 1, 1)
            ac.glQuad(10, 7, (rpmPercentageValue * 196), 6)
    elif maxPowerRpmLights and maxPowerRpm < rpmMaxValue:
        if orangeLimitEnabled and maxPowerRpmPercentageValue > orangeLimitPowerPercentage and maxPowerRpmPercentageValue < redLimitPowerPercentage:
            ac.glColor4f(1, 0.46, 0.18, 1)
            ac.glQuad(10, 7, (rpmPercentageValue * 196), 6)
        elif redLimitEnabled and maxPowerRpmPercentageValue >= redLimitPowerPercentage:
            ac.glColor4f(1, 0.18, 0.18, 1)
            ac.glQuad(10, 7, (rpmPercentageValue * 196), 6)
        else:
            ac.glColor4f(1, 1, 1, 1)
            ac.glQuad(10, 7, (rpmPercentageValue * 196), 6)

    # Delta gain bar
    ac.glColor4f(1, 1, 1, 0.3)
    ac.glQuad(352, 83, 100, 6)
    if deltaButtonValue:
        if ttpb > 0:
            ac.glColor4f(1, 0.18, 0.18, 1)
            deltaOffset = min(ttpb * 1000, 50)
            ac.glQuad((402 - deltaOffset), 83, deltaOffset, 6)
        if ttpb < 0:
            ac.glColor4f(0.18, 1, 0.18, 1)
            deltaOffset = min(abs(ttpb * 1000), 50)
            ac.glQuad(402, 83, deltaOffset, 6)
    else:
        if ttb > 0:
            ac.glColor4f(1, 0.18, 0.18, 1)
            deltaOffset = min(ttb * 1000, 50)
            ac.glQuad((402 - deltaOffset), 83, deltaOffset, 6)
        if ttb < 0:
            ac.glColor4f(0.18, 1, 0.18, 1)
            deltaOffset = min(abs(ttb * 1000), 50)
            ac.glQuad(402, 83, deltaOffset, 6)

    # Clutch
    if pedalButtonValue == 1:
        ac.glColor4f(1, 1, 1, 0.3)
        ac.glQuad(142, 33, 14, 14)
        if clutchValue < 1:
            ac.glColor4f(0.18, 0.46, 1, 1)
            ac.glQuad(142, 33, 14, 14)
    elif pedalButtonValue == 2:
        ac.glColor4f(1, 1, 1, 0.3)
        ac.glQuad(142, 33, 14, 40)
        ac.glColor4f(0.18, 0.46, 1, 1)
        ac.glQuad(142, ((1 - (1 - clutchValue)) * 40 + 33), 14, ((1 - clutchValue) * 40))

    # Brake
    if pedalButtonValue == 1:
        ac.glColor4f(1, 1, 1, 0.3)
        ac.glQuad(160, 33, 14, 14)
        if brakeValue >= 0.01:
            ac.glColor4f(1, 0.18, 0.18, 1)
            ac.glQuad(160, 33, 14, 14)
    elif pedalButtonValue == 2:
        ac.glColor4f(1, 1, 1, 0.3)
        ac.glQuad(160, 33, 14, 40)
        ac.glColor4f(1, 0.18, 0.18, 1)
        ac.glQuad(160, ((1 - brakeValue) * 40 + 33), 14, (brakeValue * 40))

    # Throttle
    if pedalButtonValue == 1:
        ac.glColor4f(1, 1, 1, 0.3)
        ac.glQuad(178, 33, 14, 14)
        if throttleValue >= 0.01:
            ac.glColor4f(0.18, 1, 0.18, 1)
            ac.glQuad(178, 33, 14, 14)
    elif pedalButtonValue == 2:
        ac.glColor4f(1, 1, 1, 0.3)
        ac.glQuad(178, 33, 14, 40)
        ac.glColor4f(0.18, 1, 0.18, 1)
        ac.glQuad(178, ((1 - throttleValue) * 40 + 33), 14, (throttleValue * 40))

    # DRS
    if drsEnabledValue:
        ac.setVisible(drsLabel, 1)
        ac.setBackgroundTexture(drsLabel, drs_enabled)
    elif drsAvailableValue:
        ac.setVisible(drsLabel, 1)
        ac.setBackgroundTexture(drsLabel, drs_available)
    else:
        ac.setVisible(drsLabel, 0)

    # Flags
    ac.glColor4f(1, 1, 1, 0.3)
    ac.glQuad(360, 3, 77, 14)
    ac.glColor4f(1, 1, 1, 0.3)
    ac.glQuad(360, 20, 77, 14)

    # Yellow
    if flagValue == 2:
        ac.glColor4f(1, 1, 0, 1)
        ac.glQuad(360, 3, 77, 14)

    # Blue
    if flagValue == 1:
        ac.glColor4f(0.18, 0.46, 1, 1)
        ac.glQuad(360, 20, 77, 14)

    carDamageValueFront = round(carDamageValue[0], 0)
    carDamageValueBack = round(carDamageValue[1], 0)
    carDamageValueLeft = round(carDamageValue[2], 0)
    carDamageValueRight = round(carDamageValue[3], 0)

    maxColorRangeBlue = 35
    maxColorRangeGreen = 62

    # Front
    if carDamageValueFront == 0:
        rColor = 0.18
        gColor = 0.18
        bcolor = 0.18
    elif carDamageValueFront < maxColorRangeBlue:
        rColor = 1
        gColor = 1
        bcolor = ((maxColorRangeBlue - carDamageValueFront) / (maxColorRangeBlue - 0)) * 1
    elif carDamageValueFront < maxColorRangeGreen:
        rColor = 1
        gColor = ((maxColorRangeGreen - carDamageValueFront) / (maxColorRangeGreen - maxColorRangeBlue)) * 1
        bcolor = 0
    else:
        rColor = 1
        gColor = 0
        bcolor = 0

    ac.glColor4f(rColor, gColor, bcolor, 1)
    ac.glQuad(84, 47, 12, 7)

    # Back
    if carDamageValueBack == 0:
        rColor = 0.18
        gColor = 0.18
        bcolor = 0.18
    elif carDamageValueBack < maxColorRangeBlue:
        rColor = 1
        gColor = 1
        bcolor = ((maxColorRangeBlue - carDamageValueBack) / (maxColorRangeBlue - 0)) * 1
    elif carDamageValueBack < maxColorRangeGreen:
        rColor = 1
        gColor = ((maxColorRangeGreen - carDamageValueBack) / (maxColorRangeGreen - maxColorRangeBlue)) * 1
        bcolor = 0
    else:
        rColor = 1
        gColor = 0
        bcolor = 0

    ac.glColor4f(rColor, gColor, bcolor, 1)
    ac.glQuad(84, 72, 12, 7)

    # Left
    if carDamageValueLeft == 0:
        rColor = 0.18
        gColor = 0.18
        bcolor = 0.18
    elif carDamageValueLeft < maxColorRangeBlue:
        rColor = 1
        gColor = 1
        bcolor = ((maxColorRangeBlue - carDamageValueLeft) / (maxColorRangeBlue - 0)) * 1
    elif carDamageValueLeft < maxColorRangeGreen:
        rColor = 1
        gColor = ((maxColorRangeGreen - carDamageValueLeft) / (maxColorRangeGreen - maxColorRangeBlue)) * 1
        bcolor = 0
    else:
        rColor = 1
        gColor = 0
        bcolor = 0

    ac.glColor4f(rColor, gColor, bcolor, 1)
    ac.glQuad(77, 54, 7, 18)

    # Right
    if carDamageValueRight == 0:
        rColor = 0.18
        gColor = 0.18
        bcolor = 0.18
    elif carDamageValueRight < maxColorRangeBlue:
        rColor = 1
        gColor = 1
        bcolor = ((maxColorRangeBlue - carDamageValueRight) / (maxColorRangeBlue - 0)) * 1
    elif carDamageValueRight < maxColorRangeGreen:
        rColor = 1
        gColor = ((maxColorRangeGreen - carDamageValueRight) / (maxColorRangeGreen - maxColorRangeBlue)) * 1
        bcolor = 0
    else:
        rColor = 1
        gColor = 0
        bcolor = 0

    ac.glColor4f(rColor, gColor, bcolor, 1)
    ac.glQuad(96, 54, 7, 18)


# Do on AC shutdown
def acShutdown():
    global personalBestDir, configDir
    global filePersonalBest, personalBestLapValue
    global filePersonalBestPosList, personalBestPosList
    global filePersonalBestTimeList, personalBestTimeList
    global fileCompoundButton, compoundButtonValue
    global filePedalButton, pedalButtonValue
    global filetempColorButton, tempColorButtonValue
    global filepressColorButton, pressColorButtonValue
    global filewearColorButton, wearColorButtonValue
    global fileDeltaButton, deltaButtonValue
    global fileAppActive, appActiveValue

    writeFile(filePersonalBest, personalBestLapValue, personalBestDir)
    writeFile(filePersonalBestPosList, personalBestPosList, personalBestDir)
    writeFile(filePersonalBestTimeList, personalBestTimeList, personalBestDir)
    writeFile(fileCompoundButton, compoundButtonValue, configDir)
    writeFile(filePedalButton, pedalButtonValue, configDir)
    writeFile(filetempColorButton, tempColorButtonValue, configDir)
    writeFile(filepressColorButton, pressColorButtonValue, configDir)
    writeFile(filewearColorButton, wearColorButtonValue, configDir)
    writeFile(fileDeltaButton, deltaButtonValue, configDir)
    writeFile(fileAppActive, appActiveValue, configDir)


# Button actions
def deltaButtonClicked(*args):
    global deltaButtonValue, deltaButton
    global ttb, ttpb

    if deltaButtonValue == 1:
        deltaButtonValue = 0
        ac.setText(deltaButton, "Delta B:")
        ttb = 0

    elif deltaButtonValue == 0:
        deltaButtonValue = 1
        ac.setText(deltaButton, "Delta P:")
        ttpb = 0


def pedalButtonClicked(*args):
    global pedalButtonValue

    if pedalButtonValue == 0:
        pedalButtonValue = 1

    elif pedalButtonValue == 1:
        pedalButtonValue = 2

    elif pedalButtonValue == 2:
        pedalButtonValue = 0


def tempColorButtonClicked(*args):
    global tempColorButtonValue

    if tempColorButtonValue == 0:
        tempColorButtonValue = 1

    elif tempColorButtonValue == 1:
        tempColorButtonValue = 0


def pressColorButtonClicked(*args):
    global pressColorButtonValue

    if pressColorButtonValue == 0:
        pressColorButtonValue = 1

    elif pressColorButtonValue == 1:
        pressColorButtonValue = 0


def wearColorButtonClicked(*args):
    global wearColorButtonValue

    if wearColorButtonValue == 0:
        wearColorButtonValue = 1

    elif wearColorButtonValue == 1:
        wearColorButtonValue = 0


# Activity listeners
def appActivated(*args):
    global appActiveValue

    appActiveValue = 1


def appDismissed(*args):
    global appActiveValue

    appActiveValue = 0


# Helper functions
def writeFile(file, list, dir):
    if not os.path.exists(dir):
        os.makedirs(dir)

    f = open(file, "wb")
    pickle.dump(list, f)
    f.close()


def loadFile(file, var):
    if os.path.exists(file):
        f = open(file, "rb")
        var = pickle.load(f)
        f.close()

    return var


def listenKey1():
    try:
        ctypes.windll.user32.RegisterHotKey(None, 1, raceessentials_lib.win32con.MOD_ALT, 0x44)
        msg = ctypes.wintypes.MSG()
        while listenKeyActive:
            if ctypes.windll.user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == raceessentials_lib.win32con.WM_HOTKEY:
                    deltaButtonClicked()

                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageA(ctypes.byref(msg))
    finally:
        ctypes.windll.user32.UnregisterHotKey(None, 1)


def listenKey2():
    try:
        ctypes.windll.user32.RegisterHotKey(None, 1, raceessentials_lib.win32con.MOD_ALT, 0x43)
        msg = ctypes.wintypes.MSG()
        while listenKeyActive:
            if ctypes.windll.user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
                # if msg.message == raceessentials_lib.win32con.WM_HOTKEY:
                # compoundButtonClicked()
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageA(ctypes.byref(msg))
    finally:
        ctypes.windll.user32.UnregisterHotKey(None, 1)


keyListener1 = threading.Thread(target=listenKey1)
keyListener1.daemon = True
keyListener1.start()

keyListener2 = threading.Thread(target=listenKey2)
keyListener2.daemon = True
keyListener2.start()
