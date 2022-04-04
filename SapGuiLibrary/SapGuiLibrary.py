import pythoncom
import win32com.client
import time
from pythoncom import com_error
import robot.libraries.Screenshot as screenshot
import os
from robot.api import logger


class SapGuiLibrary:
    """The SapGuiLibrary is a library that enables users to create tests for the Sap Gui application

    The library uses the Sap Scripting Engine, therefore Scripting must be enabled in Sap in order for this library to work.

    = Opening a connection / Before running tests =

    First of all, you have to *make sure the Sap Logon Pad is started*. You can automate this process by using the
    AutoIT library or the Process Library.

    After the Sap Login Pad is started, you can connect to the Sap Session using the keyword `connect to session`.

    If you have a successful connection you can use `Open Connection` to open a new connection from the Sap Logon Pad
    or `Connect To Existing Connection` to connect to a connection that is already open.

    = Locating or specifying elements =

    You need to specify elements starting from the window ID, for example, wnd[0]/tbar[1]/btn[8]. In some cases the SAP
    ID contains backslashes. Make sure you escape these backslashes by adding another backslash in front of it.

    = Screenshots (on error) =

    The SapGUILibrary offers an option for automatic screenshots on error.
    Default this option is enabled, use keyword `disable screenshots on error` to skip the screenshot functionality.
    Alternatively, this option can be set at import.
    """
    __version__ = '1.2'
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    def __init__(self, screenshots_on_error=True, screenshot_directory=None):
        """Sets default variables for the library
        """
        self.explicit_wait = float(0.0)

        self.sapapp = -1
        self.session = -1
        self.connection = -1

        self.take_screenshots = screenshots_on_error
        self.screenshot = screenshot.Screenshot()

        if screenshot_directory is not None:
            if not os.path.exists(screenshot_directory):
                os.makedirs(screenshot_directory)
            self.screenshot.set_screenshot_directory(screenshot_directory)

    def click_element(self, element_id):
        """Performs a single click on a given element. Used only for buttons, tabs and menu items.

        In case you want to change a value of an element like checkboxes of selecting an option in dropdown lists,
        use `select checkbox` or `select from list by label` instead.
        """

        # Performing the correct method on an element, depending on the type of element
        element_type = self.get_element_type(element_id)
        if (element_type == "GuiTab"
                or element_type == "GuiMenu"):
            self.session.findById(element_id).select()
        elif element_type == "GuiButton":
            self.session.findById(element_id).press()
        else:
            self.take_screenshot()
            message = "You cannot use 'click_element' on element type '%s', maybe use 'select checkbox' instead?" % element_type
            raise Warning(message)
        time.sleep(self.explicit_wait)

    def click_toolbar_button(self, table_id, button_id):
        """Clicks a button of a toolbar within a GridView 'table_id' which is contained within a shell object.
        Use the Scripting tracker recorder to find the 'button_id' of the button to click
        """
        self.element_should_be_present(table_id)

        try:
            self.session.findById(table_id).pressToolbarButton(button_id)
        except AttributeError:
            self.take_screenshot()
            self.session.findById(table_id).pressButton(button_id)
        except com_error:
            self.take_screenshot()
            message = "Cannot find Button_id '%s'." % button_id
            raise ValueError(message)
        time.sleep(self.explicit_wait)

    def connect_to_existing_connection(self, connection_name):
        """Connects to an open connection. If the connection matches the given connection_name, the session is connected
        to this connection.
        """
        self.connection = self.sapapp.Children(0)
        if self.connection.Description == connection_name:
            self.session = self.connection.children(0)
        else:
            self.take_screenshot()
            message = "No existing connection for '%s' found." % connection_name
            raise ValueError(message)

    def connect_to_session(self, explicit_wait=0):
        """Connects to an open session SAP.

        See `Opening a connection / Before running tests` for details about requirements before connecting to a session.

        Optionally `set explicit wait` can be used to set the explicit wait time.

        *Examples*:
        | *Keyword*             | *Attributes*          |
        | connect to session    |                       |
        | connect to session    | 3                     |
        | connect to session    | explicit_wait=500ms   |

        """
        lenstr = len("SAPGUI")
        rot = pythoncom.GetRunningObjectTable()
        rotenum = rot.EnumRunning()
        while True:
            monikers = rotenum.Next()
            if not monikers:
                break
            ctx = pythoncom.CreateBindCtx(0)
            name = monikers[0].GetDisplayName(ctx, None);

            if name[-lenstr:] == "SAPGUI":
                obj = rot.GetObject(monikers[0])
                sapgui = win32com.client.Dispatch(obj.QueryInterface(pythoncom.IID_IDispatch))
                self.sapapp = sapgui.GetScriptingEngine
                # Set explicit_wait after connection succeed
                self.set_explicit_wait(explicit_wait)

        if hasattr(self.sapapp, "OpenConnection") == False:
            self.take_screenshot()
            message = "Could not connect to Session, is Sap Logon Pad open?"
            raise Warning(message)
        # run explicit wait last
        time.sleep(self.explicit_wait)

    def disable_screenshots_on_error(self):
        """Disables automatic screenshots on error.
        """
        self.take_screenshots = False

    def doubleclick_element(self, element_id, item_id, column_id):
        """Performs a double-click on a given element. Used only for shell objects.
        """

        # Performing the correct method on an element, depending on the type of element
        element_type = self.get_element_type(element_id)
        if element_type == "GuiShell":
            self.session.findById(element_id).doubleClickItem(item_id, column_id)
        else:
            self.take_screenshot()
            message = "You cannot use 'doubleclick element' on element type '%s', maybe use 'click element' instead?" % element_type
            raise Warning(message)
        time.sleep(self.explicit_wait)

    def element_should_be_present(self, element_id, message=None):
        """Checks whether an element is present on the screen.
        """
        try:
            self.session.findById(element_id)
        except com_error:
            self.take_screenshot()
            if message is None:
                message = "Cannot find Element '%s'." % element_id
            raise ValueError(message)

    def element_value_should_be(self, element_id, expected_value, message=None):
        """Checks whether the element value is the same as the expected value.
        The possible expected values depend on the type of element (see usage).

         Usage:
         | *Element type*   | *possible values*                 |
         | textfield        | text                              |
         | label            | text                              |
         | titlebar         | text                              |
         | button           | text on the button                |
         | checkbox         | checked / unchecked               |
         | radiobutton      | checked / unchecked               |
         | combobox         | text of the option to be expected |
         """
        element_type = self.get_element_type(element_id)
        actual_value = self.get_value(element_id)

        # Breaking up the different element types so we can check the value the correct way
        if (element_type == "GuiTextField"
                or element_type == "GuiCTextField"
                or element_type == "GuiComboBox"
                or element_type == "GuiTitlebar"
                or element_type == "GuiButton"
                or element_type == "GuiLabel"):
            self.session.findById(element_id).setfocus()
            time.sleep(self.explicit_wait)
            # In these cases we can simply check the text value against the value of the element
            if expected_value != actual_value:
                if message is None:
                    message = "Element value of '%s' should be '%s', but was '%s'" % (
                        element_id, expected_value, actual_value)
                self.take_screenshot()
                raise AssertionError(message)
        elif element_type == "GuiStatusPane":
            if expected_value != actual_value:
                if message is None:
                    message = "Element value of '%s' should be '%s', but was '%s'" % (
                        element_id, expected_value, actual_value)
                self.take_screenshot()
                raise AssertionError(message)
        elif (element_type == "GuiCheckBox"
              or element_type == "GuiRadioButton"):
            # First check if there is a correct value given, otherwise raise an assertion error
            self.session.findById(element_id).setfocus()
            if (expected_value.lower() != "checked"
                    and expected_value.lower() != "unchecked"):
                # Raise an AsertionError when no correct expected_value is given
                self.take_screenshot()
                if message is None:
                    message = "Incorrect value for element type '%s', provide checked or unchecked" % element_type
                raise AssertionError(message)

            # Check whether the expected value matches the actual value. If not, raise an assertion error
            if expected_value.lower() != actual_value:
                self.take_screenshot()
                if message is None:
                    message = "Element value of '%s' didn't match the expected value" % element_id
                raise AssertionError(message)
        else:
            # When the type of element can't be checked, raise an assertion error
            self.take_screenshot()
            message = "Cannot use keyword 'element value should be' for element type '%s'" % element_type
            raise Warning(message)
        # Run explicit wait as last
        time.sleep(self.explicit_wait)

    def element_value_should_contain(self, element_id, expected_value, message=None):
        """Checks whether the element value contains the expected value.
        The possible expected values depend on the type of element (see usage).

         Usage:
         | *Element type*   | *possible values*                 |
         | textfield        | text                              |
         | label            | text                              |
         | titlebar         | text                              |
         | button           | text on the button                |
         | combobox         | text of the option to be expected |
         """
        element_type = self.get_element_type(element_id)

        # Breaking up the different element types so we can check the value the correct way
        if (element_type == "GuiTextField"
                or element_type == "GuiCTextField"
                or element_type == "GuiComboBox"
                or element_type == "GuiTitlebar"
                or element_type == "GuiButton"
                or element_type == "GuiLabel"):
            self.session.findById(element_id).setfocus()
            actual_value = self.get_value(element_id)
            time.sleep(self.explicit_wait)
            # In these cases we can simply check the text value against the value of the element
            if expected_value not in actual_value:
                self.take_screenshot()
                if message is None:
                    message = "Element value '%s' does not contain '%s', (but was '%s')" % (
                        element_id, expected_value, actual_value)
                raise AssertionError(message)
        else:
            # When the element content can't be checked, raise an assertion error
            self.take_screenshot()
            message = "Cannot use keyword 'element value should contain' for element type '%s'" % element_type
            raise Warning(message)
        # Run explicit wait as last
        time.sleep(self.explicit_wait)

    def enable_screenshots_on_error(self):
        """Enables automatic screenshots on error.
        """
        self.take_screenshots = True

    def get_cell_value(self, table_id, row_num, col_id):
        """Returns the cell value for the specified cell.
        """
        self.element_should_be_present(table_id)

        try:
            cellValue = self.session.findById(table_id).getCell(row_num, col_id).text
            return cellValue
        except com_error:
            self.take_screenshot()
            message = "Cannot find Column_id '%s'." % col_id
            raise ValueError(message)

    def get_element_location(self, element_id):
        """Returns the Sap element location for the given element.
        """
        self.element_should_be_present(element_id)
        screenleft = self.session.findById(element_id).screenLeft
        screentop = self.session.findById(element_id).screenTop
        return screenleft, screentop

    def get_element_type(self, element_id):
        """Returns the Sap element type for the given element.
        """
        try:
            type = self.session.findById(element_id).type
            return type
        except com_error:
            self.take_screenshot()
            message = "Cannot find element with id '%s'" % element_id
            raise ValueError(message)

    def get_row_count(self, table_id):
        """Returns the number of rows found in the specified table.
        """
        self.element_should_be_present(table_id)
        rowCount = self.session.findById(table_id).rowCount
        return rowCount

    def get_scroll_position(self, element_id):
        """Returns the scroll position of the scrollbar of an element 'element_id' that is contained within a shell object.
        """
        self.element_should_be_present(element_id)
        currentPosition = self.session.findById(element_id).verticalScrollbar.position
        return currentPosition

    def get_value(self, element_id):
        """Gets the value of the given element. The possible return values depend on the type of element (see Return values).

        Return values:
        | *Element type*   | *Return values*                   |
        | textfield        | text                              |
        | label            | text                              |
        | checkbox         | checked / unchecked               |
        | radiobutton      | checked / unchecked               |
        | combobox         | text of the selected option       |
        | guibutton        | text                              |
        | guititlebar      | text                              |
        | guistatusbar     | text                              |
        | guitab           | text                              |
        """
        element_type = self.get_element_type(element_id)
        return_value = ""
        if (element_type == "GuiTextField"
                or element_type == "GuiCTextField"
                or element_type == "GuiLabel"
                or element_type == "GuiTitlebar"
                or element_type == "GuiStatusbar"
                or element_type == "GuiButton"
                or element_type == "GuiTab"
                or element_type == "GuiShell"):
            self.set_focus(element_id)
            return_value = self.session.findById(element_id).text
        elif element_type == "GuiStatusPane":
            return_value = self.session.findById(element_id).text
        elif (element_type == "GuiCheckBox"
              or element_type == "GuiRadioButton"):
            actual_value = self.session.findById(element_id).selected
            # In these situations we return check / unchecked, so we change these values here
            if actual_value == True:
                return_value = "checked"
            elif actual_value == False:
                return_value = "unchecked"
        elif element_type == "GuiComboBox":
            return_value = self.session.findById(element_id).text
            # In comboboxes there are many spaces after the value. In order to check the value, we strip them away.
            return_value = return_value.strip()
        else:
            # If we can't return the value for this element type, raise an assertion error
            self.take_screenshot()
            message = "Cannot get value for element type '%s'" % element_type
            raise Warning(message)
        return return_value

    def get_window_title(self, locator):
        """Retrieves the window title of the given window.
        """
        return_value = ""
        try:
            return_value = self.session.findById(locator).text
        except com_error:
            self.take_screenshot()
            message = "Cannot find window with locator '%s'" % locator
            raise ValueError(message)

        return return_value

    def input_password(self, element_id, password):
        """Inserts the given password into the text field identified by locator.
        The password is not recorded in the log.
        """
        element_type = self.get_element_type(element_id)
        if (element_type == "GuiTextField"
                or element_type == "GuiCTextField"
                or element_type == "GuiShell"
                or element_type == "GuiPasswordField"):
            self.session.findById(element_id).text = password
            logger.info("Typing password into text field '%s'." % element_id)
            time.sleep(self.explicit_wait)
        else:
            self.take_screenshot()
            message = "Cannot use keyword 'input password' for element type '%s'" % element_type
            raise ValueError(message)

    def input_text(self, element_id, text):
        """Inserts the given text into the text field identified by locator.
        Use keyword `input password` to insert a password in a text field.
        """
        element_type = self.get_element_type(element_id)
        if (element_type == "GuiTextField"
                or element_type == "GuiCTextField"
                or element_type == "GuiShell"
                or element_type == "GuiPasswordField"):
            self.session.findById(element_id).text = text
            logger.info("Typing text '%s' into text field '%s'." % (text, element_id))
            time.sleep(self.explicit_wait)
        else:
            self.take_screenshot()
            message = "Cannot use keyword 'input text' for element type '%s'" % element_type
            raise ValueError(message)

    def maximize_window(self, window=0):
        """Maximizes the SapGui window.
        """
        try:
            self.session.findById("wnd[%s]" % window).maximize()
            time.sleep(self.explicit_wait)
        except com_error:
            self.take_screenshot()
            message = "Cannot maximize window wnd[% s], is the window actually open?" % window
            raise ValueError(message)

        # run explicit wait last
        time.sleep(self.explicit_wait)

    def open_connection(self, connection_name):
        """Opens a connection to the given connection name. Be sure to provide the full connection name, including the bracket part.
        """
        # First check if the sapapp is set and OpenConnection method exists
        if hasattr(self.sapapp, "OpenConnection") == False:
            self.take_screenshot()
            message = "Cannot find an open Sap Login Pad, is Sap Logon Pad open?"
            raise Warning(message)

        try:
            self.connection = self.sapapp.OpenConnection(connection_name, True)
        except com_error:
            self.take_screenshot()
            message = "Cannot open connection '%s', please check connection name." % connection_name
            raise ValueError(message)
        self.session = self.connection.children(0)
        # run explicit wait last
        time.sleep(self.explicit_wait)

    def run_transaction(self, transaction):
        """Runs a Sap transaction. An error is given when an unknown transaction is specified.
        """
        self.session.findById("wnd[0]/tbar[0]/okcd").text = transaction
        time.sleep(self.explicit_wait)
        self.send_vkey(0)

        if transaction == '/nex':
            return

        pane_value = self.session.findById("wnd[0]/sbar/pane[0]").text
        if pane_value in ("Transactie %s bestaat niet" % transaction.upper(),
                          "Transaction %s does not exist" % transaction.upper(),
                          "Transaktion %s existiert nicht" % transaction.upper()):
            self.take_screenshot()
            message = "Unknown transaction: '%s'" % transaction
            raise ValueError(message)

    def scroll(self, element_id, position):
        """Scrolls the scrollbar of an element 'element_id' that is contained within a shell object.
        'Position' is the number of rows to scroll.
        """
        self.element_should_be_present(element_id)
        self.session.findById(element_id).verticalScrollbar.position = position
        time.sleep(self.explicit_wait)

    def select_checkbox(self, element_id):
        """Selects checkbox identified by locator.
        Does nothing if the checkbox is already selected.
        """
        element_type = self.get_element_type(element_id)
        if element_type == "GuiCheckBox":
            self.session.findById(element_id).selected = True
        else:
            self.take_screenshot()
            message = "Cannot use keyword 'select checkbox' for element type '%s'" % element_type
            raise ValueError(message)
        time.sleep(self.explicit_wait)

    def select_context_menu_item(self, element_id, menu_or_button_id, item_id):
        """Selects an item from the context menu by clicking a button or right-clicking in the node context menu.
        """
        self.element_should_be_present(element_id)

        # The function checks if the element has an attribute "nodeContextMenu" or "pressContextButton"
        if hasattr(self.session.findById(element_id), "nodeContextMenu"):
            self.session.findById(element_id).nodeContextMenu(menu_or_button_id)
        elif hasattr(self.session.findById(element_id), "pressContextButton"):
            self.session.findById(element_id).pressContextButton(menu_or_button_id)
        # The element has neither attributes, give an error message
        else:
            self.take_screenshot()
            element_type = self.get_element_type(element_id)
            message = "Cannot use keyword 'select context menu item' for element type '%s'" % element_type
            raise ValueError(message)
        self.session.findById(element_id).selectContextMenuItem(item_id)
        time.sleep(self.explicit_wait)

    def select_from_list_by_label(self, element_id, value):
        """Selects the specified option from the selection list.
        """
        element_type = self.get_element_type(element_id)
        if element_type == "GuiComboBox":
            self.session.findById(element_id).value = value
            time.sleep(self.explicit_wait)
        else:
            self.take_screenshot()
            message = "Cannot use keyword 'select from list by label' for element type '%s'" % element_type
            raise ValueError(message)

    def select_node(self, tree_id, node_id, expand=False):
        """Selects a node of a TableTreeControl 'tree_id' which is contained within a shell object.

        Use the Scripting tracker recorder to find the 'node_id' of the node.
        Expand can be set to True to expand the node. If the node cannot be expanded, no error is given.
        """
        self.element_should_be_present(tree_id)
        self.session.findById(tree_id).selectedNode = node_id
        if expand:
            #TODO: elegantere manier vinden om dit af te vangen
            try:
                self.session.findById(tree_id).expandNode(node_id)
            except com_error:
                pass
        time.sleep(self.explicit_wait)

    def select_node_link(self, tree_id, link_id1, link_id2):
        """Selects a link of a TableTreeControl 'tree_id' which is contained within a shell object.

        Use the Scripting tracker recorder to find the 'link_id1' and 'link_id2' of the link to select.
        """
        self.element_should_be_present(tree_id)
        self.session.findById(tree_id).selectItem(link_id1, link_id2)
        self.session.findById(tree_id).clickLink(link_id1, link_id2)
        time.sleep(self.explicit_wait)

    def select_radio_button(self, element_id):
        """Sets radio button to the specified value.
        """
        element_type = self.get_element_type(element_id)
        if element_type == "GuiRadioButton":
            self.session.findById(element_id).selected = True
        else:
            self.take_screenshot()
            message = "Cannot use keyword 'select radio button' for element type '%s'" % element_type
            raise ValueError(message)
        time.sleep(self.explicit_wait)

    def select_table_column(self, table_id, column_id):
        """Selects an entire column of a GridView 'table_id' which is contained within a shell object.

        Use the Scripting tracker recorder to find the 'column_id' of the column to select.
        """
        self.element_should_be_present(table_id)
        try:
            self.session.findById(table_id).selectColumn(column_id)
        except com_error:
            self.take_screenshot()
            message = "Cannot find Column_id '%s'." % column_id
            raise ValueError(message)
        time.sleep(self.explicit_wait)

    def select_table_row(self, table_id, row_num):
        """Selects an entire row of a table. This can either be a TableControl or a GridView 'table_id'
        which is contained within a shell object. The row is an index to select the row, starting from 0.
        """
        element_type = self.get_element_type(table_id)
        if (element_type == "GuiTableControl"):
            id = self.session.findById(table_id).getAbsoluteRow(row_num)
            id.selected = -1
        else:
            try:
                self.session.findById(table_id).selectedRows = row_num
            except com_error:
                self.take_screenshot()
                message = "Cannot use keyword 'select table row' for element type '%s'" % element_type
                raise ValueError(message)
        time.sleep(self.explicit_wait)

    def send_vkey(self, vkey_id, window=0):
        """Sends a SAP virtual key combination to the window, not into an element.
        If you want to send a value to a text field, use `input text` instead.

        To send a vkey, you can either use te *VKey ID* or the *Key combination*.

        Sap Virtual Keys (on Windows)
        | *VKey ID* | *Key combination*     | *VKey ID* | *Key combination*     | *VKey ID* | *Key combination*     |
        | *0*       | Enter                 | *26*      | Ctrl + F2             | *72*      | Ctrl + A              |
        | *1*       | F1                    | *27*      | Ctrl + F3             | *73*      | Ctrl + D              |
        | *2*       | F2                    | *28*      | Ctrl + F4             | *74*      | Ctrl + N              |
        | *3*       | F3                    | *29*      | Ctrl + F5             | *75*      | Ctrl + O              |
        | *4*       | F4                    | *30*      | Ctrl + F6             | *76*      | Shift + Del           |
        | *5*       | F5                    | *31*      | Ctrl + F7             | *77*      | Ctrl + Ins            |
        | *6*       | F6                    | *32*      | Ctrl + F8             | *78*      | Shift + Ins           |
        | *7*       | F7                    | *33*      | Ctrl + F9             | *79*      | Alt + Backspace       |
        | *8*       | F8                    | *34*      | Ctrl + F10            | *80*      | Ctrl + Page Up        |
        | *9*       | F9                    | *35*      | Ctrl + F11            | *81*      | Page Up               |
        | *10*      | F10                   | *36*      | Ctrl + F12            | *82*      | Page Down             |
        | *11*      | F11 or Ctrl + S       | *37*      | Ctrl + Shift + F1     | *83*      | Ctrl + Page Down      |
        | *12*      | F12 or ESC            | *38*      | Ctrl + Shift + F2     | *84*      | Ctrl + G              |
        | *14*      | Shift + F2            | *39*      | Ctrl + Shift + F3     | *85*      | Ctrl + R              |
        | *15*      | Shift + F3            | *40*      | Ctrl + Shift + F4     | *86*      | Ctrl + P              |
        | *16*      | Shift + F4            | *41*      | Ctrl + Shift + F5     | *87*      | Ctrl + B              |
        | *17*      | Shift + F5            | *42*      | Ctrl + Shift + F6     | *88*      | Ctrl + K              |
        | *18*      | Shift + F6            | *43*      | Ctrl + Shift + F7     | *89*      | Ctrl + T              |
        | *19*      | Shift + F7            | *44*      | Ctrl + Shift + F8     | *90*      | Ctrl + Y              |
        | *20*      | Shift + F8            | *45*      | Ctrl + Shift + F9     | *91*      | Ctrl + X              |
        | *21*      | Shift + F9            | *46*      | Ctrl + Shift + F10    | *92*      | Ctrl + C              |
        | *22*      | Ctrl + Shift + 0      | *47*      | Ctrl + Shift + F11    | *93*      | Ctrl + V              |
        | *23*      | Shift + F11           | *48*      | Ctrl + Shift + F12    | *94*      | Shift + F10           |
        | *24*      | Shift + F12           | *70*      | Ctrl + E              | *97*      | Ctrl + #              |
        | *25*      | Ctrl + F1             | *71*      | Ctrl + F              |           |                       |

        Examples:
        | *Keyword*     | *Attributes*      |           |
        | send_vkey     | 8                 |           |
        | send_vkey     | Ctrl + Shift + F1 |           |
        | send_vkey     | Ctrl + F7         | window=1  |
        """
        vkey_id = str(vkey_id)
        vkeys_array = ["ENTER", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
                       None, "SHIFT+F2", "SHIFT+F3", "SHIFT+F4", "SHIFT+F5", "SHIFT+F6", "SHIFT+F7", "SHIFT+F8",
                       "SHIFT+F9", "CTRL+SHIFT+0", "SHIFT+F11", "SHIFT+F12", "CTRL+F1", "CTRL+F2", "CTRL+F3", "CTRL+F4",
                       "CTRL+F5", "CTRL+F6", "CTRL+F7", "CTRL+F8", "CTRL+F9", "CTRL+F10", "CTRL+F11", "CTRL+F12",
                       "CTRL+SHIFT+F1", "CTRL+SHIFT+F2", "CTRL+SHIFT+F3", "CTRL+SHIFT+F4", "CTRL+SHIFT+F5",
                       "CTRL+SHIFT+F6", "CTRL+SHIFT+F7", "CTRL+SHIFT+F8", "CTRL+SHIFT+F9", "CTRL+SHIFT+F10",
                       "CTRL+SHIFT+F11", "CTRL+SHIFT+F12", None, None, None, None, None, None, None, None, None, None,
                       None, None, None, None, None, None, None, None, None, None, None, "CTRL+E", "CTRL+F", "CTRL+A",
                       "CTRL+D", "CTRL+N", "CTRL+O", "SHIFT+DEL", "CTRL+INS", "SHIFT+INS", "ALT+BACKSPACE",
                       "CTRL+PAGEUP", "PAGEUP",
                       "PAGEDOWN", "CTRL+PAGEDOWN", "CTRL+G", "CTRL+R", "CTRL+P", "CTRL+B", "CTRL+K", "CTRL+T",
                       "CTRL+Y",
                       "CTRL+X", "CTRL+C", "CTRL+V", "SHIFT+F10", None, None, "CTRL+#"]

        # If a key combi is given, replace vkey_id by correct id based on given combination
        if not vkey_id.isdigit():
            search_comb = vkey_id.upper()
            search_comb = search_comb.replace(" ", "")
            search_comb = search_comb.replace("CONTROL", "CTRL")
            search_comb = search_comb.replace("DELETE", "DEL")
            search_comb = search_comb.replace("INSERT", "INS")
            try:
                vkey_id = vkeys_array.index(search_comb)
            except ValueError:
                if search_comb == "CTRL+S":
                    vkey_id = 11
                elif search_comb == "ESC":
                    vkey_id = 12
                else:
                    message = "Cannot find given Vkey, provide a valid Vkey number or combination"
                    raise ValueError(message)

        try:
            self.session.findById("wnd[% s]" % window).sendVKey(vkey_id)
        except com_error:
            self.take_screenshot()
            message = "Cannot send Vkey to given window, is window wnd[% s] actually open?" % window
            raise ValueError(message)
        time.sleep(self.explicit_wait)

    def set_cell_value(self, table_id, row_num, col_id, text):
        """Sets the cell value for the specified cell of a GridView 'table_id' which is contained within a shell object.

        Use the Scripting tracker recorder to find the 'col_id' of the cell to set.
        """
        self.element_should_be_present(table_id)

        try:
            self.session.findById(table_id).modifyCell(row_num, col_id, text)
            logger.info("Typing text '%s' into cell '%s', '%s'" % (text, row_num, col_id))
            time.sleep(self.explicit_wait)
        except com_error:
            self.take_screenshot()
            message = "Cannot type text '%s' into cell '%s', '%s'" % (text, row_num, col_id)
            raise ValueError(message)

    def set_explicit_wait(self, speed):
        """Sets the delay time that is waited after each SapGui keyword.

        The value can be given as a number that is considered to be seconds or as a human-readable string like 1 second
        or 700 ms.

        This functionality is designed to be used for demonstration and debugging purposes. It is not advised to use
        this keyword to wait for an element to appear or function to finish.

         *Possible time formats:*
        | miliseconds       | milliseconds, millisecond, millis, ms |
        | seconds           | seconds, second, secs, sec, s         |
        | minutes           | minutes, minute, mins, min, m         |

         *Example:*
        | *Keyword*         | *Attributes*      |
        | Set explicit wait | 1                 |
        | Set explicit wait | 3 seconds         |
        | Set explicit wait | 500 ms            |
        """
        speed = str(speed)
        if not speed.isdigit():
            speed_elements = speed.split()
            if not speed_elements[0].isdigit():
                message = "The given speed %s doesn't begin with an numeric value, but it should" % speed
                raise ValueError(message)
            else:
                speed_elements[0] = float(speed_elements[0])
                speed_elements[1] = speed_elements[1].lower()
                if (speed_elements[1] == "seconds"
                        or speed_elements[1] == "second"
                        or speed_elements[1] == "s"
                        or speed_elements[1] == "secs"
                        or speed_elements[1] == "sec"):
                    self.explicit_wait = speed_elements[0]
                elif (speed_elements[1] == "minutes"
                      or speed_elements[1] == "minute"
                      or speed_elements[1] == "mins"
                      or speed_elements[1] == "min"
                      or speed_elements[1] == "m"):
                    self.explicit_wait = speed_elements[0] * 60
                elif (speed_elements[1] == "milliseconds"
                      or speed_elements[1] == "millisecond"
                      or speed_elements[1] == "millis"
                      or speed_elements[1] == "ms"):
                    self.explicit_wait = speed_elements[0] / 1000
                else:
                    self.take_screenshot()
                    message = "%s is a unknown time format" % speed_elements[1]
                    raise ValueError(message)
        else:
            # No timeformat given, so time is expected to be given in seconds
            self.explicit_wait = float(speed)

    def set_focus(self, element_id):

        """Sets the focus to the given element.
        """
        element_type = self.get_element_type(element_id)
        if element_type != "GuiStatusPane":
            self.session.findById(element_id).setFocus()
        time.sleep(self.explicit_wait)

    def take_screenshot(self, screenshot_name="sap-screenshot"):
        """Takes a screenshot, only if 'screenshots on error' has been enabled,
        either at import of with keyword `enable screenshots on error`.

        This keyword uses Robots' internal `Screenshot` library.
        """
        if self.take_screenshots == True:
            self.screenshot.take_screenshot(screenshot_name)

    def unselect_checkbox(self, element_id):
        """Removes selection of checkbox identified by locator.
        Does nothing if the checkbox is not selected.
        """
        element_type = self.get_element_type(element_id)
        if element_type == "GuiCheckBox":
            self.session.findById(element_id).selected = False
        else:
            self.take_screenshot()
            message = "Cannot use keyword 'unselect checkbox' for element type '%s'" % element_type
            raise ValueError(message)
        time.sleep(self.explicit_wait)
