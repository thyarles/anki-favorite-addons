import operator
import os
import re

from anki.hooks import addHook, wrap
from aqt import mw
from aqt.editor import Editor

from aqt.qt import (
    QKeySequence,
    Qt,
)


from .config import gc
from .helpers import (
    get_modifier_state,
)
from .main_menu_entries_and_options import (
    regex_replace_dialog,
    simple_replace_dialog,
)
from .replacement_vars import (
    regular_replacements,
    regex_replacements,
)


def batch_replacer_helper(editor, field):
    self = editor
    if field is None:  # no field focused
        return
    html = self.note.fields[field]

    # P: i.e is sorted before i.e. so the latter wouldn't be replaced
    replace_dict = regular_replacements()
    for old in sorted(replace_dict, key=len, reverse=True):
        new = replace_dict.get(old)
        html = html.replace(old, new)
        
    for match, repl in regex_replacements().items():
        html = re.sub(match, repl, html)


    # remove most frequent abbreviation
    def counter(ges):
        return html.lower().count(ges)
    user_abbrevs = gc("user_abbrev_dict")
    counts = {}
    for g in user_abbrevs.keys():
        counts[g]=counter(g)
    if not all(v == 0 for v in counts.values()):
        highest = max(counts.items(), key=operator.itemgetter(1))[0]
        to_insert = user_abbrevs[highest]
        abbrev_replacements = {
            "xxx ": "",
            " xxx": "",
            "xxx": "",
        }
        for old, new in abbrev_replacements.items():
            html = html.replace(old.replace("xxx", to_insert), new)
            html = html.replace(old.replace("xxx", to_insert.lower()), new)

        
    self.note.fields[field] = html
    if not self.addMode:
        self.note.flush()
    self.loadNote(focusTo=field)


def batch_replacer(editor, should_show_simple=False):
    self = editor
    text = editor.web.selectedText()
    field = self.currentField
    modshift, modctrl, modalt, modmeta = get_modifier_state()
    # print(f"should_show_simple is: {should_show_simple}, text is {text}, Modifiers: {modshift}, {modctrl}, {modalt}, {modmeta}")
    if modctrl and (modshift or should_show_simple):
        regex_replace_dialog(editor.parentWindow, text)
        return
    elif modshift or should_show_simple:
        simple_replace_dialog(editor.parentWindow, text)
        return
    self.saveNow(lambda e=editor, f=field: batch_replacer_helper(e, f))


def keystr(k):
    key = QKeySequence(k)
    return key.toString(QKeySequence.SequenceFormat.NativeText)


def setupEditorButtonsFilter(buttons, editor):
    addon_path = os.path.dirname(__file__)
    icons_dir = os.path.join(addon_path, 'icons')
    cut = gc('shortcut')
    if cut:
        cutfmt = f"({keystr(cut)})"
    else:
        cutfmt = ""
    b = editor.addButton(
        icon=os.path.join(icons_dir, 'Octicons-mirror.svg'),
        cmd="i_batch_replacer", 
        func=lambda e=editor: batch_replacer(e),
        tip=f"batch replacer {cutfmt}",
        keys=gc('shortcut')
    )
    buttons.append(b)
    return buttons
addHook("setupEditorButtons", setupEditorButtonsFilter)


def add_to_context(view, menu):
    a = menu.addAction("batch replacer (press ctrl for regex)")
    a.triggered.connect(lambda _,e=view.editor: batch_replacer(e, True))


if gc("show_in_context_menu", True):
    addHook("EditorWebView.contextMenuEvent", add_to_context)
