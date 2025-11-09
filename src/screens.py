from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Static, Input, Log
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual.widget import Widget
from rich.text import Text
import os

from .backend import get_dex_entry, get_all_pokemon

# --- Helper Widgets ---

class DexEntryInfo(Static):
    """A widget to display the detailed information of a Pokémon."""
    def update_info(self, data: dict) -> None:
        if "error" in data:
            self.update(data["error"])
            return

        height_m = data.get('height', 0) / 10.0
        weight_kg = data.get('weight', 0) / 10.0

        info = (
            f"[bold]{data.get('name', 'Unknown')} (#{data.get('id', 'N/A')})[/bold]\n\n"
            f"Types: {', '.join(data.get('types', []))}\n"
            f"Abilities: {', '.join(data.get('abilities', []))}\n"
            f"Height: {height_m:.1f} m\n"
            f"Weight: {weight_kg:.1f} kg\n\n"
            "[bold]Stats:[/bold]\n"
        )
        stats = data.get("stats", {})
        for stat, value in stats.items():
            info += f"- {stat.replace('_', '-').capitalize()}: {value}\n"

        if data.get("flavor_text"):
            info += f"\n[bold]Dex Entry:[/bold]\n{data['flavor_text']}\n"

        self.update(info)


class ArtDisplay(Static):
    """A widget that displays ASCII art of a Pokémon."""
    pass

# --- Application Screens ---

class DexScreen(Screen):
    """The main screen of the Pokédex application."""
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("slash", "focus_search", "Search"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Search by name or ID...", id="search")
        yield Horizontal(
            DexEntryInfo(id="dex_entry"),
            ArtDisplay(id="art_display"),
            DataTable(id="pokemon_table"),
        )
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Name")
        self.run_worker(self.load_initial_data, exclusive=True, thread=True)

    def on_input_changed(self, message: Input.Changed) -> None:
        if not hasattr(self, "all_pokemon") or not self.all_pokemon:
            return

        table = self.query_one(DataTable)
        search_term = message.value.lower()

        table.clear()
        for pokemon in self.all_pokemon:
            if search_term in pokemon["name"].lower() or search_term == str(pokemon["id"]):
                table.add_row(pokemon["id"], pokemon["name"].capitalize())

    def on_input_submitted(self, message: Input.Submitted) -> None:
        table = self.query_one(DataTable)
        if table.row_count > 0:
            table.move_cursor(row=0)
            self.action_select_pokemon()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_select_pokemon()

    def action_select_pokemon(self) -> None:
        table = self.query_one(DataTable)
        if table.row_count == 0:
            return

        row_key = table.cursor_row
        row_data = table.get_row_at(row_key)
        if not row_data:
            return

        entry_id = row_data[0]
        self.query_one(DexEntryInfo).update("Loading...")
        
        art_widget = self.query_one(ArtDisplay)
        art_widget.update("")
        art_widget.refresh()

        self.run_worker(lambda: self.fetch_pokemon_data(entry_id), exclusive=True, thread=True)

    def action_focus_search(self) -> None:
        self.query_one("#search").focus()

    # --- Worker Methods ---
    def load_initial_data(self) -> None:
        pokemon_list = get_all_pokemon()
        self.app.call_from_thread(self.update_pokemon_table, pokemon_list)

    def fetch_pokemon_data(self, pokemon_id: int) -> None:
        data = get_dex_entry(pokemon_id)
        self.app.call_from_thread(self.update_dex_entry, data)

    # --- UI Update Methods ---
    def update_pokemon_table(self, pokemon_list: list[dict]) -> None:
        self.all_pokemon = pokemon_list
        table = self.query_one(DataTable)
        for pokemon in self.all_pokemon:
            table.add_row(pokemon["id"], pokemon["name"].capitalize())

    def update_dex_entry(self, data: dict) -> None:
        self.query_one(DexEntryInfo).update_info(data)
        
        art_widget = self.query_one(ArtDisplay)
        art_widget.update(Text(data.get("ascii_art", "")))
        art_widget.refresh()


class SetupScreen(Screen):
    """A screen to set up the application on the first run."""

    def compose(self) -> ComposeResult:
        yield Header()
        yield Log(id="setup_log", auto_scroll=True)
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one(Log)
        log.write_line("Welcome to the Pokédex!")
        log.write_line("The local database was not found.")
        log.write_line("Starting automatic setup... (This takes a little while, we're not frozen! Don't quit the app)")
        log.write_line("-" * 30)
        self.run_worker(self.run_setup_process, exclusive=True, thread=True)

    def on_setup_complete(self, return_code: int) -> None:
        """Called when the setup process worker is finished."""
        log = self.query_one(Log)
        log.write_line("-" * 30)
        if return_code == 0:
            log.write_line("[bold green]Setup complete![/bold green]")
            log.write_line("Please restart the application to begin.")
        else:
            log.write_line(f"[bold red]Setup failed with exit code: {return_code}[/bold red]")
            log.write_line("Please check the errors above.")
        log.write_line("You can now exit the app by pressing 'q'.")

    def run_setup_process(self) -> None:
        """Runs the data pipeline script as a subprocess and streams the output."""
        import subprocess

        log = self.query_one(Log)
        command = ["uv", "run", "data_pipeline.py", "--yes"]
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding='utf-8'
        )

        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                self.app.call_from_thread(log.write, line)
        
        process.wait()
        self.app.call_from_thread(self.on_setup_complete, process.returncode)

    def on_key(self, event) -> None:
        if event.key == "q":
            self.app.exit()
