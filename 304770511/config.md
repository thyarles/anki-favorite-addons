* add tag shortcut: The key which, when pressed during review, will open the tag adder.
* edit tag shortcut: The key which, when pressed during review, will open the tag editor.
* quick tags: A dictionary which associates a key(shortcut) with a set of actions to do. One such action consists of a dictionary. This dictionary may have the following keys:
  * `tags`: The tag or tags which will be added to the note. Add "marked" to this string to ensure the card becomes marked.
  * `action`: What to do to the card/note. The possible values are:
    * `bury note`
    * `bury card`
    * `suspend card`

For example: 
`'l': {'tags': 'hard marked', 'action': 'bury card'}`
When you press "l", the tags "hard" and "marked" are added to the card and the card is buried.

If you're already in the review mode, you won't be able to use newly configured shortcuts until you leave this mode and go back to it.
