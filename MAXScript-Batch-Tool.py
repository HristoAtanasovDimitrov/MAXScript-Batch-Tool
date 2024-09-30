# --< Description >-- # # # # # # # # # # # # # # # # # # # # # #
#                                                               #
#    This is a Python application designed to automate          #
#    the execution of multiple MAXScript files on a             #
#    batch of 3ds Max files. This tool provides a convenient    #
#    interface within 3ds Max, allowing users to optimize       #
#    repetitive tasks and enhance productivity.                 #
#                                                               #
#    MIT License                                                #
#    Copyright (c) 2024 Hristo Dimitrov                         #
#                                                               #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# Dynamic import of PySide2 or PySide6 based on availability
try:
    from PySide6.QtCore import Qt, Signal, Slot
    from PySide6.QtWidgets import (
        QApplication, QLabel, QMenu, QSplitter, QWidget, QVBoxLayout,
        QGroupBox, QPushButton, QHBoxLayout, QFileDialog,
        QListWidgetItem, QMessageBox, QCheckBox, QProgressBar, QTextEdit,
        QAbstractItemView
    )
    from PySide6.QtGui import QFont
    print("Running with PySide6")
except ImportError:
    from PySide2.QtCore import Qt, Signal, Slot
    from PySide2.QtWidgets import (
        QApplication, QLabel, QMenu, QSplitter, QWidget, QVBoxLayout,
        QGroupBox, QPushButton, QHBoxLayout, QFileDialog,
        QListWidgetItem, QMessageBox, QCheckBox, QProgressBar, QTextEdit,
        QAbstractItemView
    )
    from PySide2.QtGui import QFont
    print("Running with PySide2")

import time
import os
import re
from pathlib import Path

# Importing 'runtime' from pymxs
from pymxs import runtime

# Importing qtmax to get the main Max window
import qtmax

