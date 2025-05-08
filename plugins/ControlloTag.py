#!/usr/bin/env python3
"""
Plugin per il controllo dei tag PHP
"""
from typing import List

try:
    from analizzatore import PluginBase, SyntaxError
except ImportError:
    # Definizione di fallback per IDE
    class PluginBase:
        def get_id(self): pass
        def get_hooks(self): pass
    
    class SyntaxError:
        def __init__(self, line_number, line_content, error_type, description, suggestion):
            self.line_number = line_number
            self.line_content = line_content
            self.error_type = error_type
            self.description = description
            self.suggestion = suggestion

class PHPTagsChecker(PluginBase):
    """
    Plugin per il controllo dei tag PHP
    """
    
    def get_id(self):
        return "php_tags_checker"
        
    def get_name(self):
        return "Controllo Tag PHP"
        
    def get_description(self):
        return "Controlla la corretta apertura e chiusura dei tag PHP"
        
    def get_version(self):
        return "1.0.0"
        
    def get_author(self):
        return "Proietti House & Claude"
        
    def get_hooks(self):
        return {
            'syntax_check': [self.check_php_tags]
        }
    
    def check_php_tags(self, filepath: str, lines: List[str], plugin_config=None, **kwargs) -> List[SyntaxError]:
        """Controlla i tag PHP"""
        errors = []
        php_open = False
        open_line = 0
        
        for i, line in enumerate(lines, 1):
            if '<?php' in line or '<?' in line:
                if php_open:
                    errors.append(SyntaxError(
                        i, line.strip(), "Tag PHP già aperto",
                        "Trovato un nuovo tag di apertura PHP senza chiudere il precedente",
                        "Aggiungi '?>' prima di questo tag o rimuovi questo tag"
                    ))
                php_open = True
                open_line = i
            
            if '?>' in line:
                if not php_open:
                    errors.append(SyntaxError(
                        i, line.strip(), "Tag PHP chiuso senza apertura",
                        "Trovato '?>' senza corrispondente '<?php' o '<?'",
                        "Rimuovi '?>' o aggiungi '<?php' prima"
                    ))
                php_open = False
        
        return errors