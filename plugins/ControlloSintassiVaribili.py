#!/usr/bin/env python3
"""
Plugin per il controllo della sintassi delle variabili in PHP
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

class VariableSyntaxChecker(PluginBase):
    """
    Plugin per il controllo della sintassi delle variabili in PHP
    """
    
    def get_id(self):
        return "variable_syntax_checker"
        
    def get_name(self):
        return "Controllo Sintassi Variabili"
        
    def get_description(self):
        return "Controlla la corretta sintassi delle variabili nei file PHP"
        
    def get_version(self):
        return "1.0.0"
        
    def get_author(self):
        return "Proietti House & Claude"
        
    def get_hooks(self):
        return {
            'syntax_check': [self.check_variable_syntax]
        }
    
    def _is_in_html_context(self, line: str, pos: int) -> bool:
    """Verifica se siamo in un contesto HTML dentro echo/print"""
    # Cerca se siamo dentro un echo o print con HTML
    echo_match = re.search(r'echo\s+["\'].*?["\']', line[:pos])
    print_match = re.search(r'print\s+["\'].*?["\']', line[:pos])
    
    if echo_match or print_match:
        # Verifica se contiene tag HTML
        if re.search(r'<[^>]+>', line):
            return True
    return False
    
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
    
    def check_variable_syntax(self, filepath: str, lines: List[str], plugin_config=None, **kwargs) -> List[SyntaxError]:
        """Controlla la sintassi delle variabili"""
        errors = []
        
        for i, line in enumerate(lines, 1):
            # Se siamo in un blocco HTML o JavaScript, salta
            if self._is_in_html_block(lines, i - 1):
                continue
                
            # Ignora il codice JavaScript
            if re.search(r'<script|var\s+\w+|let\s+\w+|const\s+\w+|document\.|function\s*\(', line):
                continue
                
            # Ignora commenti
            in_single_comment, in_multi_comment = self._is_in_comment(lines, i)
            if in_single_comment or in_multi_comment:
                continue
                
            # Trova variabili senza $ in PHP
            words = re.findall(r'\b\w+\b', line)
            for word in words:
                # Se la parola è seguita da = e non è una keyword
                match = re.search(fr'\b{word}\s*=(?!=)', line)
                if match:
                    if word not in ['function', 'class', 'public', 'private', 'protected', 'static', 'const', 'var']:
                        # Verifica che non sia in una stringa o in JavaScript
                        if not self._is_in_string(line, match.start()):
                            # Verifica che non sia già una variabile PHP con $
                            if not re.search(fr'\${word}', line):
                                errors.append(SyntaxError(
                                    i, line.strip(), "Variabile senza $",
                                    f"La variabile '{word}' non ha il simbolo $",
                                    f"Cambia '{word}' in '${word}'"
                                ))
        
        return errors