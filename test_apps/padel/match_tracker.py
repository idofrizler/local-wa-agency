"""
Match tracking for the padel scenario.
"""
from typing import List
from colorama import Fore, Style, init
from test_apps.padel import Match

# Initialize colorama for colored console output
init(autoreset=True)

class MatchTracker:
    """Tracks and displays potential padel game matches for the GUI helpers."""
    
    def __init__(self):
        self.matches: List[Match] = []
    
    def add_match(self, match: Match):
        """Add a new match to the tracker."""
        self.matches.append(match)
    
    def get_confidence_color(self, confidence: str) -> str:
        """Get the color code for a confidence level."""
        colors = {
            "HIGH": Fore.GREEN,
            "MEDIUM": Fore.YELLOW,
            "LOW": Fore.RED
        }
        return colors.get(confidence, Fore.WHITE)
    
    def get_confidence_symbol(self, confidence: str) -> str:
        """Get a symbol for confidence level."""
        symbols = {
            "HIGH": "✓",
            "MEDIUM": "~",
            "LOW": "✗"
        }
        return symbols.get(confidence, "?")
    
    def display_matches(self, title: str = "PADEL MATCH TRACKER"):
        """Display matches in a formatted console table (used for debugging)."""
        if not self.matches:
            print(f"\\n{Fore.CYAN}{'='*80}")
            print(f"{title:^80}")
            print(f"{'='*80}{Style.RESET_ALL}")
            print(f"\\n{Fore.YELLOW}No matches found yet.{Style.RESET_ALL}\\n")
            return
        
        # Print header
        print(f"\\n{Fore.CYAN}{'='*80}")
        print(f"{title:^80}")
        print(f"{'='*80}{Style.RESET_ALL}\\n")
        
        # Column widths
        col_time = 10
        col_group = 20
        col_sender = 15
        col_phone = 15
        col_conf = 15
        
        header = (
            f"{Fore.CYAN}"
            f"{'Time':<{col_time}} "
            f"{'Group':<{col_group}} "
            f"{'Sender':<{col_sender}} "
            f"{'Phone':<{col_phone}} "
            f"{'Confidence':<{col_conf}}"
            f"{Style.RESET_ALL}"
        )
        print(header)
        print(f"{Fore.CYAN}{'-'*80}{Style.RESET_ALL}")
        
        for match in self.matches:
            color = self.get_confidence_color(match.confidence)
            symbol = self.get_confidence_symbol(match.confidence)
            time_str = match.timestamp[:col_time-1]
            group_str = match.group_name[:col_group-1]
            sender_str = match.sender[:col_sender-1]
            phone_str = match.phone_number[:col_phone-1]
            conf_str = f"{match.confidence} {symbol}"
            
            row = (
                f"{time_str:<{col_time}} "
                f"{group_str:<{col_group}} "
                f"{sender_str:<{col_sender}} "
                f"{phone_str:<{col_phone}} "
                f"{color}{conf_str:<{col_conf}}{Style.RESET_ALL}"
            )
            print(row)
            message_preview = match.message.replace('\\n', ' ')[:70]
            if len(match.message) > 70:
                message_preview += "..."
            print(f"  {Fore.WHITE}→ {message_preview}{Style.RESET_ALL}")
            if match.analysis:
                print(f"  {Fore.LIGHTBLACK_EX}  {match.analysis.reasoning}{Style.RESET_ALL}")
            print()
        
        print(f"{Fore.CYAN}{'-'*80}{Style.RESET_ALL}")
        high_count = sum(1 for m in self.matches if m.confidence == "HIGH")
        medium_count = sum(1 for m in self.matches if m.confidence == "MEDIUM")
        low_count = sum(1 for m in self.matches if m.confidence == "LOW")
        
        summary = (
            f"Total matches: {len(self.matches)} "
            f"({Fore.GREEN}{high_count} HIGH{Style.RESET_ALL}, "
            f"{Fore.YELLOW}{medium_count} MEDIUM{Style.RESET_ALL}, "
            f"{Fore.RED}{low_count} LOW{Style.RESET_ALL})"
        )
        print(summary)
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\\n")
    
    def clear(self):
        """Clear all matches."""
        self.matches.clear()
    
    def count(self) -> int:
        """Get the number of matches."""
        return len(self.matches)
