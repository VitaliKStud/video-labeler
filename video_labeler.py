import sys
import os
import json
import locale
import mpv
from PyQt5.QtWidgets import QTableWidget, QMainWindow, QLabel, QWidget, QGridLayout, QScrollArea, QSlider, QStyle, \
    QShortcut, QTableWidgetItem, QApplication, QSplitter, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QColor, QBrush
from qt_material import apply_stylesheet

"""
To do: 
- clean up code
- document code
- video scanning + save video data table (session-like)
- command_mpv 
"""


class Labeler(QMainWindow):
    def __init__(self, application, parent=None):
        super().__init__(parent)
        self.mouse_event = MouseEventHandler(self)
        self.layout = Layout(self)

        self.installEventFilter(self)
        self.setWindowTitle("Video Labeler")
        self.app = application
        self.time_window_activity = []
        self.start_end_time_activity = []
        self.logging_activity = []

        # Loading shortcuts, commands for the mpv player and the settings
        self.shortcuts()
        self.commands_mpv()
        self.settings()

        self.playtime = self.layout.playtime
        self.video_name_playing = self.layout.now_playing  # Showing name of Video
        self.app_window = self.layout.app_window_layout  # Main Window

        self.video = self.layout.video
        self.player = self.layout.player

        # Define Playlist (left side list, to play videos from) // IS A TABLE!
        # If click on a row, it will play the video (only if there is a value in the clicked cell)
        self.video_table = self.layout.video_table
        # noinspection PyUnresolvedReferences
        self.video_table.itemClicked.connect(self.mouse_event.playlist_row_click)
        self.__populate_video_table()
        # Scroll Area for Video Table
        self.scroll_video_table = self.layout.scroll_video_table

        # Define DataTable, for entered observations
        self.data_table = self.layout.data_table
        # Scroll Area for data Table
        self.scroll_data_table = self.layout.scroll_data_table
        # noinspection PyUnresolvedReferences
        self.data_table.itemClicked.connect(self.mouse_event.data_table_click)

        # Define Time Slider
        self.time_slider = self.layout.time_slider
        self.time_slider.mousePressEvent = self.mouse_event.slider_move
        self.time_slider.mouseMoveEvent = self.mouse_event.slider_move

        self.label_vis = self.layout.label_vis
        self.scroll_vis = self.layout.scroll_vis
        self.layout_vis = self.layout.layout_vis

        self.label_vis_2 = self.layout.label_vis_2
        self.scroll_vis_2 = self.layout.scroll_vis_2
        self.layout_vis_2 = self.layout.layout_vis_2

        self.splitter_v = self.layout.splitter_v
        self.splitter_h = self.layout.splitter_h
        # noinspection PyUnresolvedReferences
        self.splitter_h.splitterMoved.connect(self.__update_size_of_table)

        # Testing the labels
        self.__create_labels()
        # self.layout.create_layout()

    def __create_labels(self):
        with open('label_shortcuts.json', 'r') as file:
            shortcuts = json.load(file)

        for act_type in shortcuts:
            for idx, value in enumerate(shortcuts[act_type].items()):
                # shortcut = value[0]
                label_value = value[1]
                label = QLabel(label_value)
                self.layout_vis_2.addWidget(label, idx, 1)

    def __update_size_of_table(self):
        """
        Update the sizes of widgets based on the size of the first element in the splitter.
        """
        video_table_size = int(self.splitter_h.sizes()[0] * 0.8)
        data_table_size = int(self.splitter_h.sizes()[2] * 0.95)
        columns_videos = self.video_table.columnCount()
        columns_data = self.data_table.columnCount()
        video_table_size = video_table_size // columns_videos
        data_table_size = data_table_size // columns_data
        for column in range(columns_videos):
            self.video_table.setColumnWidth(column, video_table_size)
        for column in range(columns_data):
            self.data_table.setColumnWidth(column, data_table_size)

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
            shortcut.activated.connect(lambda commands=command: self.__handle_commands_mpv(commands))

    def __handle_commands_mpv(self, commands):
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
            if value == "delete_row":
                shortcut = QShortcut(QKeySequence(key), self)
                # noinspection PyUnresolvedReferences
                shortcut.activated.connect(self.__delete_selected_row)
            if value == "sort_table":
                shortcut = QShortcut(QKeySequence(key), self)
                # noinspection PyUnresolvedReferences
                shortcut.activated.connect(self.__sort_data_table)
            if value == "style":
                # https://pypi.org/project/qt-material/
                apply_stylesheet(self.app, theme=key, extra={"density_scale": "0"})
            if value == "width_height":
                w_h = key.split(":")
                self.resize(int(w_h[0]), int(w_h[1]))

    def __sort_data_table(self):
        """
        Will sort the data table by the first column (in this case StartTime)
        """
        self.data_table.sortByColumn(0, Qt.AscendingOrder)

    def __delete_selected_row(self):
        """
        Will deleted selected row in the data tale
        """
        selected_rows = self.data_table.selectedItems()
        if selected_rows:
            rows_to_delete = set()
            for item in selected_rows:
                rows_to_delete.add(item.row())
            for row in sorted(rows_to_delete, reverse=True):
                self.data_table.removeRow(row)

    def shortcuts(self):
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
                    lambda labels=label, act_types=act_type, shortcut_keys=shortcut_key: self.__handle_shortcuts(labels,
                                                                                                                 act_types,
                                                                                                                 shortcut_keys))

    def __handle_shortcuts(self, labels, act_types, shortcut_keys):
        """
        Is handling the shortcuts for the labels. In this case there are only two options,
        time_window and point_activity to handle. Where The time_window needs to be pressed
        twice to write two values within the table. The point_activity needs only once to be pressed
        to track StartTime and EndTime.
        """
        # "StartTime", "EndTime", "ActType", "Label", "Video"
        video_name = self.video_name_playing.text()
        play_time = self.playtime.text()
        data_to_insert = [play_time, play_time, act_types, labels, video_name]

        if act_types == "time_window":
            self.__populate_table_time_window(data_to_insert, shortcut_keys)
        elif act_types == "point_activity":
            self.__populate_table_point_activity(data_to_insert, shortcut_keys)

    def __get_logging_idx(self, act_idx, shortcut_keys):
        for idx, activity in enumerate(self.logging_activity):
            if activity[1] == shortcut_keys and activity[0] == act_idx:
                return idx
        return None


    def __vis_labeling(self, act_type, shortcut_keys):
        # [current_row_count, shortcut_keys, "#333333", "darkred", list(data)]
        # len_logging = len(self.logging_activity)

        for idx, activity in enumerate(self.logging_activity):
            act_row = activity[0]
            act_key = activity[1]
            act_bg_color = activity[2]
            act_border_color = activity[3]
            act_data = activity[4]
            # if shortcut_keys == act_key:
            label = [str(act_row), act_key, act_data[0], act_data[1], act_data[2], act_data[3]]
            label = " | ".join(label)
            label = QLabel(label)
            label.setStyleSheet(f"background-color: {act_bg_color}; border: 2px solid {act_border_color};")
            self.layout_vis.addWidget(label, idx, 1)

        len_logging = len(self.logging_activity)
        counter = 0
        while len_logging > 12 and counter < 12:
            len_logging = len(self.logging_activity)
            for idx, logg in reversed(list(enumerate(self.logging_activity))):
                if logg[3] == "darkgreen":
                    self.logging_activity.pop(idx)
                    len_logging = len(self.logging_activity)
                else:
                    pass
                counter += 1


    def __get_saved_time_window(self, shortcut_keys):
        for idx, activity in enumerate(self.time_window_activity):
            if activity[2] == shortcut_keys:
                return (activity, idx)
        return None


    def __handle_first_tw_activity(self, data, shortcut_keys):
        current_row_count = self.data_table.rowCount()
        self.time_window_activity.append((current_row_count, 1, shortcut_keys, data[0]))

        self.data_table.setRowCount(current_row_count + 1)
        for j, item in enumerate(data):
            self.data_table.setItem(current_row_count, j, QTableWidgetItem(item))

        self.logging_activity.append([current_row_count, shortcut_keys, "#333333", "darkred", data])
        self.__vis_labeling(act_type="time_window", shortcut_keys=shortcut_keys)

    def __handle_second_tw_activity(self, data, shortcut_keys, activity, act_idx):
        self.data_table.setItem(activity[0], activity[1],
                                QTableWidgetItem(data[1]))
        self.time_window_activity.pop(act_idx)

        logg_idx = self.__get_logging_idx(activity[0], shortcut_keys)

        if logg_idx is not None:
            self.logging_activity[logg_idx] = [activity[0], shortcut_keys, "#333333", "darkgreen", data]
        else:
            self.logging_activity.append([activity[0], shortcut_keys, "#333333", "darkgreen", data])
        self.__vis_labeling(act_type="time_window", shortcut_keys=shortcut_keys)

    def __populate_table_time_window(self, data, shortcut_keys):
        """
        As described in __handle_shortcuts() above, this function will handle time_window option. (writing twice)
        """
        act = self.__get_saved_time_window(shortcut_keys)
        if act is None:
            data[1] = "WAIT..."
            self.__handle_first_tw_activity(data, shortcut_keys)
        else:
            activity = act[0]
            act_idx = act[1]
            data[0] = act[0][-1]
            self.__handle_second_tw_activity(data, shortcut_keys, activity, act_idx)

    def __populate_table_point_activity(self, data, shortcut_keys):
        """
        Handling point activity (writing once)
        """
        current_row_count = self.data_table.rowCount()
        self.data_table.setRowCount(current_row_count + 1)
        for j, item in enumerate(data):
            self.data_table.setItem(current_row_count, j, QTableWidgetItem(item))

        self.logging_activity.append([current_row_count, shortcut_keys, "#333333", "darkgreen", list(data)])
        self.__vis_labeling(act_type="point_activity", shortcut_keys=shortcut_keys)

    def __populate_video_table(self):
        """
        Will create the playlist as a table, so all the videos in the "videos" directory will be shown as a table.
        Disable edits for column 0 (Video).
        """
        videos = os.listdir("videos")
        for idx, video in enumerate(videos):
            current_row_count = self.video_table.rowCount()
            self.video_table.setRowCount(current_row_count + 1)
            self.video_table.setItem(current_row_count, 0, QTableWidgetItem(video))
            for row in range(self.video_table.rowCount()):
                item = self.video_table.item(row, 0)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)

    def __slider_time_change(self, value):
        """
        Change the position of the slider, defined by current video time.
        """
        if self.player.duration != 0 and not self.time_slider.isSliderDown():
            slider_value = int((value / self.player.duration) * 1000)
            self.time_slider.setValue(slider_value)

    def __change_labels_color(self, value):
        pass

    def observe_time_position(self):
        """
        Observing the time position and writing it into the playtime widget.
        """

        @self.player.property_observer('time-pos')
        def time_observer(_name, value):
            if value is not None:
                self.playtime.setText(f"{value:.3f}")
                self.__slider_time_change(value)
                # self.color_change_values(value)
                # self.player.register_message_handler()
                # frame = self.player.frame
                # print(frame)
            else:
                self.playtime.setText("NaN")


