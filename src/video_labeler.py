# For handling different OS
import sys
import os
import locale

# For different file-formats
import json
import csv

# For plotting Hotkeys
import pandas as pd
import matplotlib.pyplot as plt

# App Widgets
from PyQt5.QtWidgets import QTableWidget, QMainWindow, QLabel, QWidget, QGridLayout, QScrollArea, QSlider, QStyle, \
    QShortcut, QTableWidgetItem, QApplication, QSplitter, QVBoxLayout, QAbstractItemView, QMessageBox
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence, QCloseEvent

# MPV Player and Style of the App
import mpv
from qt_material import apply_stylesheet

# For Documentation
from typing import Iterator, List


class Labeler(QMainWindow):
    """
    This is the "main" class for the application. It brings everything together. Also loading
    classes:

    - MouseEventHandler() as mouse_event
    - Layout() as layout
    - AppFunctions() as app_functions
    - Logger() as logger
    - ActivityHandler() as activity_handler

    Everything is set up here. Also loading the .json files and processing and binding them.a
    """

    def __init__(self, application, parent=None):
        super().__init__(parent)
        self.initialize_folders_and_settings()
        self.mouse_event = MouseEventHandler(self)  # Get access to MouseEventHandler
        self.layout = Layout(self)  # Get access to Layout
        self.app_functions = AppFunctions(self)  # Get access to Settings methods
        self.logger = Logger(self)  # Get access to Logger
        self.activity_handler = ActivityHandler(self)  # Get access to ActivityHandler

        self.installEventFilter(self)
        self.setWindowTitle("Video Labeler")
        self.app = application

        # Cached values
        self.time_window_activity = []
        self.data_table_changed = False  # Needed for saving data, if some changes happened

        self.playtime = self.layout.playtime  #
        self.video_name_playing = self.layout.now_playing  # Showing name of Video
        self.app_window = self.layout.app_window_layout  # Main Window

        self.video = self.layout.video
        self.player = self.layout.player

        # Define Playlist (left side list, to play videos from)
        # If click on a row, it will play the video
        self.video_table = self.layout.video_table
        # noinspection PyUnresolvedReferences
        self.video_table.itemClicked.connect(self.mouse_event.video_table_click)
        self.app_functions.update_video_table()
        self.video_table_scroll = self.layout.video_table_scroll

        # Define DataTable, for entered observations
        self.data_table = self.layout.data_table
        # Scroll Area for data Table
        self.data_table_scroll = self.layout.data_table_scroll
        # noinspection PyUnresolvedReferences
        self.data_table.itemClicked.connect(self.mouse_event.data_table_click)

        # Define Time Slider
        self.time_slider = self.layout.time_slider
        self.time_slider.mousePressEvent = self.mouse_event.slider_move
        self.time_slider.mouseMoveEvent = self.mouse_event.slider_move

        # Define Logger
        self.logger_widget = self.layout.logger_widget
        self.logger_scroller = self.layout.logger_scroll
        self.logger_grid = self.layout.logger_grid

        # Vertical (v) und Horizontal (h) splitter
        self.splitter_v = self.layout.splitter_v
        self.splitter_h = self.layout.splitter_h
        # noinspection PyUnresolvedReferences

        # Resizing tables, if clicking on the splitter
        self.splitter_h.splitterMoved.connect(self.mouse_event.splitter_click)
        QTimer.singleShot(0, self.mouse_event.splitter_click)

        # Loading shortcuts, commands for the mpv player and the settings
        self.closeEvent = self.mouse_event.close_app
        self.label_shortcuts()
        self.commands_mpv()
        self.settings()

    def initialize_folders_and_settings(self):
        """
        Creating and initializing all the needed files. Also auto-creating the settings.json,
        commands_mpv.json and label_shortcuts.json files as an example.
        """
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists("videos"):
            os.makedirs("videos")
        if not os.path.exists('settings.json'):
            with open('settings.json', 'w') as f:
                settings = {
                    "X": "delete_selected_rows()",
                    "CTRL+S": "save_csv()",
                    "S": "sort_data_table()",
                    "U": "update_video_table()",
                    "P": "plot_hotkeys()",
                    "dark_amber.xml": "style",
                    "1600:800": "width_height",
                    "12": "log_max"
                }
                json.dump(settings, f, sort_keys=True, indent=4,
                          ensure_ascii=False)
        if not os.path.exists('commands_mpv.json'):
            with open('commands_mpv.json', 'w') as f:
                commands_mpv = {
                    "SPACE": ["cycle", "pause"],
                    "right": "frame-step",
                    "left": "frame-back-step",
                    "up": ["multiply", "speed", "1.1"],
                    "down": ["multiply", "speed", "1/1.1"],
                    ".": "frame-step",
                    ",": "frame-back-step",
                    "+": ["add", "video-zoom", "0.1"],
                    "-": ["add", "video-zoom", "-0.1"],
                    "Shift+up": ["add", "video-pan-y", "0.1"],
                    "Shift+right": ["add", "video-pan-x", "-0.1"],
                    "Shift+left": ["add", "video-pan-x", "0.1"],
                    "Shift+down": ["add", "video-pan-y", "-0.1"],
                    "BACKSPACE": ["set", "speed", "1.0"]
                }
                json.dump(commands_mpv, f, sort_keys=True, indent=4,
                          ensure_ascii=False)
        if not os.path.exists('label_shortcuts.json'):
            with open('label_shortcuts.json', 'w') as f:
                label_shortcuts = {
                    "time_window": {
                        "Ctrl+R": "Running",
                        "Ctrl+W": "Walking"
                    },
                    "point_activity": {
                        "L": "StepLeft",
                        "R": "StepRight"
                    }
                }
                json.dump(label_shortcuts, f, sort_keys=True, indent=4,
                          ensure_ascii=False)

    def commands_mpv(self):
        """
        All the commands defined in commands_mpv.json will be loaded and set for the mpv-player.

        For more information, see:
        https://github.com/mpv-player/mpv/blob/master/etc/input.conf
        https://mpv.io/manual/stable/#command-interface
        """
        with open('commands_mpv.json', 'r') as file:
            shortcuts = json.load(file)
        for shortcut, command in shortcuts.items():
            shortcut = QShortcut(QKeySequence(shortcut), self)
            # noinspection PyUnresolvedReferences
            shortcut.activated.connect(lambda commands=command: self._handle_commands_mpv(commands))

    def _handle_commands_mpv(self, commands: str or list[str]):
        """
        Handles the commands defined in commands_mpv and set this to the mpv-player
        """
        if isinstance(commands, list):
            self.player.command(commands[0], *commands[1:])
        else:
            self.player.command(commands)

    def settings(self):
        """
        Will load the settings.json file and process the settings, that are set up.
        Like the size of the window, or some other hotkeys etc.
        """
        with open('settings.json', 'r') as file:
            settings = json.load(file)
        for key, value in settings.items():
            if value[-2:] == "()":
                shortcut = QShortcut(QKeySequence(key), self)
                # noinspection PyUnresolvedReferences
                shortcut.activated.connect(getattr(self.app_functions, value[:-2]))
            elif value == "style":
                # https://pypi.org/project/qt-material/
                apply_stylesheet(self.app, theme=key, extra={"density_scale": "0"})
            elif value == "width_height":
                w_h = key.split(":")
                self.resize(int(w_h[0]), int(w_h[1]))
            elif value == "log_max":
                self.logger.log_max = int(key)
            else:
                pass

    def label_shortcuts(self):
        """
        Will load the label_shortcuts.json file and process the shortcuts.
        """
        with open('label_shortcuts.json', 'r') as file:
            shortcuts = json.load(file)

        for act_type in shortcuts:
            for shortcut_key, label in shortcuts[act_type].items():
                shortcut = QShortcut(QKeySequence(shortcut_key), self)
                # noinspection PyUnresolvedReferences
                shortcut.activated.connect(
                    lambda labels=label, act_types=act_type, shortcut_keys=shortcut_key:
                    self._handle_label_shortcuts(labels, act_types, shortcut_keys))

    def _handle_label_shortcuts(self, labels: str, act_types: str, shortcut_keys: str):
        """
        Is handling the shortcuts for the labels. In this case there are only two options,
        time_window and point_activity to handle. Where The time_window needs to be pressed
        twice to write two values within the table. The point_activity needs only once to be pressed
        to track StartTime and EndTime.
        """
        video_name = self.video_name_playing.text()
        play_time = self.playtime.text()

        # "StartTime", "EndTime", "ActType", "Label", "Video"
        data_to_insert = [play_time, play_time, act_types, labels, video_name]

        if act_types == "time_window":
            self.activity_handler.populate_data_table_time_window(data_to_insert, shortcut_keys)
        elif act_types == "point_activity":
            self.activity_handler.populate_data_table_point_activity(data_to_insert, shortcut_keys)

    def _slider_time_change(self, value: float):
        """
        Change the position of the slider, defined by current video time.
        """
        if self.player.duration != 0 and not self.time_slider.isSliderDown() and self.player.duration is not None:
            slider_value = int((value / self.player.duration) * 1000)
            self.time_slider.setValue(slider_value)

    def observe_time_position(self):
        """
        Observing the time position and writing it into the playtime widget.
        """

        @self.player.property_observer('time-pos')
        def time_observer(_name, value: float):
            if value is not None:
                self.playtime.setText(f"{value:.3f}")
                self._slider_time_change(value)
            else:
                self.playtime.setText("NaN")


