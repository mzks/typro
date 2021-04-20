#!/usr/bin/env python3

import argparse
import collections
import curses
import os
import random
import sys
import time
from multiprocessing import Array, Event, Process, Value

import numpy as np
import pandas as pd
from tqdm import tqdm


def main():

    parser = argparse.ArgumentParser(description='Stupid typing practice')
    parser.add_argument('-t', '--time', default=60,
                        help='Practice time (sec.)', type=int)
    parser.add_argument('-p', '--path', default='ENV',
                        help='Path to training file')
    parser.add_argument('-f', '--file', default='root1.txt',
                        help='Training filename')
    parser.add_argument('-l', '--logfile', default='log.csv',
                        help='Log filename')
    parser.add_argument('-m', '--logpath', default='ENV',
                        help='Path to log file')
    parser.add_argument('-u', '--user', default='user', help='User name')
    parser.add_argument('-q', '--quiet', action='store_false',
                        help='Run without log')
    parser.add_argument('-o', '--order', action='store_true',
                        help='Not shuffle the training data')
    parser.add_argument('-r', '--ranking', action='store_true',
                        help='Show ranking')
    parser.add_argument('-s', '--summary', action='store_true',
                        help='Show user summary')

    args = parser.parse_args()

    timeout_msec = args.time * 1000
    delta_time_msec = 200

    path = args.path
    logpath = args.logpath
    filename = args.file
    order = args.order

    if path == 'ENV':
        path = os.getenv('CONSOLE_TYPE_PATH')
        if path == None:
            path = os.path.dirname(os.path.abspath(__file__))
    if logpath == 'ENV':
        logpath = os.getenv('CONSOLE_TYPE_LOG_PATH')
        if logpath == None:
            logpath = path
    if path[-1] != '/':
        path += '/'
    if logpath[-1] != '/':
        logpath += '/'

    train_filename = path + filename
    if not os.path.exists(train_filename):
        print('No such file : ' + train_filename)
        return 1

    if args.user == 'user':
        for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
            user = os.environ.get(name)
            if user:
                break
    else:
        user = args.user

    if args.ranking:
        show_ranking(logpath+args.logfile)
        return 0
    if args.summary:
        show_summary(logpath+args.logfile, user)
        return 0

    timeout_event = Event()
    time_msec = Value('i', 0)
    mistake_char_list_as_int = Array('i', [-1]*1000)
    n_correct = Value('i', 0)

    timer_process = Process(target=timer,
                            args=(timeout_event, timeout_msec, time_msec))
    timer_process.start()

    input_process = Process(target=load_input,
                            args=(timeout_event, timeout_msec, time_msec,
                                  delta_time_msec, mistake_char_list_as_int,
                                  n_correct, train_filename, order))
    input_process.start()
    input_process.join()


    mistake_char_list = [chr(c) for c in mistake_char_list_as_int if c > 0]
    mistake_char_list_as_int = [c for c in mistake_char_list_as_int if c > 0]

    print('User : ' + user)
    print('Correct types : ' + str(n_correct.value))
    print('Speed : ' +
          '{:.1f} types/sec'.format(n_correct.value/time_msec.value*1000))

    if args.quiet:
        if not os.path.isfile(logpath + args.logfile):
            with open(logpath+args.logfile, mode='a') as f:
                f.write('user,timestamp,time,correct,speed,file' +
                        "".join([','+str(i) for i
                                in np.arange(33, 127).tolist()])
                        + '\n')

        with open(logpath+args.logfile, mode='a') as f:
            write_str = user + ',' + str(int(time.time()))\
                        + ',' + str(time_msec.value/1000) + ','\
                        + str(int(n_correct.value)) + ','\
                        + str(n_correct.value/time_msec.value*1000.)\
                        + ',' + filename
            mistake_array = np.zeros(94)
            for char_int in mistake_char_list_as_int:
                mistake_array[char_int-33] += 1
            write_str += "".join([','+str(int(n)) for n in mistake_array])
            write_str += '\n'
            f.write(write_str)

    return 0


def make_bar(window_y_size, timeout_msec, time_msec):

    bar_size = window_y_size - 17  # Space to show time
    progress_percentage = time_msec.value / timeout_msec
    shape_length = int(bar_size * progress_percentage)
    under_length = int(bar_size - shape_length)
    bar_str = '[' + '#'*shape_length + '_'*under_length + ']'
    bar_str += ' {:.1f}/{:.0f} sec.'.format(time_msec.value/1000, timeout_msec/1000)
    return bar_str


