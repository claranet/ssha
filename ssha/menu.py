import curses

from curses import panel

from . import config


class Menu(object):

    def __init__(self, title, instances, stdscreen):
        self.window = stdscreen.subwin(0, 0)
        self.window.timeout(1000)
        self.window.keypad(1)
        self.panel = panel.new_panel(self.window)
        self.panel.hide()
        panel.update_panels()

        self.title = title

        self.position = 0
        self.instances = instances

    def navigate(self, n):
        self.position += n
        if self.position < 0:
            self.position = len(self.instances) - 1
        elif self.position >= len(self.instances):
            self.position = 0

    def display(self):

        self.panel.top()
        self.panel.show()
        self.window.clear()

        while True:

            self.window.refresh()
            curses.doupdate()

            # Display the menu title.
            self.window.addstr(1, 2, self.title, curses.A_NORMAL)
            self.window.addstr(2, 2, '-' * len(self.title), curses.A_NORMAL)

            for index, instance in enumerate(self.instances):

                # Highlight the selected instance.
                if index == self.position:
                    mode = curses.A_REVERSE
                else:
                    mode = curses.A_NORMAL

                # Display the instance.
                msg = _get_label(instance)
                self.window.addstr(3 + index, 2, msg, mode)

                # Write out spaces to handle when a message becomes shorter.
                self.window.addstr(
                    3 + index,
                    2 + len(msg),
                    ' ' * 100,
                    curses.A_NORMAL,
                )

            # Because window.timeout was called,
            # this returns -1 if nothing was pressed.
            key = self.window.getch()

            if key in [curses.KEY_ENTER, ord('\n')]:
                return self.instances[self.position]
            elif key == curses.KEY_UP:
                self.navigate(-1)
            elif key == curses.KEY_DOWN:
                self.navigate(1)
            elif key in (81, 113):
                # Either q or Q was pressed.
                return None

        self.window.clear()
        self.panel.hide()
        panel.update_panels()
        curses.doupdate()


def _display(screen, instances):
    curses.curs_set(0)
    menu = Menu('EC2 Instances', instances, screen)
    return menu.display()


def _get_label(instance):

    result = []
    for field in config.get('display.fields') or []:
        value = instance
        for key in field.split('.'):
            value = value.get(key)
        if value:
            result.append(value)
    return ' '.join(result) or instance['InstanceId']


def choose_instance(instances, search):
    if search:
        instances = [inst for inst in instances if search.lower() in _get_label(inst).lower()]
    if len(instances) == 1 and search:
        return instances[0]
    try:
        return curses.wrapper(_display, instances)
    except KeyboardInterrupt:
        return None
