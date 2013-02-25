import sublime


def fix_cloned_view(f):
    """ Workaround for clone view bug. """
    def _f(self, view, *args, **kwargs):
        # It may be wrong view that given as view argument.
        window = view.window()
        if window is None:
            window = sublime.active_window()
        if window is not None:
            if window.active_view() is not None:
                view = window.active_view()
        f(self, view, *args, **kwargs)
    return _f
