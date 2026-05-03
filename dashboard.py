"""
Dashboard module for terminal UI display.

Provides rich terminal formatting for real-time trading dashboard.
"""

import os
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from utils import format_currency, format_percentage

console = Console()


class Dashboard:
    """Manages terminal UI for the trading system."""
    
    @staticmethod
    def clear_screen():
        """Clear the terminal screen."""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    @staticmethod
    def show_header(title: str = "NIFTY50 OPTIONS TRADING SYSTEM"):
        """
        Display the application header.
        
        Args:
            title: Title to display
        """
        Dashboard.clear_screen()
        header = Panel(
            Text(title, justify="center", style="bold cyan"),
            style="bold white on blue"
        )
        console.print(header)
        console.print()
    
    @staticmethod
    def show_idle_state(nifty_price: Optional[float] = None):
        """
        Display idle state waiting for user input.
        
        Args:
            nifty_price: Current NIFTY spot price
        """
        Dashboard.show_header()
        
        if nifty_price:
            price_text = Text(f"Current NIFTY 50: {nifty_price:.2f}", style="bold yellow")
            console.print(Panel(price_text, title="Live Price", border_style="yellow"))
            console.print()
        
        console.print("📊 System is monitoring market prices", style="cyan")
        console.print("⏳ Press [bold green]ENTER[/bold green] to designate Entry Candle", style="cyan")
        console.print()
    
    @staticmethod
    def show_entry_candle(high: float, low: float):
        """
        Display entry candle details.
        
        Args:
            high: Entry candle high
            low: Entry candle low
        """
        table = Table(show_header=True, header_style="bold magenta", border_style="magenta")
        table.add_column("Entry Candle High", justify="right", style="green")
        table.add_column("Entry Candle Low", justify="right", style="red")
        
        table.add_row(f"{high:.2f}", f"{low:.2f}")
        
        console.print()
        console.print(Panel(table, title="📌 Entry Candle Set", border_style="magenta"))
        console.print("⏳ Waiting for breakout...", style="yellow")
        console.print()
    
    @staticmethod
    def show_breakout_monitoring(
        direction: str,
        entry_candle_high: float,
        entry_candle_low: float,
        entry_candle_start,
        entry_candle_end,
        current_price: Optional[float] = None
    ):
        """
        Display breakout monitoring dashboard.

        Args:
            direction: 'CALL' or 'PUT'
            entry_candle_high: Entry candle high
            entry_candle_low: Entry candle low
            entry_candle_start: Entry candle start time
            entry_candle_end: Entry candle end time
            current_price: Current NIFTY price
        """
        Dashboard.clear_screen()

        # Header
        direction_style = "bold green" if direction == "CALL" else "bold red"
        header = Panel(
            Text(f"MONITORING {direction} BREAKOUT", justify="center", style=direction_style),
            style="bold white on blue"
        )
        console.print(header)
        console.print()

        # Entry candle info
        candle_text = f"Entry Candle ({entry_candle_start.strftime('%H:%M:%S')} - {entry_candle_end.strftime('%H:%M:%S')}):"
        console.print(candle_text, style="bold cyan")
        console.print(f"  High: {entry_candle_high:,.2f}", style="green")
        console.print(f"  Low:  {entry_candle_low:,.2f}", style="red")
        console.print()

        # Direction and trigger
        console.print(f"Direction: {direction}", style=direction_style)

        if direction == "CALL":
            trigger_text = f"Breakout Trigger: Price > {entry_candle_high:,.2f}"
            trigger_style = "bold green"
        else:
            trigger_text = f"Breakout Trigger: Price < {entry_candle_low:,.2f}"
            trigger_style = "bold red"

        console.print(trigger_text, style=trigger_style)

        if current_price:
            console.print(f"Current NIFTY: {current_price:,.2f}", style="bold yellow")

        console.print()
        console.print("⏳ Waiting for breakout...", style="cyan")
        console.print()

        # Cancellation instruction
        cancel_panel = Panel(
            "[bold yellow]Type 'Q' and press ENTER to cancel monitoring[/bold yellow]",
            border_style="yellow",
            padding=(0, 1)
        )
        console.print(cancel_panel)

    @staticmethod
    def show_breakout(direction: str, spot_price: float, trigger_level: float):
        """
        Display breakout notification.

        Args:
            direction: 'CALL' or 'PUT'
            spot_price: Current spot price
            trigger_level: Breakout trigger level
        """
        console.print()
        style = "bold green" if direction == "CALL" else "bold red"
        console.print(f"🚀 BREAKOUT DETECTED: {direction}", style=style)
        console.print(f"   Spot Price: {spot_price:.2f}")
        console.print(f"   Trigger Level: {trigger_level:.2f}")
        console.print()
    
    @staticmethod
    def show_position_dashboard(
        direction: str,
        quantity_lots: int,
        quantity_units: int,
        entry_price: float,
        current_price: float,
        stop_loss: float,
        target: float,
        pnl: float,
        return_pct: float,
        trading_symbol: str = ""
    ):
        """
        Display active position dashboard.
        
        Args:
            direction: 'CALL' or 'PUT'
            quantity_lots: Number of lots
            quantity_units: Total units
            entry_price: Entry premium price
            current_price: Current premium price
            stop_loss: Stop loss price
            target: Target price
            pnl: Unrealized P&L
            return_pct: Return percentage
            trading_symbol: Option trading symbol
        """
        Dashboard.clear_screen()
        
        # Header
        header_text = "ACTIVE POSITION DASHBOARD"
        header = Panel(
            Text(header_text, justify="center", style="bold white"),
            style="bold white on blue"
        )
        console.print(header)
        console.print()
        
        # Position details
        table = Table(show_header=False, border_style="cyan", padding=(0, 2))
        table.add_column("Label", style="cyan", width=20)
        table.add_column("Value", style="yellow")
        
        direction_style = "bold green" if direction == "CALL" else "bold red"
        table.add_row("Direction", Text(direction, style=direction_style))
        
        if trading_symbol:
            table.add_row("Instrument", trading_symbol)
        
        table.add_row("Quantity", f"{quantity_lots} Lots ({quantity_units} units)")
        table.add_row("Entry Price", format_currency(entry_price))
        table.add_row("Current Price", format_currency(current_price))
        table.add_row("Stop Loss", format_currency(stop_loss))
        table.add_row("Target", format_currency(target))
        
        # P&L styling
        pnl_style = "bold green" if pnl >= 0 else "bold red"
        return_style = "bold green" if return_pct >= 0 else "bold red"
        
        table.add_row("Return %", Text(format_percentage(return_pct), style=return_style))
        table.add_row("P&L (Unrealized)", Text(format_currency(pnl), style=pnl_style))
        
        console.print(table)
        console.print()

        # Instructions
        instructions = Panel(
            "[bold cyan]'M' + ENTER: Modify Stop Loss | 'T' + ENTER: Modify Target | 'Q' + ENTER: Force Exit[/bold cyan]",
            border_style="yellow",
            padding=(0, 1)
        )
        console.print(instructions)
    
    @staticmethod
    def show_trade_summary(
        direction: str,
        entry_price: float,
        exit_price: float,
        exit_reason: str,
        pnl: float,
        return_pct: float,
        trading_symbol: str = ""
    ):
        """
        Display trade summary after exit.
        
        Args:
            direction: 'CALL' or 'PUT'
            entry_price: Entry price
            exit_price: Exit price
            exit_reason: Reason for exit
            pnl: Final P&L
            return_pct: Return percentage
            trading_symbol: Option trading symbol
        """
        Dashboard.clear_screen()
        
        # Header
        header = Panel(
            Text("TRADE SUMMARY", justify="center", style="bold white"),
            style="bold white on blue"
        )
        console.print(header)
        console.print()
        
        # Summary table
        table = Table(show_header=False, border_style="cyan", padding=(0, 2))
        table.add_column("Label", style="cyan", width=20)
        table.add_column("Value", style="yellow")
        
        direction_style = "bold green" if direction == "CALL" else "bold red"
        table.add_row("Direction", Text(direction, style=direction_style))
        
        if trading_symbol:
            table.add_row("Instrument", trading_symbol)
        
        table.add_row("Entry Price", format_currency(entry_price))
        table.add_row("Exit Price", format_currency(exit_price))
        table.add_row("Exit Reason", exit_reason)
        
        pnl_style = "bold green" if pnl >= 0 else "bold red"
        return_style = "bold green" if return_pct >= 0 else "bold red"
        
        table.add_row("Total P&L", Text(format_currency(pnl), style=pnl_style))
        table.add_row("Return %", Text(format_percentage(return_pct), style=return_style))
        
        console.print(table)
        console.print()
        
        # Footer
        console.print("[bold yellow]Press ENTER to return to Idle State...[/bold yellow]")
        console.print()
