import collections
import curses

from curses import panel

from . import config, ec2


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

    def addstr(self, y, x, str, attr=None):
        if y + 1 < self.max_y and x + len(str) < self.max_x:
            self.window.addstr(y, x, str, attr)

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
                self.addstr(1, 2, self.title, curses.A_NORMAL)
                self.addstr(2, 2, '-' * len(self.title), curses.A_NORMAL)
                offset_y = 3
            else:
                offset_y = 1

            for index, item in enumerate(self.items):

                # Highlight the selected item.
                if index == self.position:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                # Display the item.
                self.addstr(
                    offset_y + index,
                    2,
                    item.label,
                    mode,
                )

                # Write out spaces to handle when a message becomes shorter.
                self.addstr(
                    offset_y + index,
                    2 + len(item.label),
                    ' ' * 100,
                    curses.A_NORMAL,
                )

            # Because window.timeout was called,
            # this returns -1 if nothing was pressed.
            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord('\n')]:
                return self.items[self.position].value
            elif key == curses.KEY_UP:
                self.navigate(-1)
            elif key == curses.KEY_DOWN:
                self.navigate(1)
            elif key in (81, 113):
                # Either q or Q was pressed.
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


def choose_instance(instances, search):

    items = [Item(label=ec2.label(inst), value=inst) for inst in instances]

    if search:
        search = search.lower()
        items = [item for item in items if search in item.label.lower()]
        if len(items) == 1:
            return items[0].value

    if not items:
        return None

    return curses.wrapper(_display, items)
