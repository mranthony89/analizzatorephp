#!/usr/bin/env python3
"""
Plugin per il controllo della sintassi delle funzioni in PHP
"""
from typing import List, Tuple
import re

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

class FunctionSyntaxChecker(PluginBase):
    """
    Plugin per il controllo della sintassi delle funzioni in PHP
    """
    
    def get_id(self):
        return "function_syntax_checker"
        
    def get_name(self):
        return "Controllo Sintassi Funzioni"
        
    def get_description(self):
        return "Controlla la corretta sintassi delle dichiarazioni di funzioni nei file PHP"
        
    def get_version(self):
        return "1.0.0"
        
    def get_author(self):
        return "Proietti House & Claude"
        
    def get_hooks(self):
        return {
            'syntax_check': [self.check_function_syntax]
        }
    
    def _is_in_html_block(self, lines: List[str], line_num: int) -> bool:
        """Verifica se una linea è all'interno di un blocco HTML (dopo ?>)"""
        in_php = True
        for i in range(line_num):
            if '<?php' in lines[i] or '<?' in lines[i]:
                in_php = True
            elif '?>' in lines[i]:
                in_php = False
        return not in_php
    
    def check_function_syntax(self, filepath: str, lines: List[str], plugin_config=None, **kwargs) -> List[SyntaxError]:
        """Controlla la sintassi delle funzioni"""
        errors = []
        
        for i, line in enumerate(lines, 1):
            # Se siamo in un blocco HTML, salta
            if self._is_in_html_block(lines, i - 1):
                continue
                
            # Non controllare funzioni JavaScript
            if 'function(' in line and not 'function ' in line:
                # È probabilmente una funzione anonima JavaScript
                continue
                
            if 'function' in line:
                # Controlla sintassi base funzione PHP
                pattern = r'^\s*(public|private|protected|static)?\s*function\s+\w+\s*\([^)]*\)\s*{'
                if not re.match(pattern, line) and not re.match(pattern, line + (lines[i] if i < len(lines) else '')):
                    # Verifica se è una funzione JavaScript anonima
                    if not re.search(r'function\s*\([^)]*\)\s*{', line):
                        errors.append(SyntaxError(
                            i, line.strip(), "Sintassi funzione errata",
                            "La dichiarazione della funzione non segue il pattern corretto",
                            "Usa: function nomeFunzione(parametri) {"
                        ))
        
        return errors