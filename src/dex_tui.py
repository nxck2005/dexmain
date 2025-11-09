import os
from textual.app import App
from .screens import DexScreen, SetupScreen
from .database import DB_PATH

__version__ = "1.0.0"
_current_dir = os.path.dirname(os.path.abspath(__file__))

class DexTUI(App):
    """The main application class."""

    CSS_PATH = os.path.join(_current_dir, "static", "dex.css")
    
    SCREENS = {
        "dex": DexScreen,
        "setup": SetupScreen,
    }

    def on_mount(self) -> None:
        """Called when the app is first mounted."""
        if os.path.exists(DB_PATH):
            self.push_screen("dex")
        else:
            self.push_screen("setup")

