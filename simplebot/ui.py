from typing import Tuple, Sequence, Optional


class KeyboardLayout:
    __slots__ = ("_col", "_lines")

    def __init__(self, buttons: Optional[Sequence] = None, col: int = 1):
        self._col = col
        self._lines = []
        if buttons:
            self.add_buttons(*buttons, col=col)

    def add_buttons(self, *buttons, col: int = 1):
        for idx in range(0, len(buttons), col):
            self.add_line(*buttons[idx : idx + col])

    def add_line(self, *buttons):
        self._lines.append(list(buttons))

    def keyboard(self) -> Tuple:
        return tuple(self._lines)
