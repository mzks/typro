import curses

stdscr = curses.initscr()
stdscr.keypad(True)
c = stdscr.getch()

stdscr.keypad(False)
curses.endwin()

print(c)