class ActivityHandler:
    def __init__(self, labeler_instance: Labeler):
        self.labeler = labeler_instance

    def _get_saved_time_window(self, shortcut_keys: str) -> tuple or None:
        """
        Similar to _get_logging_idx(), but for data-table.
        """
        for idx, activity in enumerate(self.labeler.time_window_activity):
            if activity[2] == shortcut_keys:
                values = (activity, idx)
                return values
        return None

    def _handle_first_time_window(self, data: list, shortcut_keys: str):
        """
        Handling the first shortcut-pressed key for time_window activities.
        """
        current_row_count = self.labeler.data_table.rowCount()
        self.labeler.time_window_activity.append((current_row_count, 1, shortcut_keys, data[0]))

        self.labeler.data_table.setRowCount(current_row_count + 1)
        for j, item in enumerate(data):
            self.labeler.data_table.setItem(current_row_count, j, QTableWidgetItem(item))

        self.labeler.logger.logging_activity.append([current_row_count, shortcut_keys, "#333333", "darkorange", data])
        self.labeler.logger.write_logger()

    def _handle_second_time_window(self, data: list, shortcut_keys: str, activity: list, act_idx: int):
        """
        Handling the second time shortcut-pressed key for time_window activities. It is important to know,
        that "WAIT..." means, it is waiting for the second time to be pressed. So a time_window should be always
        closed and got StartTime and EndTime.
        """
        self.labeler.data_table.setItem(activity[0], activity[1],
                                        QTableWidgetItem(data[1]))
        self.labeler.time_window_activity.pop(act_idx)

        logg_idx = self.labeler.logger.get_logging_idx(activity[0], shortcut_keys)

        if logg_idx is not None:
            self.labeler.logger.logging_activity[logg_idx] = [activity[0], shortcut_keys, "#333333", "#333333", data]
        else:
            self.labeler.logger.logging_activity.append([activity[0], shortcut_keys, "#333333", "#333333", data])
        self.labeler.logger.write_logger()

    def populate_data_table_time_window(self, data: list, shortcut_keys: str):
        """
        As described in _handle_shortcuts() above, this function will handle time_window option. (writing twice)
        It checks if it is first time pressed or second time pressed for the time_window activity.
        """
        self.labeler.data_table_changed = True
        act = self._get_saved_time_window(shortcut_keys)
        if act is None:
            data[1] = "WAIT..."
            self._handle_first_time_window(data, shortcut_keys)
        else:
            activity = act[0]
            act_idx = act[1]
            data[0] = act[0][-1]
            self._handle_second_time_window(data, shortcut_keys, activity, act_idx)

    def populate_data_table_point_activity(self, data: list, shortcut_keys: str):
        """
        Handling point activity (writing once)
        """
        self.labeler.data_table_changed = True
        current_row_count = self.labeler.data_table.rowCount()
        self.labeler.data_table.setRowCount(current_row_count + 1)
        for j, item in enumerate(data):
            self.labeler.data_table.setItem(current_row_count, j, QTableWidgetItem(item))
        self.labeler.logger.logging_activity.append(
            [current_row_count, shortcut_keys, "#222222", "#222222", list(data)])
        self.labeler.logger.write_logger()


