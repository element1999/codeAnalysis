"""Main entry point for CodeMind CLI"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from codemind.cli.commands import app as cli_app
from codemind.core.logger import setup_logger

console = Console()
app = typer.Typer(
    name="codemind",
    help="AI-powered code understanding and documentation tool",
    add_completion=True,
)

# Setup logger
setup_logger()

# Import commands directly
from codemind.cli.commands import init, build, chat, status, clean, wiki, website

# Add commands
app.command()(init)
app.command()(build)
app.command()(chat)
app.command()(status)
app.command()(clean)
app.command()(wiki)
app.command()(website)

@app.callback()
def main():
    """CodeMind main entry point"""
    pass

@app.command()
def version():
    """Show CodeMind version"""
    from codemind import __version__
    version_text = Text(f"CodeMind v{__version__}", style="bold cyan")
    description = Text("AI-powered code understanding tool", style="green")
    panel = Panel.fit(
        version_text + "\n" + description,
        title="CodeMind",
        border_style="blue"
    )
    console.print(panel)

if __name__ == "__main__":
    app()