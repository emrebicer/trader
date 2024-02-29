from dataclasses import dataclass
from collections import deque
from typing import Dict

import time
import threading
import datetime

from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live

def make_layout() -> Layout:
    layout = Layout(name="root")

    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
    )
    layout["main"].split_column(
        Layout(name="live_data"),
        Layout(name="logs"),
    )
    layout["logs"].split_column(Layout(name="transaction_log"), Layout(name="program_log"))
    return layout

class Header:

    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right")
        grid.add_row(
            "[b magenta]Trader Bot[/b magenta]",
            f"[b blue]{datetime.datetime.now().ctime()}[/b blue]",
        )
        return Panel(grid, border_style="yellow")

@dataclass
class LiveDataInfo:
    owned: bool
    base_currency: str
    target_currency: str
    current_price: float
    last_operation_price: float
    difference: float
    indicator_signals: str
    last_updated: str

class LiveData:

    data_points: Dict[str, LiveDataInfo] = {}

    def update_data_points(self, points: Dict[str, LiveDataInfo] = {}):
        self.data_points = points

    def __rich__(self) -> Table:
        table = Table(expand=True)

        table.add_column("👾 Owned", style="magenta")
        table.add_column("Symbol", style="cyan")
        table.add_column("Current Price", style="magenta")
        table.add_column("Last Operation Price", style="cyan")
        table.add_column("Difference", style="magenta")
        table.add_column("Indicator Signals", style="cyan")
        table.add_column("Last Updated", style="magenta")

        for symbol, point in self.data_points.items():
            table.add_row("🚩 true" if point.owned else "➖ false", f"{point.base_currency}/{point.target_currency}", f"{point.current_price} {point.target_currency}", f"{point.last_operation_price} {point.target_currency}", f"{point.difference:.2f}%", f"{point.indicator_signals}", f"{point.last_updated}")

        return table


class TransactionLog:

    queue = deque([], maxlen = 30)

    def add_log(self, log: str, date = None):
        if date == None:
            date = datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')
        rich_text = Text.assemble((f"[{date}]: ", "bold cyan"), (f"{str(log)}", "blue"), "\n")
        self.queue.append(rich_text)

    def __rich__(self) -> Text:
        text = Text()

        for rich_log in reversed(self.queue):
            text.append(rich_log)

        return text

class ProgramLog:

    queue = deque([], maxlen = 30)

    def add_log(self, log: str):
        date = datetime.datetime.now().strftime('%Y.%m.%d - %H:%M:%S')
        rich_text = Text.assemble((f"[{date}]: ", "bold cyan"), (f"{str(log)}", "magenta"), "\n")
        self.queue.append(rich_text)

    def __rich__(self) -> Text:
        text = Text(justify="full")

        for rich_log in reversed(self.queue):
            text.append(rich_log)

        return text

class TUI:
    live_data = LiveData()
    transaction_log = TransactionLog()
    program_log = ProgramLog()

    def nonblocking_draw(self):
        thread = threading.Thread(target=self.draw)
        thread.daemon = True
        thread.start()

    def draw(self):
        layout = make_layout()
        layout["header"].update(Header())
        layout["live_data"].update(Panel(self.live_data, border_style="yellow", title="Live Data"))
        layout["transaction_log"].update(Panel(self.transaction_log, border_style="yellow", title="Transaction Log"))
        layout["program_log"].update(Panel(self.program_log, border_style="yellow", title="Program Log"))

        with Live(layout, auto_refresh=False, screen=True) as live:
            while True:
                live.update(layout, refresh=True)
                time.sleep(0.5)
