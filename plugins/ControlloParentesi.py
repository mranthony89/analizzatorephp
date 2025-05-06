#!/usr/bin/env python3
"""
Plugin per il controllo delle parentesi per PHP Analyzer
Controlla la corretta apertura e chiusura di parentesi, graffe e quadre
"""
import re
from typing import List, Dict, Tuple, Any

try:
    # Tentativo di import diretto
    from analizzatore import PluginBase, SyntaxError
except ImportError:
    try:
        # Tentativo di import relativo
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from analizzatore import PluginBase, SyntaxError
    except ImportError:
        # Definizione di fallback per IDE e debugging
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

class ParentesiSyntaxChecker(PluginBase):
    """
    Plugin per il controllo della sintassi di parentesi, graffe e quadre in PHP
    """
    
    def get_id(self):
        return "parentesi_syntax_checker"
        
    def get_name(self):
        return "Controllo Parentesi"
        
    def get_description(self):
        return "Controlla la corretta apertura e chiusura di parentesi, graffe e quadre nei file PHP"
        
    def get_version(self):
        return "1.1.0"
        
    def get_author(self):
        return "PHP Analyzer Team"
        
    def get_hooks(self):
        return {
            'syntax_check': [self.check_parentesi]
        }
        
    def get_dependencies(self):
        return []
        
    def get_config_defaults(self):
        return {
            "check_in_html": False,
            "check_in_strings": False,
            "strict_mode": True,
            "ignore_patterns": [
                "*/vendor/*",
                "*/node_modules/*"
            ],
            "error_levels": {
                "parentesi_non_chiusa": "error",
                "parentesi_non_corrispondente": "warning",
                "parentesi_chiusa_senza_apertura": "error"
            },
            "custom_rules": {
                "max_nesting_depth": 5
            }
        }
        
    def check_parentesi(self, filepath: str, lines: List[str], plugin_config: Dict = None, **kwargs) -> List[SyntaxError]:
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
        
        # Usa la configurazione fornita o quella predefinita
        config = plugin_config or self.get_config_defaults()
        
        # Controlla se il file deve essere ignorato in base ai pattern nella configurazione
        if self._should_ignore_file(filepath, config):
            return errors
        
        # Prima uniamo tutte le linee per avere una visione completa del codice
        full_code = '\n'.join(lines)
        
        # Rimuoviamo stringhe e commenti per evitare falsi positivi
        cleaned_code = self._remove_strings_and_comments(full_code)
        
        # Ora controlliamo i bracket nel codice pulito
        stack = []
        brackets = {'(': ')', '{': '}', '[': ']'}
        
        line_number = 1
        column = 0
        max_nesting = 0
        current_nesting = 0
        
        for i, char in enumerate(cleaned_code):
            if char == '\n':
                line_number += 1
                column = 0
                continue
            
            column += 1
            
            if char in brackets.keys():
                stack.append((char, line_number, column))
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
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
                    current_nesting -= 1
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
        
        # Controlla nidificazione eccessiva
        max_nesting_allowed = config.get("custom_rules", {}).get("max_nesting_depth", 5)
        if max_nesting > max_nesting_allowed:
            errors.append(SyntaxError(
                1,  # Mettiamo come prima riga per semplicità
                "Intero file",
                "Nidificazione eccessiva",
                f"La profondità massima di nidificazione ({max_nesting}) supera il limite consentito ({max_nesting_allowed})",
                "Considera di ristrutturare il codice per ridurre la nidificazione"
            ))
            
        return errors
    
    def _should_ignore_file(self, filepath: str, config: Dict) -> bool:
        """Verifica se il file deve essere ignorato in base ai pattern"""
        import fnmatch
        
        ignore_patterns = config.get("ignore_patterns", [])
        for pattern in ignore_patterns:
            if fnmatch.fnmatch(filepath, pattern):
                return True
        return False
    
    def _remove_strings_and_comments(self, text: str) -> str:
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
                if not in_multi_comment and i + 1 < len(text) and text[i:i+2] == '/*':
                    in_multi_comment = True
                    result.append('  ')  # Sostituisci con spazi per mantenere la posizione
                    i += 2
                    continue
                elif in_multi_comment and i + 1 < len(text) and text[i:i+2] == '*/':
                    in_multi_comment = False
                    result.append('  ')
                    i += 2
                    continue
                elif in_multi_comment:
                    result.append(' ' if char != '\n' else '\n')
                    i += 1
                    continue
                
                # Gestione commenti single-line
                if not in_single_comment and i + 1 < len(text) and text[i:i+2] == '//':
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