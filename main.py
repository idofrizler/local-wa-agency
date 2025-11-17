#!/usr/bin/env python3
"""
WhatsApp Multi-Scenario Group Monitor
Generic main entry point that outputs structured insights from all configured scenarios.
"""
import sys
import asyncio
import argparse
import json
from typing import List
from colorama import Fore, Style, init

from src.config import config, ScenarioDefinition
from src.agent import get_agent_for_scenario
from src.whatsapp_scanner import WhatsAppScanner, Message

# Initialize colorama
init(autoreset=True)

def print_banner():
    """Print application banner."""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{'WhatsApp Multi-Scenario Group Monitor':^80}")
    print(f"{'='*80}{Style.RESET_ALL}\n")

async def analyze_messages(messages: List[Message], group_name: str, scenario: ScenarioDefinition, limit: int = None):
    """
    Analyze messages with AI agent and return structured results.
    
    Args:
        messages: List of messages to analyze
        group_name: Name of the WhatsApp group
        scenario: ScenarioDefinition guiding the analysis
        limit: Maximum number of messages to analyze (None for no limit)
        
    Returns:
        List of analysis results (Pydantic model instances)
    """
    if not messages:
        return []
    
    # Apply limit if specified
    if limit and limit > 0:
        messages = messages[:limit]
    
    agent = get_agent_for_scenario(scenario)
    results = []
    
    print(f"\n{Fore.CYAN}Analyzing {len(messages)} messages from {group_name} "
          f"(scenario: {scenario.name})...{Style.RESET_ALL}")
    
    for i, msg in enumerate(messages, 1):
        print(f"  [{i}/{len(messages)}] Analyzing message from {msg.sender}...", end="\r")
        
        try:
            analysis = await agent.analyze_message(msg.text)
            if analysis is None:
                continue
            
            # Create result dict with message context and analysis
            result = {
                "message": {
                    "timestamp": msg.timestamp,
                    "group_name": group_name,
                    "sender": msg.sender,
                    "phone_number": msg.phone_number,
                    "text": msg.text
                },
                "scenario": scenario.name,
                "analysis": analysis.model_dump()
            }
            results.append(result)
            
            # Get confidence for colored output
            confidence = getattr(analysis, scenario.confidence_field, "N/A")
            confidence_color = {
                "HIGH": Fore.GREEN,
                "MEDIUM": Fore.YELLOW,
                "LOW": Fore.RED
            }.get(str(confidence), Fore.WHITE)
            
            print(f"  [{i}/{len(messages)}] {confidence_color}Analyzed{Style.RESET_ALL} "
                  f"(confidence: {confidence}) - {msg.sender}")
        
        except Exception as e:
            print(f"  [{i}/{len(messages)}] {Fore.RED}Error:{Style.RESET_ALL} {str(e)}")
    
    print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Analysis complete for {group_name}")
    return results

async def scan_groups(groups: List[str], scroll_count: int, output_format: str = "json", limit: int = None):
    """
    Scan groups and output structured insights.
    
    Args:
        groups: List of group names to scan
        scroll_count: Number of times to scroll up in each group
        output_format: Output format ('json' or 'pretty')
        limit: Maximum number of messages to analyze per group (None for no limit)
    """
    print(f"{Fore.YELLOW}Scanning {len(groups)} group(s)...{Style.RESET_ALL}")
    print(f"Scroll count: {scroll_count}\n")
    
    scanner = WhatsAppScanner()
    all_results = []
    
    try:
        await scanner.start()
        
        # Scan each group
        for group in groups:
            try:
                scenario = config.get_scenario_for_group(group)
                if not scenario:
                    print(f"{Fore.YELLOW}⚠ Warning: No scenario configured for group '{group}', skipping{Style.RESET_ALL}\n")
                    continue
                    
                messages = await scanner.scan_group_history(group, scroll_count)
                results = await analyze_messages(messages, group, scenario, limit)
                all_results.extend(results)
            
            except ValueError as e:
                # Group not found or couldn't be opened
                print(f"{Fore.YELLOW}⚠ Skipping group '{group}': {str(e)}{Style.RESET_ALL}\n")
                continue
            
            except Exception as e:
                # Other errors - log and continue
                print(f"{Fore.RED}✗ Error processing group '{group}': {str(e)}{Style.RESET_ALL}\n")
                continue
        
        # Output results
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Scan complete!{Style.RESET_ALL}")
        print(f"Total insights extracted: {len(all_results)}\n")
        
        if output_format == "json":
            print(json.dumps(all_results, indent=2, ensure_ascii=False))
        else:
            # Pretty print
            for result in all_results:
                print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Group:{Style.RESET_ALL} {result['message']['group_name']}")
                print(f"{Fore.YELLOW}Sender:{Style.RESET_ALL} {result['message']['sender']} ({result['message']['timestamp']})")
                print(f"{Fore.YELLOW}Scenario:{Style.RESET_ALL} {result['scenario']}")
                print(f"\n{Fore.YELLOW}Analysis:{Style.RESET_ALL}")
                for key, value in result['analysis'].items():
                    print(f"  {key}: {value}")
                print()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Scan interrupted by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
    finally:
        await scanner.cleanup()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="WhatsApp Multi-Scenario Group Monitor - Extract structured insights from WhatsApp groups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Scan all configured groups:
    python main.py --scrolls 5
  
  Output as pretty-printed text:
    python main.py --scrolls 5 --output pretty
  
  Scan specific groups:
    python main.py --scrolls 5 --groups "Group 1" "Group 2"
        """
    )
    
    parser.add_argument(
        '--scrolls',
        type=int,
        default=5,
        help='Number of times to scroll up when loading history (default: 5)'
    )
    
    parser.add_argument(
        '--output',
        choices=['json', 'pretty'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.add_argument(
        '--groups',
        nargs='+',
        help='Specific groups to scan (default: all configured groups)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of messages to analyze per group (default: no limit)'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    print(f"{Fore.YELLOW}Configuration:{Style.RESET_ALL}")
    print(f"  Ollama URL: {config.ollama_base_url}")
    print(f"  Model: {config.ollama_model}")
    print(f"  Scenarios loaded: {len(config.scenario_definitions)}")
    print()
    
    # Load groups
    try:
        if args.groups:
            groups = args.groups
            # Verify they're configured
            for group in groups:
                if group not in config.group_to_scenario:
                    print(f"{Fore.YELLOW}Warning: Group '{group}' not found in configuration{Style.RESET_ALL}")
        else:
            groups = config.load_groups()
    except ValueError as e:
        print(f"{Fore.RED}Configuration Error:{Style.RESET_ALL}")
        print(f"  {str(e)}")
        print(f"\nPlease add scenario JSON files to {config.scenarios_dir}")
        sys.exit(1)
    
    # Run scan
    try:
        asyncio.run(scan_groups(groups, args.scrolls, args.output, args.limit))
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
