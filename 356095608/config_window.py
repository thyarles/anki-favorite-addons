# this file is a slight modification of "symbol_window.py" from
# https://github.com/jefdongus/insert-symbols-anki-addon/blob/master/src/symbol_window.py
# with some additions from
# https://github.com/jefdongus/insert-symbols-anki-addon/blob/master/src/symbol_manager.py
# (which are at top of the class ConfigWindow in this file and)
# which are made by github.com/jefdongus and licensed as AGPLv3 see
# https://github.com/jefdongus/insert-symbols-anki-addon


""" 
This file houses the controller for Ui_ConfigWindow, which is the PyQt GUI that 
lets users edit the symbol list.

All symbol edits are performed on a local copy of the list owned by 
ConfigWindow (henceforth referred to as the "working list")
until the 'OK' button is clicked, which
internally triggers a call to ConfigWindow.accept().
"""

import string

import aqt
import io
import csv

from anki import version
from aqt.qt import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QHeaderView,
    QMessageBox,
    QTableWidgetItem,
    qtmajor,
)

from .file_load_save import (
    pickleload_nestedlist_list,
    picklesave_nestedlist,
)

if qtmajor == 5:
    from .forms5.Ui_ConfigWindow import Ui_ConfigWindow
else:
    from .forms6.Ui_ConfigWindow import Ui_ConfigWindow

ANKI_VER_21 = version.startswith("2.1.")