def point_mistake(correct, char_list):
    mistake_str = '            '
    for i in range(len(correct)):
        if len(correct) <= i or len(char_list) <= i:
            mistake_str += ' '
        elif correct[i] == char_list[i]:
            mistake_str += ' '
        else:
            mistake_str += '^'
    return mistake_str


def load_input(timeout_event, timeout_msec, time_msec, delta_time_msec,
               mistake_char_list_as_int, n_correct, training_file_name, order):

    stdscr = curses.initscr()
    curses.noecho()
    curses.curs_set(0)
    curses.raw()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.timeout(int(delta_time_msec))

    with open(training_file_name) as f:
        practice_type = [s.strip() for s in f.readlines() if len(s.strip()) > 0]
    if not order:
        random.shuffle(practice_type)

    # Remove decoration lines like // --------------------------
    practice_type = [st for st in practice_type
                     if collections.Counter([s for s in st]).most_common()[0][1] < 15]

    index_practice = 0
    char_list = []
    window_y_size = stdscr.getmaxyx()[1]
    number_of_mistake = 0
    mistake_char_list = []

    while not timeout_event.is_set():
        stdscr.clear()
        stdscr.addstr(0, 0, make_bar(window_y_size, timeout_msec, time_msec))
        stdscr.addstr(2, 0, 'Type This : %s' % "".join(practice_type[index_practice]))
        stdscr.addstr(3, 0, 'Your type : %s' % "".join(char_list) + '_')
        stdscr.addstr(4, 0, point_mistake(practice_type[index_practice], char_list))
        # stdscr.addstr(5, 0, str(n_correct.value))
        # stdscr.addstr(6, 0, ''.join(mistake_char_list))

        stdscr.refresh()
        # stdscr.noutrefresh()
        # curses.doupdate()

        c = stdscr.getch()
        if c != -1:  # Find key type
            if c == 27:  # escape key
                timeout_event.set()
            elif c == 263 or c == 127 or c == 8:  # Backspace/Ctrl-H
                if len(char_list) > 0:
                    del char_list[-1]
            elif c == 10:  # Enter/Return
                if "".join(char_list) == practice_type[index_practice]:
                    index_practice += 1
                    char_list = []
                    if index_practice >= len(practice_type):
                        timeout_event.set()
            elif c == curses.KEY_RIGHT or c == curses.KEY_LEFT:
                pass
            elif c == curses.KEY_UP or c == curses.KEY_DOWN:
                pass
            elif c == 21:  # Ctrl-U
                char_list = []
            else:
                char_list.append(chr(c))
                if len(practice_type[index_practice]) < len(char_list):
                    pass
                elif char_list[-1] == practice_type[index_practice][len(char_list)-1]:
                    n_correct.value += 1
                else:
                    correct_char = practice_type[index_practice][len(char_list)-1]
                    mistake_char_list_as_int[number_of_mistake] = ord(correct_char)
                    number_of_mistake += 1
                    mistake_char_list.append(correct_char)

    stdscr.keypad(False)
    curses.curs_set(1)
    curses.nocbreak()
    curses.noecho()
    curses.endwin()


def timer(timeout_event, timeout_msec, time_msec):
    ut_start = time.time()
    while time_msec.value < timeout_msec and not timeout_event.is_set():
        time.sleep(0.001)  # wait in sec
        time_msec.value = int((time.time() - ut_start) * 1000)
    timeout_event.set()


def get_df(log_filename):
    
    df_origin = pd.read_csv(log_filename)
    char_int = df_origin.columns[6:]
    char = [chr(int(i)) for i in char_int]
    df = df_origin.rename(columns=dict(zip(char_int, char)))
    df.insert(4, 'mistype',  df_origin.iloc[:,6:].sum(axis=1), True)
    df.index = pd.DatetimeIndex(pd.to_datetime(df.timestamp, unit='s',utc=True), name='date').tz_convert('Asia/Tokyo')
    # df = df[df['time'] > args.time]
    return df


def show_ranking(log_filename):
    print(log_filename)
    df = get_df(log_filename)
    user_speed = {}
    for user in np.unique(df['user']):
        _df = df[df['user'] == user]
        user_speed[user] = _df['speed'].max()
    rank = sorted(user_speed.items(), key = lambda x : x[1], reverse=True)
    print('user ranking')
    for r in rank:
        print(r[0] + '\t\t' + '{:.1f}'.format(r[1]))

def show_summary(log_filename, user):

    df = get_df(log_filename)
    df = df[df['user'] == user]
    print(user)
    print('Top 10 miss')
    print(df.sum(axis=0)[7:].sort_values(ascending=False)[:10])


if __name__ == "__main__":
    main()
