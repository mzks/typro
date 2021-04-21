# typro
Typing game on console

## Usage
Execute `type.py` on your console.
The game starts immidiately.
The display of the game like
```
[#################                  ] 30.0/60 sec.
Type This : import numpy as np
Your type : import nm_
                    ^
```
The top line shows the time bar.
Type like the "Type This" line.
If you mistype, the game points that with `^`.
You have to remove the wrong character with `Backspace`.
When you fill the line correctrly, you can go the next line with `Enter`

Press Esc to quit.

## Available options
optional arguments:
```
  -h, --help            show this help message and exit
  -t TIME, --time TIME  Practice time (sec.)
  -p PATH, --path PATH  Path to training file
  -f FILE, --file FILE  Training filename
  -l LOGFILE, --logfile LOGFILE Log filename
  -m LOGPATH, --logpath LOGPATH Path to log file
  -u USER, --user USER  User name
  -q, --quiet           Run without log
  -o, --order           Not shuffle the training data
  -r, --ranking         Show ranking
  -s, --summary         Show user summary
  -d DATE, --date DATE  Date to collect data
```

Environment variables are used when you don't specify the options.
| Environment varibale    | option |
| ------------------------| -------|
| `TYPRO_FILE`            | -f     |
| `TYPRO_PATH`            | -l     |
| `TYPRO_LOG_PATH`        | -m     |


## Analysis
As a default, the typing game generates output log in `LOGFILE`.
The format is csv, pandas friendlly style.
The example of the loader is `read_log.py`
The numeric indexes mean the ASCII code of key which you mistouched.
