from aqt import mw
from aqt.qt import Qt


def get_modifier_state():
    if mw.app.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier:
        modshift = True
    else:
        modshift = False
    if mw.app.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
        modctrl = True
    else:
        modctrl = False
    if mw.app.keyboardModifiers() & Qt.KeyboardModifier.AltModifier:
        modalt = True
    else:
        modalt = False
    if mw.app.keyboardModifiers() & Qt.KeyboardModifier.MetaModifier:
        modmeta = True
    else:
        modmeta = False
    return modshift, modctrl, modalt, modmeta
