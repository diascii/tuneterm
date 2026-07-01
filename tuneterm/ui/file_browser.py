from textual.widgets import DirectoryTree
from textual.message import Message

class FileBrowser(DirectoryTree):
    class FileSelectedMessage(Message):
        def __init__(self, filepath: str) -> None:
            self.filepath = filepath
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(".", *args, **kwargs)
        
    def load_directory(self, path: str):
        self.path = path
        self.reload()

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        if event.path.is_file():
            if event.path.suffix.lower() in [".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"]:
                self.post_message(self.FileSelectedMessage(str(event.path)))
