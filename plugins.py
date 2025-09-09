import re
import asyncio
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import cv2
import pytesseract
import io

class PluginManager:
    def __init__(self):
        self.plugins = {
            'filter': FilterPlugin(),
            'format': FormatPlugin(),
            'replace': ReplacePlugin(),
            'caption': CaptionPlugin(),
            'watermark': WatermarkPlugin(),
            'ocr': OCRPlugin()
        }
    
    async def process_message(self, message, config: Dict[str, Any]):
        """Process message through all enabled plugins"""
        processed_message = message
        
        for plugin_name, plugin in self.plugins.items():
            if plugin_name in config and config[plugin_name].get('enabled', False):
                processed_message = await plugin.process(processed_message, config[plugin_name])
                if processed_message is None:  # Message filtered out
                    return None
        
        return processed_message

class FilterPlugin:
    def __init__(self):
        self.name = "filter"
    
    async def process(self, message, config: Dict[str, Any]):
        """Filter messages based on blacklist/whitelist"""
        if not config.get('enabled', False):
            return message
        
        text = message.text or ""
        
        # Blacklist filter
        if config.get('blacklist'):
            blacklist_patterns = config['blacklist']
            for pattern in blacklist_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return None  # Filter out message
        
        # Whitelist filter
        if config.get('whitelist'):
            whitelist_patterns = config['whitelist']
            for pattern in whitelist_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return message  # Allow message
            return None  # Filter out if not in whitelist
        
        return message

class FormatPlugin:
    def __init__(self):
        self.name = "format"
    
    async def process(self, message, config: Dict[str, Any]):
        """Format message text"""
        if not config.get('enabled', False) or not message.text:
            return message
        
        text = message.text
        
        # Bold
        if config.get('bold', False):
            text = f"**{text}**"
        
        # Italic
        if config.get('italic', False):
            text = f"*{text}*"
        
        # Code
        if config.get('code', False):
            text = f"`{text}`"
        
        # Strikethrough
        if config.get('strikethrough', False):
            text = f"~~{text}~~"
        
        message.text = text
        return message

class ReplacePlugin:
    def __init__(self):
        self.name = "replace"
    
    async def process(self, message, config: Dict[str, Any]):
        """Replace text using regex"""
        if not config.get('enabled', False) or not message.text:
            return message
        
        text = message.text
        replacements = config.get('replacements', [])
        
        for replacement in replacements:
            pattern = replacement.get('pattern', '')
            replacement_text = replacement.get('replacement', '')
            flags = replacement.get('flags', 0)
            
            if pattern:
                text = re.sub(pattern, replacement_text, text, flags=flags)
        
        message.text = text
        return message

class CaptionPlugin:
    def __init__(self):
        self.name = "caption"
    
    async def process(self, message, config: Dict[str, Any]):
        """Add header/footer to message"""
        if not config.get('enabled', False):
            return message
        
        header = config.get('header', '')
        footer = config.get('footer', '')
        
        if message.text:
            if header:
                message.text = f"{header}\n{message.text}"
            if footer:
                message.text = f"{message.text}\n{footer}"
        
        return message

class WatermarkPlugin:
    def __init__(self):
        self.name = "watermark"
    
    async def process(self, message, config: Dict[str, Any]):
        """Add watermark to images/videos"""
        if not config.get('enabled', False):
            return message
        
        # This would require more complex implementation for actual watermarking
        # For now, just return the message as-is
        return message

class OCRPlugin:
    def __init__(self):
        self.name = "ocr"
    
    async def process(self, message, config: Dict[str, Any]):
        """Perform OCR on images"""
        if not config.get('enabled', False):
            return message
        
        # This would require downloading and processing images
        # For now, just return the message as-is
        return message
