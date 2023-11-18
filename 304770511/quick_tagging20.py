# Quick Tagging is an anki2 addon for quickly adding tags while reviewing
# Copyright 2012 Cayenne Boyer
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

from aqt import mw
from aqt.utils import getTag, tooltip
from aqt.reviewer import Reviewer
userOption = mw.addonManager.getConfig(__name__)
tag_shortcut = userOption.get("tag shortcut","t")
quick_tags = userOption.get("quick tags",dict()) # end quick_tags

def debug(t):
    print(t)
    pass
# add space separated tags to a note

def addTags(note, tagString):
    debug(f"Call addTags({note},{tagString})")
    # add tags to card
    tagList = mw.col.tags.split(tagString)
    for tag in tagList:
        note.addTag(tag)
    note.flush()

# prompt for tags and add the results to a note
def promptAndAddTags():
    # prompt for new tags
    debug(f"Call promptAndAddTags()")
    mw.checkpoint(_("Add Tags"))
    note = mw.reviewer.card.note()
    prompt = _("Enter tags to add:")
    (tagString, r) = getTag(mw, mw.col, prompt)
    # don't do anything if we didn't get anything
    if not r:
        return
    # otherwise, add the given tags:
    addTags(note, tagString)
    tooltip('Added tag(s) "%s"' % tagString)

def quick_tag_method(map):
  debug(f"Call quick_tag_method({map})")
  def r():
    debug(f"Call function defined thanks to ({map})")
    note = mw.reviewer.card.note()
    if 'bury' in map and map['bury']:
        mw.checkpoint("Add Tags and Bury")
        addTags(note, map['tags'])
        mw.col.sched.buryNote(note.id)
        mw.reset()
        tooltip('Added tag(s) "%s" and buried note' 
                % map['tags'])
    else:
        mw.checkpoint(_("Add Tags"))
        addTags(note, map['tags'])
        tooltip('Added tag(s) "%s"' % map['tags'])
  return r

def new_shortcutKeys():
    sk=[(tag_shortcut, promptAndAddTags)]
    for key,map in quick_tags.items():
        sk.append((key,quick_tag_method(map)))
    debug(f"new_shortcutKeys(), returning {sk}")
    return sk
        
old_shortcutKeys = Reviewer._shortcutKeys
def _shortcutKeys(self):
    shortcutKeys = old_shortcutKeys(self)+new_shortcutKeys()
    # shortcutKeys= []
    debug(f"new_shortcutKeys(), returning {shortcutKeys}")
    return shortcutKeys
Reviewer._shortcutKeys=_shortcutKeys 

