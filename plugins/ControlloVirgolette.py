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
            # Verifica se è un caso valido di stringa multilinea
            if in_string and i == string_start_line:
                # NUOVO: Verifica se è una query SQL
                if self._is_sql_query(line):
                    continue  # Non segnalare errore per query SQL
                
                # NUOVO: Verifica se è un echo/print con HTML multilinea
                if self._is_multiline_echo_or_print(line):
                    continue  # Non segnalare errore per echo/print multilinea
                
                # Controlla se è un echo/print che apre una stringa multilinea (logica originale)
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

    def _is_sql_query(self, line: str) -> bool:
        """Verifica se la linea contiene una query SQL"""
        # Lista delle parole chiave SQL più comuni
        sql_keywords = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'JOIN', 
            'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'ORDER BY', 'GROUP BY',
            'HAVING', 'UNION', 'CREATE', 'ALTER', 'DROP', 'INDEX'
        ]
        
        line_upper = line.upper().strip()
        
        # Verifica se la linea contiene prepare() con query SQL
        if 'prepare(' in line.lower() or 'query(' in line.lower():
            return True
        
        # Verifica se contiene parole chiave SQL
        for keyword in sql_keywords:
            if keyword in line_upper:
                return True
        
        return False

    def _is_multiline_echo_or_print(self, line: str) -> bool:
        """Verifica se è un echo o print che inizia una stringa multilinea"""
        line_stripped = line.strip()
        
        # Pattern per echo/print seguiti da virgolette di apertura
        patterns = [
            r'^\s*echo\s+["\']',
            r'^\s*print\s+["\']',
            r'^\s*echo\s*\(\s*["\']',
            r'^\s*print\s*\(\s*["\']'
        ]
        
        for pattern in patterns:
            if re.match(pattern, line_stripped):
                return True
        
        return False