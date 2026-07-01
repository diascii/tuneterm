from textual.widgets import DirectoryTree, Tree
from textual.message import Message

class FileBrowser(DirectoryTree):
    BINDINGS = [
        ("space", "toggle_node", "Toggle folder"),
        ("enter", "open_file", "Play file"),
        ("h", "toggle_node", "Toggle folder"),
        ("l", "open_file", "Play file"),
    ]

    class FileSelectedMessage(Message):
        def __init__(self, filepath: str) -> None:
            self.filepath = filepath
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(".", *args, **kwargs)

    def load_directory(self, path: str):
        self.path = path
        self.reload()

    def action_toggle_node(self) -> None:
        """Toggle expand/collapse on the currently highlighted node."""
        node = self.cursor_node
        if node and node.allow_expand:
            node.toggle()

    def action_open_file(self) -> None:
        """Play the selected file."""
        node = self.cursor_node
        if node and not node.is_expandable:
            data = self.get_node_data(node)
            if data and data.path.suffix.lower() in [".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"]:
                self.post_message(self.FileSelectedMessage(str(data.path)))

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle node selection — toggle folder or play file."""
        path = event.node.data.path if event.node.data else None
        if path is None:
            return
        if path.is_dir():
            event.node.toggle()
        elif path.suffix.lower() in [".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"]:
            self.post_message(self.FileSelectedMessage(str(path)))