class Layout:
    def __init__(self, labeler_instance):
        self.labeler = labeler_instance
        self.playtime = QLabel("0")
        self.now_playing = QLabel("No Video Playing")
        self.app_window, self.app_window_layout = self.create_app_window()
        self.video, self.player = self.create_mpv_player()
        self.video_table, self.scroll_video_table = self.create_video_table()
        self.data_table, self.scroll_data_table = self.create_data_table()
        self.time_slider = self.create_time_slider()
        self.label_vis, self.scroll_vis, self.layout_vis = self.create_label_vis()
        self.label_vis_2, self.scroll_vis_2, self.layout_vis_2 = self.create_label_vis()
        self.video_widget, self.video_layout = self.create_second_column_video_layout()
        self.splitter_h, self.splitter_v = self.create_splitter()
        self.create_style()

    def create_app_window(self):
        app_window = QWidget(self.labeler)
        self.labeler.setCentralWidget(app_window)
        app_window_layout = QGridLayout(app_window)
        return app_window, app_window_layout

    def create_mpv_player(self):
        video = QWidget(self.labeler)
        player = mpv.MPV(
            wid=str(int(video.winId())),
            vo="x11",
            input_default_bindings=True,
            input_vo_keyboard=True,
            osc=True
        )
        player["vo"] = "gpu"
        return video, player

    def create_video_table(self):
        video_table = QTableWidget(self.labeler)
        video_table.setRowCount(0)
        video_table.setColumnCount(2)
        video_table.setHorizontalHeaderLabels(["Video", "Labeled"])

        scroll_video_table = QScrollArea(self.labeler)
        scroll_video_table.setWidgetResizable(True)
        scroll_video_table.setWidget(video_table)

        return video_table, scroll_video_table

    def create_data_table(self):
        data_table = QTableWidget(self.labeler)
        data_table.setRowCount(0)
        data_table.setColumnCount(5)
        data_table.setHorizontalHeaderLabels(
            ["STime", "ETime", "Type", "Label", "Vid"])

        # Create a scroll are for the table and set table widget as its widget
        scroll_data_table = QScrollArea()
        scroll_data_table.setWidgetResizable(True)
        scroll_data_table.setWidget(data_table)
        return data_table, scroll_data_table

    def create_time_slider(self):
        time_slider = QSlider(Qt.Horizontal)
        time_slider.setMinimum(0)
        time_slider.setMaximum(1000)
        time_slider.setTickPosition(QSlider.TicksBelow)
        time_slider.setSingleStep(1)
        return time_slider

    def create_second_column_video_layout(self):
        video_widget = QWidget(self.labeler)
        video_layout = QVBoxLayout(video_widget)
        video_layout.addWidget(self.video, stretch=10)
        video_layout.addWidget(self.playtime)
        video_layout.addWidget(self.now_playing)
        video_layout.addWidget(self.time_slider)
        return video_widget, video_layout

    def create_label_vis(self):
        # Will show the labels for every frame (ongoing, not done)
        label_vis = QWidget(self.labeler)
        scroll_vis = QScrollArea()
        scroll_vis.setWidgetResizable(True)
        layout_vis = QGridLayout(label_vis)
        scroll_vis.setWidget(label_vis)
        return label_vis, scroll_vis, layout_vis

    def create_splitter(self):
        # Add scroll_video_table to the first column
        splitter_v = QSplitter(Qt.Vertical)
        splitter_v.addWidget(self.scroll_video_table)
        splitter_v.addWidget(self.scroll_vis)

        # splitter_v2 = QSplitter(Qt.Vertical)
        # splitter_v2.addWidget(self.scroll_data_table)
        # splitter_v2.addWidget(self.scroll_vis_2)

        splitter_h = QSplitter(Qt.Horizontal)
        splitter_h.addWidget(splitter_v)
        splitter_h.addWidget(self.video_widget)
        splitter_h.addWidget(self.scroll_data_table)

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
                int(height * 0.5),
                int(height * 0.5)
            ]

        )

        # splitter_v2.setSizes(
        #     [
        #         int(height * 0.8),
        #         int(height * 0.2)
        #     ]
        #
        # )

        # Set the splitter as the central widget of the main window
        self.labeler.setCentralWidget(splitter_h)

        return splitter_h, splitter_v

    def create_style(self):
        self.data_table.horizontalHeader().setStyleSheet("QHeaderView::section { padding: 1px; }")
        self.video_table.horizontalHeader().setStyleSheet("QHeaderView::section { padding: 1px; }")
        self.label_vis.setStyleSheet("background-color: black; color : #999999;")