class Layout:
    """
    This class is for creating the app-layout of the widgets. No functionality, only widgets. If it's needed to
    insert more widgets, should be done here. And can be accessed within Labeler class.
    """

    def __init__(self, labeler_instance: Labeler):
        self.labeler = labeler_instance
        self.playtime = QLabel("0")
        self.now_playing = QLabel("No Video Playing")
        self.app_window, self.app_window_layout = self.create_app_window()
        self.video, self.player = self.create_mpv_player()
        self.video_table, self.video_table_scroll = self.create_video_table()
        self.data_table, self.data_table_scroll = self.create_data_table()
        self.time_slider = self.create_time_slider()
        self.logger_widget, self.logger_scroll, self.logger_grid = self.create_logger()
        self.video_widget, self.video_layout = self.create_second_column_video_layout()
        self.splitter_h, self.splitter_v = self.create_splitter()
        self.create_style()

    def create_app_window(self) -> tuple[QWidget, QGridLayout]:
        """
        Will open the main-window and center it.
        """
        app_window = QWidget(self.labeler)
        self.labeler.setCentralWidget(app_window)
        app_window_layout = QGridLayout(app_window)
        return app_window, app_window_layout

    def create_mpv_player(self) -> tuple[QWidget, mpv.MPV]:
        """
        Starting MPV-Player and putting in withing a Widget.
        """
        video = QWidget(self.labeler)
        player = mpv.MPV(
            wid=str(int(video.winId())),
            vo="x11",
            input_default_bindings=True,
            input_vo_keyboard=True,
            osc=True,
            # script_opts="osd-level=3"
        )
        player["vo"] = "gpu"
        return video, player

    def create_video_table(self) -> tuple[QTableWidget, QScrollArea]:
        """
        Creating a table for all videos within the folder "videos".
        """
        video_table = QTableWidget(self.labeler)
        video_table.setRowCount(0)
        video_table.setColumnCount(1)
        video_table.setHorizontalHeaderLabels(["Video"])
        video_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        video_table_scroll = QScrollArea(self.labeler)
        video_table_scroll.setWidgetResizable(True)
        video_table_scroll.setWidget(video_table)

        return video_table, video_table_scroll

    def create_data_table(self) -> tuple[QTableWidget, QScrollArea]:
        """
        Here will be all the values, that are labeled as an overview
        """
        data_table = QTableWidget(self.labeler)
        data_table.setRowCount(0)
        data_table.setColumnCount(5)
        data_table.setHorizontalHeaderLabels(
            ["STime", "ETime", "Type", "Label", "Vid"])
        data_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Create a scroll are for the table and set table widget as its widget
        data_table_scroll = QScrollArea()
        data_table_scroll.setWidgetResizable(True)
        data_table_scroll.setWidget(data_table)
        return data_table, data_table_scroll

    def create_second_column_video_layout(self) -> tuple[QWidget, QVBoxLayout]:
        """
        Combining MPV-Player, Playing-Time, Video-Name and Time-Slider
        within one column.
        """
        video_widget = QWidget(self.labeler)
        video_layout = QVBoxLayout(video_widget)
        video_layout.addWidget(self.video, stretch=10)
        video_layout.addWidget(self.playtime)
        video_layout.addWidget(self.now_playing)
        video_layout.addWidget(self.time_slider)
        return video_widget, video_layout

    def create_logger(self) -> tuple[QWidget, QScrollArea, QGridLayout]:
        """
        The logging window, to get some feedback, what is going on.
        """
        # Will show the labels for every frame (ongoing, not done)
        logger_widget = QWidget(self.labeler)
        logger_scroller = QScrollArea()
        logger_scroller.setWidgetResizable(True)
        logger_grid = QGridLayout(logger_widget)
        logger_scroller.setWidget(logger_widget)
        return logger_widget, logger_scroller, logger_grid

    def create_splitter(self) -> tuple[QSplitter, QSplitter]:
        """
        To make it more user-friendly, there are some splitters.
        So the user can drag the windows to the size he wants to.
        """
        # Add scroll_video_table to the first column
        splitter_v = QSplitter(Qt.Vertical)
        splitter_v.addWidget(self.video_table_scroll)
        splitter_v.addWidget(self.logger_scroll)

        splitter_h = QSplitter(Qt.Horizontal)
        splitter_h.addWidget(splitter_v)
        splitter_h.addWidget(self.video_widget)
        splitter_h.addWidget(self.data_table_scroll)

        width = self.labeler.width()
        height = self.labeler.height()
        splitter_h.setSizes(
            [
                int(width * 0.2),
                (int(width * 0.5)),
                (int(width * 0.3))
            ]
        )

        splitter_v.setSizes(
            [
                int(height * 0.3),
                int(height * 0.7)
            ]

        )

        self.labeler.setCentralWidget(splitter_h)

        return splitter_h, splitter_v

    def create_time_slider(self) -> QSlider:
        """
        Is like a slider within any video-player.
        """
        time_slider = QSlider(Qt.Horizontal)
        time_slider.setMinimum(0)
        time_slider.setMaximum(1000)
        time_slider.setTickPosition(QSlider.TicksBelow)
        time_slider.setSingleStep(1)
        return time_slider

    def create_style(self):
        """
        Styling the app. Making it more visual-friendly
        """
        self.data_table.horizontalHeader().setStyleSheet("QHeaderView::section { padding: 1px; }")
        self.video_table.horizontalHeader().setStyleSheet("QHeaderView::section { padding: 1px; }")
        self.logger_widget.setStyleSheet("color : #999999;")