class FileListWidget(QListWidget):
    """
    Custom QListWidget to handle drag-and-drop of files.
    """
    fileDropped = Signal(list)  # Signal to emit when files are dropped

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(FileListWidget, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(FileListWidget, self).dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path:
                    files.append(file_path)
            if files:
                self.fileDropped.emit(files)
            event.acceptProposedAction()
        else:
            super(FileListWidget, self).dropEvent(event)

class FileBrowser(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.save_max_file = False  # Flag to save .max files after processing
        self.stopButtonPressed = False  # Flag for the "Abort" button
        self.errors_occurred = False  # Flag to track if any errors occurred
        self.initUI()  # Initialize UI components

    def initUI(self):
        """
        Initializes the user interface components.
        """
        self.setWindowTitle('MAXScript Batch Tool')
        self.setGeometry(100, 100, 800, 800)

        # Set window flags
        self.setWindowFlags(Qt.Window)

        main_splitter = QSplitter(Qt.Horizontal)

        # Create left splitter with two group boxes for MAXScript and 3ds Max files
        left_splitter = QSplitter(Qt.Vertical)
        self.maxscript_group_box, self.maxscript_list_widget = self.createGroupBox(
            "MAXScript files - 0", self.browseMaxScriptFiles, self.clearMaxScriptFiles, self.showMaxScriptContextMenu, 'maxscript'
        )
        self.max_group_box, self.max_list_widget = self.createGroupBox(
            "3ds Max files - 0", self.browseMaxFiles, self.clearMaxFiles, self.showMaxContextMenu, 'max'
        )
        left_splitter.addWidget(self.maxscript_group_box)
        left_splitter.addWidget(self.max_group_box)
        left_splitter.setStretchFactor(0, 1)
        left_splitter.setStretchFactor(1, 1)
        left_layout = QVBoxLayout()
        left_layout.addWidget(left_splitter)

        # Create process group box with checkbox and buttons
        process_group_box = QGroupBox("")
        process_layout = QVBoxLayout()

        # Create top row with checkbox and list file button
        top_row_layout = QHBoxLayout()
        self.save_max_checkbox = QCheckBox("Save .max files after processing")
        self.save_max_checkbox.stateChanged.connect(self.handleSaveMaxFile)
        self.save_max_checkbox.setStyleSheet("QCheckBox { font-weight: bold; }")
        self.save_max_checkbox.setToolTip("When enabled, 3ds Max files will be saved after the execution of each MAXScript file.")
        top_row_layout.addWidget(self.save_max_checkbox)

        self.browse_list_file_button = QPushButton("Browse List File")
        self.browse_list_file_button.clicked.connect(self.browseListFile)
        self.browse_list_file_button.setStyleSheet("QPushButton { font-weight: bold; }")
        self.browse_list_file_button.setToolTip("Select a .txt file containing paths to MAXScript or 3ds Max files.")
        top_row_layout.addWidget(self.browse_list_file_button)

        process_layout.addLayout(top_row_layout)

        # Create bottom row with "Process All" and "Abort" buttons
        bottom_row_layout = QHBoxLayout()
        self.process_button_all = QPushButton("Process All")
        self.process_button_all.clicked.connect(self.processAll)
        self.process_button_all.setStyleSheet("QPushButton { font-weight: bold; }")
        self.process_button_all.setToolTip("Executes each MAXScript file on every 3ds Max file.")
        self.process_button_all.setFixedHeight(30)
        bottom_row_layout.addWidget(self.process_button_all)

        self.process_button_stop = QPushButton("Abort")
        self.process_button_stop.setVisible(False)
        self.process_button_stop.clicked.connect(self.stopProcessing)
        self.process_button_stop.setToolTip("Interrupts the execution of the MAXScript files on the 3ds Max files.")
        self.setAbortButtonStyle("#FF6B6B", "black")  # Text color is black
        self.process_button_stop.setFixedHeight(30)
        bottom_row_layout.addWidget(self.process_button_stop)

        process_group_box.setLayout(process_layout)
        left_layout.addWidget(process_group_box)

        left_layout.addLayout(bottom_row_layout)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        main_splitter.addWidget(left_widget)

        # Create right layout for progress bar and log output
        right_layout = QVBoxLayout()
        self.progress_group_box = QGroupBox("Progress:")
        self.progress_group_box.setToolTip("Displays the progress of the processing tasks.")
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setToolTip("Shows the progress percentage.")
        progress_layout.addWidget(self.progress_bar)
        self.progress_group_box.setLayout(progress_layout)
        right_layout.addWidget(self.progress_group_box)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setContextMenuPolicy(Qt.CustomContextMenu)
        self.log_output.customContextMenuRequested.connect(self.showLogContextMenu)
        self.log_output.setToolTip("Displays log messages. Right-click for options.")
        right_layout.addWidget(self.log_output)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_splitter.addWidget(right_widget)

        main_splitter.setSizes([480, 320])

        main_layout = QHBoxLayout()
        main_layout.addWidget(main_splitter)

        self.setLayout(main_layout)

    def createGroupBox(self, title, browse_func, clear_func, context_menu_func, file_type):
        """
        Creates a group box with a list widget, browse, and clear buttons.

        Args:
            title (str): The title of the group box.
            browse_func (callable): Function to call when 'Browse Files' is clicked.
            clear_func (callable): Function to call when 'Clear List' is clicked.
            context_menu_func (callable): Function to call for the context menu.
            file_type (str): The type of files ('maxscript' or 'max').

        Returns:
            tuple: A tuple containing the group box and list widget.
        """
        group_box = QGroupBox(title)
        group_box.setToolTip(f"List of {'MAXScript' if file_type == 'maxscript' else '3ds Max'} files to process.")
        layout = QVBoxLayout()
        label = QLabel("File Names  /  Directory Paths")
        label.setStyleSheet("color: gray;")
        layout.addWidget(label)
        list_widget = FileListWidget()
        list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        list_widget.customContextMenuRequested.connect(context_menu_func)
        list_widget.setFont(QFont("Consolas", 10))
        list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        list_widget.fileDropped.connect(lambda files, lw=list_widget: self.handleFilesDropped(files, lw, file_type))
        list_widget.setToolTip(f"Drag and drop {'MAXScript' if file_type == 'maxscript' else '3ds Max'} files here.")
        layout.addWidget(list_widget)
        browse_button = QPushButton("Browse Files")
        browse_button.setStyleSheet("QPushButton { font-weight: bold; }")
        browse_button.clicked.connect(browse_func)
        browse_button.setToolTip(f"Browse and select {'MAXScript' if file_type == 'maxscript' else '3ds Max'} files.")
        clear_button = QPushButton("Clear List")
        clear_button.setStyleSheet("QPushButton { font-weight: bold; }")
        clear_button.clicked.connect(clear_func)
        clear_button.setToolTip("Clear all files from the list.")
        button_layout = QHBoxLayout()
        button_layout.addWidget(browse_button)
        button_layout.addWidget(clear_button)
        layout.addLayout(button_layout)
        group_box.setLayout(layout)
        return group_box, list_widget

    def handleFilesDropped(self, files, list_widget, file_type):
        """
        Handles files dropped onto the list widget.

        Args:
            files (list): List of file paths.
            list_widget (QListWidget): The list widget to add files to.
            file_type (str): The type of files expected ('maxscript' or 'max').
        """
        # Filter files based on file_type
        if file_type == 'maxscript':
            filtered_files = [f for f in files if f.lower().endswith('.ms')]
        elif file_type == 'max':
            filtered_files = [f for f in files if f.lower().endswith('.max')]
        else:
            filtered_files = files  # No filtering

        if filtered_files:
            self.addFilesToListWidget(filtered_files, list_widget)
            self.updateGroupBoxTitles()
            self.log(f"Added {len(filtered_files)} files via drag and drop.", level="INFO")
        else:
            self.log("No valid files found in the drop.", level="WARNING")

    def updateGroupBoxTitles(self):
        """
        Updates the titles of the group boxes with the count of items.
        """
        self.maxscript_group_box.setTitle(f"MAXScript files - {self.maxscript_list_widget.count()}")
        self.max_group_box.setTitle(f"3ds Max files - {self.max_list_widget.count()}")

    def log(self, message, level="INFO"):
        """
        Appends a message to the log output with a specific color based on the logging level.
        Includes a timestamp for each message.

        Args:
            message (str): The message to log.
            level (str): The logging level ('INFO', 'LOADING', 'RUNNING', 'SAVING', 'WARNING', 'ERROR').
        """
        color_map = {
            "INFO": "#FFFFFF",     # White
            "LOADING": "#539dd3",  # Blue
            "RUNNING": "#00FF00",  # Green
            "SAVING": "#c687be",   # Purple
            "WARNING": "#FFA500",  # Orange
            "ERROR": "#f74040"     # Red
        }
        color = color_map.get(level, "#FFFFFF")
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.log_output.append(f'<span style="color:{color}">[{timestamp}] {message}</span>')
        # Scroll to the end
        self.log_output.verticalScrollBar().setValue(self.log_output.verticalScrollBar().maximum())
        QApplication.processEvents()

    def browseFiles(self, file_type, filter_text, list_widget):
        """
        Opens a file dialog to select files and adds them to the list widget.

        Args:
            file_type (str): The type of files to display in the dialog title.
            filter_text (str): The file filter for the dialog.
            list_widget (QListWidget): The list widget to add the files to.
        """
        files, _ = QFileDialog.getOpenFileNames(self, f"Select {file_type}", "", filter_text)
        if files:
            self.addFilesToListWidget(files, list_widget)
            self.updateGroupBoxTitles()
            self.log(f"Added {len(files)} {file_type} to the list.", level="INFO")

    def browseListFile(self):
        """
        Opens a file dialog to select a list file and processes it to extract file paths.
        """
        list_file, _ = QFileDialog.getOpenFileName(self, "Select List File", "", "Text Files (*.txt)")
        if list_file:
            with open(list_file, 'r') as file:
                content = file.read()
                # Use regex to extract paths, handling quotes and different separators
                paths = re.findall(r'"([^"]+)"|\S+', content.replace('\\', '/'))
                max_files = [path for path in paths if path.endswith('.max') and Path(path).exists()]
                ms_files = [path for path in paths if path.endswith('.ms') and Path(path).exists()]
                self.addFilesToListWidget(ms_files, self.maxscript_list_widget)
                self.addFilesToListWidget(max_files, self.max_list_widget)
                self.updateGroupBoxTitles()
                total_files = len(ms_files) + len(max_files)
                self.log(f"Loaded {total_files} files from list.", level="INFO")

    def browseMaxScriptFiles(self):
        """
        Browses for MAXScript files and adds them to the MAXScript list widget.
        """
        self.browseFiles("MAXScript Files", "MAXScript files (*.ms)", self.maxscript_list_widget)

    def browseMaxFiles(self):
        """
        Browses for 3ds Max files and adds them to the Max files list widget.
        """
        self.browseFiles("3ds Max Files", "3ds Max Files (*.max)", self.max_list_widget)

    def addFilesToListWidget(self, files, list_widget):
        """
        Adds selected files to the list widget, ensuring no duplicates.
        Updates the padding for all items to align filenames and directory paths.

        Args:
            files (list): List of file paths to add.
            list_widget (QListWidget): The list widget to add files to.
        """
        # Normalize existing file paths in the list widget
        existing_files = []
        for index in range(list_widget.count()):
            item_file_path = list_widget.item(index).data(Qt.UserRole)
            normalized_path = os.path.normcase(os.path.abspath(item_file_path))
            existing_files.append(normalized_path)

        # Prepare to determine the padding for filenames
        # Include both existing and new files for padding calculation
        all_file_paths = existing_files + [os.path.normcase(os.path.abspath(f)) for f in files]
        basenames = [os.path.basename(file_path) for file_path in all_file_paths]
        if basenames:
            longest_filename = max(basenames, key=len)
            length_of_longest = len(longest_filename)
        else:
            length_of_longest = 0

        # Update existing items in the list widget with new padding
        for index in range(list_widget.count()):
            item = list_widget.item(index)
            file_path = item.data(Qt.UserRole)
            file_name = os.path.basename(file_path)
            file_name_padded = file_name.ljust(length_of_longest + 5)
            dir_path = os.path.dirname(file_path)
            item.setText(f"{file_name_padded}{dir_path}")

        # Add new files to the list widget if they are not already present
        for file_path in files:
            normalized_new_file = os.path.normcase(os.path.abspath(file_path))
            if normalized_new_file not in existing_files:
                file_name = os.path.basename(file_path)
                file_name_padded = file_name.ljust(length_of_longest + 5)
                dir_path = os.path.dirname(file_path)
                list_item = QListWidgetItem(f"{file_name_padded}{dir_path}")
                list_item.setData(Qt.UserRole, file_path)
                list_widget.addItem(list_item)
            else:
                self.log(f"File already in the list: {file_path}", level="INFO")

    def clearListWidget(self, list_widget):
        """
        Clears all items from the specified list widget.

        Args:
            list_widget (QListWidget): The list widget to clear.
        """
        list_widget.clear()
        self.updateGroupBoxTitles()
        self.log("Cleared the list.", level="INFO")

    def clearMaxScriptFiles(self):
        """
        Clears the MAXScript files list widget.
        """
        self.clearListWidget(self.maxscript_list_widget)

    def clearMaxFiles(self):
        """
        Clears the 3ds Max files list widget.
        """
        self.clearListWidget(self.max_list_widget)

    def handleSaveMaxFile(self, state):
        """
        Updates the save_max_file flag based on the checkbox state.

        Args:
            state (Qt.CheckState): The state of the checkbox.
        """
        self.save_max_file = state == Qt.Checked
        status = "enabled" if self.save_max_file else "disabled"
        self.log(f"Save .max files after processing is {status}.", level="INFO")

    def stopProcessing(self):
        """
        Signals to stop processing.
        """
        self.stopButtonPressed = True
        runtime.g_abortRequested = True  # Set the abort flag in runtime
        self.log("Abort requested. The process will stop after the current operation.", level="WARNING")

    def setAbortButtonStyle(self, background_color, text_color):
        """
        Sets the style for the Abort button.

        Args:
            background_color (str): The background color in hex format.
            text_color (str): The text color in hex format.
        """
        self.process_button_stop.setStyleSheet(f"""
            QPushButton {{
                font-weight: bold;
                background-color: {background_color};
                color: {text_color};
            }}
        """)

    def hideElements(self):
        """
        Disables input controls during processing.
        """
        self.process_button_stop.setVisible(True)
        self.process_button_all.setVisible(False)
        self.maxscript_list_widget.setEnabled(False)
        self.max_list_widget.setEnabled(False)
        self.save_max_checkbox.setEnabled(False)
        self.browse_list_file_button.setEnabled(False)

        # Disable browse and clear buttons
        for group_box in [self.maxscript_group_box, self.max_group_box]:
            for button in group_box.findChildren(QPushButton):
                button.setEnabled(False)

    def revealeElements(self):
        """
        Enables input controls after processing.
        """
        self.process_button_stop.setVisible(False)
        self.process_button_all.setVisible(True)
        self.maxscript_list_widget.setEnabled(True)
        self.max_list_widget.setEnabled(True)
        self.save_max_checkbox.setEnabled(True)
        self.browse_list_file_button.setEnabled(True)

        # Enable browse and clear buttons
        for group_box in [self.maxscript_group_box, self.max_group_box]:
            for button in group_box.findChildren(QPushButton):
                button.setEnabled(True)

    def processAll(self):
        """
        Initiates the processing of all selected MAXScript and 3ds Max files.
        Validates the input lists and starts the processing.
        """
        self.hideElements()
        self.stopButtonPressed = False  # Reset the stop button flag
        runtime.g_abortRequested = False  # Reset the abort flag in runtime
        self.errors_occurred = False  # Reset the error flag

        if self.maxscript_list_widget.count() == 0 or self.max_list_widget.count() == 0:
            QMessageBox.warning(self, "Warning", "MAXScript or 3ds Max file lists are empty!")
            self.revealeElements()
            return

        max_script_files = [self.maxscript_list_widget.item(index).data(Qt.UserRole) for index in range(self.maxscript_list_widget.count())]
        max_files = [self.max_list_widget.item(index).data(Qt.UserRole) for index in range(self.max_list_widget.count())]

        # Start processing without pre-validating file paths
        self.log(f"Starting processing of {len(max_files)} 3ds Max files with {len(max_script_files)} MAXScript files.", level="INFO")

        # Start processing
        self.processFiles(max_script_files, max_files, self.save_max_file)
        self.revealeElements()
        self.progress_bar.setValue(0)  # Reset progress bar after processing

    def processFiles(self, max_script_files, max_files, save_max_file):
        """
        Processes each 3ds Max file with the selected MAXScript files.
        """
        start_time = time.time()
        total_steps = len(max_files) * len(max_script_files)
        if total_steps == 0:
            self.log("No files to process.", level="WARNING")
            self.progress_bar.setValue(0)
            self.progress_group_box.setTitle(f"Progress:")
            return

        current_step = 0

        for i, max_file in enumerate(max_files):
            if self.stopButtonPressed:
                self.stopButtonPressed = False
                runtime.g_abortRequested = False  # Reset the abort flag in runtime
                aborted_percentage = (current_step) / total_steps * 100
                QMessageBox.information(self, "Aborted!", "Processing 3ds Max files aborted!")
                self.progress_bar.setValue(0)
                self.progress_group_box.setTitle(f"Progress:")
                self.log(f"Processing aborted at {aborted_percentage:.1f}%.", level="WARNING")
                return

            if not os.path.exists(max_file):
                self.log(f"3ds Max file not found: {max_file}", level="ERROR")
                self.errors_occurred = True
                continue  # Skip to next file

            try:
                self.log(f"Loading 3ds Max file: {max_file}", level="LOADING")
                QApplication.processEvents()
                runtime.loadMaxFile(max_file, missingDllAction='quiet', useFileUnits=True)
            except Exception as e:
                self.log(f"Error loading '{max_file}': {e}", level="ERROR")
                self.errors_occurred = True  # Mark that an error occurred
                continue  # Skip to next file

            for max_script_file in max_script_files:
                if self.stopButtonPressed:
                    break  # Exit the scripts loop

                if not os.path.exists(max_script_file):
                    self.log(f"MAXScript file not found: {max_script_file}", level="ERROR")
                    self.errors_occurred = True
                    continue  # Skip to next script

                try:
                    self.log(f"Running MAXScript file: {max_script_file}", level="RUNNING")
                    QApplication.processEvents()
                    runtime.fileIn(max_script_file)
                    if runtime.g_abortRequested:
                        self.log(f"Execution aborted during script: {max_script_file}", level="WARNING")
                        break  # Exit the scripts loop
                except Exception as e:
                    self.log(f"Error executing '{max_script_file}': {e}", level="ERROR")
                    self.errors_occurred = True  # Mark that an error occurred
                    continue

                # Update progress after each MAXScript file
                current_step += 1
                self.updateProgress(current_step, total_steps, start_time)
                QApplication.processEvents()

                if self.stopButtonPressed:
                    runtime.g_abortRequested = False  # Reset the abort flag in runtime
                    aborted_percentage = (current_step) / total_steps * 100
                    QMessageBox.information(self, "Aborted!", "Processing 3ds Max files aborted!")
                    self.progress_bar.setValue(0)
                    self.progress_group_box.setTitle(f"Progress:")
                    self.log(f"Processing aborted at {aborted_percentage:.1f}%.", level="WARNING")
                    return

            if save_max_file and not self.stopButtonPressed:
                try:
                    self.log(f"Saving 3ds Max file: {max_file}", level="SAVING")
                    QApplication.processEvents()
                    runtime.saveMaxFile(max_file)
                except Exception as e:
                    self.log(f"Error saving '{max_file}': {e}", level="ERROR")
                    self.errors_occurred = True  # Mark that an error occurred

        if self.errors_occurred:
            self.log("Processing completed with errors. Check the log for details.", level="WARNING")
        else:
            self.log("Processing finished successfully.", level="INFO")

        QMessageBox.information(self, "Done!", "Processing 3ds Max files completed!")
        self.progress_bar.setValue(0)
        self.progress_group_box.setTitle(f"Progress:")

    def updateProgress(self, current_step, total_steps, start_time):
        """
        Updates the progress bar and progress group box title.

        Args:
            current_step (int): The current step in the process.
            total_steps (int): The total number of steps in the process.
            start_time (float): The time when processing started.
        """
        progress_value = (current_step) / total_steps * 100
        elapsed_time = time.time() - start_time
        time_per_step = elapsed_time / current_step if current_step > 0 else 0
        remaining_steps = total_steps - current_step
        estimated_remaining_time = remaining_steps * time_per_step
        h, m, s = self.secondsToHMS(estimated_remaining_time)
        self.progress_group_box.setTitle(f"Progress: {progress_value:.1f}%, ~ {int(h):02d}:{int(m):02d}:{int(s):02d} remaining")
        self.progress_bar.setValue(progress_value)
        QApplication.processEvents()

    def secondsToHMS(self, seconds):
        """
        Converts seconds to hours, minutes, and seconds.

        Args:
            seconds (float): The number of seconds.

        Returns:
            tuple: A tuple containing hours, minutes, and seconds.
        """
        hours = int(seconds) // 3600
        minutes = (int(seconds) % 3600) // 60
        seconds = int(seconds) % 60
        return hours, minutes, seconds

    def showContextMenu(self, pos, list_widget):
        """
        Shows a context menu for removing items from the list widget.

        Args:
            pos (QPoint): The position where the context menu should appear.
            list_widget (QListWidget): The list widget to interact with.
        """
        selected_items = list_widget.selectedItems()
        if selected_items:
            menu = QMenu()
            remove_action = menu.addAction("Remove")
            remove_action.triggered.connect(lambda: self.removeSelectedItems(list_widget))
            menu.exec_(list_widget.mapToGlobal(pos))

    def showMaxScriptContextMenu(self, pos):
        """
        Shows context menu for the MAXScript files list widget.

        Args:
            pos (QPoint): The position where the context menu should appear.
        """
        self.showContextMenu(pos, self.maxscript_list_widget)

    def showMaxContextMenu(self, pos):
        """
        Shows context menu for the 3ds Max files list widget.

        Args:
            pos (QPoint): The position where the context menu should appear.
        """
        self.showContextMenu(pos, self.max_list_widget)

    def showLogContextMenu(self, pos):
        """
        Shows context menu for the log output to clear the log or copy text.

        Args:
            pos (QPoint): The position where the context menu should appear.
        """
        menu = QMenu()
        selected_text = self.log_output.textCursor().selectedText()
        if selected_text:
            copy_action = menu.addAction("Copy")
            copy_action.triggered.connect(self.copySelectedText)
        clear_action = menu.addAction("Clear")
        clear_action.triggered.connect(self.clearLog)
        menu.exec_(self.log_output.mapToGlobal(pos))

    def clearLog(self):
        # Clears the log output.
        self.log_output.clear()
        self.log("Log cleared.", level="INFO")

    def copySelectedText(self):
        # Copies the selected text from the log output to the clipboard.
        selected_text = self.log_output.textCursor().selectedText()
        clipboard = QApplication.clipboard()
        clipboard.setText(selected_text)
        self.log("Selected text copied to clipboard.", level="INFO")

    def removeSelectedItems(self, list_widget):
        """
        Removes selected items from the specified list widget.

        Args:
            list_widget (QListWidget): The list widget to remove items from.
        """
        count = len(list_widget.selectedItems())
        for item in list_widget.selectedItems():
            list_widget.takeItem(list_widget.row(item))
        self.updateGroupBoxTitles()
        self.log(f"Removed {count} items from the list.", level="INFO")

# Create and show the application window
app = QApplication.instance()
if not app:
    app = QApplication([])

# Get the main 3ds Max window
max_main_window = qtmax.GetQMaxMainWindow()

# Create the FileBrowser window with max_main_window as parent
window = FileBrowser(parent=max_main_window)
window.show()
app.exec_()