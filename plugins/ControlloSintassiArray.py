#!/usr/bin/env python3
"""
Plugin per il controllo della sintassi degli array in PHP
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

class ArraySyntaxChecker(PluginBase):
    """
    Plugin per il controllo della sintassi degli array in PHP
    """
    
    def get_id(self):
        return "array_syntax_checker"
        
    def get_name(self):
        return "Controllo Sintassi Array"
        
    def get_description(self):
        return "Controlla la corretta sintassi degli array nei file PHP"
        
    def get_version(self):
        return "1.0.0"
        
    def get_author(self):
        return "Proietti House & Claude"
        
    def get_hooks(self):
        return {
            'syntax_check': [self.check_array_syntax]
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
    
    def check_array_syntax(self, filepath: str, lines: List[str], plugin_config=None, **kwargs) -> List[SyntaxError]:
    errors = []
    
    for i, line in enumerate(lines, 1):
        # Salta se in HTML
        if self._is_in_html_block(lines, i - 1):
            continue
            
        # Salta commenti
        in_single_comment, in_multi_comment = self._is_in_comment(lines, i)
        if in_single_comment or in_multi_comment:
            continue
        
        # NUOVO: Ignora concatenazioni PHP
        if re.search(r'\$\w+\s*\.\s*["\']', line):
            continue  # È una concatenazione, non un errore array
            
        # NUOVO: Controlla solo dentro array() o []
        if ('array(' in line or '[' in line) and (']' in line or ')' in line):
            # Cerca pattern SOLO dentro le parentesi dell'array
            array_content = self._extract_array_content(line)
            if array_content and re.search(r'["\'\w]\s+["\'\w]', array_content):
                if not self._is_in_string(line, 0):
                    errors.append(SyntaxError(
                        i, line.strip(), "Virgola mancante in array",
                        "Possibile virgola mancante tra elementi dell'array",
                        "Aggiungi ',' tra gli elementi dell'array"
                    ))
    
    return errors

def _extract_array_content(self, line: str) -> str:
    """Estrae solo il contenuto degli array"""
    # Implementa logica per estrarre contenuto tra parentesi/quadre
    pass