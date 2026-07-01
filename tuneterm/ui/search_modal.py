from textual.screen import ModalScreen
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option
from textual.containers import Vertical
from textual import work
from tuneterm.player.metadata import TrackInfo

class SearchModal(ModalScreen):
    BINDINGS = [("escape", "dismiss", "Dismiss")]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results = []

    def compose(self):
        with Vertical(id="search-container"):
            yield Input(placeholder="Search library...", id="search-input")
            yield OptionList(id="search-results")

    def on_input_changed(self, event: Input.Changed):
        self.perform_search(event.value)

    @work(thread=True, exclusive=True)
    def perform_search(self, query: str) -> None:
        if not query.strip():
            results = []
        else:
            if hasattr(self.app, 'library'):
                results = self.app.library.search(query)
            elif hasattr(self.app, 'query_library'):
                results = self.app.query_library(query)
            else:
                results = []
        
        def update_ui():
            self.results = results
            op_list = self.query_one(OptionList)
            op_list.clear_options()
            for idx, track in enumerate(results):
                op_list.add_option(Option(f"{track.title} - {track.artist}", id=str(idx)))
                
        self.app.call_from_thread(update_ui)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        idx = int(event.option.id)
        if 0 <= idx < len(self.results):
            track = self.results[idx]
            if hasattr(self.app, 'play_from_search'):
                self.app.play_from_search(track)
        self.action_dismiss()

    def action_dismiss(self):
        self.app.pop_screen()