class ConfigWindow(QDialog):
    """
    ConfigWindow is a controller for Ui_ConfigWindow. It makes changes to the
    working list and updates the GUI in accordance with user input.

    The working list must obey the following rules at all times:
    1. It must be sorted in alphabetical order by key
    2. There must be no duplicate or conflicting keys (ie. keys that are 
      substrings of one another).
    """


    # some methods from symbol_manager.py
    """ Validation Static Functions """

    @staticmethod
    def check_format(kv_list, ignore_empty=False):
        """ 
        Checks that each entry is of the format (key, value), and that each key
        is not None or the empty string. This function can be set to ignore 
        emtpy lines.

        @param kv_list: A list.
        @param ignore_empty: Whether to skip empty lines (represented as an 
          empty list)
        @return: Returns a list of (index, line_contents), or None if no 
          invalid lines.
        """
        has_error = False
        errors = []
        for i in range(len(kv_list)):
            item = kv_list[i]
            if ignore_empty and len(item) == 0:
                continue

            if len(item) != 2 or not item[0]:  # or not item[1]:  # allow empty replacements
                has_error = True
                err_str = ' '.join(map(str, item))
                errors.append(tuple((i + 1, err_str)))
        return errors if has_error else None

    @staticmethod
    def check_if_key_valid(key):
        #""" Checks whether key is a valid standalone key. """
        #return not True in [c in key for c in string.whitespace]
        return True  # allow whitespace in replacements

    @staticmethod
    def check_if_key_duplicate(new_key, kv_list):
        """ 
        Checks to see if the new key would be a duplicate of any existing keys
        in the given key-value list.
        """
        for k, v in kv_list:
            if new_key == k:
                return True
        return None

    @staticmethod
    def check_for_duplicates(kv_list):
        """
        Checks for duplicate keys within the key-value list and returns a list
        of duplicate keys. This function accepts empty lines within the key-
        value list, empty list.

        @return: Returns a set of duplicate keys, or None if there are no 
          duplicates.
        """
        has_duplicate = False
        duplicates = set()

        for i in range(len(kv_list)):
            if len(kv_list[i]) == 0:
                continue

            for j in range(i):
                if len(kv_list[j]) == 0:
                    continue
                k1 = kv_list[i][0]
                k2 = kv_list[j][0]

                if k1 == k2:
                    has_duplicate = True
                    duplicates.add(k1)

        return duplicates if has_duplicate else None



    """ Setters """
    def _set_symbol_list(self, new_list):
        """ 
        Performs error-checking, then updates self._symbols. Returns None if 
        there are no errors, or otherwise returns a tuple of the format 
        (ERROR_CODE, ERRORS) as detailed below:

         Error Code:         Content of ERRORS:
        -------------       ----------------------
        ERR_INVALID_FORMAT  List of indices where format of new_list is wrong.
        ERR_KEY_CONFLICT    List of key conflicts in new_list.
        """
        self.SUCCESS = 0
        self.ERR_INVALID_FORMAT = -2
        self.ERR_KEY_CONFLICT = -3
        errors = self.check_format(new_list)
        if errors:
            return (self.ERR_INVALID_FORMAT, errors)

        errors = self.check_for_duplicates(new_list)
        if errors:
            return (self.ERR_KEY_CONFLICT, errors)
        return None

    def update_and_save_symbol_list(self, new_list):
        """ 
        Attempts to update the symbol list, and if successful, saves the symbol 
        list to database and calls the callback function. Returns the same 
        output as _set_symbol_list().
        """
        errors = self._set_symbol_list(new_list)
        if not errors:
            picklesave_nestedlist(new_list, self.conffile)
        return errors












    def __init__(self, parent_widget, conffile, windowtitle, dialogname_for_restore, prefill):
        super(ConfigWindow, self).__init__(parent_widget)
        self.list = None
        self.prefill = prefill
        self._selected_row = -1

        self.ui = Ui_ConfigWindow()
        self.ui.setupUi(self)

        self.ui.importButton.clicked.connect(self.import_list)
        self.ui.exportButton.clicked.connect(self.export_list)
        self.ui.okButton.clicked.connect(self.accept)
        self.ui.cancelButton.clicked.connect(self.reject)
        self.ui.resetButton.clicked.connect(self.reset_working_list)

        self.ui.addReplaceButton.clicked.connect(self.add_pair_to_list)
        self.ui.deleteButton.clicked.connect(self.delete_pair_from_list)

        # This is the text box labeled 'key':
        self.ui.keyLineEdit.textEdited.connect(self.on_key_text_changed)
        self.ui.keyLineEdit.returnPressed.connect(self.on_kv_return_pressed)

        # This is the text box labeled 'value':
        self.ui.valueLineEdit.textEdited.connect(self.on_value_text_changed)
        self.ui.valueLineEdit.returnPressed.connect(self.on_kv_return_pressed)

        self.ui.tableWidget.cellClicked.connect(self.on_cell_clicked)
        h_header = self.ui.tableWidget.horizontalHeader()
        if ANKI_VER_21:
            h_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            h_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        else:
            h_header.setResizeMode(0, QHeaderView.ResizeMode.Stretch)
            h_header.setResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.setWindowTitle(windowtitle)
        self.conffile = conffile
        self.dialogname_for_restore = dialogname_for_restore
        aqt.utils.restoreGeom(self, self.dialogname_for_restore)
        self.list = pickleload_nestedlist_list(conffile)
        self.list_as_of_import = self.list.copy()
        self._reload_view()
        if self.prefill:
            self.ui.keyLineEdit.setText(self.prefill)

    """ Editor State Getters """

    def _get_key_text(self):
        return self.ui.keyLineEdit.text().strip()

    def _get_val_text(self):
        return self.ui.valueLineEdit.text()#.strip()

    def is_row_selected(self):
        """ Returns true if a row in the tableWidget is selected. """
        return self._selected_row >= 0
    
    def is_key_valid(self):
        text = self._get_key_text()
        return bool(text) and self.check_if_key_valid(text)

    def is_val_valid(self):
        return True # bool(self._get_val_text())    # allow empty replacements

    def is_val_different(self):
        """ 
        Checks if the value in the LineEdit is different than the value of the
        selected k-v entry. If nothing is selected, return False.
        """
        if not self.is_row_selected(): 
            return False
        old = self.list[self._selected_row][1]
        new = self._get_val_text()
        return old != new


    """ 
    UI Update Functions 

    An add operation (where no existing k-v pair is selected) can occur if:
     - The new key is valid
     - The new value is valid

    A replace operation (where an existing k-v pair is selected) can occur if:
     - The new key is valid 
     - The new value is valid 
     - The new value is different from the selected k-v pair's value
    """

    def _on_row_selected(self, row, enable_add_replace):
        """ 
        Called when a row in the tableView is selected, which occurs either 
        A) when the user types a string into keyLineEdit that matches an 
        existing key or B) when the user clicks on a cell in the tableView. 

        Changes addReplaceButton to replace mode and enables the delete 
        command. In scenario A addReplaceButton may be enabled if the text in 
        valueLineEdit is different (so that users may replace the existing 
        entry), but in scenario B addReplaceButton should NOT be enabled since 
        both keyLineEdit and valueLineEdit are updated to cell contents.
        """
        if self._selected_row == -1:
            self.ui.addReplaceButton.setText("Replace")
            self.ui.addReplaceButton.clicked.disconnect(self.add_pair_to_list)
            self.ui.addReplaceButton.clicked.connect(self.replace_pair_in_list)

        self.ui.addReplaceButton.setEnabled(enable_add_replace)
        self.ui.deleteButton.setEnabled(True)
        self._selected_row = row

    def _on_row_deselected(self, enable_add_replace):
        """ 
        Called when a row in the tableView is deselected, which occurs either 
        A) when the user types a string into keyLineEdit that doesn't match any
        existing keys or B) when the working list is somehow otherwise updated. 

        Changes addReplaceButton to add mode and disables the delete command. 
        In scenario A addReplaceButton may be enabled if the text in 
        valueLineEdit is different (so that users may add a new entry), but in
        scenario B addReplaceButton should NOT be enabled since both 
        keyLineEdit and valueLineEdit will be reset.
        """
        if self._selected_row != -1:
            self.ui.addReplaceButton.setText("Add")
            self.ui.addReplaceButton.clicked.disconnect(
                self.replace_pair_in_list)
            self.ui.addReplaceButton.clicked.connect(self.add_pair_to_list)
            
        self.ui.addReplaceButton.setEnabled(enable_add_replace)
        self.ui.deleteButton.setEnabled(False)
        self._selected_row = -1

    def _on_working_list_updated(self):
        """ 
        Called when the working list is updated. Clears keyLineEdit, 
        valueLineEdit, and deselects any selected rows in the tableView. 
        """
        self.ui.keyLineEdit.setText("")
        self.ui.valueLineEdit.setText("")

        self._on_row_deselected(True)
        self._check_table_widget_integrity()

    def _scroll_to_index(self, index):
        if len(self.list) <= 0:
            return
        # Scroll to last row if key would be placed at the end
        index = min(index, self.ui.tableWidget.rowCount() - 1)

        item = self.ui.tableWidget.item(index, 0)
        self.ui.tableWidget.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtTop)

    def on_key_text_changed(self, current_text):
        """ 
        Called when the text in keyLineEdit is changed. First scrolls the 
        tableWidget, then updates add/replace and delete buttons.
        """
        current_text = current_text.strip()
        found, idx = self._find_prospective_index(current_text)
        self._scroll_to_index(idx)

        if not self.is_key_valid():
            self._on_row_deselected(False)
        else:
            # If current_text is not found, this should be an add operation.
            # Otherwise, this should be a replace.
            if found:
                can_replace = self.is_val_valid() and self.is_val_different()
                self._on_row_selected(idx, can_replace)
            else:
                self._on_row_deselected(self.is_val_valid())

    def on_value_text_changed(self, current_text):
        """ 
        Called when the text in valueLineEdit is changed. Toggles whether 
        addReplaceButton is clickable.
        """
        if self.is_row_selected():
            can_replace = (self.is_key_valid() and self.is_val_valid() 
                and self.is_val_different())
            self.ui.addReplaceButton.setEnabled(can_replace)
        else:
            can_add = (self.is_key_valid() and self.is_val_valid())
            self.ui.addReplaceButton.setEnabled(can_add)

    def on_kv_return_pressed(self):
        """ 
        Called when the Enter key is pressed while either keyLineEdit or 
        valueLineEdit has focus, and performs an add or replace action if 
        allowed.
        """
        if self.is_row_selected():
            can_replace = (self.is_key_valid() and self.is_val_valid() 
                and self.is_val_different())
            if can_replace:
                self.replace_pair_in_list()
        else:
            can_add = (self.is_key_valid() and self.is_val_valid())
            if can_add:
                self.add_pair_to_list()

    def on_cell_clicked(self, row, col):
        """ 
        When a cell in the tableWidget is clicked, update keyLineEdit, 
        valueLineEdit, and tableWidget to select that key-value pair. 
        """
        self.ui.keyLineEdit.setText(self.ui.tableWidget.item(row, 0).text())
        self.ui.valueLineEdit.setText(self.ui.tableWidget.item(row, 1).text())
        self._on_row_selected(row, False)


    """ Protected Actions """

    def _reload_view(self):
        """ 
        Reloads the entire editor and populates it with the working list.
        """
        self.ui.tableWidget.clear()

        count = 0
        for k, v in self.list:
            self.ui.tableWidget.insertRow(count)
            self.ui.tableWidget.setItem(count, 0, QTableWidgetItem(k))
            self.ui.tableWidget.setItem(count, 1, QTableWidgetItem(v))
            count += 1

        self.ui.tableWidget.setRowCount(count)  
        self._on_working_list_updated()

    def _save(self):
        """
        Attemps to save the working list. This is the ONLY time where changes 
        are pushed to SymbolManager.
        """
        errors = self.update_and_save_symbol_list(self.list)
        
        if errors:
            # I don't use  the SymbolManager class
            # if errors[0] == SymbolManager.ERR_INVALID_FORMAT:
            #     aqt.utils.showInfo(self._make_err_str_format(errors, 
            #         'Changes will not be saved', 'Row'))
            # elif errors[0] == SymbolManager.ERR_KEY_CONFLICT:
            #     aqt.utils.showInfo(self._make_err_str_duplicate(errors[1], 
            #         'Changes will not be saved'))
            # else:
            #     aqt.utils.showInfo("Error: Invalid key-value list to save. "
            #         "Changes will not be saved.")
            aqt.utils.showInfo("Error: Changes will not be saved.")
            return False

        return True




    """ Open & Close Actions """

    def accept(self):
        """ Saves changes if possible, then closes the editor.ConfigWindow """
        self._save()
        aqt.utils.saveGeom(self, self.dialogname_for_restore)
        super(ConfigWindow, self).accept()

    def reject(self):
        """ Closes the editor without saving. """
        old_list = self.list_as_of_import

        if old_list != self.list:
            confirm_msg = "Close without saving?"
            reply = QMessageBox.question(self, 'Message', confirm_msg, 
                QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                aqt.utils.saveGeom(self, self.dialogname_for_restore)
                super(ConfigWindow, self).reject()
        else:
            aqt.utils.saveGeom(self, self.dialogname_for_restore)
            super(ConfigWindow, self).reject()


    """ 
    Working List Update Actions 

    These functions update the working list and the UI, but does NOT push any 
    changes back to SymbolManager.
    """

    def _find_prospective_index(self, key):
        """ 
        Checks if the given key exists in the working list. If it does, returns 
        the index where the key can be found. If it does not, returns the index 
        where the key would be inserted.

        @return: (key_exists, index)
        """
        low, high = 0, len(self.list) - 1
        mid = 0

        while low <= high:
            mid = int((low + high) / 2)
            k = self.list[mid][0]

            if key == k:
                return (True, mid)
            elif k < key:
                low = mid + 1
                mid += 1
            else:
                high = mid - 1
        return (False, mid)

    def add_pair_to_list(self):
        """ 
        Adds an entry to the working list, performs validation, and then 
        updates the UI. 
        """
        if self.is_row_selected():
            aqt.utils.showInfo("Error: Cannot add entry when a row is "
                "already selected.")
            return

        new_key = self._get_key_text()
        new_val = self._get_val_text()

        has_conflict = self.check_if_key_duplicate(new_key, 
            self.list)
        if has_conflict:
            aqt.utils.showInfo(("Error: Cannot add '%s' as a key with the same"
                " name already exists." % (new_key)))
            return

        (_, idx) = self._find_prospective_index(new_key)
        self.list.insert(idx, (new_key, new_val))

        self.ui.tableWidget.insertRow(idx)
        self.ui.tableWidget.setItem(idx, 0, QTableWidgetItem(new_key))
        self.ui.tableWidget.setItem(idx, 1, QTableWidgetItem(new_val))
        self._on_working_list_updated()

    def replace_pair_in_list(self):
        """ Replaces an existing key-value pair from the working list. """
        if not self.is_row_selected():
            aqt.utils.showInfo("Error: Cannot replace when no valid "
                "row is selected.")
            return

        new_val = self._get_val_text()
        old_pair = self.list[self._selected_row]

        self.list[self._selected_row] = (old_pair[0], new_val)

        widget_item = self.ui.tableWidget.item(self._selected_row, 1)
        widget_item.setText(new_val)
        self._on_working_list_updated()

    def delete_pair_from_list(self):
        """ Deletes an existing key-value pair from the working list. """
        if not self.is_row_selected():
            aqt.utils.showInfo("Error: Cannot delete when no valid "
                "row is selected.")
            return

        del self.list[self._selected_row]

        self.ui.tableWidget.removeRow(self._selected_row)
        self._on_working_list_updated()

    def reset_working_list(self):
        """ Resets the working list to the default symbol list. """
        confirm_msg = ("Load default symbols? This will delete any "
            "unsaved changes!")
        reply = QMessageBox.question(self, 'Message', confirm_msg, 
            QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.list = []
            self._reload_view()


    """ Import and Export Actions """

    def import_list(self):
        """ 
        Imports key-value pairs from a .txt file into the editor. The import 
        procedure is successful only if each and every entry in the .txt file 
        is valid; otherwise, an error will be displayed and the operation
        will abort.
        """
        if ANKI_VER_21:
            fname, _ = QFileDialog.getOpenFileName(self, 'Open file', '',
                "CSV (*.csv)")
        else:
            fname = QFileDialog.getOpenFileName(self, 'Open file', '', 
                "CSV (*.csv)")
        if not fname:
            return

        with io.open(fname, 'r', encoding='utf8') as file:
            reader = csv.reader(file)
            new_list = []

            for row in reader:
                new_list.append(row)

            if self._validate_imported_list(new_list):
                # Filter out empty lines before updating the list, but do so 
                # AFTER error checking so that accurate line numbers will be 
                # shown during error checking.
                new_list = [x for x in new_list if len(x) > 0]

                new_list = sorted(new_list, key=lambda x: x[0])
                self.list = new_list
                self._reload_view()

    def _validate_imported_list(self, new_list):
        """ 
        Checks that the imported file is valid, and displays an error message 
        if not. This function takes in a list that DOES contain empty lines 
        (which will be an empty list) so that accurate line numbers will be 
        displayed.
        """
        errors = self.check_format(new_list, ignore_empty=True)
        if errors:
            aqt.utils.showInfo(self._make_err_str_format(errors, 
                'Unable to import', 'Line'))
            return False

        errors = self.check_for_duplicates(new_list)
        if errors:
            aqt.utils.showInfo(self._make_err_str_duplicate(errors, 
                'Unable to import'))
            return False

        return True

    def export_list(self):
        """ 
        Exports the current symbol list into a .txt file. Before exporting, 
        the list displayed in the editor must match the symbol list stored 
        in the system. 
        """
        old_list = self.list_as_of_import

        if old_list != self.list:
            confirm_msg = "You must save changes before exporting. Save now?"
            reply = QMessageBox.question(self, 'Message', confirm_msg, 
                QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                is_success = self._save()
                if is_success:
                    aqt.utils.showInfo('The symbol list has been saved.')
                else:
                    return
            else:
                return

        if ANKI_VER_21:
            fname, _ = QFileDialog.getSaveFileName(self, 'Save file', '', 
                "CSV (*.csv)")
        else:
            fname = QFileDialog.getSaveFileName(self, 'Save file', '', 
                "CSV (*.csv)")
        if not fname:
            return

        with io.open(fname, 'w', newline='\n', encoding='utf-8') as file:
            writer = csv.writer(file)
            for k, v in self.list:
                writer.writerow([k, v])
            aqt.utils.showInfo("Symbol list written to: " + fname)


    """ Error Strings """

    def _make_err_str_format(self, errors, op_desc, entry_type):
        """ 
        Creates an error message for format errors:

        @param op_desc: Which operation is being performed.
        @param entry_type: Either 'Line' or 'Row'
        """
        err_str = ("Error: %s due to incorrect format in the following lines "
            "(expecting <key> <value>).\n\n") % op_desc

        for i, string in errors:
            err_str += "%s %d: %s\n" % (entry_type, i, string)
        return err_str

    def _make_err_str_duplicate(self, errors, op_desc):
        """ 
        Creates an error message for key conflicts. 

        @param op_desc: Which operation is being performed.
        @param entry_type: Either 'Line' or 'Row'
        """
        err_str = ("Error: %s as the following duplicate keys "
            "were detected: \n\n" % op_desc)
            
        for key in errors:
            err_str += "%s\n" % key
        return err_str


    """ Validation Functions """

    def _check_table_widget_integrity(self):
        """ 
        Checks that the tableWidget displays the same items in the same order 
        as the working list. 
        """
        wl_len = len(self.list)
        tw_len = self.ui.tableWidget.rowCount()

        # Checks that tableWidget has same # of entries as the working list:
        if wl_len != tw_len:
            aqt.utils.showInfo(("Error: working list length %d does not match "
                "tableWidget length %d.") % (wl_len, tw_len))
            return

        # Checks that entries in the tableWidget & working list match:
        for i in range(wl_len):
            tw_k = self.ui.tableWidget.item(i, 0).text()
            tw_v = self.ui.tableWidget.item(i, 1).text()

            l_k = self.list[i][0]
            l_v = self.list[i][1]

            k_match = (tw_k == l_k)
            v_match = (tw_v == l_v)

            if not k_match or not v_match:
                err_str = ("Error: kv pair at row %d does not match.\n"
                    "List: %s, %s\nWidget: %s, %s") % (i, l_k, l_v, tw_k, tw_v)
                aqt.utils.showInfo(err_str)
                return

        # Checks that the tableWidget is displaying entries in alphabetical 
        # order by key:
        sorted_list = sorted(self.list, key=lambda x: x[0])
        has_error = False
        err_str = ""

        for i in range(wl_len):
            l_k = self.list[i][0]
            s_k = sorted_list[i][0]

            if l_k != s_k:
                has_error = True
                err_str += ("at row %d key is %s, but should be %s\n" 
                    % (i, l_k, s_k))

        if has_error:
            aqt.utils.showInfo("Error: list not alphabetical:" + err_str)
