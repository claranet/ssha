import collections
import curses
import re

from curses import panel

from . import ec2


Item = collections.namedtuple('Item', field_names=('label', 'value'))


class Menu(object):

    def __init__(self, title, items, stdscreen):
        self.window = stdscreen.subwin(0, 0)
        self.window.timeout(1000)
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.title = title

        self.position = 0
        self.items = items

        self.offset_x = 2

    def addstr(self, y, x, string, attr):
        try:
            self.window.addstr(y, x, string, attr)
        except curses.error:
            # Curses will error on the last line even when it works.
            # https://stackoverflow.com/questions/7063128/last-character-of-a-window-in-python-curses
            if y == self.max_y - 1:
                pass
            else:
                raise

    def addline(self, y, string, attr):
        """
        Displays a string on the screen. Handles truncation and borders.

        """

        if y >= self.max_y:
            return

        # Display the left blank border.
        self.addstr(
            y=y,
            x=0,
            string=' ' * self.offset_x,
            attr=curses.A_NORMAL,
        )

        # Remove trailing spaces so the truncate logic works correctly.
        string = string.rstrip()

        # Truncate the string if it is too long.
        if self.offset_x + len(string) + self.offset_x > self.max_x:
            string = string[:self.max_x - self.offset_x - self.offset_x - 2] + '..'

        # Add whitespace between the end of the string and the edge of the
        # screen. This is required when scrolling, to blank out characters
        # from other lines that had been displayed here previously.
        string += ' ' * (self.max_x - self.offset_x - len(string) - self.offset_x)

        # Display the string.
        self.addstr(
            y=y,
            x=self.offset_x,
            string=string,
            attr=attr,
        )

        # Display the right blank border.
        self.addstr(
            y=y,
            x=self.max_x - self.offset_x,
            string=' ' * self.offset_x,
            attr=curses.A_NORMAL,
        )

    def navigate(self, n):
        self.position += n
        if self.position < 0:
            self.position = len(self.items) - 1
        elif self.position >= len(self.items):
            self.position = 0

    def display(self):

        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:

            self.window.refresh()
            curses.doupdate()

            self.max_y, self.max_x = self.window.getmaxyx()

            # Display the menu title.
            if self.title:
                self.addline(1, self.title)
                self.addline(2, '-' * len(self.title))
                offset_top = 3
            else:
                offset_top = 1
            offset_bottom = 1

            window_height = max(self.max_y - offset_top - offset_bottom - 1, 0)

            if self.position < window_height:
                window = (0, window_height)
            else:
                window = (self.position - window_height, self.position)

            row = 0

            for index, item in enumerate(self.items):

                if index < window[0] or index > window[1]:
                    continue

                # Highlight the selected item.
                if index == self.position:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                # Display the item.
                self.addline(
                    offset_top + row,
                    item.label,
                    mode,
                )

                row += 1

            # Blank bottom lines if screen was resized
            for y in range(offset_bottom):
                self.addline(
                    self.max_y - y - 1,
                    '',
                    curses.A_NORMAL,
                )

            # Because window.timeout was called,
            # this returns -1 if nothing was pressed.
            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord('\n')]:
                return self.items[self.position].value
            elif key in (curses.KEY_UP, ord('k')):
                self.navigate(-1)
            elif key in (curses.KEY_DOWN, ord('j')):
                self.navigate(1)
            elif key in (ord('q'), ord('Q')):
                raise KeyboardInterrupt

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()


def _display(screen, items, title=None):
    curses.curs_set(0)
    menu = Menu(title, items, screen)
    return menu.display()


def choose_config(names, search):
    if search:
        return search
    elif len(names) > 1:
        items = [Item(label=name, value=name) for name in names]
        return curses.wrapper(_display, items)
    elif names:
        return names[0]
    else:
        return None


def _find_each_column_width(table):
    if not table:
        return []

    columns_size = [0] * len(table[0])
    for row in table:
        for j, column_element in enumerate(row):
            columns_size[j] = max(columns_size[j], len(column_element))
    return columns_size


def choose_instance(instances, search, show_menu=True):

    labels = [ec2.label(inst) for inst in instances]
    columns_width = _find_each_column_width(labels)

    items = []
    for i, inst in enumerate(instances):
        formatted_labels = [label.ljust(columns_width[j]) for j, label in enumerate(labels[i])]
        items.append(Item(label=' '.join(formatted_labels), value=inst))

    if search:
        search = search.lower()
        items = [item for item in items if search in item.label.lower()]
        if len(items) == 1:
            return items[0].value

    if not items:
        return None

    if not show_menu:
        if search:
            # If there is a search string, use word boundaries
            # to increase the changes of it being a good choice.
            pattern = r'\b{}\b'.format(re.escape(search))
            items.sort(
                key=lambda item: bool(re.search(pattern, item.label, re.IGNORECASE)),
                reverse=True,
            )
        return items[0].value

    return curses.wrapper(_display, items)
