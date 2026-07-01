from textual.screen import ModalScreen
from textual.widgets import Input, Label
from textual.containers import Vertical
from textual import work

class AddUrlModal(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Cancel")]
    
    def compose(self):
        with Vertical(id="add-url-container", classes="modal-container"):
            yield Label("Paste URL (YouTube, Radio Stream, etc.):", id="add-url-label")
            yield Input(placeholder="https://...", id="url-input")
            yield Label("Press Enter to add, ESC to cancel", id="add-url-footer")
            
    def on_input_submitted(self, event: Input.Submitted):
        url = event.value.strip()
        if url:
            self.app.add_url_and_play(url)
        self.app.pop_screen()

    def action_dismiss(self):
        self.app.pop_screen()
