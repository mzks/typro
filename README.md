# typro
Typing practice game on console for professional

## Install and Usage
```
pip install git+https://github.com/mzks/typro
```
Execute `typro` on your console.
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
  -q, --quiet           Run without writing log
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


## Available training files

| Name    | description                           |
| ------- | ------------------------------------- |
| default | C++ simple code (used as default)     |
| root    | ROOT (cern) hist examples             |

The `-f` option switch the file like `typro -f root`.
If you want to use your own file, (1) use option (`-p` and `-f`) or (2) use environment variables.


## Examples
#### training with root code without shuffle
```
typro -f root -o
```

#### training with your code
```
typro -p /path/to/your/file -f your_file
```

#### show your weak keys
```
typro -s
```

#### show user ranking in the privious 3 days
```
typro -r -d 3
```


## Analysis
As a default, the typing game generates output log in `LOGFILE` (default: `typro_results.csv`)
The format is csv, pandas friendlly style.
The numeric indexes mean the ASCII code of key which you mistouched.
