#!/usr/bin/env python3
"""
Plugin base ultra-minimo
"""
from analizzatore import PluginBase

class BasePlugin(PluginBase):
    def get_id(self):
        return "base_plugin"
        
    def get_name(self):
        return "Base Plugin"
        
    def get_description(self):
        return "Plugin base minimo"
        
    def get_version(self):
        return "1.0.0"
        
    def get_author(self):
        return "PHP Analyzer Team"
        
    def get_hooks(self):
        return {}