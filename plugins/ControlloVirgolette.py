#!/usr/bin/env python3
"""
Plugin per il controllo delle virgolette in PHP
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

class QuotesChecker(PluginBase):
    """
    Plugin per il controllo delle virgolette in PHP
    """
    
    def get_id(self):
        return "quotes_checker"
        
    def get_name(self):
        return "Controllo Virgolette"
        
    def get_description(self):
        return "Controlla la corretta apertura e chiusura delle virgolette nei file PHP"
        
    def get_version(self):
        return "1.0.0"
        
    def get_author(self):
        return "Proietti House & Claude"
        
    def get_hooks(self):
        return {
            'syntax_check': [self.check_quotes]
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
    
    def _is_in_comment(self, lines: List[str], line_num: int) -> Tuple[bool, bool]:
        """Verifica se una linea è in un commento. Ritorna (in_single_comment, in_multi_comment)"""
        line = lines[line_num - 1]
        
        # Commento single-line
        if '//' in line:
            comment_pos = line.find('//')
            # Verifica se // è dentro una stringa
            if not self._is_in_string(line, comment_pos):
                return True, False
                
        # Verifica commenti multi-line
        in_multi = False
        for i in range(line_num):
            if '/*' in lines[i]:
                in_multi = True
            if '*/' in lines[i]:
                in_multi = False
                
        return False, in_multi
    
    def _is_in_string(self, line: str, pos: int) -> bool:
        """Verifica se una posizione è all'interno di una stringa"""
        in_single = False
        in_double = False
        escaped = False
        
        for i in range(pos):
            char = line[i]
            if escaped:
                escaped = False
                continue
                
            if char == '\\':
                escaped = True
                continue
                
            if char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double
                
        return in_single or in_double
    
    def check_quotes(self, filepath: str, lines: List[str], plugin_config=None, **kwargs) -> List[SyntaxError]:
        """Controlla virgolette non chiuse - versione migliorata per gestire stringhe multilinea"""
        errors = []
        in_string = False
        string_char = None
        string_start_line = 0
        
        for i, line in enumerate(lines, 1):
            # Se siamo in un blocco HTML, salta
            if self._is_in_html_block(lines, i - 1):
                continue
                
            # Controlla se siamo in un commento
            in_single_comment, in_multi_comment = self._is_in_comment(lines, i)
            if in_multi_comment:
                continue
                
            # Se è un commento single-line, analizza solo la parte prima del commento
            if in_single_comment and '//' in line:
                comment_pos = line.find('//')
                line_to_check = line[:comment_pos]
            else:
                line_to_check = line
                
            # Analizza carattere per carattere
            escaped = False
            for j, char in enumerate(line_to_check):
                if escaped:
                    escaped = False
                    continue
                    
                if char == '\\':
                    escaped = True
                    continue
                    
                if char in ['"', "'"]:
                    if not in_string:
                        in_string = True
                        string_char = char
                        string_start_line = i
                    elif char == string_char:
                        in_string = False
                        string_char = None
            
            # Se la stringa non è chiusa alla fine della riga, potrebbe essere multilinea
            # Verifica se è un caso valido di stringa multilinea (es. echo con HTML)
            if in_string and i == string_start_line:
                # Controlla se è un echo/print che apre una stringa multilinea
                if re.match(r'^\s*(echo|print)\s+["\']', line.strip()):
                    # È probabilmente una stringa multilinea valida, non segnalare errore
                    continue
                else:
                    # Potrebbe essere un errore reale
                    quote_type = 'singola' if string_char == "'" else 'doppia'
                    errors.append(SyntaxError(
                        i, line.strip(), 
                        f"Virgoletta {quote_type} non chiusa",
                        f"La stringa iniziata con {string_char} non è stata chiusa",
                        f"Verifica se manca una {string_char} alla fine della stringa"
                    ))
        
        return errors