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

text = 'Implemented both types, 
time-window and point-acitivities. Writting 
data into the data_table. If any new activities 
needs to be implemented, should be done here'

```mermaid
---
title: Classes within video_labeler.py
---
classDiagram
    note for Labeler "Check the __init__(). Loading and init 
    everything. This class especially load all the .json files
    and set all the hotkeys"
    note for ActivityHandler "Time-Window and Point-Activities are
    implemented within this class. Any new activities should be done
    here. Also populating the data-table."
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
        _get_saved_time_window()
        _handle_first_time_window()
        _handle_second_time_window()
        _populate_data_table_point_activity()
        _populate_data_table_time_window()
    }
    class AppFunctions{
        -int sizeInFeet
        -canEat()
    }
    class HotkeyPlotter{
        +bool is_wild
        +run()
    }
    class Layout{
        +bool is_wild
        +run()
    }
    class Logger{
        +bool is_wild
        +run()
    }
    class MouseEventHandler{
        +bool is_wild
        +run()
    }
```


- Put some videos inside the "videos" folder
- Run video_labeler.py
- Setup the .json files (shortcuts etc.)

