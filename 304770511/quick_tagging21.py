# Quick Tagging is an anki2.1 addon for quickly adding tags while reviewing
# Copyright 2012 Cayenne Boyer
# Copyright 2018 Arthur Milchior
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from anki.lang import _
from aqt import mw
from aqt.utils import getTag, getText, tooltip
from aqt.reviewer import Reviewer
from aqt.utils import tooltip
from anki.hooks import addHook
from .config import *


# add space separated tags to a note

def addTags(note, tagString):
    # add tags to card
    tagList = mw.col.tags.split(tagString)
    for tag in tagList:
        note.addTag(tag)
    note.flush()

# prompt for tags and add the results to a note
def promptAndAddTags():
    # prompt for new tags
    mw.checkpoint(_("Add Tags"))
    note = mw.reviewer.card.note()
    prompt = _("Enter tags to add:")
    (tagString, r) = getTag(mw, mw.col, prompt)
    # don't do anything if we didn't get anything
    if (not r or not tagString):
        return
    # otherwise, add the given tags:
    addTags(note, tagString)
    tooltip('Added tag(s) "%s"' % tagString)

def getTagAndNotSelectDefaultText(parent, deck, question, tags="user", default="", **kwargs):
    from aqt.tagedit import TagEdit
    te = TagEdit(parent)
    te.setCol(deck)
    te.setText(default)
    ret = getText(question, parent, edit=te,
                  geomKey='getTag', **kwargs)
    te.hideCompleter()

    return ret
    
# prompt for tags and edit the results to a note
def promptAndEditTags():
    # prompt for edit tags
    mw.checkpoint(_("Edit Tags"))
    note = mw.reviewer.card.note()
    prompt = _("Edit tags:")
    stringTags = note.stringTags()
    (tagString, r) = getTagAndNotSelectDefaultText(mw, mw.col, prompt, default=stringTags)
    # don't do anything if we didn't get anything
    if not r:
        return
    # otherwise, add the given tags:
    note.setTagsFromStr(tagString)
    note.flush()
    tooltip('Edited tags "%s"' % tagString)

def quick_tag_method(map):
  def r():
    card = mw.reviewer.card
    note = card.note()
    if 'bury' in map and map['bury']:#old config. May eventually be removed.
        map['action']='bury note'
        del map['bury']
        updateConfig()
    action = map.get('action',"")
    checkSuffix = {
        "bury card":" and Bury Card",
        "bury note":" and Bury Note",
        "suspend card":" and Suspend Card",
    }.get(action,"")
    mw.checkpoint("Add Tags"+checkSuffix)
    addTags(note, map['tags'])
    if action == "bury card":
        mw.col.sched.buryCards([card.id])
    elif action == "bury note":
        mw.col.sched.buryNote(note.id)
    elif action == "suspend card":
        mw.col.sched.suspendCards([card.id])
    if action:
        mw.reset()
    tooltipSuffix = {
        "bury card":" and buried card",
        "bury note":" and buried note",
        "suspend card":" and suspended card",
    }.get(action,"")
    tooltip(f'Added tag(s) "%s"{tooltipSuffix}'
                % map['tags'])
  return r

def new_shortcutKeys():
    tag_shortcut = getConfig().get("add tag shortcut","q")
    tag_edit_shortcut = getConfig().get("edit tag shortcut","w")
    quick_tags = getConfig().get("quick tags",dict()) # end quick_tags
    sk=[(tag_shortcut, promptAndAddTags),(tag_edit_shortcut,promptAndEditTags)]
    for key,map in quick_tags.items():
        sk.append((key,quick_tag_method(map)))
    return sk

def addShortcuts(shortcuts):
    usedShortcuts = {presentShortcut: fn for presentShortcut, fn in shortcuts}
    newShortcuts = new_shortcutKeys()
    for shortcut, fn in newShortcuts:
        if shortcut not in usedShortcuts:
            shortcuts.append((shortcut, fn))
            usedShortcuts[shortcut] = fn
        else:
            tooltip(f"Warning: shortcut {shortcut} is already used by {usedShortcuts[shortcut]}. Please change it by editing quick tagging's configuration file.")
addHook("reviewStateShortcuts", addShortcuts)
