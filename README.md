<style>
r { color: Red }
o { color: Orange }
g { color: Green }
</style>

The idea behind the video-labeler is to tag time-window and point-activities.


- Point-Activity: happens at a single point on a timeline  (....<r>TAG</r>......<r>TAG</r>.....)
- Time-Window: happens between two point on a timeline (...<r>FIRST_TAG.....SECOND_TAG</r>......)

<img src="./docs/example.png">


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


- Put some videos inside the "videos" folder
- Run video_labeler.py
- Setup the .json files (shortcuts etc.)

