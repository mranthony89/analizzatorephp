#!/usr/bin/env python3
"""
Plugin per il controllo dei parentesi in PHP
"""
import re
from typing import List

try:
    from analizzatore import PluginBase, SyntaxError
except ImportError:
    # Definizione di fallback per IDE
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
        def get_name(self): pass
        def get_description(self): pass
        def get_version(self): pass
        def get_author(self): pass
        def get_hooks(self): pass
        def get_dependencies(self): pass
        def get_config_defaults(self): pass

class BracketsSyntaxChecker(PluginBase):
    """
    Plugin per il controllo della sintassi di parentesi in PHP
    """
    
    def get_id(self):
        return "brackets_syntax_checker"
        
    def get_name(self):
        return "Brackets Syntax Checker"
        
    def get_description(self):
        return "Controlla la corretta apertura e chiusura di parentesi, graffe e quadre"
        
    def get_version(self):
        return "1.0.0"
        
    def get_author(self):
        return "PHP Analyzer Team"
        
    def get_hooks(self):
        return {
            'syntax_check': [self.check_brackets]
        }
        
    def get_config_defaults(self):
        return {}
        
    def check_brackets(self, filepath: str, lines: List[str], plugin_config: dict = None, **kwargs) -> List[SyntaxError]:
        """
        Controlla la corretta apertura e chiusura di parentesi in un file PHP
        
        Args:
            filepath: Il percorso del file PHP
            lines: Le linee del file
            plugin_config: La configurazione del plugin
            
        Returns:
            Una lista di errori trovati
        """
        errors = []
        
        # Prima uniamo tutte le linee per avere una visione completa del codice
        full_code = '\n'.join(lines)
        
        # Rimuoviamo stringhe e commenti per evitare falsi positivi
        cleaned_code = self._remove_strings_and_comments(full_code)
        
        # Ora controlliamo i bracket nel codice pulito
        stack = []
        brackets = {'(': ')', '{': '}', '[': ']'}
        
        line_number = 1
        column = 0
        
        for i, char in enumerate(cleaned_code):
            if char == '\n':
                line_number += 1
                column = 0
                continue
            
            column += 1
            
            if char in brackets.keys():
                stack.append((char, line_number, column))
            elif char in brackets.values():
                if not stack:
                    errors.append(SyntaxError(
                        line_number, 
                        lines[line_number-1].strip() if line_number <= len(lines) else "", 
                        "Parentesi chiusa senza apertura",
                        f"Trovata '{char}' senza corrispondente apertura",
                        f"Verifica se manca una '{list(brackets.keys())[list(brackets.values()).index(char)]}' prima"
                    ))
                else:
                    opening, open_line, open_col = stack.pop()
                    if brackets[opening] != char:
                        errors.append(SyntaxError(
                            line_number, 
                            lines[line_number-1].strip() if line_number <= len(lines) else "", 
                            "Parentesi non corrispondente",
                            f"Atteso '{brackets[opening]}' ma trovato '{char}'",
                            f"Sostituisci '{char}' con '{brackets[opening]}'"
                        ))
        
        # Controlla parentesi non chiuse
        while stack:
            opening, line_num, col = stack.pop()
            errors.append(SyntaxError(
                line_num, 
                lines[line_num-1].strip() if line_num <= len(lines) else "", 
                "Parentesi non chiusa",
                f"'{opening}' aperta ma mai chiusa",
                f"Aggiungi '{brackets[opening]}' alla fine del blocco"
            ))
            
        return errors
    
    def _remove_strings_and_comments(self, text):
        """Rimuove stringhe e commenti dal testo per evitare falsi positivi"""
        result = []
        i = 0
        in_single_quote = False
        in_double_quote = False
        in_single_comment = False
        in_multi_comment = False
        
        while i < len(text):
            char = text[i]
            
            # Gestione commenti multi-linea
            if not in_single_quote and not in_double_quote:
                if not in_multi_comment and text[i:i+2] == '/*':
                    in_multi_comment = True
                    result.append('  ')  # Sostituisci con spazi per mantenere la posizione
                    i += 2
                    continue
                elif in_multi_comment and text[i:i+2] == '*/':
                    in_multi_comment = False
                    result.append('  ')
                    i += 2
                    continue
                elif in_multi_comment:
                    result.append(' ' if char != '\n' else '\n')
                    i += 1
                    continue
                
                # Gestione commenti single-line
                if not in_single_comment and text[i:i+2] == '//':
                    in_single_comment = True
                    result.append('  ')
                    i += 2
                    continue
                elif in_single_comment and char == '\n':
                    in_single_comment = False
                    result.append('\n')
                    i += 1
                    continue
                elif in_single_comment:
                    result.append(' ')
                    i += 1
                    continue
            
            # Gestione stringhe
            if not in_single_comment and not in_multi_comment:
                # Verifica escape
                if i > 0 and text[i-1] == '\\':
                    result.append(' ')
                    i += 1
                    continue
                
                if char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote
                    result.append(' ')
                elif char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                    result.append(' ')
                elif in_single_quote or in_double_quote:
                    result.append(' ' if char != '\n' else '\n')
                else:
                    result.append(char)
            else:
                result.append(' ' if char != '\n' else '\n')
            
            i += 1
        
        return ''.join(result)