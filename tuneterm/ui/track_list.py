from textual.widgets import DataTable
from textual.message import Message

class TrackList(DataTable):
    BINDINGS = [
        ("delete", "delete_track", "Remove"),
        ("d", "delete_track", "Remove"),
        ("ctrl+up", "move_up", "Move Up"),
        ("ctrl+down", "move_down", "Move Down"),
        ("alt+up", "move_up", "Move Up"),
        ("alt+down", "move_down", "Move Down"),
    ]

    class TrackSelectedMessage(Message):
        def __init__(self, index: int) -> None:
            self.index = index
            super().__init__()

    class TrackDeletedMessage(Message):
        def __init__(self, index: int) -> None:
            self.index = index
            super().__init__()

    class TrackMovedMessage(Message):
        def __init__(self, from_index: int, to_index: int) -> None:
            self.from_index = from_index
            self.to_index = to_index
            super().__init__()

    def on_mount(self):
        self.add_columns("Title", "Artist", "Album", "Duration")
        self.cursor_type = "row"

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.post_message(self.TrackSelectedMessage(event.cursor_row))
        
    def action_delete_track(self) -> None:
        if self.cursor_row is not None:
            self.post_message(self.TrackDeletedMessage(self.cursor_row))

    def action_move_up(self) -> None:
        if self.cursor_row is not None and self.cursor_row > 0:
            self.post_message(self.TrackMovedMessage(self.cursor_row, self.cursor_row - 1))

    def action_move_down(self) -> None:
        if self.cursor_row is not None and self.cursor_row < self.row_count - 1:
            self.post_message(self.TrackMovedMessage(self.cursor_row, self.cursor_row + 1))
