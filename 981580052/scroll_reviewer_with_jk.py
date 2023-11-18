# -*- coding: utf-8 -*-

"""
Anki Add-on: Scroll Reviewer using j and k

While review window is focused j and k will now scroll down and
scroll up respectivly, also J and K will be page up, page down

Copyright:  (c) 2021 Yaroslav Fedorichenko <yar.fed99@gmail.com>
License: GNU AGPLv3 or later <https://www.gnu.org/licenses/agpl.html>
"""

from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
from aqt import AnkiQt, mw
from anki.hooks import wrap

config = mw.addonManager.getConfig(__name__)
def _scroll(self, vertical):
    self.web.eval(f"window.scrollBy(0,{vertical})")

def _scrollDown(self, vertical = 50):
    _scroll(self, abs(vertical))

def _scrollUp(self, vertical = 50):
    _scroll(self, -abs(vertical))

def add_jkJK_shortcuts(self, shortcuts):
    if not self.state == "review":
        return
    shortcuts = [
        ("j", lambda: _scrollDown(self, config['j_scroll_distance'])),
        ("k", lambda: _scrollUp(self, config['k_scroll_distance'])),
        ("Shift+J", lambda: _scrollDown(self, config['Shift_J_scroll_distance'])),
        ("Shift+K", lambda: _scrollUp(self, config['Shift_K_scroll_distance']))
    ]
    qshortcuts = []
    for key, fn in shortcuts:
        scut = QShortcut(QKeySequence(key), self, activated=fn)  # type: ignore
        scut.setAutoRepeat(True)
        qshortcuts.append(scut)
    self.stateShortcuts.extend(qshortcuts)


AnkiQt.setStateShortcuts = wrap(AnkiQt.setStateShortcuts, add_jkJK_shortcuts)
