#!/usr/bin/env python3
"""
WhatsApp Padel Match Tracker
Main entry point for scanning WhatsApp groups and finding padel game matches.
"""
import sys
import time
import asyncio
import argparse
from typing import List
from colorama import Fore, Style

from src.config import config
from src.agent import get_agent
from src.match_tracker import MatchTracker
from src.whatsapp_scanner import WhatsAppScanner, Message
from src.models import Match, ScanMode
from src.gui_display import MatchDisplayWindow

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

async def analyze_messages(messages: List[Message], group_name: str, tracker: MatchTracker, gui_window=None):
    """
    Analyze messages with AI agent and add matches to tracker.
    
    Args:
        messages: List of messages to analyze
        group_name: Name of the WhatsApp group
        tracker: MatchTracker instance to store matches
        gui_window: Optional GUI window to update with matches
    """
    if not messages:
        return
    
    agent = get_agent()
    await agent.initialize()
    
    print(f"\n{Fore.CYAN}Analyzing {len(messages)} messages from {group_name}...{Style.RESET_ALL}")
    
    for i, msg in enumerate(messages, 1):
        print(f"  [{i}/{len(messages)}] Analyzing message from {msg.sender}...", end="\r")
        
        try:
            analysis = await agent.analyze_message(msg.text)
            
            if analysis and analysis.is_game_invite:
                # Only track if it's actually a game invite
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
                
                # Add to GUI if provided
                if gui_window:
                    gui_window.add_match(match)
                    gui_window.update()
                
                # Show immediate feedback for matches
                color = tracker.get_confidence_color(analysis.confidence)
                symbol = tracker.get_confidence_symbol(analysis.confidence)
                print(f"  [{i}/{len(messages)}] {color}MATCH FOUND{Style.RESET_ALL} ({analysis.confidence} {symbol}) - {msg.sender}")
        
        except Exception as e:
            print(f"  [{i}/{len(messages)}] Error analyzing message: {str(e)}")
    
    print(f"  {Fore.GREEN}✓{Style.RESET_ALL} Analysis complete for {group_name}")

async def scan_history_mode(groups: List[str], scroll_count: int):
    """
    Scan historical messages from groups.
    
    Args:
        groups: List of group names to scan
        scroll_count: Number of times to scroll up in each group
    """
    print(f"{Fore.YELLOW}Mode: Historical Scan{Style.RESET_ALL}")
    print(f"Groups to scan: {', '.join(groups)}")
    print(f"Scroll count: {scroll_count}\n")
    
    scanner = WhatsAppScanner()
    tracker = MatchTracker()
    
    # Create GUI window
    gui_window = MatchDisplayWindow(title="סריקת היסטוריה - מציאת משחקי פאדל")
    
    try:
        await scanner.start()
        
        # Scan each group
        for group in groups:
            messages = await scanner.scan_group_history(group, scroll_count)
            await analyze_messages(messages, group, tracker, gui_window)
        
        # Show console summary
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Scan complete! Opening results window...{Style.RESET_ALL}")
        print(f"Total matches found: {tracker.count()}")
        
        # Show GUI window (blocks until closed)
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
    """
    Monitor groups for new messages in real-time.
    
    Args:
        groups: List of group names to monitor
        interval: Seconds between checks
    """
    print(f"{Fore.YELLOW}Mode: Live Monitoring{Style.RESET_ALL}")
    print(f"Groups to monitor: {', '.join(groups)}")
    print(f"Check interval: {interval} seconds")
    print(f"Press Ctrl+C to stop\n")
    
    scanner = WhatsAppScanner()
    tracker = MatchTracker()
    
    # Create GUI window
    gui_window = MatchDisplayWindow(title="ניטור חי - מציאת משחקי פאדל")
    
    try:
        await scanner.start()
        
        # Initial scan to populate seen messages
        print(f"{Fore.CYAN}Loading existing messages...{Style.RESET_ALL}")
        for group in groups:
            messages = await scanner.scan_group_history(group, scroll_count=3)
            # Mark as seen but don't analyze
            for msg in messages:
                msg_id = scanner._get_message_id(msg)
                scanner.seen_message_ids.add(msg_id)
        
        print(f"{Fore.GREEN}✓ Loaded existing messages. Now monitoring for new messages...{Style.RESET_ALL}\n")
        print(f"{Fore.CYAN}Opening monitoring window... (Close window or press Ctrl+C to stop){Style.RESET_ALL}\n")
        
        # Monitor loop
        check_count = 0
        while True:
            check_count += 1
            print(f"\n{Fore.CYAN}Check #{check_count} - {time.strftime('%H:%M:%S')}{Style.RESET_ALL}")
            
            # Check each group
            for group in groups:
                new_messages = await scanner.scan_group_new_messages(group)
                
                if new_messages:
                    print(f"  Found {len(new_messages)} new message(s) in {group}")
                    await analyze_messages(new_messages, group, tracker, gui_window)
                else:
                    print(f"  No new messages in {group}")
            
            if check_count == 1 and tracker.count() == 0:
                print(f"\n{Fore.YELLOW}No matches yet. Continuing to monitor...{Style.RESET_ALL}")
            
            # Update GUI
            try:
                gui_window.update()
            except:
                # Window was closed
                print(f"\n{Fore.YELLOW}Window closed by user. Stopping monitor...{Style.RESET_ALL}")
                break
            
            print(f"  Waiting {interval} seconds until next check...")
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
        description="WhatsApp Padel Match Tracker - Find padel game matches in WhatsApp groups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Scan historical messages (default 5 scrolls):
    python main.py scan-history
  
  Scan with custom scroll count:
    python main.py scan-history --scrolls 10
  
  Monitor for new messages (check every 60 seconds):
    python main.py monitor-live
  
  Monitor with custom interval:
    python main.py monitor-live --interval 30
        """
    )
    
    parser.add_argument(
        'mode',
        choices=['scan-history', 'monitor-live'],
        help='Scanning mode: scan-history (review past messages) or monitor-live (watch for new messages)'
    )
    
    parser.add_argument(
        '--scrolls',
        type=int,
        default=config.default_scroll_count,
        help=f'Number of times to scroll up when loading history (default: {config.default_scroll_count})'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=config.default_monitor_interval,
        help=f'Seconds between checks in live mode (default: {config.default_monitor_interval})'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    print_config_info()
    
    # Load groups from config
    try:
        groups = config.load_groups()
    except (FileNotFoundError, ValueError) as e:
        print(f"{Fore.RED}Configuration Error:{Style.RESET_ALL}")
        print(f"  {str(e)}")
        print(f"\nPlease edit {config.groups_file} and add your WhatsApp group names (one per line).")
        sys.exit(1)
    
    # Run appropriate mode
    try:
        if args.mode == 'scan-history':
            asyncio.run(scan_history_mode(groups, args.scrolls))
        elif args.mode == 'monitor-live':
            asyncio.run(monitor_live_mode(groups, args.interval))
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
