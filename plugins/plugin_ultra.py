#!/usr/bin/env python3
"""
Plugin ultra-minimo
"""
from analizzatore import PluginBase

class PluginUltra(PluginBase):
    def get_id(self):
        return "plugin_ultra"
    def get_name(self):
        return "Plugin Ultra"
    def get_description(self):
        return "Plugin ultra-minimo"
    def get_version(self):
        return "1.0.0"
    def get_author(self):
        return "PHP Analyzer Team"
    def get_hooks(self):
        return {}