class AppFunctions:
    """
    This class gives some functionality to the app. Every function can also be accessed within settings.py and
    bind to a shortcut.
    """

    def __init__(self, labeler_instance: Labeler):
        self.labeler = labeler_instance
        # Now you have access to all self objects from the Labeler instance

    def sort_data_table(self):
        """
        Will sort the data table by the first column (in this case StartTime)
        """
        self.labeler.data_table.sortByColumn(0, Qt.AscendingOrder)

    def delete_selected_rows(self):
        """
        Will deleted selected row in the data tale
        """
        selected_rows = self.labeler.data_table.selectedItems()
        if selected_rows:
            rows_to_delete = set()
            for item in selected_rows:
                rows_to_delete.add(item.row())
            for row in sorted(rows_to_delete, reverse=True):
                self.labeler.data_table.removeRow(row)
        self.labeler.data_table_changed = True

    def write_csv_data(self):
        """
        Will write the data to csv. Loading the values from data_table and saving the video_name.csv.
        """
        video_name_csv = self.labeler.video_name_playing.text()
        video_name_csv = "_".join(video_name_csv.split(".")[:-1])
        video_name_csv = video_name_csv.replace(" ", "_")

        if self.labeler.data_table_changed is True:
            with open(f"data\\{video_name_csv}.csv", 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=";")
                csvwriter.writerow(["STIME", "ETIME", "TYPE", "LABEL", "VID"])
                self._csv_write_rows(csvwriter)
            self.labeler.logger.logging_activity.append(["Saved", video_name_csv, "#0e1a40", "#0e1a40", "Format: CSV"])
            self.labeler.logger.write_logger()
            self.labeler.data_table_changed = False

    def save_csv(self):
        """
        Is needed to hard-save the csv file. It saves the csv file even the table is not changed. Where write_csv_data()
        checks if the data_table was changed or not.
        """
        self.labeler.data_table_changed = True
        self.write_csv_data()

    def _csv_write_rows(self, csvwriter: csv.writer):
        """
        Helper to write the rows to the csv file
        """
        for data_table_row in range(self.labeler.data_table.rowCount()):
            row_data = []
            for column in range(self.labeler.data_table.columnCount()):
                row_column_item = self.labeler.data_table.item(data_table_row, column)
                if row_column_item is not None:
                    row_data.append(row_column_item.text())
                else:
                    row_data.append("")
            csvwriter.writerow(row_data)

    def load_csv_data(self):
        """
        If there are any safed files for the loaded video. It will open the csv file and convert it into the
        data_table. So you can switch between videos and still have the actual data.
        """
        row = self.labeler.video_table.currentRow()
        video_name = self.labeler.video_table.item(row, 0).text()
        video_name_csv = "_".join(video_name.split(".")[:-1])
        video_name_csv = video_name_csv.replace(" ", "_")
        try:
            with open(f"data\\{video_name_csv}.csv", 'r', newline='') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=";")
                next(csvreader)
                self._csv_load_rows(csvreader)
            self.labeler.logger.logging_activity.append(["Loaded", video_name_csv, "#0e1a40", "#0e1a40", "Format: CSV"])
            self.labeler.logger.write_logger()
        except FileNotFoundError:
            self.labeler.data_table.setRowCount(0)  # Clear existing rows

    def _csv_load_rows(self, csvreader: Iterator[List[str]]):
        """
        Helper to load the rows from the csv file.
        """
        self.labeler.data_table.setRowCount(0)  # Clear existing rows
        for row_data in csvreader:
            row = self.labeler.data_table.rowCount()
            self.labeler.data_table.insertRow(row)
            for column, data in enumerate(row_data):
                item = QTableWidgetItem(data)
                self.labeler.data_table.setItem(row, column, item)

    def update_video_table(self):
        """
        Will create the playlist as a table, so all the videos in the "videos" directory will be shown as a table.
        Disable edits for column 0 (Video).
        """

        videos = os.listdir("videos")
        self.labeler.video_table.setRowCount(0)
        for idx, video in enumerate(videos):
            current_row_count = self.labeler.video_table.rowCount()
            self.labeler.video_table.setRowCount(current_row_count + 1)
            self.labeler.video_table.setItem(current_row_count, 0, QTableWidgetItem(video))

    def plot_hotkeys(self):
        """
        To get access to plot hotkeys within settings.json. Important to know here. It will also open the plotted
        hotkeys and write it into the logger.
        """
        HotkeyPlotter().load_and_plot()
        os.startfile("Hotkeys.png")
        self.labeler.logger.logging_activity.append(["Saved",
                                                     "Hotkeys.png",
                                                     "#0e1a40",
                                                     "#0e1a40",
                                                     "\nIF CHANGE .json -> RESTART APP"])
        self.labeler.logger.write_logger()


