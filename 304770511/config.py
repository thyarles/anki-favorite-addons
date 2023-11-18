userOption = None
from aqt import mw


def getConfig():
    global userOption
    if userOption is None:
        userOption = mw.addonManager.getConfig(__name__)
    return userOption

def updateConfig():
    mw.addonManager.writeConfig(__name__,userOption)

def newConf(newUserOption):
    global userOption
    userOption = newUserOption
mw.addonManager.setConfigUpdatedAction(__name__,newConf)
