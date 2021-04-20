#!/usr/bin/env python3

import os, sys
import numpy as np
import pandas as pd
import argparse


def main():

    parser = argparse.ArgumentParser(description='Display typing result')
    parser.add_argument('-l', '--file', default='log.csv',
                        help='Log filename')
    parser.add_argument('-p', '--path', default='None',
                        help='Path to log file')
    parser.add_argument('-u', '--user', default='user', help='User name')
    parser.add_argument('-t', '--time', default=1,
                        help='Minimum ractice time (sec.)', type=int)
    args = parser.parse_args()

    path = args.path
    filename = args.file
    if path == 'None':
        path = os.path.dirname(os.path.abspath(__file__))
    if path[-1] != '/':
        path += '/'
    log_filename = path + filename
    if not os.path.exists(log_filename):
        print('No such file : ' + log_filename)
        return 1
    if args.user == 'user':
        for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
            user = os.environ.get(name)
            if user:
                break
    else:
        user = args.user

    df_origin = pd.read_csv(log_filename)
    char_int = df_origin.columns[6:]
    char = [chr(int(i)) for i in char_int]
    df = df_origin.rename(columns=dict(zip(char_int, char)))
    df.insert(4, 'mistype',  df_origin.iloc[:,6:].sum(axis=1), True)
    df.index = pd.DatetimeIndex(pd.to_datetime(df.timestamp, unit='s',utc=True), name='date').tz_convert('Asia/Tokyo')

    df = df[df['time'] > args.time]

    if user != 'None':
        user_speed = {}
        for user in np.unique(df['user']):
            _df = df[df['user'] == user]
            user_speed[user] = _df['speed'].max()
        rank = sorted(user_speed.items(), key = lambda x : x[1], reverse=True)
        print(rank)

    else:
        df = df[df['user'] == user]
        print(df)
        print('Top 10 miss')
        print(df.sum(axis=0)[7:].sort_values(ascending=False)[:10])

if __name__ == '__main__':
    main()
