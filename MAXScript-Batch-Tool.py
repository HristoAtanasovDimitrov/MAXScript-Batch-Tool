from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QApplication, QLabel, QMenu, QSplitter, QWidget, QVBoxLayout, 
    QGroupBox, QListWidget, QPushButton, QHBoxLayout, QFileDialog, 
    QListWidgetItem, QMessageBox, QCheckBox, QProgressBar, QTextEdit, 
    QAbstractItemView
)
from PySide2.QtGui import QFont, QPalette, QColor
from pymxs import runtime
import time
import os

class FileBrowser(QWidget):
    def __init__(self):
        super().__init__()
        self.save_max_file = False # Flag to indicate whether to save .max files after processing
        self.stopButtonPressed = False # Flag to indicate if the stop button was pressed
        self.initUI() # Initialize the UI components

    def initUI(self):
        # Initialize the user interface components
        self.setWindowTitle('MAXScript Batch Tool')
        self.setGeometry(100, 100, 800, 800)

        main_splitter = QSplitter(Qt.Horizontal)

        # Create left splitter with two group boxes for MAXScript and 3ds Max files
        left_splitter = QSplitter(Qt.Vertical)
        self.maxscript_group_box, self.maxscript_list_widget = self.createGroupBox(
            "MAXScript files - 0", self.browseMaxScriptFiles, self.clearMaxScriptFiles, self.showMaxScriptContextMenu
        )
        self.max_group_box, self.max_list_widget = self.createGroupBox(
            "3ds Max files - 0", self.browseMaxFiles, self.clearMaxFiles, self.showMaxContextMenu
        )
        left_splitter.addWidget(self.maxscript_group_box)
        left_splitter.addWidget(self.max_group_box)
        left_splitter.setStretchFactor(0, 1)
        left_splitter.setStretchFactor(1, 1)
        left_layout = QVBoxLayout()
        left_layout.addWidget(left_splitter)

        # Create process group box with checkbox and buttons for processing files
        process_group_box = QGroupBox("")
        process_layout = QVBoxLayout()

        # Create the layout for the checkbox and browse list file button
        top_row_layout = QHBoxLayout()
        self.save_max_checkbox = QCheckBox("Save .max files after processing")
        self.save_max_checkbox.stateChanged.connect(self.handleSaveMaxFile)
        self.save_max_checkbox.setStyleSheet("QCheckBox { font-weight: bold; }")
        self.save_max_checkbox.setToolTip("When enabled 3ds Max files will be saved\nafter the execution of each MAXScript file")
        top_row_layout.addWidget(self.save_max_checkbox)

        self.browse_list_file_button = QPushButton("Browse List File")
        self.browse_list_file_button.clicked.connect(self.browseListFile)
        self.browse_list_file_button.setStyleSheet("QPushButton { font-weight: bold; }")
        self.browse_list_file_button.setToolTip("Pick a .txt file that cantains list of paths to MAXScript or ds Max files in the folowing format\n\"path\\to\\the\\file\"\nor\npath\\to\\the\\file\nor\n\"path/to/the/file\"\nor\npath/to/the/file\nbe sure that on a line is only one path")
        top_row_layout.addWidget(self.browse_list_file_button)

        process_layout.addLayout(top_row_layout)

        # Create the layout for the process and abort buttons
        bottom_row_layout = QHBoxLayout()
        self.process_button_all = QPushButton("Process All")
        self.process_button_all.clicked.connect(self.processAll)
        self.process_button_all.setStyleSheet("QPushButton { font-weight: bold; }")
        self.process_button_all.setToolTip("Executes each MAXScript file on every 3ds Max file")
        self.process_button_all.setFixedHeight(30)
        bottom_row_layout.addWidget(self.process_button_all)

        self.process_button_stop = QPushButton("Abort")
        self.process_button_stop.setVisible(False)
        self.process_button_stop.clicked.connect(self.stopProcessing)
        self.process_button_stop.setStyleSheet("QPushButton { font-weight: bold; }")
        self.process_button_stop.setToolTip("Interrupts the execution of the MAXScript\nfiles on the 3ds Max files")
        self.setAbortButtonStyle("#FF6B6B", "white")
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
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        progress_layout.addWidget(self.progress_bar)
        self.progress_group_box.setLayout(progress_layout)
        right_layout.addWidget(self.progress_group_box)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setContextMenuPolicy(Qt.CustomContextMenu)
        self.log_output.customContextMenuRequested.connect(self.showLogContextMenu)
        right_layout.addWidget(self.log_output)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        main_splitter.addWidget(right_widget)

        main_splitter.setSizes([480, 320])

        main_layout = QHBoxLayout()
        main_layout.addWidget(main_splitter)

        self.setLayout(main_layout)

    def createGroupBox(self, title, browse_func, clear_func, context_menu_func):
        # Create a group box with a list widget, browse, and clear buttons
        group_box = QGroupBox(title)
        layout = QVBoxLayout()
        label = QLabel("File Names  /  Directory Paths")
        label.setStyleSheet("color: gray;")
        layout.addWidget(label)
        list_widget = QListWidget()
        list_widget.setDragDropMode(QListWidget.InternalMove)
        list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        list_widget.customContextMenuRequested.connect(context_menu_func)
        list_widget.setFont(QFont("Consolas", 10))
        list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(list_widget)
        self.browse_button = QPushButton("Browse Files")
        self.browse_button.setStyleSheet("QPushButton { font-weight: bold; }")
        self.browse_button.clicked.connect(browse_func)
        self.clear_button = QPushButton("Clear List")
        self.clear_button.setStyleSheet("QPushButton { font-weight: bold; }")
        self.clear_button.clicked.connect(clear_func)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.browse_button)
        button_layout.addWidget(self.clear_button)
        layout.addLayout(button_layout)
        group_box.setLayout(layout)
        return group_box, list_widget

    def updateGroupBoxTitles(self):
        # Update the titles of the group boxes with the count of items
        self.maxscript_group_box.setTitle(f"MAXScript files - {self.maxscript_list_widget.count()}")
        self.max_group_box.setTitle(f"3ds Max files - {self.max_list_widget.count()}")

    def log(self, message, color="#ffffff"):
        # Append a message to the log output with a specific color
        self.log_output.append(f'<span style="color:{color}">{message}</span>')

    def browseFiles(self, filter_text, list_widget):
        # Open a file dialog to select files and add them to the list widget
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", filter_text)
        if files:
            self.addFilesToListWidget(files, list_widget)
            self.updateGroupBoxTitles()

    def browseListFile(self):
        # Define the behavior for the "Browse List File" button
        # This method should open a file dialog to select a list file and process it accordingly
        list_file, _ = QFileDialog.getOpenFileName(self, "Select List File", "", "Text Files (*.txt)")
        if list_file:
            with open(list_file, 'r') as file:
                lines = file.read().splitlines()
                max_files = []
                ms_files = []
                for line in lines:
                    # Replace backslashes with forward slashes
                    line = line.replace('\\', '/')
                    line = line.replace('"', '')
                    if line.endswith('.max') and os.path.exists(line):
                        max_files.append(line)
                    elif line.endswith('.ms') and os.path.exists(line):
                        ms_files.append(line)
                self.addFilesToListWidget(ms_files, self.maxscript_list_widget)
                self.addFilesToListWidget(max_files, self.max_list_widget)
                self.updateGroupBoxTitles()

    def browseMaxScriptFiles(self):
        # Browse for MAXScript files
        self.browseFiles("MAXScript files (*.ms)", self.maxscript_list_widget)

    def browseMaxFiles(self):
        # Browse for 3ds Max files
        self.browseFiles("3ds Max Files (*.max)", self.max_list_widget)

    def addFilesToListWidget(self, files, list_widget):
        # Add selected files to the list widget, ensuring no duplicates
        basenames = [os.path.basename(file_path) for file_path in files]
        
        if basenames:
            longest_filename = max(basenames, key=len)
            length_of_longest = len(longest_filename)
        else:
            length_of_longest = 0
            
        existing_files = [list_widget.item(index).data(Qt.UserRole) for index in range(list_widget.count())]
        
        for file_path in files:
            if file_path not in existing_files:
                file_name = os.path.basename(file_path)
                file_name_padded = file_name.ljust(length_of_longest + 5)
                dir_path = os.path.dirname(file_path)
                list_item = QListWidgetItem(f"{file_name_padded}{dir_path}")
                list_item.setData(Qt.UserRole, file_path)
                list_widget.addItem(list_item)

    def clearListWidget(self, list_widget):
        # Clear all items from the list widget
        list_widget.clear()
        self.updateGroupBoxTitles()

    def clearMaxScriptFiles(self):
        # Clear the MAXScript files list widget
        self.clearListWidget(self.maxscript_list_widget)

    def clearMaxFiles(self):
        # Clear the 3ds Max files list widget
        self.clearListWidget(self.max_list_widget)

    def handleSaveMaxFile(self, state):
        # Update the save_max_file flag based on the checkbox state
        self.save_max_file = state == Qt.Checked

    def stopProcessing(self):
        # Set the flag indicating the stop button is pressed
        self.stopButtonPressed = True

    def setAbortButtonStyle(self, background_color, text_color):
        # Set style for Abort button
        palette = self.process_button_stop.palette()
        palette.setColor(QPalette.Button, QColor(background_color))
        palette.setColor(QPalette.ButtonText, QColor(text_color))
        self.process_button_stop.setStyleSheet("QPushButton { font-weight: bold; }")
        self.process_button_stop.setAutoFillBackground(True)
        self.process_button_stop.setPalette(palette)

    def hideElements(self):
    # Disable elements during procesing
        self.process_button_stop.setVisible(True)
        self.process_button_all.setVisible(False)


    def revealeElements(self):
        # Enable elements after procesing
        self.process_button_stop.setVisible(False)
        self.process_button_all.setVisible(True)


    def processAll(self):
        # Process all files, showing a warning if any list is empty
        self.hideElements()

        if self.maxscript_list_widget.count() == 0 or self.max_list_widget.count() == 0:
            QMessageBox.warning(self, "Warning", "MAXScript or 3ds Max file lists are empty!")
            self.revealeElements()
            return

        max_script_files = [self.maxscript_list_widget.item(index).data(Qt.UserRole) for index in range(self.maxscript_list_widget.count())]
        max_files = [self.max_list_widget.item(index).data(Qt.UserRole) for index in range(self.max_list_widget.count())]

        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.show()

        self.processFiles(max_script_files, max_files, self.save_max_file)

        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show()

        self.revealeElements()

    def processFiles(self, max_script_files, max_files, save_max_file):
        # Process each 3ds Max file with the selected MAXScript files
        start_time = time.time()
        max_files_count = len(max_files)
        for i, max_file in enumerate(max_files):
            self.log(f"<span style='color:#539dd3; font-weight:bold;'>Loading:</span> {os.path.basename(max_file)}")
            QApplication.processEvents()
            runtime.loadMaxFile(max_file, missingDllAction='#logmsg', quiet=True)
            for max_script_file in max_script_files:
                indentation = "&nbsp;" * 4
                self.log(f"{indentation}<span style='color:#dcdcad; font-weight:bold;'>Running: </span>{os.path.basename(max_script_file)}")
                QApplication.processEvents()
                runtime.fileIn(max_script_file)
            if save_max_file:
                self.log(f"<span style='color:#c687be; font-weight:bold;'>Saving:</span> {os.path.basename(max_file)}")
                QApplication.processEvents()
                runtime.saveMaxFile(max_file)
            self.updateProgress(i, max_files_count, start_time)
            QApplication.processEvents()

            if self.stopButtonPressed:
                self.stopButtonPressed = False
                aborted_percentage = (i + 1) / max_files_count * 100
                QMessageBox.information(self, "Aborted!", "Processing 3ds Max files aborted!")
                self.progress_bar.setValue(0)
                self.progress_group_box.setTitle(f"Progress:")
                self.log(f"<span style='color:#cf917a; font-weight:bold;'>---- The Processing Has Been Aborted At {aborted_percentage:.1f}% ----</span>")
                return

        QMessageBox.information(self, "Done!", "Processing 3ds Max files completed!")
        self.progress_bar.setValue(0)
        self.progress_group_box.setTitle(f"Progress:")
        self.log(f"<span style='color:#46c9b1; font-weight:bold;'>---- The Processing Has Finished Successfully ----</span>")

    def updateProgress(self, current_index, total_files, start_time):
        # Update the progress bar and progress group box title
        progress_value = (current_index + 1) / total_files * 100
        elapsed_time = time.time() - start_time
        time_per_file = elapsed_time / (current_index + 1)
        remaining_files = total_files - (current_index + 1)
        estimated_remaining_time = remaining_files * time_per_file
        h, m, s = self.secondsToHMS(estimated_remaining_time)
        self.progress_group_box.setTitle(f"Progress: {progress_value:.1f}%, ~ {int(h):02d}:{int(m):02d}:{int(s):02d}")
        self.progress_bar.setValue(progress_value)

    def secondsToHMS(self, seconds):
        # Convert seconds to hours, minutes, and seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return hours, minutes, seconds

    def showContextMenu(self, pos, list_widget):
        # Show a context menu for removing an item from the list widget
        selected_items = list_widget.selectedItems()
        if selected_items:
            menu = QMenu()
            remove_action = menu.addAction("Remove")
            remove_action.triggered.connect(lambda: self.removeSelectedItems(list_widget))
            menu.exec_(list_widget.mapToGlobal(pos))

    def showMaxScriptContextMenu(self, pos):
        # Show context menu for the MAXScript files list widget
        self.showContextMenu(pos, self.maxscript_list_widget)

    def showMaxContextMenu(self, pos):
        # Show context menu for the 3ds Max files list widget
        self.showContextMenu(pos, self.max_list_widget)

    def showLogContextMenu(self, pos):
        # Show context menu for the log output to clear the log
        menu = QMenu()
        selected_text = self.log_output.textCursor().selectedText()
        if selected_text:
            copy_action = menu.addAction("Copy")
            copy_action.triggered.connect(self.copySelectedText)
        clear_action = menu.addAction("Clear")
        clear_action.triggered.connect(self.clearLog)
        menu.exec_(self.log_output.mapToGlobal(pos))

    def clearLog(self):
        # Clear the log output
        self.log_output.clear()

    def copySelectedText(self):
        # Copy the selected text to the clipboard
        selected_text = self.log_output.textCursor().selectedText()
        clipboard = QApplication.clipboard()
        clipboard.setText(selected_text)

    def removeSelectedItems(self, list_widget):
        # Remove selected items from the list widget
        for item in list_widget.selectedItems():
            list_widget.takeItem(list_widget.row(item))
        self.updateGroupBoxTitles()

# Create and show the application window
app = QApplication.instance()
if not app:
    app = QApplication([])

window = FileBrowser()
window.show()
app.exec_()
