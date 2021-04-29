#!/usr/bin/env python3

import argparse
import collections
import curses
import os
import random
import sys
import time
import pkg_resources
from multiprocessing import Array, Event, Process, Value

import numpy as np
import pandas as pd


def main():

    parser = argparse.ArgumentParser(description='Typing game on console')
    parser.add_argument('-t', '--time', default=60,
                        help='Practice time (sec.)', type=int)
    parser.add_argument('-p', '--path', default='None',
                        help='Path to training file')
    parser.add_argument('-f', '--file', default='None',
                        help='Training filename')
    parser.add_argument('-l', '--logfile', default='typro_results.csv',
                        help='Log filename')
    parser.add_argument('-m', '--logpath', default='None',
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
    parser.add_argument('-d', '--date', default=7,
                        help='Date to collect data', type=int)
    parser.add_argument('-i', '--list', action='store_true',
                        help='Display lists of training file included')

    args = parser.parse_args()
    training_list, path, filename, logpathfile = make_trainings(args)

    if args.list:
        print('Predefined training file (e.g., typro -f cmd)')
        print(pkg_resources.resource_listdir('typro', 'data'))
        return 0

    timeout_msec = args.time * 1000
    delta_time_msec = 200

    if args.user == 'user':
        for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
            user = os.environ.get(name)
            if user:
                break
    else:
        user = args.user

    if args.ranking:
        show_ranking(logpathfile, args.date)
        return 0
    if args.summary:
        show_summary(logpathfile, user, args.date)
        return 0

        
    start_event = Event()
    timeout_event = Event()
    time_msec = Value('i', 0)
    mistake_char_list_as_int = Array('i', [-1]*1000)
    n_correct = Value('i', 0)

    timer_process = Process(target=timer,
                            args=(start_event, timeout_event,
                                  timeout_msec, time_msec))
    timer_process.start()

    input_process = Process(target=load_input,
                            args=(start_event, timeout_event,
                                  timeout_msec, time_msec,
                                  delta_time_msec, 
                                  mistake_char_list_as_int,
                                  n_correct, training_list))
    input_process.start()
    input_process.join()


    mistake_char_list = [chr(c) for c in mistake_char_list_as_int if c > 0]
    mistake_char_list_as_int = [c for c in mistake_char_list_as_int if c > 0]

    if time_msec.value > 0:
        print('User : ' + user)
        print('Correct types : ' + str(n_correct.value))
        print('Speed : ' +
          '{:.1f} types/sec'.format(n_correct.value/time_msec.value*1000))

    if args.quiet and n_correct.value:
        if not os.path.isfile(logpathfile):
            with open(logpathfile, mode='a') as f:
                f.write('user,timestamp,time,correct,speed,file' +
                        "".join([','+str(i) for i
                                in np.arange(33, 127).tolist()])
                        + '\n')

        with open(logpathfile, mode='a') as f:
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


def load_input(start_event, timeout_event, timeout_msec, 
               time_msec, delta_time_msec,
               mistake_char_list_as_int, n_correct, training_list):

    stdscr = curses.initscr()
    curses.noecho()
    curses.curs_set(0)
    curses.raw()
    curses.cbreak()
    stdscr.keypad(True)
    stdscr.timeout(-1)

    practice_type = training_list

    index_practice = 0
    char_list = []
    window_y_size = stdscr.getmaxyx()[1]
    number_of_mistake = 0
    mistake_char_list = []

    stdscr.clear()
    sp0 = " _                         "
    sp1 = "| |_ _   _ _ __  _ __ ___  "
    sp2 = "| __| | | | '_ \| '__/ _ \ "
    sp3 = "| |_| |_| | |_) | | | (_) |"
    sp4 = " \__|\__, | .__/|_|  \___/ "
    sp5 = "     |___/|_|              "
    stdscr.addstr(0, 0, sp0)
    stdscr.addstr(1, 0, sp1)
    stdscr.addstr(2, 0, sp2 + ' Press any keys to start')
    stdscr.addstr(3, 0, sp3 + 
                  ' Training time {:.0f} sec.'.format(timeout_msec/1000))
    stdscr.addstr(4, 0, sp4)
    stdscr.addstr(5, 0, sp5)
    stdscr.refresh()
    c = stdscr.getch()
    if c == 27 or c == 113:  # escape key or q
        timeout_event.set()
    start_event.set()

    stdscr.timeout(int(delta_time_msec))

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
                    if "".join(char_list) != practice_type[index_practice][:len(char_list)]:
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
                if "".join(char_list) != practice_type[index_practice][:len(char_list)]:
                    char_list = []
            else:
                char_list.append(chr(c))
                if len(practice_type[index_practice]) < len(char_list):
                    pass
                elif char_list[-1] == practice_type[index_practice][len(char_list)-1]:
                    if "".join(char_list) == practice_type[index_practice][:len(char_list)]:
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


def timer(start_event, timeout_event, timeout_msec, time_msec):
    while not start_event.is_set():
        time.sleep(0.001)
    ut_start = time.time()
    while time_msec.value < timeout_msec and not timeout_event.is_set():
        time.sleep(0.001)  # wait in sec
        time_msec.value = int((time.time() - ut_start) * 1000)
    timeout_event.set()


def get_df(log_filename, date):
    
    df_origin = pd.read_csv(log_filename)
    char_int = df_origin.columns[6:]
    char = [chr(int(i)) for i in char_int]
    df = df_origin.rename(columns=dict(zip(char_int, char)))
    df.insert(4, 'mistype',  df_origin.iloc[:,6:].sum(axis=1), True)
    df.index = pd.DatetimeIndex(pd.to_datetime(df.timestamp, unit='s',utc=True), name='date').tz_convert('Asia/Tokyo')
    # df = df[df['time'] > args.time]
    current_date = pd.to_datetime(int(time.time()), unit='s', utc=True)
    current_date = current_date.tz_convert('Asia/Tokyo')
    return df[df.index>current_date - pd.Timedelta(date, 'days') ]


def show_ranking(log_filename, date):
    print(log_filename)
    df = get_df(log_filename, date)
    user_speed = {}
    for user in np.unique(df['user']):
        _df = df[df['user'] == user]
        user_speed[user] = _df['speed'].max()
    rank = sorted(user_speed.items(), key = lambda x : x[1], reverse=True)
    print('user ranking')
    for r in rank:
        print(r[0] + '\t\t' + '{:.1f}'.format(r[1]))


def show_summary(log_filename, user, date):
    df = get_df(log_filename, date)
    df = df[df['user'] == user]
    print(user)
    print('Top 10 miss')
    print(df.sum(axis=0)[7:].sort_values(ascending=False)[:10])


def make_trainings(args):

    # File
    env_path = os.getenv('TYPRO_PATH')
    env_file = os.getenv('TYPRO_FILE')
    use_user_file = True
    if not args.path is 'None': # Priority 1 : Use option
        path = args.path
    elif not env_path is None: # Priority 2 : Use environment variable
        path = env_path
    else: # Priority 3 : Use package data
        path = 'data'
        use_user_file = False

    if not args.file is 'None':
        filename = args.file
    elif not env_file is None:
        filename = env_file
    else:
        filename = 'default'

    if use_user_file:
        if path[-1] != '/':
            path += '/'
        train_filename = path + filename
        if not os.path.exists(train_filename):
            print('No such file : ' + train_filename)
            sys.exit()
        with open(train_filename) as f:
            training_list = [s.strip() for s in f.readlines() if len(s.strip()) > 0]
    else:
        # package file
        training_files = pkg_resources.resource_listdir('typro', 'data')
        if not filename in training_files:
            print('No such training file included. Use')
            print(training_files)
            sys.exit()
        st = pkg_resources.resource_string('typro', 'data/' + filename).decode('utf-8')
        training_list = st.split('\n')
        training_list = [s.strip() for s in training_list if len(s) > 0]


    if not args.order:
        random.shuffle(training_list)
    # Remove decoration lines like // --------------------------
#    training_list = [st for st in training_list
#                     if collections.Counter([s for s in st]).most_common()[0][1] < 15]

    # Log file
    logpath = os.getenv('TYPRO_LOG_PATH')
    if not args.logpath is 'None':
        logpath = args.logpath
    elif logpath is None:
        logpath = os.getenv('HOME')
    if logpath[-1] != '/':
        logpath += '/'
    logpathfile = logpath + args.logfile

    return training_list, path, filename, logpathfile



if __name__ == "__main__":
    main()
