"""CLI commands implementation"""

import typer
import os
import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from codemind.config.manager import ConfigManager
from codemind.core.logger import logger
from codemind.parser.file_scanner import FileScanner
from codemind.parser.tree_sitter_parser import TreeSitterParser
from codemind.parser.symbol_extractor import SymbolExtractor
from codemind.parser.dependency_analyzer import DependencyAnalyzer
from codemind.parser.chunk_builder import ChunkBuilder
from codemind.parser.md5_cache import MD5Cache
from codemind.storage.manager import StorageManager

console = Console()
app = typer.Typer(
    name="codemind",
    help="CodeMind CLI commands",
)

@app.command()
def init(project_path: str = typer.Option(".", help="Project path"),
         debug: bool = typer.Option(True, "--debug/--no-debug", help="Enable debug mode")):
    """Initialize CodeMind project"""
    # Set logger level based on debug flag
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    console.print("[bold cyan]Initializing CodeMind project...[/bold cyan]")
    console.print(f"[blue]Debug mode:[/blue] {'Enabled' if debug else 'Disabled'}")
    console.print()
    
    try:
        config_manager = ConfigManager(project_path)
        config_manager.initialize()
        console.print("[green]✓ Project initialized successfully![/green]")
        console.print(f"[blue]Config file:[/blue] {config_manager.config_path}")
    except Exception as e:
        logger.error(f"Failed to initialize project: {e}")
        console.print(f"[red]✗ Failed: {e}[/red]")

@app.command()
def build(full: bool = typer.Option(False, "--full", help="Full rebuild"),
          docs_only: bool = typer.Option(False, "--docs-only", help="Only generate docs"),
          debug: bool = typer.Option(True, "--debug/--no-debug", help="Enable debug mode"),
          mock: bool = typer.Option(False, "--mock", help="Enable mock mode for LLM")):
    """Build documentation and indexes"""
    # Set logger level based on debug flag
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    console.print("[bold cyan]Building CodeMind project...[/bold cyan]")
    console.print(f"[blue]Debug mode:[/blue] {'Enabled' if debug else 'Disabled'}")
    console.print(f"[blue]Mock mode:[/blue] {'Enabled' if mock else 'Disabled'}")
    console.print()
    
    try:
        # Initialize components
        console.print("[bold blue]=== Initializing components ===[/bold blue]")
        config_manager = ConfigManager(".")
        storage_manager = StorageManager()
        md5_cache = MD5Cache()
        console.print("[green]✓ Components initialized[/green]")
        console.print()
        
        # Clear cache if full rebuild
        if full:
            console.print("[bold blue]=== Clearing cache (full rebuild) ===[/bold blue]")
            md5_cache.clear()
            storage_manager.clear_all()
            console.print("[green]✓ Cache cleared[/green]")
            console.print()
        
        # Step 1: Scan files
        console.print("[bold blue]=== Step 1: Scanning files ===[/bold blue]")
        file_scanner = FileScanner()
        files = file_scanner.scan()
        console.print(f"[green]✓ Found {len(files)} files to process[/green]")
        for file in files[:10]:  # Show first 10 files
            console.print(f"  - {file}")
        if len(files) > 10:
            console.print(f"  ... and {len(files) - 10} more files")
        console.print()
        
        # Step 2: Parse files
        console.print("[bold blue]=== Step 2: Parsing files ===[/bold blue]")
        parser = TreeSitterParser()
        symbol_extractor = SymbolExtractor()
        dependency_analyzer = DependencyAnalyzer()
        chunk_builder = ChunkBuilder()
        
        all_symbols = []
        all_chunks = []
        processed_files = 0
        updated_files = 0
        
        for file_path in files:
            processed_files += 1
            console.print(f"[cyan]Processing file {processed_files}/{len(files)}:[/cyan] {file_path}")
            
            # Check if file needs parsing
            if not md5_cache.needs_update(file_path):
                console.print("  [yellow]✓ Already up to date, skipping[/yellow]")
                continue
            
            updated_files += 1
            
            # Parse file
            console.print("  [blue]Parsing file...[/blue]")
            tree = parser.parse_file(file_path)
            if not tree:
                console.print("  [red]✗ Failed to parse[/red]")
                continue
            console.print("  [green]✓ Parsed successfully[/green]")
            
            # Extract symbols
            console.print("  [blue]Extracting symbols...[/blue]")
            symbols = symbol_extractor.extract_from_tree(tree, file_path)
            console.print(f"  [green]✓ Extracted {len(symbols)} symbols[/green]")
            all_symbols.extend(symbols)
            
            # Analyze dependencies
            console.print("  [blue]Analyzing dependencies...[/blue]")
            dependency_analyzer.analyze(symbols)
            console.print("  [green]✓ Dependencies analyzed[/green]")
            
            # Build chunks
            console.print("  [blue]Building chunks...[/blue]")
            chunks = chunk_builder.build_chunks(file_path, tree, symbols)
            console.print(f"  [green]✓ Built {len(chunks)} chunks[/green]")
            all_chunks.extend(chunks)
            
            # Update cache
            md5_cache.update(file_path)
            console.print()
        
        console.print(f"[bold green]✓ Parsing completed![/bold green]")
        console.print(f"  Total files: {len(files)}")
        console.print(f"  Updated files: {updated_files}")
        console.print(f"  Total symbols: {len(all_symbols)}")
        console.print(f"  Total chunks: {len(all_chunks)}")
        console.print()
        
        # Step 3: Save data
        console.print("[bold blue]=== Step 3: Saving data ===[/bold blue]")
        storage_manager.save_all(all_symbols, all_chunks)
        console.print("[green]✓ Data saved to storage[/green]")
        console.print()
        
        # Step 4: Generate docs if requested
        if docs_only:
            console.print("[bold blue]=== Step 4: Generating documentation ===[/bold blue]")
            console.print("[blue]This may take a while...[/blue]")
            console.print()
            
            from codemind.generator.manager import GeneratorManager
            from codemind.config.schemas import LLMConfig
            config = config_manager.load()
            
            # Create a copy of the LLM config and add mock flag
            llm_config_data = config.llm.model_dump()
            llm_config_data['mock'] = mock
            llm_config = LLMConfig(**llm_config_data)
            
            generator_manager = GeneratorManager(
                llm_config=llm_config,
                generator_config=config.generator
            )
            
            console.print("[cyan]Calling GeneratorManager.generate_docs()...[/cyan]")
            console.print(f"  Project path: .")
            console.print(f"  Storage path: {storage_manager.storage_path}")
            console.print(f"  LLM provider: {config.llm.provider}")
            console.print(f"  LLM model: {config.llm.model}")
            console.print(f"  Mock mode: {mock}")
            console.print()
            
            result = generator_manager.generate_docs(".", storage_manager.storage_path)
            
            console.print("[bold green]✓ Documentation generated![/bold green]")
            console.print(f"[blue]Wiki path:[/blue] {result.get('wiki_path', 'unknown')}")
            console.print(f"[blue]Total documents:[/blue] {result.get('total_documents', 0)}")
            console.print(f"[blue]Overview doc:[/blue] {result.get('overview', 'unknown')}")
            console.print(f"[blue]Architecture doc:[/blue] {result.get('architecture', 'unknown')}")
            console.print(f"[blue]Modules documented:[/blue] {result.get('modules', 0)}")
            console.print()
        
        console.print("[bold green]✓ Build completed successfully![/bold green]")
    except Exception as e:
        logger.error(f"Failed to build project: {e}")
        console.print(f"[red]✗ Failed: {e}[/red]")
        import traceback
        traceback.print_exc()

