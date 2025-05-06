# test_plugin.py - metti questo file nella cartella plugins
#!/usr/bin/env python3
"""
Plugin di test per PHP Analyzer
"""
import os
import sys

# Aggiungi percorso principale al sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("Tentativo di importare PluginBase...")
    from analizzatoreTest import PluginBase, SyntaxError
    print("Importazione riuscita!")
except ImportError as e:
    print(f"Errore di importazione: {e}")
    from dataclasses import dataclass
    
    @dataclass
    class SyntaxError:
        line_number: int
        line_content: str
        error_type: str
        description: str
        suggestion: str
    
    class PluginBase:
        def get_id(self): pass
        def get_hooks(self): pass
        # Altri metodi...

class TestPlugin(PluginBase):
    """
    Plugin di test molto semplice
    """
    
    def get_id(self):
        return "test_plugin"
        
    def get_name(self):
        return "Test Plugin"
        
    def get_description(self):
        return "Plugin di test per verificare il sistema di caricamento"
        
    def get_version(self):
        return "1.0.0"
        
    def get_author(self):
        return "PHP Analyzer Team"
        
    def get_hooks(self):
        return {
            'syntax_check': [self.test_syntax]
        }
        
    def get_dependencies(self):
        return []
        
    def get_config_defaults(self):
        return {}
        
    def test_syntax(self, filepath, lines, plugin_config=None, **kwargs):
        print(f"Test plugin eseguito su: {filepath}")
        return []

print("File test_plugin.py caricato!")