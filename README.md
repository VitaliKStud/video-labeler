
The idea behind the video-labeler is to tag time-window and point-activities.


- Point-Activity: happens at a single point on a timeline  (....<r>TAG</r>......<r>TAG</r>.....)
- Time-Window: happens between two point on a timeline (...<r>FIRST_TAG.....SECOND_TAG</r>......)

<img src="./docs/_example_images/example.png">


Download following files:

https://sourceforge.net/projects/mpv-player-windows/files/

Tested and stable version (windows): 
- mpv-dev-x86_64-v3-20240211-git-f5c4f0b 
- mpv-x86_64-v3-20240211-git-f5c4f0b
- 02.11.2024 stable version

Insert it into your python environment\\Script. It should looks following:

<img src="./docs/_example_images/mpv_to_script.png">

### Requirements
```
pip install -r requirements.txt
```


### Folder Structure
```
├── data 
│   ├── .csv
│   └── .csv
├── videos 
│   ├── .mp4
│   ├── .avi
│   └── .                                   all types supported by mpv player
├── Hotkeys.png                             (if created)
├── commands_mpv.json                       (setting for mpv player)
├── label_shortcuts.json                    (hotkeys for labeling)
├── settings.json                           (hotkeys and settings for the app)
├── requirements.txt
└── video_labeler.py                        (run this to start)
```

### Start app (Video Labeler)

```
python video_labeler.py
```

### Class Description

- Labeler
  - Check the __init__(). Loading and init 
    everything. This class especially load all the .json files
    and set all the hotkeys. Also to bring everything together
- ActivityHandler
  - Time-Window and Point-Activities are
    implemented within this class. Any new activities should be done
    here. Also populating the data-table.
- AppFunctions
  - Any function that can be set up within 
    settings.json is within this class.
- HotkeyPlotter
  - Plotting an overview named Hotkeys.png.
    Also checks for duplicated Hotkeys. Marked as red inside image.
- Layout
  - Creating all the widgets.
- Logger
  - Handling logging-window (bottom left of the app).
- MouseEventHandler
  - Any mouse-event that needs to be handled
    is done here.

```mermaid
---
title: Classes within video_labeler.py
---
classDiagram
    Labeler <|-- ActivityHandler
    Labeler <|-- AppFunctions
    Labeler <|-- HotkeyPlotter
    Labeler <|-- Layout
    Labeler <|-- Logger
    Labeler <|-- MouseEventHandler
    Labeler : settings()
    Labeler : commands_mpv()
    Labeler : label_shortcuts()
    Labeler : observe_time_position()
    Labeler : _slider_time_change()
    Labeler : _handle_label_shortcuts()
    Labeler : _handle_commands_mpv()
    class ActivityHandler{
        populate_data_table_point_activity()
        populate_data_table_time_window()
        _get_saved_time_window()
        _handle_first_time_window()
        _handle_second_time_window()
    }
    class AppFunctions{
        delete_selected_rows()
        plot_hotkeys()
        sort_data_table()
        update_video_table()
        load_csv_data()
        write_csv_data()
        _csv_load_rows()
        _csv_write_rows()  
    }
    class HotkeyPlotter{
        load_and_plot()
        _check_for_duplicates()
        _load_files()
        _make_colors()
        _plot_hotkeys()
    }
    class Layout{
        create_app_window()
        create_data_table()
        create_logger()
        create_mpv_player()
        create_second_column_video_layout()
        create_splitter()
        create_style()
        create_time_slider()
        create_video_table()
    }
    class Logger{
        write_logger()
        get_logging_idx()
        _clear_logger()
        _remove_too_many_logs()
    }
    class MouseEventHandler{
        close_app()
        data_table_click()
        splitter_click()
        splitter_move()
        video_table_click()
    }
```

### .json-Files as Configurations

Take care of duplicated Hotkeys within .json-Files. 

---
[commands_mpv.json](src/commands_mpv.json)

[examples1](https://github.com/mpv-player/mpv/blob/master/etc/input.conf)

[examples2](https://mpv.io/manual/stable/#command-interface)

Every hotkey for the MPV-Player can be set here.
Similar to mpv.commands(**kwargs). Single commands are **STRINGS** multiple
commands are **LISTS**

**EXAMPLE**
```json
{
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

```

---
[label_shortcuts.json](src/label_shortcuts.json)

time_window and point_activities available.

**EXAMPLE**
```json
{
  "time_window": {
    "Ctrl+Q": "Running",
    "Ctrl+W": "Running",
    "Ctrl+E": "Running",
    "Ctrl+R": "Walking",
    "V": "Walking"
  },
  "point_activity": {
    "P": "StepLeft",
    "Q": "StepRight",
    "W": "StepRight",
    "E": "StepRight",
    "R": "StepRight", # DUPLICATED (AVOID) USE plot_hotkeys() to find duplicates
    "R": "SETTPER", # DUPLICATED (AVOID) USE plot_hotkeys() to find duplicates
    "Z": "StepRight",
    "U": "StepRight",
    "I": "StepRight"
  }
}
```

---
[settings.json](src/settings.json)

Any method from AppFunctions ([video_labeler.py](src/video_labeler.py)) 
can be accessed with "()" at the end of the values. 

- "log_max" is for the Logger. Defines what max. number
of logs should be shown.
- "style" https://pypi.org/project/qt-material/ changing
the them of the app.
- "width_height" initial width:height
- plot_hotkeys() creates Hotkeys.png with all shortcuts. Also shows 
if there are duplicated values
- update_video_table() If there are always new incoming videos within 
the folder "videos" probably you will need this function.
- sort_data_table() sorts all the values within the data_table by "STIME"

plot_hotkeys()
<img src="docs/_example_images/Hotkeys.png">


**EXAMPLE**

```json
{
  "X": "delete_selected_rows()",
  "CTRL+S": "write_csv_data()",
  "S": "sort_data_table()",
  "L": "update_video_table()",
  "M": "plot_hotkeys()",
  "dark_amber.xml": "style",
  "1600:800": "width_height",
  "12": "log_max"
}
```

### Create executable (.exe)

All dependencies are split out from the executable (app will be faster, but a folder
with dependencies).

Terminal:
```
pip install pyinstaller
cd src
pyinstaller video_labeler.py
```

---------------------------------
Just one file as executable (app will be slower, but only one file to execute).

Terminal:
```
pip install pyinstaller
cd src
pyinstaller video_labeler.py --onefile
```

This will create a "build" and a "dist" folder. Go to dist folder. There you
will find the executable.
