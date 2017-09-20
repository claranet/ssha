import collections
import curses

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

    def addstr(self, y, x, string, attr=None):
        if y < self.max_y:
            self.window.addstr(y, x, string[:self.max_x - self.offset_x - x], attr)

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
                self.addstr(1, self.offset_x, self.title, curses.A_NORMAL)
                self.addstr(2, self.offset_x, '-' * len(self.title), curses.A_NORMAL)
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
                self.addstr(
                    offset_top + row,
                    self.offset_x,
                    item.label,
                    mode,
                )

                # Write out spaces to handle when a message becomes shorter.
                self.addstr(
                    offset_top + row,
                    self.offset_x + len(item.label),
                    ' ' * self.max_x,
                    curses.A_NORMAL,
                )

                row += 1

            # Blank bottom lines if screen was resized
            for y in range(offset_bottom):
                self.addstr(
                    self.max_y - y - 1,
                    self.offset_x,
                    ' ' * self.max_x,
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
    columns_size = [0] * len(table[0])
    for row in table:
        for j, column_element in enumerate(row):
            columns_size[j] = max(columns_size[j], len(column_element))
    return columns_size


def choose_instance(instances, search):

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

    return curses.wrapper(_display, items)