class MouseEventHandler:
    """
    A helper class for handling all the events of Labeler class.
    Everything that happens with Mouse-Clicks is an Event in this case.
    """

    def __init__(self, labeler_instance):
        self.labeler = labeler_instance
        # Now you have access to all self objects from the Labeler instance

    def playlist_row_click(self, item):
        """
        Starting and playing a video, by clicking on the row of the video in the table (play_list)
        """
        row = item.row()
        video_name = self.labeler.video_table.item(row, 0).text()
        self.labeler.player.loop_playlist = "inf"
        self.labeler.player.play(f'videos/{video_name}')
        self.labeler.observe_time_position()
        self.labeler.video_name_playing.setText(video_name)

    def data_table_click(self, item):
        """
        Handling a row click on the populated data table. If row StartTime is selected, it will go to the
        video with the StartTime. If EndTime, it will go there. If something else. It will go to StartTime
        """
        row = item.row()
        column = item.column()
        if column == 0 or column == 1:
            start_time = self.labeler.data_table.item(row, column).text()
        else:
            start_time = self.labeler.data_table.item(row, 0).text()
        video_name = self.labeler.data_table.item(row, 4).text()

        self.labeler.player.loop_playlist = "inf"
        self.labeler.player.loadfile(f'videos/{video_name}', sub_file="sub_test.srt")
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
        seek_time = self.labeler.time_slider.value() / 1000 * self.labeler.player.duration
        self.labeler.player.command('seek', seek_time, 'absolute')


locale.setlocale(locale.LC_NUMERIC, 'C')
app = QApplication(sys.argv)
win = Labeler(app)
win.show()
sys.exit(app.exec_())
