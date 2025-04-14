#!/usr/bin/env python3
"""
Wrapper script for the Recipe Substitution Search System.
This script provides a simple interface to run the system components.
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))


def run_command(command, shell=False):
    """Run a command and print output."""
    try:
        if shell:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT, universal_newlines=True)
        else:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, 
                                     stderr=subprocess.STDOUT, universal_newlines=True)
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end="")
        
        # Wait for process to complete
        process.wait()
        
        return process.returncode
        
    except Exception as e:
        print(f"Error running command: {e}")
        return 1


def init(args):
    """Initialize the system."""
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts/initialize_system.py")]
    
    if args.force:
        cmd.append("--force")
    
    if args.count:
        cmd.extend(["--count", str(args.count)])
    
    return run_command(cmd)


def search(args):
    """Run search."""
    cmd = [sys.executable, str(PROJECT_ROOT / "src/main.py"), "search"]
    
    if args.query:
        cmd.append(args.query)
    else:
        # If no query provided, run in interactive mode
        cmd = [sys.executable, str(PROJECT_ROOT / "src/main.py")]
    
    if args.basic:
        cmd.append("--basic")
    
    if args.results:
        cmd.extend(["--results", str(args.results)])
    
    if args.details:
        cmd.append("--details")
    
    return run_command(cmd)


def collect(args):
    """Run data collection."""
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts/data_collector.py"), "collect"]
    
    if args.query:
        cmd.extend(["--query", args.query])
    
    return run_command(cmd)


def annotate(args):
    """Run annotation."""
    if not args.query:
        print("Error: Query is required for annotation.")
        return 1
    
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts/data_collector.py"), 
           "annotate", "--query", args.query]
    
    return run_command(cmd)


def generate(args):
    """Generate dummy data."""
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts/data_collector.py"), "generate"]
    
    if args.count:
        cmd.extend(["--count", str(args.count)])
    
    return run_command(cmd)


def evaluate(args):
    """Run evaluation."""
    cmd = [sys.executable, str(PROJECT_ROOT / "src/evaluation/run_evaluation.py")]
    
    if args.no_plots:
        cmd.append("--no-plots")
    
    if args.output:
        cmd.extend(["--output", args.output])
    
    return run_command(cmd)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Recipe Substitution Search System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize the system")
    init_parser.add_argument("--force", action="store_true", 
                           help="Force reset of the system")
    init_parser.add_argument("--count", type=int, default=50, 
                           help="Number of dummy recipes to create")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for recipes")
    search_parser.add_argument("query", nargs="?", help="Search query")
    search_parser.add_argument("--basic", action="store_true", 
                             help="Use basic search engine")
    search_parser.add_argument("--results", type=int, default=5, 
                             help="Number of results to display")
    search_parser.add_argument("--details", action="store_true", 
                             help="Show full recipe details")
    
    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Collect recipe data")
    collect_parser.add_argument("--query", type=str, 
                              help="Query for collection (or interactive mode if not provided)")
    
    # Annotate command
    annotate_parser = subparsers.add_parser("annotate", help="Annotate search results")
    annotate_parser.add_argument("--query", type=str, required=True, 
                               help="Query for annotation")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate dummy data")
    generate_parser.add_argument("--count", type=int, default=50, 
                               help="Number of dummy recipes to create")
    
    # Evaluate command
    evaluate_parser = subparsers.add_parser("evaluate", help="Run system evaluation")
    evaluate_parser.add_argument("--no-plots", action="store_true", 
                               help="Disable plot generation")
    evaluate_parser.add_argument("--output", type=str, 
                               help="Directory for output files")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle default command
    if not args.command:
        parser.print_help()
        return 0
    
    # Dispatch to appropriate function
    command_functions = {
        "init": init,
        "search": search,
        "collect": collect,
        "annotate": annotate,
        "generate": generate,
        "evaluate": evaluate
    }
    
    if args.command in command_functions:
        return command_functions[args.command](args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main()) 