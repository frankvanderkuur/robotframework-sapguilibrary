# SapGui Library
This library is created to automate testing the SAP GUI desktop client using the Robot Framework. It uses the native Sap Gui Scripting engine to interact with the SAP GUI interface.

## Installation
SapGuiLibrary can be found on PyPI: https://pypi.org/project/robotframework-sapguilibrary.

To install, simply use pip:

```dos
pip install robotframework-sapguilibrary
```

Dependencies are automatically installed.

## Importing in Robot Framework
As soon as installation has succeeded, you can import the library in Robot Framework:

```robot
*** Settings ***
Library  SapGuiLibrary
```

## Usage
First of all be sure you've enabled the user_scripting option on the server. I haven't done this myself so I can't give you a proven example on how to do this. I've checked it on Google and it looks like you can change this using the RZ11 transaction.

When de Scripting Engine is enabled, you have to start de Sap Logon Pad. Unfortunately the scripting engine doesn't enable you to start this so you have to use something like the Process or the AutoIT library. When the Sap Logon Pad is available, you use the 'Connect to session' keyword to attach to the session.

## Finding locators
Finding the locators for the elements requires you to use an extra tool to identify these locators. To best tool for that is the SAP Scripting Tracker. More information about this tool can be found at [this blogpost on the SAP website](https://blogs.sap.com/2014/11/20/scripting-tracker-development-tool-for-sap-gui-scripting/)

If you just want to download the tool follow [this link](https://tracker.stschnell.de/tracker.zip). To tool Tracker.exe is the one you want to use.

Tip: Finding an element within a Shell type component requires an extra step, because the Tracker will only show you the Shell identifier. You can find the identifier by using de recorder function and than perform the actions you want to automate. After saving the recording you can find the identifiers within the recorded script.

## Keyword documentation
For the keyword documentation [go here](https://frankvanderkuur.github.io/SapGuiLibrary.html).