@app.command()
def chat(query: str = typer.Option(None, "--query", help="Query text"),
         interactive: bool = typer.Option(True, "--interactive", help="Interactive mode"),
         k: int = typer.Option(5, "--k", help="Number of results to retrieve"),
         debug: bool = typer.Option(True, "--debug/--no-debug", help="Enable debug mode"),
         mock: bool = typer.Option(False, "--mock", help="Enable mock mode for LLM")):
    """Start interactive chat"""
    # Set logger level based on debug flag
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    console.print("[bold cyan]Starting CodeMind chat...[/bold cyan]")
    console.print(f"[blue]Debug mode:[/blue] {'Enabled' if debug else 'Disabled'}")
    console.print(f"[blue]Mock mode:[/blue] {'Enabled' if mock else 'Disabled'}")
    console.print()
    
    try:
        # Initialize components
        config_manager = ConfigManager(".")
        config = config_manager.load()
        
        # Create a copy of the LLM config and add mock flag
        llm_config = config.llm.model_dump()
        llm_config['mock'] = mock
        
        from codemind.chat.manager import ChatManager
        chat_manager = ChatManager(
            llm_config=llm_config,
            embedding_config=config.embedding
        )
        
        if query:
            # Non-interactive mode
            console.print(f"[blue]Query:[/blue] {query}")
            result = chat_manager.chat(query, k=k)
            console.print("[bold green]Answer:[/bold green]")
            console.print(result["answer"])
            
            if result["sources"]:
                console.print("[bold blue]Sources:[/bold blue]")
                for i, source in enumerate(result["sources"]):
                    console.print(f"[blue]{i+1}.[/blue] Score: {source['score']:.2f}")
                    console.print(f"   File: {source.get('metadata', {}).get('file_path', 'unknown')}")
        else:
            # Interactive mode
            console.print("[green]✓ Chat session started![/green]")
            console.print("[blue]Type 'exit' to quit[/blue]")
            console.print()
            
            while True:
                try:
                    user_input = console.input("[bold cyan]You:[/bold cyan] ")
                    if user_input.lower() == 'exit':
                        break
                    
                    result = chat_manager.chat(user_input, k=k)
                    console.print("[bold green]CodeMind:[/bold green]")
                    console.print(result["answer"])
                    
                    if result["sources"]:
                        console.print("[bold blue]Sources:[/bold blue]")
                        for i, source in enumerate(result["sources"]):
                            console.print(f"[blue]{i+1}.[/blue] Score: {source['score']:.2f}")
                            console.print(f"   File: {source.get('metadata', {}).get('file_path', 'unknown')}")
                    console.print()
                except KeyboardInterrupt:
                    break
    except Exception as e:
        logger.error(f"Failed to start chat: {e}")
        console.print(f"[red]✗ Failed: {e}[/red]")

