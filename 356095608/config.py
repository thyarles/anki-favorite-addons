import os

from aqt import mw

def gc(arg, fail=False):
    conf = mw.addonManager.getConfig(__name__)
    if conf:
        return conf.get(arg, fail)
    return fail


addon_folder_abs_path = os.path.dirname(__file__)
user_files_folder = os.path.join(addon_folder_abs_path, "user_files")
file_replacements = os.path.join(user_files_folder, "regular.pypickle")
file_regex = os.path.join(user_files_folder, "regex.pypickle")
