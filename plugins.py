import re
import asyncio
from typing import Dict, Any, Optional

class PluginManager:
    def __init__(self):
        self.plugins = {
            'filter': FilterPlugin(),
            'format': FormatPlugin(),
            'replace': ReplacePlugin(),
            'caption': CaptionPlugin()
        }
    
    async def process_message(self, message, config: Dict[str, Any]):
        processed_message = message
        
        for plugin_name, plugin in self.plugins.items():
            if plugin_name in config and config[plugin_name].get('enabled', False):
                processed_message = await plugin.process(processed_message, config[plugin_name])
                if processed_message is None:
                    return None
        
        return processed_message

class FilterPlugin:
    def __init__(self):
        self.name = "filter"
    
    async def process(self, message, config: Dict[str, Any]):
        if not config.get('enabled', False):
            return message
        
        text = message.text or ""
        
        if config.get('blacklist'):
            blacklist_patterns = config['blacklist']
            for pattern in blacklist_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return None
        
        if config.get('whitelist'):
            whitelist_patterns = config['whitelist']
            for pattern in whitelist_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return message
            return None
        
        return message

class FormatPlugin:
    def __init__(self):
        self.name = "format"
    
    async def process(self, message, config: Dict[str, Any]):
        if not config.get('enabled', False) or not message.text:
            return message
        
        text = message.text
        
        if config.get('bold', False):
            text = f"**{text}**"
        
        if config.get('italic', False):
            text = f"*{text}*"
        
        if config.get('code', False):
            text = f"{text}"
        
        message.text = text
        return message

class ReplacePlugin:
    def __init__(self):
        self.name = "replace"
    
    async def process(self, message, config: Dict[str, Any]):
        if not config.get('enabled', False) or not message.text:
            return message
        
        text = message.text
        replacements = config.get('replacements', [])
        
        for replacement in replacements:
            pattern = replacement.get('pattern', '')
            replacement_text = replacement.get('replacement', '')
            
            if pattern:
                text = re.sub(pattern, replacement_text, text)
        
        message.text = text
        return message

class CaptionPlugin:
    def __init__(self):
        self.name = "caption"
    
    async def process(self, message, config: Dict[str, Any]):
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
