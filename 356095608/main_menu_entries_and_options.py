from aqt import mw
from aqt.qt import (
    QAction,
    QMenu,
)
from aqt.utils import (
    tooltip
)

from .config import (
    file_replacements,
    file_regex,
)
from .config_window import ConfigWindow
from .file_load_save import (
    pickleload_nestedlist_list,
    picklesave_nestedlist,
)
from .replacement_vars import (
    update_regex,
    update_regular,
)





def simple_replace_dialog(parent, prefill=None):
    windowtitle = "Anki - Editor Batch Replacements"
    dialogname_for_restore = "batch_replace_regular"
    file = file_replacements
    dialog = ConfigWindow(parent, file, windowtitle, dialogname_for_restore, prefill)
    if dialog.exec():
        update_regular()


def regex_replace_dialog(parent, prefill=None):
    windowtitle = "Anki - Editor Batch Replacements REGEX"
    dialogname_for_restore = "batch_replace_regex"
    file = file_regex
    dialog = ConfigWindow(parent, file, windowtitle, dialogname_for_restore, prefill)
    if dialog.exec():
        update_regex()


ebrm = QMenu("Editor Batch Replacer", mw)
mw.form.menuTools.addMenu(ebrm)

act1 = QAction("... edit simple replacements", mw)
act1.triggered.connect(lambda _,w=mw: simple_replace_dialog(w))
ebrm.addAction(act1)

act2 = QAction("... edit regular expressions", mw)
act2.triggered.connect(lambda _,w=mw: regex_replace_dialog(w))
ebrm.addAction(act2)
