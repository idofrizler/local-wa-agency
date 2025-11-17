"""
WhatsApp scanner for multiple groups with message extraction.
"""
import re
import time
import asyncio
from enum import Enum
from typing import List, Dict, Set, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
from src.config import config

class ScanMode(Enum):
    """Scanning mode for WhatsApp groups."""
    HISTORY = "history"
    LIVE = "live"

class Message:
    """Simple message data structure."""
    def __init__(self, sender: str, text: str, timestamp: str, phone_number: str = "N/A"):
        self.sender = sender
        self.text = text
        self.timestamp = timestamp
        self.phone_number = phone_number

class WhatsAppScanner:
    """Scans WhatsApp groups for messages."""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page: Optional[Page] = None
        self.seen_message_ids: Set[str] = set()
    
    async def start(self):
        """Initialize browser and WhatsApp Web."""
        print("Starting WhatsApp scanner...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch_persistent_context(
            str(config.session_dir),
            headless=False,
            args=['--no-sandbox']
        )
        
        self.page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()
        
        # Navigate to WhatsApp Web
        print("Navigating to WhatsApp Web...")
        await self.page.goto("https://web.whatsapp.com", timeout=30000)
        
        # Wait for WhatsApp to load
        await self._wait_for_whatsapp_load()
    
    async def _wait_for_whatsapp_load(self):
        """Wait for WhatsApp Web to fully load."""
        print("Waiting for WhatsApp Web to load...")
        
        try:
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            # Check if QR code is present
            qr_present = await self.page.locator('canvas').count() > 0
            
            if qr_present:
                print("QR code detected. Please scan with your phone...")
                print("Waiting for login (up to 2 minutes)...")
                
                # Wait for chat list to appear
                for _ in range(120):
                    await asyncio.sleep(1)
                    if await self.page.locator('[data-testid="chat-list"]').count() > 0:
                        print("Successfully logged in!")
                        await asyncio.sleep(3)
                        return
                
                print("WARNING: Timeout waiting for QR scan. Proceeding anyway...")
            else:
                print("Already logged in (session restored).")
                await asyncio.sleep(2)
        
        except PlaywrightTimeoutError:
            print("WARNING: Timeout during load. Attempting to continue...")
            await asyncio.sleep(5)
    
    async def scan_group_history(self, group_name: str, scroll_count: int = 5) -> List[Message]:
        """
        Scan a group's message history.
        
        Args:
            group_name: Name of the WhatsApp group
            scroll_count: Number of times to scroll up to load history
            
        Returns:
            List of Message objects
        """
        print(f"\nScanning group: {group_name}")
        
        # Navigate to group
        await self._navigate_to_group(group_name)
        
        # Scroll to load history
        print(f"Scrolling {scroll_count} times to load history...")
        for i in range(scroll_count):
            await self.page.keyboard.press("PageUp")
            await asyncio.sleep(1)
            print(f"  Scroll {i+1}/{scroll_count}")
        
        # Extract messages
        messages = await self._extract_messages(group_name)
        print(f"Extracted {len(messages)} messages from {group_name}")
        
        return messages
    
    async def scan_group_new_messages(self, group_name: str) -> List[Message]:
        """
        Scan a group for new messages only.
        
        Args:
            group_name: Name of the WhatsApp group
            
        Returns:
            List of new Message objects
        """
        # Navigate to group
        await self._navigate_to_group(group_name)
        
        # Extract only new messages
        all_messages = await self._extract_messages(group_name)
        
        # Filter to only new messages
        new_messages = []
        for msg in all_messages:
            msg_id = self._get_message_id(msg)
            if msg_id not in self.seen_message_ids:
                self.seen_message_ids.add(msg_id)
                new_messages.append(msg)
        
        return new_messages
    
    async def _navigate_to_group(self, group_name: str):
        """Navigate to a specific WhatsApp group."""
        try:
            print(f"  Looking for group in chat list...")
            
            # Method 1: Try to find the group directly in the chat list
            group_in_list = self.page.locator(f'span[title="{group_name}"]').first
            if await group_in_list.count() > 0:
                print(f"  Found group in chat list, clicking...")
                await group_in_list.click()
                await asyncio.sleep(3)
            else:
                # Method 2: Use search
                print(f"  Group not visible, using search...")
                
                # Try multiple search box selectors
                search_selectors = [
                    '[data-testid="chat-list-search"]',
                    'div[contenteditable="true"]',
                    '[title="Search input textbox"]'
                ]
                
                search_found = False
                for selector in search_selectors:
                    search_box = self.page.locator(selector).first
                    if await search_box.count() > 0:
                        print(f"  Found search box with selector: {selector}")
                        await search_box.click()
                        await asyncio.sleep(1)
                        search_found = True
                        break
                
                if not search_found:
                    print(f"  No search box found, trying keyboard shortcut...")
                    await self.page.keyboard.press("Control+Alt+/")
                    await asyncio.sleep(1)
                
                # Clear any existing text with select all + delete
                # Use Command on macOS, Control on other platforms
                import platform
                select_all_key = "Meta+a" if platform.system() == "Darwin" else "Control+a"
                await self.page.keyboard.press(select_all_key)
                await asyncio.sleep(0.3)
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(0.5)
                
                # Type group name
                print(f"  Typing group name: {group_name}")
                await self.page.keyboard.type(group_name)
                await asyncio.sleep(3)  # Give time for search results
                
                # Check if we got the "No chats, contacts or messages found" message
                no_results = await self.page.locator('text=/No chats, contacts or messages found/i').count()
                if no_results > 0:
                    raise ValueError(f"No search results found for group '{group_name}'")
                
                # Try to click on the first search result
                print(f"  Looking for first search result...")
                first_result = self.page.locator(f'span[title="{group_name}"]').first
                result_count = await first_result.count()
                
                if result_count > 0:
                    print(f"  Clicking on search result...")
                    await first_result.click()
                    await asyncio.sleep(2)
                else:
                    # Fallback: Try pressing Enter
                    print(f"  Search result not found, trying Enter key...")
                    await self.page.keyboard.press("Enter")
                    await asyncio.sleep(2)
            
            # Wait for chat to load
            print(f"  Waiting for chat to load...")
            await asyncio.sleep(3)  # Give it time to load
            
            # Check if chat loaded by looking for message containers
            # Note: WhatsApp uses div[data-id] for messages, not [data-testid="msg-container"]
            msg_count = await self.page.locator('div[data-id]').count()
            
            if msg_count > 0:
                print(f"  ✓ Chat loaded successfully (found {msg_count} messages)")
            else:
                # Could be an empty chat - check if we're at least in a conversation view
                # by looking for the message input box
                input_box = await self.page.locator('[data-testid="conversation-compose-box-input"]').count()
                if input_box > 0:
                    print(f"  ✓ Chat loaded (empty chat, no messages yet)")
                else:
                    raise ValueError(f"Chat did not load for group '{group_name}'")
            
        except Exception as e:
            print(f"  ✗ Error navigating to group: {str(e)}")
            await asyncio.sleep(2)
            raise  # Re-raise the exception to stop processing this group
    
    async def _extract_messages(self, group_name: str) -> List[Message]:
        """Extract messages from the current chat."""
        messages = []
        
        try:
            # Get all message containers
            print(f"  Looking for message containers...")
            message_elements = await self.page.locator('[data-testid="msg-container"]').all()
            print(f"  Found {len(message_elements)} messages with [data-testid='msg-container']")
            
            if not message_elements or len(message_elements) == 0:
                # Fallback to alternative selector
                print(f"  Trying alternative selector: div[data-id]")
                message_elements = await self.page.locator('div[data-id]').all()
                print(f"  Found {len(message_elements)} messages with div[data-id]")
            
            skipped_own = 0
            skipped_empty = 0
            errors = 0
            
            for elem in message_elements:
                try:
                    # Check if it's our own message (skip it)
                    if await self._is_own_message(elem):
                        skipped_own += 1
                        continue
                    
                    sender = await self._extract_sender(elem)
                    text = await self._extract_text(elem)
                    timestamp = await self._extract_timestamp(elem)
                    phone = await self._extract_phone_number(elem)
                    
                    if text and text.strip():
                        messages.append(Message(sender, text, timestamp, phone))
                    else:
                        skipped_empty += 1
                
                except Exception as e:
                    errors += 1
                    continue
            
            print(f"  Processing summary: {len(messages)} kept, {skipped_own} own messages, {skipped_empty} empty, {errors} errors")
        
        except Exception as e:
            print(f"Error extracting messages: {str(e)}")
        
        return messages
    
    async def _is_own_message(self, element) -> bool:
        """Check if message is from current user."""
        try:
            # Check for outgoing message indicator
            classes = await element.get_attribute('class') or ''
            if 'message-out' in classes:
                return True
            
            # More specific check: look for the green checkmark or double checkmark
            # which indicates sent messages
            checkmarks = await element.locator('[data-icon="msg-check"], [data-icon="msg-dblcheck"]').count()
            if checkmarks > 0:
                return True
            
            return False
        except:
            return False
    
    async def _extract_sender(self, element) -> str:
        """Extract sender name from message element."""
        try:
            # Method 1: Look for sender name in the aria-label attribute
            aria_label_elem = await element.locator('span[aria-label^="Maybe "]').first.count()
            if aria_label_elem > 0:
                aria_elem = element.locator('span[aria-label^="Maybe "]').first
                aria_text = await aria_elem.inner_text()
                if aria_text and len(aria_text) > 0:
                    return aria_text.strip()
            
            # Method 2: Look for copyable-text with data-pre-plain-text attribute
            full_html = await element.inner_html()
            pre_text_match = re.search(r'data-pre-plain-text="[^"]*\]\s*([^:]+):', full_html)
            if pre_text_match:
                sender = pre_text_match.group(1).strip()
                # Decode HTML entities
                sender = sender.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                # Make sure it's not a phone number
                if sender and len(sender) > 0 and not re.match(r'^[\d\s\-+()]+$', sender):
                    return sender
            
            # Method 3: Look for sender name span (but not phone button)
            sender_spans = await element.locator('span[dir="auto"]').all()
            for span in sender_spans:
                try:
                    # Skip if it's the phone button
                    span_class = await span.get_attribute('class') or ''
                    span_role = await span.get_attribute('role') or ''
                    if '_ahx_' in span_class or span_role == 'button':
                        continue
                    
                    text = await span.inner_text()
                    text = text.strip()
                    # Filter out timestamps, phone numbers, emojis, and very short/long strings
                    if text and 2 < len(text) < 50:
                        # Skip if it's a timestamp
                        if re.match(r'^\d{1,2}:\d{2}', text):
                            continue
                        # Skip if it's mostly digits (phone number)
                        if re.match(r'^[\d\s\-+()]+$', text):
                            continue
                        # Must have letters
                        if any(c.isalpha() for c in text):
                            return text
                except:
                    continue
            
            return "Unknown"
        except Exception as e:
            return "Unknown"
    
    async def _extract_text(self, element) -> str:
        """Extract message text from element."""
        try:
            # Try specific text selectors
            text_elem = element.locator('span.selectable-text').first
            if await text_elem.count() > 0:
                text = await text_elem.inner_text()
                text = text.strip()
                if text:
                    return text
            
            # Fallback to full text
            full_text = await element.inner_text()
            full_text = full_text.strip()
            return full_text if full_text else ""
        except:
            return ""
    
    async def _extract_timestamp(self, element) -> str:
        """Extract timestamp from message."""
        try:
            full_text = await element.inner_text()
            time_pattern = r'\[?(\d{1,2}:\d{2})\]?'
            matches = re.findall(time_pattern, full_text)
            if matches:
                return matches[-1]
            return "Unknown"
        except:
            return "Unknown"
    
    async def _extract_phone_number(self, element) -> str:
        """Extract phone number from message element."""
        try:
            # Method 1: Look for phone number in button span with class _ahx_
            phone_button = element.locator('span._ahx_[role="button"]').first
            if await phone_button.count() > 0:
                phone = await phone_button.inner_text()
                phone = phone.strip().replace(' ', '').replace('-', '')
                if phone:
                    return phone
            
            # Method 2: Extract from data-pre-plain-text attribute
            full_html = await element.inner_html()
            pre_text_match = re.search(r'data-pre-plain-text="[^"]*\]\s*([^:]+):', full_html)
            if pre_text_match:
                potential_phone = pre_text_match.group(1).strip()
                # Check if it matches phone pattern
                if re.match(r'^[\d\s\-+()]+$', potential_phone):
                    return potential_phone.replace(' ', '').replace('-', '')
            
            # Method 3: Look in message text
            text = await self._extract_text(element)
            patterns = [
                r'\+972[-\s]?\d{1,2}[-\s]?\d{3}[-\s]?\d{4}',  # +972-XX-XXX-XXXX
                r'0\d{1,2}[-\s]?\d{3}[-\s]?\d{4}',  # 0XX-XXX-XXXX
                r'\d{10}',  # 10 digits together
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    phone = match.group(0)
                    # Clean up formatting
                    phone = phone.replace(' ', '').replace('-', '')
                    return phone
            
            return "N/A"
        except:
            return "N/A"
    
    def _get_message_id(self, message: Message) -> str:
        """Generate a unique ID for a message."""
        return hash(f"{message.sender}_{message.text[:50]}_{message.timestamp}")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
