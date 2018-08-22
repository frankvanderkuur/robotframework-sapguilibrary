# SapGui Library
This library is created to automate testing the SAP GUI desktop client using the Robot Framework. It uses the native Sap Gui Scripting engine to interact with the SAP GUI interface.

## Installation
ExcellentLibrary can be found on PyPI: https://pypi.org/project/robotframework-sapguilibrary.

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

## Keyword documentation
For the keyword documentation [go here](https://frankvanderkuur.github.io/SapGuiLibrary.html).
