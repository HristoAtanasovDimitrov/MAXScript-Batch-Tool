# MAXScript-Batch-Tool
 This Python script, designed for 3ds Max users, provides a batch processing tool that allows users to apply multiple MAXScript files to multiple 3ds Max scene files. It dynamically imports either PySide2 or PySide6, depending on availability, ensuring compatibility with different PySide versions. The UI offers functionality to browse, select, and manage files, along with controls to batch process and save scenes.

## Table of Contents
- [Features](#features)
- [License](#license)

## Features
- Dynamic PySide2/PySide6 Import: Automatically switches between PySide versions based on availability, ensuring compatibility across different environments.
- Batch Processing: Allows the execution of multiple MAXScript files on multiple 3ds Max files.
- Save 3ds Max Files: Provides the option to save 3ds Max files after processing.
- UI Components:
  - Browse and select MAXScript files (*.ms) and 3ds Max files (*.max).
  - Progress bar to monitor the processing progress.
  - Log output to track actions performed during the batch process.
  - Abort option to stop the batch processing at any point.
- Supports file lists: Ability to browse and load files using a list from a .txt file containing paths.

## License

[MIT](https://choosealicense.com/licenses/mit/)