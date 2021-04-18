#!/usr/bin/env python3

import argparse
import curses
import os
import random
import sys
import time
from multiprocessing import Array, Event, Process, Value

import numpy as np
from tqdm import tqdm


def main():

    parser = argparse.ArgumentParser(description='Stupid typing practice')
    parser.add_argument('-t', '--time', default=60, help='Practice time (sec.)', type=int)
    parser.add_argument('-p', '--path', default='None', help='Path to training file')
    parser.add_argument('-f', '--file', default='root1.txt', help='Training filename')
    parser.add_argument('-l', '--logfile', default='log.csv', help='Log filename')

    args = parser.parse_args()

    timeout_msec = args.time * 1000
    delta_time_msec = 100

    path = args.path
    filename = args.file

    if path == 'None':
        path = os.path.dirname(os.path.abspath(__file__))
    if path[-1] != '/':
        path += '/'

    training_filename = path + filename
    if not os.path.exists(training_filename):
        print('No such file : ' + training_filename)
        return 1

    timeout_event = Event()
    time_msec = Value('i', 0)
    mistake_char_list_as_int = Array('i', [-1]*1000)
    number_correct_types = Value('i', 0)

    timer_process = Process(target=timer, args=(timeout_event, timeout_msec, time_msec))
    timer_process.start()

    input_process = Process(target=load_input, args=(timeout_event, timeout_msec, time_msec, delta_time_msec,
        mistake_char_list_as_int, number_correct_types, training_filename))
    input_process.start()
    input_process.join()

    for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
        user = os.environ.get(name)
        if user:
            break

    mistake_char_list = [chr(c) for c in mistake_char_list_as_int if c > 0]
    mistake_char_list_as_int = [c for c in mistake_char_list_as_int if c > 0]

    print('User : ' + user)
    print('Correct types : ' + str(number_correct_types.value))
    print('Speed : {:.1f} types/sec'.format(number_correct_types.value/time_msec.value*1000))
    #print(mistake_char_list)

    if not os.path.isfile(path + args.logfile):
        with open(path+args.logfile, mode='a') as f:
            f.write('user,timestamp,time,correct' +\
            "".join([','+str(i) for i in np.arange(33,127).tolist()])+ '\n') 
            
    with open(path+args.logfile, mode='a') as f:
        write_str = user + ',' + str(int(time.time())) + ',' + str(time_msec.value/1000) + ','\
        + str(int(number_correct_types.value))
        mistake_array = np.zeros(94)
        for char_int in mistake_char_list_as_int:
            mistake_array[char_int-33] += 1
        write_str += "".join([','+str(int(n)) for n in mistake_array]) 
        write_str += '\n'
        f.write(write_str)
                

    return 0


def make_bar(window_y_size, timeout_msec, time_msec):

    bar_size =  window_y_size - 17 #
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


def load_input(timeout_event, timeout_msec, time_msec, delta_time_msec, mistake_char_list_as_int, number_correct_types, training_file_name):

    stdscr = curses.initscr()
    curses.noecho()
    curses.curs_set(0)
    curses.raw()
    curses.cbreak()
    stdscr.timeout(int(delta_time_msec)) # ms

    with open(training_file_name) as f:
        practice_type = [s.strip() for s in f.readlines() if len(s.strip()) > 0]
    random.shuffle(practice_type)


    index_practice = 0
    char_list = []
    window_y_size = stdscr.getmaxyx()[1]
    number_of_mistake = 0
    mistake_char_list = []
    #number_correct_types = 0

    while timeout_event.is_set() == False:
        stdscr.clear()
        stdscr.addstr(0, 0, make_bar(window_y_size, timeout_msec, time_msec))
        stdscr.addstr(2, 0, 'Type This : %s' % "".join(practice_type[index_practice]))
        stdscr.addstr(3, 0, 'Your type : %s' % "".join(char_list) + '_')
        stdscr.addstr(4, 0, point_mistake(practice_type[index_practice], char_list))
        #stdscr.addstr(5, 0, str(number_correct_types.value))
        #stdscr.addstr(6, 0, ''.join(mistake_char_list))
        stdscr.refresh()


        c = stdscr.getch()
        if c != -1: # Find key type
            if c == 27: # escape key
                timeout_event.set()
            elif c == 127: # Backspace
                if len(char_list) > 0:
                    del char_list[-1]
            elif c == 10: # Enter/Return
                if "".join(char_list) == practice_type[index_practice]:
                    index_practice += 1
                    char_list = []
            else:
                char_list.append(chr(c))
                if len(practice_type[index_practice]) <= len(char_list):
                    pass
                elif char_list[-1] == practice_type[index_practice][len(char_list)-1]:
                    number_correct_types.value += 1
                else:
                    correct_char = practice_type[index_practice][len(char_list)-1]
                    mistake_char_list_as_int[number_of_mistake] = ord(correct_char)
                    number_of_mistake += 1
                    mistake_char_list.append(correct_char)

    curses.curs_set(1)
    curses.nocbreak()
    curses.noecho()
    curses.endwin()


def timer(timeout_event, timeout_msec, time_msec):
    ut_start = time.time()
    while time_msec.value < timeout_msec and timeout_event.is_set() == False:
        time.sleep(0.001) ## wait in sec
        time_msec.value = int((time.time() - ut_start) * 1000)
    timeout_event.set()

if __name__ == "__main__":
    main()


