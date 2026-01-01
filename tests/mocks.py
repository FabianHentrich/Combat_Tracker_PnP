from unittest.mock import MagicMock

class MockWidget:
    def __init__(self, master=None, **kwargs):
        self.tk = MagicMock()
        self.master = master
        self.children = {}
        self._w = '.'
    def pack(self, **kwargs): pass
    def grid(self, **kwargs): pass
    def bind(self, *args): pass
    def config(self, **kwargs): pass
    def configure(self, **kwargs): pass
    def lift(self): pass
    def focus_force(self): pass
    def winfo_rooty(self): return 0
    def winfo_height(self): return 10
    def winfo_rootx(self): return 0
    def destroy(self): pass
    def columnconfigure(self, *args, **kwargs): pass
    def after(self, *args): pass
    def winfo_toplevel(self): return self
    def title(self, *args): pass
    def geometry(self, *args): pass
    def wait_window(self): pass

class MockVar:
    def __init__(self, value=None, **kwargs):
        self._value = value
        self.trace_add = MagicMock()
    def get(self):
        return self._value
    def set(self, value):
        self._value = value

class MockTreeview(MockWidget):
    heading = MagicMock()
    column = MagicMock()
    insert = MagicMock()
    delete = MagicMock()
    get_children = MagicMock(return_value=[])
    selection = MagicMock(return_value=[])
    index = MagicMock(return_value=0)
    identify_row = MagicMock(return_value=None)
    yview = MagicMock()

class MockScrollableFrame(MockWidget):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = MockWidget()
        self.scrollable_frame = MockWidget()