class MouseEventHandler:
    """
    A helper class for handling all the events of Labeler class.
    Everything that happens with Mouse-Clicks is an Event in this case.
    """

    def __init__(self, labeler_instance: Labeler):
        self.labeler = labeler_instance
        # Now you have access to all self objects from the Labeler instance

    def close_app(self, event: QCloseEvent):
        """
        Custom close event. If data-table was changed it will ask the user, if he wants to save the actual
        data-table. Save, Discard or Cancel possible.
        """
        if self.labeler.data_table_changed is True:
            reply = QMessageBox.question(self.labeler, 'Message',
                                         "Do you want to save changes?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                         QMessageBox.Save)
            if reply == QMessageBox.Save:
                video_name_csv = self.labeler.video_name_playing.text()
                if video_name_csv != "No Video Playing":
                    self.labeler.app_functions.save_csv()
                event.accept()  # Close the window
            elif reply == QMessageBox.Discard:
                event.accept()  # Close the window
            else:
                event.ignore()  # Keep the window open

    def video_table_click(self, item: QTableWidgetItem):
        """
        Starting and playing a video, by clicking on the row of the video in the table (play_list)
        """
        row = item.row()
        video_name = self.labeler.video_table.item(row, 0).text()

        video_name_csv = self.labeler.video_name_playing.text()
        if video_name_csv != "No Video Playing":
            self.labeler.app_functions.write_csv_data()

        self.labeler.player.keep_open = "yes"
        self.labeler.player.play(f'videos/{video_name}')
        self.labeler.player.pause = True
        self.labeler.observe_time_position()
        self.labeler.video_name_playing.setText(video_name)

        # self.labeler.close_event()
        self.labeler.app_functions.load_csv_data()
        self.labeler.data_table_changed = False

    def data_table_click(self, item: QTableWidgetItem):
        """
        Handling a row click on the populated data table. If row StartTime is selected, it will go to the
        video with the StartTime. If EndTime, it will go there. If something else. It will go to StartTime
        """
        row = item.row()
        column = item.column()
        if column == 0 or column == 1:
            start_time = self.labeler.data_table.item(row, column).text()
            if start_time == "WAIT...":
                start_time = self.labeler.data_table.item(row, 0).text()
        else:
            start_time = self.labeler.data_table.item(row, 0).text()

        video_name = self.labeler.data_table.item(row, 4).text()
        self.labeler.player.keep_open = "yes"
        self.labeler.player.play(f'videos/{video_name}')
        self.labeler.player.wait_for_property('seekable')
        self.labeler.player.seek(start_time, "absolute", "exact")
        self.labeler.player.pause = True
        self.labeler.observe_time_position()
        self.labeler.video_name_playing.setText(video_name)

    def slider_move(self, event):
        """
        Handling the slider mouse press event. So it acts like a normal slider for a video.
        For example, you can add self.player.pause = False at the end, and it will play the video
        after releasing the mouse. So some settings for the slider can be done here.
        """
        self.labeler.player.pause = True
        click_pos = event.pos().x()
        value = QStyle.sliderValueFromPosition(
            self.labeler.time_slider.minimum(),
            self.labeler.time_slider.maximum(),
            click_pos,
            self.labeler.time_slider.width()
        )
        self.labeler.time_slider.setValue(value)
        # noinspection PyUnresolvedReferences
        self.labeler.time_slider.valueChanged.emit(value)
        try:
            seek_time = self.labeler.time_slider.value() / 1000 * self.labeler.player.duration
        except Exception as e:
            seek_time = 0
            self.labeler.logger.append_logging(
                logg_type="Information",
                text=f"ERROR probably corrupted VIDEO: {e}",
                bg_color="#400000",
                border_color="#400000",
                ignore_if_tracked=True
            )

        self.labeler.player.command('seek', seek_time, 'absolute')

    def splitter_click(self):
        """
        Update the sizes of widgets based on the size of the first element in the splitter.
        """
        video_table_size = int(self.labeler.splitter_h.sizes()[0] * 0.8)
        data_table_size = int(self.labeler.splitter_h.sizes()[2] * 0.95)
        columns_videos = self.labeler.video_table.columnCount()
        columns_data = self.labeler.data_table.columnCount()
        video_table_size = video_table_size // columns_videos
        data_table_size = data_table_size // columns_data
        for column in range(columns_videos):
            self.labeler.video_table.setColumnWidth(column, video_table_size)
        for column in range(columns_data):
            self.labeler.data_table.setColumnWidth(column, data_table_size)


class Logger:
    """
    This class is creating some logging to inform the user what happens. The most important cases are
    handled here and will be written into the Logging window within the app.
    """

    def __init__(self, labeler_instance: Labeler):
        self.labeler = labeler_instance
        self.logging_activity = []
        self.log_max = 12  # Max number of logging rows

    def get_logging_idx(self, act_idx: int, shortcut_keys: str) -> int or None:
        """
        Needed for time_window activities. So if the shortcut was already pressed it will return the index of
        the list, else it returns None.
        """
        for idx, activity in enumerate(self.logging_activity):
            if activity[1] == shortcut_keys and activity[0] == act_idx:
                return idx
        return None

    def _remove_too_many_logs(self):
        """
        Removing too long logging list. Can be setup within settings.json as "log_max". Important to keep an
        overview about labeling.
        """
        counter = 0
        while len(self.logging_activity) > self.log_max and counter < self.log_max + 1:
            for idx, logg in enumerate(self.logging_activity):
                if logg[3] != "darkorange":
                    self.logging_activity.pop(idx)
                    break
            counter += 1

    def _clear_logger(self):
        """
        Removing log-widgets.
        """
        for i in reversed(range(self.labeler.logger_grid.count())):
            widget_item = self.labeler.logger_grid.itemAt(i)
            if widget_item is not None:
                self.labeler.logger_grid.removeWidget(widget_item.widget())

    def append_logging(self,
                       logg_type: str = "Information",
                       # "Information", "Saved", "Loaded" possible else is index of data_table
                       text: str = "",
                       bg_color: str = "#333333",
                       border_color: str = "#333333",
                       text_2: str = "",
                       ignore_if_tracked: bool = False
                       ):
        """
        Easier way to append the logging activity. More understandable.
        Set ignore_if_tracked as True if you want to show it only once or if it already in the logging window.
        Then it won't display.
        """
        if ignore_if_tracked is True:
            if [logg_type, text, bg_color, border_color, text_2] in self.logging_activity:
                pass
            else:
                self.logging_activity.append([logg_type, text, bg_color, border_color, text_2])
        else:
            self.logging_activity.append([logg_type, text, bg_color, border_color, text_2])

    def write_logger(self):
        """
        Create Labels as a logging window within the GUI. Use "Information" as the first value within
        the logging_activity list. Just append this list somewhere with three values. or just use
        append_logging() instead of self.logging_activity.append(). Both ways are fine.

        Example:
        --------
        self.logging_activity.append(["Information",
        "The data is saved to .csv",
        "Check documentation for more Information"])
        self.logger.write_logger() # Will write the appended logging

        """
        # Clearing the layout before reading widgets
        self._clear_logger()

        for idx, activity in enumerate(self.logging_activity):
            act_row = activity[0]
            act_key = activity[1]
            act_bg_color = activity[2]
            act_border_color = activity[3]
            act_data = activity[4]
            if act_row == "Saved" or act_row == "Loaded" or act_row == "Information":
                label = [act_row, act_key, act_data]
            else:
                label = [str(act_row), act_key, act_data[0], act_data[1], act_data[2], act_data[3]]
            label = " | ".join(label)
            label = QLabel(label)
            if idx == len(self.logging_activity) - 1:
                label.setStyleSheet(f"background-color: #111111; border: 1px solid darkgreen;")
            else:
                label.setStyleSheet(f"background-color: {act_bg_color}; border: 1px solid {act_border_color};")
            self.labeler.logger_grid.addWidget(label, idx, 1)

        self._remove_too_many_logs()


class HotkeyPlotter:
    """
    This class is for checking the hotkeys and creating a plot for all the available hotkeys to give an
    overview to the user. The user can instantly see all the available hotkeys and also to check if there
    are some duplicated hotkeys, which should be avoided.
    """

    def __init__(self):
        # noinspection PyUnresolvedReferences
        self.colormap = plt.get_cmap("tab10").colors

    def _check_for_duplicates(self, ordered_pairs):
        """
        Finding duplicates within a dictionary.
        """
        d = {}
        for k, v in ordered_pairs:
            if k in d:
                d[k] = "Duplicated key"
            else:
                d[k] = v
        return d

    def _make_colors(self, row):
        """
        Making the plot more visible for the user with colors. Duplicated values are marked as red for example.
        """
        if row["Duplicates"] is True or row["Value"] == "Duplicated key":
            return 4 * [self.colormap[3]]
        elif row["File"] == "settings.json":
            return 4 * [self.colormap[5]]
        elif row["File"] == "label_shortcuts.json":
            return 4 * [self.colormap[0]]
        elif row["File"] == "commands_mpv.json":
            return 4 * [self.colormap[2]]

    def _load_files(self, json_file):
        """
        Loading all the json files and adding them to a DataFrame. Also checking the duplicates.
        Is needed for plotting.
        """
        data = []
        with open(json_file, 'r') as file:
            json_data = json.load(file, object_pairs_hook=self._check_for_duplicates)

        if json_file == "label_shortcuts.json":
            for act_type in json_data:
                for key, value in json_data[act_type].items():
                    data.append((key, value, act_type, json_file))
        else:
            for key, value in json_data.items():
                data.append((key, value, "", json_file))
        df = pd.DataFrame(data, columns=["Hotkey", "Value", "ActType", "File"])
        return df

    def _plot_hotkeys(self, df):
        """
        Creating the plot of hotkeys named as Hotkeys.png within the application folder.
        """
        colors = df.apply(lambda row: self._make_colors(row), axis=1)
        df = df.drop(columns=["Duplicates"])

        fig, ax = plt.subplots()

        ax.axis('off')
        table = ax.table(
            cellText=df.values,
            colLabels=df.keys(),
            loc='center',
            cellLoc='left',
            cellColours=colors.to_list(),
        )

        for key, cell in table.get_celld().items():
            cell.set_linewidth(0.05)
            cell.get_text().set_color("white")
            cell.set_edgecolor("white")

        for i in range(0, 4):
            table.get_celld()[(0, i)].set_facecolor("black")

        fig.tight_layout()
        fig.savefig('Hotkeys.png', dpi=1000)
        plt.close()

    def load_and_plot(self):
        """
        The whole process from loading until plotting the hotkeys.
        """

        labels = self._load_files("label_shortcuts.json")
        settings = self._load_files("settings.json")
        label_shortcuts = self._load_files("commands_mpv.json")
        df = pd.concat([labels, settings], axis=0)
        df = pd.concat([df, label_shortcuts], axis=0).reset_index(drop=True)

        df["Duplicates"] = df.duplicated(subset="Hotkey", keep=False)
        df["Value"] = df["Value"].where(~df["Duplicates"], "Duplicated key")
        self._plot_hotkeys(df)


def start_app():
    locale.setlocale(locale.LC_NUMERIC, 'C')
    app = QApplication(sys.argv)
    win = Labeler(app)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    start_app()