@app.command()
def status(debug: bool = typer.Option(True, "--debug/--no-debug", help="Enable debug mode")):
    """Check project status"""
    # Set logger level based on debug flag
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    console.print("[bold cyan]Checking project status...[/bold cyan]")
    console.print(f"[blue]Debug mode:[/blue] {'Enabled' if debug else 'Disabled'}")
    console.print()
    
    try:
        storage_manager = StorageManager()
        md5_cache = MD5Cache()
        
        # Load data from file
        symbols, chunks = storage_manager.load_from_file()
        
        # Get statistics
        cache_count = len(md5_cache.get_cache())
        symbol_count = len(symbols)
        chunk_count = len(chunks)
        chroma_stats = storage_manager.get_chroma_storage().get_stats()
        
        # Display status
        console.print("[bold blue]Project Status:[/bold blue]")
        console.print(f"[green]✓ Cache entries:[/green] {cache_count}")
        console.print(f"[green]✓ Symbols:[/green] {symbol_count}")
        console.print(f"[green]✓ Code chunks:[/green] {chunk_count}")
        console.print(f"[green]✓ ChromaDB entries:[/green] {chroma_stats.get('count', 0)}")
        
        if symbol_count == 0:
            console.print("[yellow]⚠ No data found. Run 'codemind build' to analyze the project.[/yellow]")
        
    except Exception as e:
        logger.error(f"Failed to check status: {e}")
        console.print(f"[red]✗ Failed: {e}[/red]")

@app.command()
def wiki(debug: bool = typer.Option(True, "--debug/--no-debug", help="Enable debug mode"),
         mock: bool = typer.Option(False, "--mock", help="Enable mock mode for LLM")):
    """Generate markdown documentation"""
    # Set logger level based on debug flag
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    console.print("[bold cyan]Generating markdown documentation...[/bold cyan]")
    console.print(f"[blue]Debug mode:[/blue] {'Enabled' if debug else 'Disabled'}")
    console.print(f"[blue]Mock mode:[/blue] {'Enabled' if mock else 'Disabled'}")
    console.print()
    
    try:
        # Initialize components
        console.print("[bold blue]=== Initializing components ===[/bold blue]")
        config_manager = ConfigManager(".")
        storage_manager = StorageManager()
        console.print("[green]✓ Components initialized[/green]")
        console.print()
        
        # Generate documentation
        console.print("[bold blue]=== Generating documentation ===[/bold blue]")
        console.print("[blue]This may take a while...[/blue]")
        console.print()
        
        from codemind.generator.manager import GeneratorManager
        from codemind.config.schemas import LLMConfig
        config = config_manager.load()
        
        # Create a copy of the LLM config and add mock flag
        llm_config_data = config.llm.model_dump()
        llm_config_data['mock'] = mock
        llm_config = LLMConfig(**llm_config_data)
        
        generator_manager = GeneratorManager(
            llm_config=llm_config,
            generator_config=config.generator
        )
        
        console.print("[cyan]Calling GeneratorManager.generate_docs()...[/cyan]")
        console.print(f"  Project path: .")
        console.print(f"  Storage path: {storage_manager.storage_path}")
        console.print(f"  LLM provider: {config.llm.provider}")
        console.print(f"  LLM model: {config.llm.model}")
        console.print(f"  Mock mode: {mock}")
        console.print()
        
        result = generator_manager.generate_docs(".", storage_manager.storage_path)
        
        console.print("[bold green]✓ Documentation generated![/bold green]")
        console.print(f"[blue]Wiki path:[/blue] {result.get('wiki_path', 'unknown')}")
        console.print(f"[blue]Total documents:[/blue] {result.get('total_documents', 0)}")
        console.print(f"[blue]Overview doc:[/blue] {result.get('overview', 'unknown')}")
        console.print(f"[blue]Architecture doc:[/blue] {result.get('architecture', 'unknown')}")
        console.print(f"[blue]Modules documented:[/blue] {result.get('modules', 0)}")
        console.print()
        
        console.print("[bold green]✓ Wiki documentation generated successfully![/bold green]")
    except Exception as e:
        logger.error(f"Failed to generate wiki documentation: {e}")
        console.print(f"[red]✗ Failed: {e}[/red]")
        import traceback
        traceback.print_exc()

