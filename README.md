# MAXScript Batch Tool
This is a Python application designed to automate the execution of multiple MAXScript files on a batch of 3ds Max files. This tool provides a convenient interface within 3ds Max, allowing users to optimize repetitive tasks and enhance productivity.

![alt text](https://github.com/HristoAtanasovDimitrov/MAXScript-Batch-Tool/blob/main/MAXScript-Batch-Tool.png)

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Usage](#usage)
- [Loging](#loging)
- [Modifying MAXScript Files](#modifying-maxscript-files)
- [License](#license)

## Features
- **Batch Processing:** Execute multiple MAXScript files on multiple 3ds Max files simultaneously.
- **Graphical User Interface:** User-friendly interface built with PySide2/PySide6 (depends on version of 3ds Max that is used).
- **Tooltips:** Tooltips for description on every UI element.
- **Drag & Drop Functionality:** Ability to Drag & Drop files to the lists.
- **Progress Tracking:** Progress bar updates and Log after executing each MAXScript file.
- **Abort Functionality:** Ability to abort the batch process anytime.
- **Error Handling:** Detailed logging with timestamps and error notifications.
- **Save Option:** Option to save 3ds Max files after processing.
- **Custom Execution:** Supports using list files containing paths to MAXScript and 3ds Max files.

## Requirements
- 3ds Max 2021 or later

## Usage
- Run the Python script within 3ds Max.
- **Browse Files:** Click the "Browse Files" button under the "MAXScript files" section to select MAXScript files (.ms).
- **Browse Files:** Click the "Browse Files" button under the "3ds Max files" section to select 3ds Max files (.max).
- **Load from List:** Use the "Browse List File" button to load a text file (.txt) with paths to 3ds Max files.
  - **"List.txt"** syntax example:
   ```
   "The\path\to\the\MAXSctipt file.ms"
   "The\path\to\the\3dsMax file.ms"
   ```
- **Save Files:** Check the "Save .max files after processing" option to save the 3ds Max files after processing.
- **Process All:** Click the "Process All" button to begin batch processing.
- **Progress Bar:** Track the progress of the processing through the progress bar, which updates after each MAXScript file is executed.
- **Log Output:** The log window displays detailed information about current operations, including error messages and warnings.
- **Abort:** Click the "Abort" button anytime to stop the batch process.
   - **Important:** To enable aborting during MAXScript execution, your MAXScript files must check the `g_abortRequested` [flag](#modifying-maxscript-files).

## Logging
- **Timestamps:** All log messages include timestamps for easier tracking.
- **Color Coding:**
  - $${\color{#FFFFFF}INFO:}$$ - General information.
  - $${\color{#5b8fe3}LOADING:}$$ - Loading 3ds Max files.
  - $${\color{#96df5a}RUNNING:}$$ - Executing MAXScript files.
  - $${\color{#ae7fb5}SAVING:}$$ - Saving 3ds Max files.
  - $${\color{#ffc966}WARNING:}$$ - Warnings.
  - $${\color{#ff8566}ERROR:}$$ - Errors.
- **Context Menu:** Right-click on the log window to copy or clear the log output.

## Modifying MAXScript Files
To enable the abort functionality during script execution, add the following code at the beginning of your MAXScript files:
```
global g_abortRequested
if g_abortRequested do
(
    return -- or exit, depending on the context
)
```
**Tip:** If your scripts contain long loops or operations, insert checks for `g_abortRequested` within them to allow for quick aborting when needed.

## [License](https://github.com/HristoAtanasovDimitrov/MAXScript-Batch-Tool/blob/main/LICENSE)
