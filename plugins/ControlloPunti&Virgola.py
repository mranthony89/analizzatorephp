#!/usr/bin/env python3
"""
Plugin per il controllo dei punti e virgola in PHP
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

class SemicolonChecker(PluginBase):
    """
    Plugin per il controllo dei punti e virgola in PHP
    """
    
    def get_id(self):
        return "semicolon_checker"
        
    def get_name(self):
        return "Controllo Punti e Virgola"
        
    def get_description(self):
        return "Controlla la corretta presenza dei punti e virgola nei file PHP"
        
    def get_version(self):
        return "1.0.0"
        
    def get_author(self):
        return "Proietti House & Claude"
        
    def get_hooks(self):
        return {
            'syntax_check': [self.check_semicolons]
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

    def check_semicolons(self, filepath: str, lines: List[str], plugin_config=None, **kwargs) -> List[SyntaxError]:
        """Controlla i punti e virgola mancanti - versione migliorata per stringhe multi-riga"""
        errors = []
        in_multiline_string = False
        multiline_string_char = None
        multiline_start_line = 0
        
        for i, line in enumerate(lines, 1):
            # Se siamo in un blocco HTML, salta
            if self._is_in_html_block(lines, i - 1):
                continue
                
            # Controlla se siamo in un commento
            in_single_comment, in_multi_comment = self._is_in_comment(lines, i)
            if in_multi_comment:
                continue
                
            stripped = line.strip()
            
            # Se è un commento single-line, prendi solo la parte prima del commento
            if in_single_comment and '//' in line:
                comment_pos = line.find('//')
                stripped = line[:comment_pos].strip()
                
            # Ignora linee vuote
            if not stripped:
                continue
            
            # NUOVO: Gestione stringhe multi-riga
            # Controlla se inizia una stringa multi-riga
            if not in_multiline_string:
                multiline_match = self._check_multiline_string_start(stripped)
                if multiline_match:
                    in_multiline_string = True
                    multiline_string_char = multiline_match
                    multiline_start_line = i
                    continue  # Non controllare questa riga per punto e virgola
            else:
                # Siamo in una stringa multi-riga, controlla se finisce
                if self._check_multiline_string_end(stripped, multiline_string_char):
                    in_multiline_string = False
                    multiline_string_char = None
                    # Non controllare questa riga per punto e virgola se finisce con ");
                    if stripped.endswith('");') or stripped.endswith("');"):
                        continue
                else:
                    continue  # Siamo ancora dentro la stringa multi-riga
                
            # Verifica se stiamo dentro echo/print di HTML multilinea (logica originale)
            if i > 1:
                prev_line = lines[i-2].strip()
                if (prev_line.startswith('echo') or prev_line.startswith('print')) and prev_line.endswith("'") and not prev_line.endswith("';"):
                    # Siamo dentro un echo multilinea, salta
                    continue
                    
            # Ignora linee che fanno parte di HTML dentro echo/print
            if stripped.startswith('<') and not stripped.startswith('<?'):
                continue
                
            # Ignora dichiarazioni strutturali
            if any(keyword in stripped for keyword in [
                'namespace', 'class', 'interface', 'trait', 'extends', 'implements'
            ]) and not stripped.endswith(';'):
                continue
            
            # Ignora linee che aprono blocchi (inclusi array e chiamate di funzione multilinea)
            if stripped.endswith(('{', ':', '[', '(')) or '{' in stripped or '[' in stripped:
                continue
            
            # Ignora linee che chiudono blocchi o sono etichette case
            if stripped.endswith(('}', ']', ')')) or stripped.startswith('}') or stripped.startswith('case ') or stripped.startswith('default:'):
                continue
            
            # Ignora strutture di controllo
            control_structures = ['if', 'else', 'elseif', 'for', 'foreach', 'while', 'switch', 'catch', 'finally']
            if any(stripped.startswith(f"{cs}(") or stripped.startswith(f"{cs} (") for cs in control_structures):
                continue
            
            # Ignora dichiarazioni di funzione
            if re.match(r'^\s*(public|private|protected|static)?\s*function\s+\w+\s*\(', stripped):
                continue
            
            # Verifica se la linea necessita di punto e virgola
            needs_semicolon = False
            
            # Istruzioni PHP che devono terminare con ;
            statements = [
                (r'^\$\w+.*=(?!=)(?!.*\[$)', 'assegnazione variabile'),  # Escludi array e confronti
                (r'^echo\s+(?!.*[\'"]\s*$)', 'echo'),  # Escludi echo che aprono stringhe multilinea
                (r'^print\s+(?!.*[\'"]\s*$)', 'print'),
                (r'^return\s+', 'return'),
                (r'^return$', 'return vuoto'),
                (r'^include\s+', 'include'),
                (r'^include_once\s+', 'include_once'),
                (r'^require\s+', 'require'),
                (r'^require_once\s+', 'require_once'),
                (r'^die\s*\(', 'die'),
                (r'^exit\s*\(', 'exit'),
                (r'^throw\s+', 'throw'),
                (r'^break$', 'break'),
                (r'^continue$', 'continue'),
                (r'^\w+\s*\(.*\)\s*$', 'chiamata funzione'),
                (r'^unset\s*\(', 'unset'),
                (r'^isset\s*\(', 'isset'),
                (r'^empty\s*\(', 'empty'),
                (r'^list\s*\(', 'list'),
            ]
            
            for pattern, stmt_type in statements:
                if re.match(pattern, stripped):
                    needs_semicolon = True
                    break
            
            # Se la linea dovrebbe terminare con ; ma non lo fa
            if needs_semicolon and not stripped.endswith(';'):
                errors.append(SyntaxError(
                    i, stripped, "Punto e virgola mancante",
                    "La linea dovrebbe terminare con ;",
                    "Aggiungi ';' alla fine della riga"
                ))
        
        return errors

    def _check_multiline_string_start(self, line: str) -> str:
        """Controlla se la linea inizia una stringa multi-riga e ritorna il carattere di virgolette"""
        # Pattern per riconoscere l'inizio di stringhe multi-riga
        patterns = [
            # $var = $obj->method("
            (r'^\$\w+\s*=\s*\$\w+\s*->\s*\w+\s*\(\s*"$', '"'),
            (r'^\$\w+\s*=\s*\$\w+\s*->\s*\w+\s*\(\s*\'$', "'"),
            # $var = function("
            (r'^\$\w+\s*=\s*\w+\s*\(\s*"$', '"'),
            (r'^\$\w+\s*=\s*\w+\s*\(\s*\'$', "'"),
            # Varianti con spazi
            (r'^\$\w+\s*=\s*\$\w+\s*->\s*\w+\s*\(\s*"\s*$', '"'),
            (r'^\$\w+\s*=\s*\$\w+\s*->\s*\w+\s*\(\s*\'\s*$', "'"),
        ]
        
        for pattern, quote_char in patterns:
            if re.match(pattern, line):
                return quote_char
        
        return None

    def _check_multiline_string_end(self, line: str, expected_quote: str) -> bool:
        """Controlla se la linea termina una stringa multi-riga"""
        if expected_quote == '"':
            return line.endswith('");') or line.endswith('" );') or line.endswith('")') 
        elif expected_quote == "'":
            return line.endswith("');") or line.endswith("' );") or line.endswith("')")
        
        return False