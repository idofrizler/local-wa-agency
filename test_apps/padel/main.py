#!/usr/bin/env python3
"""
WhatsApp Padel Match Tracker
Main entry point for scanning WhatsApp groups and finding padel game matches.
"""
import sys
import time
import asyncio
import argparse
from pathlib import Path
from typing import List
from colorama import Fore, Style

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.config import config, ScenarioDefinition
from src.agent import get_agent_for_scenario
from test_apps.padel import MatchDisplayWindow, MatchTracker, Match
from src.whatsapp_scanner import WhatsAppScanner, Message

def print_banner():
    """Print application banner."""
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{'WhatsApp Padel Match Tracker':^80}")
    print(f"{'='*80}{Style.RESET_ALL}\n")

def print_config_info():
    """Print configuration information."""
    print(f"{Fore.YELLOW}Configuration:{Style.RESET_ALL}")
    print(f"  Ollama URL: {config.ollama_base_url}")
    print(f"  Model: {config.ollama_model}")
    print(f"  User Level: {config.user_preferences.level}")
    print(f"  Time Window: {config.user_preferences.time_window[0]}:00-{config.user_preferences.time_window[1]}:00")
    print()

async def analyze_messages(messages: List[Message], group_name: str, scenario: ScenarioDefinition, tracker: MatchTracker, gui_window=None):
    """
    Analyze messages with AI agent and add matches to tracker.
    
    Args:
        messages: List of messages to analyze
        group_name: Name of the WhatsApp group
        scenario: ScenarioDefinition guiding the analysis
        tracker: MatchTracker instance to store matches
        gui_window: Optional GUI window to update with matches
    """
    if not messages:
        return
    
    agent = get_agent_for_scenario(scenario)
    
    print(f"\n{Fore.CYAN}Analyzing {len(messages)} messages from {group_name}...{Style.RESET_ALL}")
    
    for i, msg in enumerate(messages, 1):
        print(f"  [{i}/{len(messages)}] Analyzing message from {msg.sender}...", end="\r")
        
        try:
            analysis = await agent.analyze_message(msg.text)
            if analysis is None:
                continue
            
            # Check if this is a game invite
            if analysis.is_game_invite:
                match = Match(
                    timestamp=msg.timestamp,
                    group_name=group_name,
                    sender=msg.sender,
                    phone_number=msg.phone_number,
                    message=msg.text,
                    confidence=analysis.confidence,
                    analysis=analysis
                )
                tracker.add_match(match)
                
                if gui_window:
                    gui_window.add_match(match)
                    gui_window.update()
                
                color = tracker.get_confidence_color(analysis.confidence)
                symbol = tracker.get_confidence_symbol(analysis.confidence)
                print(f"  [{i}/{len(messages)}] {color}MATCH FOUND{Style.RESET_ALL} "
                      f"({analysis.confidence} {symbol}) - {msg.sender}")
        
        except Exception as e:
            print(f"  [{i}/{len(messages)}] Error analyzing message: {str(e)}")
    
    print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Analysis complete for {group_name}")

async def scan_history_mode(groups: List[str], scroll_count: int):
    """Scan historical messages from groups."""
    print(f"{Fore.YELLOW}Mode: Historical Scan{Style.RESET_ALL}")
    print(f"Groups to scan: {', '.join(groups)}")
    print(f"Scroll count: {scroll_count}\n")
    
    scanner = WhatsAppScanner()
    tracker = MatchTracker()
    gui_window = MatchDisplayWindow(title="סריקת היסטוריה - מציאת משחקי פאדל")
    
    try:
        await scanner.start()
        
        for group in groups:
            scenario = config.get_scenario_for_group(group)
            if not scenario or scenario.name != 'padel':
                continue
            messages = await scanner.scan_group_history(group, scroll_count)
            await analyze_messages(messages, group, scenario, tracker, gui_window)
        
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Scan complete! Opening results window...{Style.RESET_ALL}")
        print(f"Total matches found: {tracker.count()}")
        
        gui_window.show()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Scan interrupted by user.{Style.RESET_ALL}")
        gui_window.destroy()
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        gui_window.destroy()
    finally:
        await scanner.cleanup()

async def monitor_live_mode(groups: List[str], interval: int):
    """Monitor groups for new messages in real-time."""
    print(f"{Fore.YELLOW}Mode: Live Monitoring{Style.RESET_ALL}")
    print(f"Groups to monitor: {', '.join(groups)}")
    print(f"Check interval: {interval} seconds")
    print(f"Press Ctrl+C to stop\n")
    
    scanner = WhatsAppScanner()
    tracker = MatchTracker()
    gui_window = MatchDisplayWindow(title="ניטור חי - מציאת משחקי פאדל")
    
    try:
        await scanner.start()
        
        print(f"{Fore.CYAN}Loading existing messages...{Style.RESET_ALL}")
        for group in groups:
            messages = await scanner.scan_group_history(group, scroll_count=3)
            for msg in messages:
                msg_id = scanner._get_message_id(msg)
                scanner.seen_message_ids.add(msg_id)
        
        print(f"{Fore.GREEN}✓ Loaded existing messages. Now monitoring...{Style.RESET_ALL}\n")
        
        check_count = 0
        while True:
            check_count += 1
            print(f"\n{Fore.CYAN}Check #{check_count} - {time.strftime('%H:%M:%S')}{Style.RESET_ALL}")
            
            for group in groups:
                scenario = config.get_scenario_for_group(group)
                if not scenario or scenario.name != 'padel':
                    continue
                new_messages = await scanner.scan_group_new_messages(group)
                
                if new_messages:
                    print(f"  Found {len(new_messages)} new message(s) in {group}")
                    await analyze_messages(new_messages, group, scenario, tracker, gui_window)
                else:
                    print(f"  No new messages in {group}")
            
            try:
                gui_window.update()
            except:
                print(f"\n{Fore.YELLOW}Window closed by user. Stopping...{Style.RESET_ALL}")
                break
            
            print(f"  Waiting {interval} seconds...")
            await asyncio.sleep(interval)
    
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Monitoring stopped by user.{Style.RESET_ALL}")
        gui_window.destroy()
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        gui_window.destroy()
    finally:
        await scanner.cleanup()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="WhatsApp Padel Match Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'mode',
        choices=['scan-history', 'monitor-live'],
        help='Scanning mode'
    )
    
    parser.add_argument('--scrolls', type=int, default=5)
    parser.add_argument('--interval', type=int, default=60)
    
    args = parser.parse_args()
    
    print_banner()
    print_config_info()
    
    # Get only padel groups
    try:
        padel_groups = []
        for group, scenario in config.group_to_scenario.items():
            if scenario.name == 'padel':
                padel_groups.append(group)
        
        if not padel_groups:
            print(f"{Fore.RED}No padel groups configured!{Style.RESET_ALL}")
            sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Configuration Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)
    
    try:
        if args.mode == 'scan-history':
            asyncio.run(scan_history_mode(padel_groups, args.scrolls))
        elif args.mode == 'monitor-live':
            asyncio.run(monitor_live_mode(padel_groups, args.interval))
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