@app.command()
def clean(cache: bool = typer.Option(False, "--cache", help="Clean cache only"),
          vectors: bool = typer.Option(False, "--vectors", help="Clean vectors only"),
          all: bool = typer.Option(False, "--all", help="Clean all"),
          debug: bool = typer.Option(True, "--debug/--no-debug", help="Enable debug mode")):
    """Clean cache and indexes"""
    # Set logger level based on debug flag
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    console.print("[bold cyan]Cleaning CodeMind project...[/bold cyan]")
    console.print(f"[blue]Debug mode:[/blue] {'Enabled' if debug else 'Disabled'}")
    console.print()
    
    try:
        storage_manager = StorageManager()
        md5_cache = MD5Cache()
        
        if all:
            # Clean everything
            md5_cache.clear()
            storage_manager.clear_all()
            console.print("[green]✓ All data cleaned![/green]")
        elif cache:
            # Clean only cache
            md5_cache.clear()
            console.print("[green]✓ Cache cleaned![/green]")
        elif vectors:
            # Clean only vectors
            storage_manager.get_chroma_storage().clear()
            console.print("[green]✓ Vectors cleaned![/green]")
        else:
            # Clean default (cache + files)
            md5_cache.clear()
            storage_manager.get_file_storage().clear()
            console.print("[green]✓ Cache and files cleaned![/green]")
            
    except Exception as e:
        logger.error(f"Failed to clean project: {e}")
        console.print(f"[red]✗ Failed: {e}[/red]")

@app.command()
def website(debug: bool = typer.Option(True, "--debug/--no-debug", help="Enable debug mode")):
    """Generate website from markdown documentation using Docusaurus"""
    # Set logger level based on debug flag
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    console.print("[bold cyan]Generating website from markdown documentation...[/bold cyan]")
    console.print(f"[blue]Debug mode:[/blue] {'Enabled' if debug else 'Disabled'}")
    console.print()
    
    try:
        # Initialize components
        console.print("[bold blue]=== Initializing components ===[/bold blue]")
        config_manager = ConfigManager(".")
        console.print("[green]✓ Components initialized[/green]")
        console.print()
        
        # Check if wiki documentation exists
        wiki_path = ".codemind/wiki"
        if not os.path.exists(wiki_path):
            console.print("[yellow]⚠ Wiki documentation not found![/yellow]")
            console.print("[blue]Please run 'codemind wiki' first to generate markdown documentation.[/blue]")
            console.print()
            return
        
        # Generate VitePress website
        console.print("[bold blue]=== Generating VitePress website ===[/bold blue]")
        console.print("[blue]This may take a while...[/blue]")
        console.print()
        
        from codemind.generator.website_generator import WebsiteGenerator
        config = config_manager.load()
        
        website_generator = WebsiteGenerator()
        result = website_generator.generate_website(wiki_path)
        
        console.print("[bold green]✓ Website generated successfully![/bold green]")
        console.print(f"[blue]Website path:[/blue] {result.get('website_path', 'unknown')}")
        console.print(f"[blue]Build output:[/blue] {result.get('build_output', 'unknown')}")
        console.print()
        
        console.print("[bold blue]=== How to view the website ===[/bold blue]")
        console.print("[green]1. Serve the website locally:[/green]")
        console.print("   cd website && npm run dev")
        console.print()
        console.print("[green]2. Open your browser:[/green]")
        console.print("   http://localhost:5173")
        console.print()
        console.print("[green]3. For production build:[/green]")
        console.print("   cd website && npm run build")
        console.print()
        
        # Start the development server and open browser
        console.print("[bold blue]=== Starting development server ===[/bold blue]")
        console.print("[blue]Starting server and opening browser...[/blue]")
        console.print()
        
        # Use WebsiteGenerator's method to start server and open browser
        server_process = website_generator.start_server_and_open_browser()
        
        console.print("[yellow]Waiting for server to start...[/yellow]")
        console.print()
        console.print("[bold green]✓ Development server started![/bold green]")
        console.print("[green]✓ Browser opened to:[/green] http://localhost:3000")
        console.print()
        console.print("[blue]To stop the server, press Ctrl+C in the terminal.[/blue]")
        
    except Exception as e:
        logger.error(f"Failed to generate website: {e}")
        console.print(f"[red]✗ Failed: {e}[/red]")
        import traceback
        traceback.print_exc()