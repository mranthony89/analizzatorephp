#!/usr/bin/env python3
"""
PHP Syntax Analyzer con Interfaccia Grafica
Analizza file PHP per trovare errori comuni di sintassi
"""

import os
import re
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import threading
import importlib.util
import json

@dataclass
class SyntaxError:
    line_number: int
    line_content: str
    error_type: str
    description: str
    suggestion: str
    category: str = "Generico"  # Categoria predefinita

class PluginBase:
    """Classe base per tutti i plugin"""
    
    def get_id(self):
        """Ritorna l'ID unico del plugin"""
        return "base_plugin"
    
    def get_name(self):
        """Ritorna il nome del plugin"""
        return "Plugin Base"
    
    def get_description(self):
        """Ritorna la descrizione del plugin"""
        return "Plugin base per l'analizzatore PHP"
    
    def get_version(self):
        """Ritorna la versione del plugin"""
        return "1.0.0"
    
    def get_author(self):
        """Ritorna l'autore del plugin"""
        return "PHP Analyzer Team"
    
    def get_hooks(self):
        """Ritorna un dizionario di hook implementati dal plugin"""
        return {}
    
    def get_dependencies(self):
        """Ritorna una lista di ID dei plugin da cui dipende"""
        return []
    
    def get_config_defaults(self):
        """Ritorna la configurazione predefinita del plugin"""
        return {}

class PluginManager:
    """Gestore dei plugin per l'analizzatore PHP"""
    
    def __init__(self, plugins_dir="plugins"):
        self.plugins_dir = plugins_dir
        self.plugins = {}
        self.hooks = {}
        self.config_file = os.path.join(plugins_dir, "config.json")
        self.plugin_configs = {}
        
        # Carica la configurazione dei plugin
        self._load_config()
    
    def diagnose_plugins_directory(self):
        """Stampa informazioni diagnostiche sulla directory dei plugin"""
        print(f"\n=== Diagnostica directory plugin ===")
        plugins_dir = os.path.abspath(self.plugins_dir)
        print(f"Directory plugin: {plugins_dir}")
        
        if not os.path.exists(plugins_dir):
            print(f"La directory {plugins_dir} non esiste!")
            return
        
        files = os.listdir(plugins_dir)
        print(f"Numero di file nella directory: {len(files)}")
        
        python_files = [f for f in files if f.endswith('.py') and not f.startswith('__')]
        print(f"File Python trovati: {len(python_files)}")
        for py_file in python_files:
            print(f"  - {py_file}")
        
        other_files = [f for f in files if not (f.endswith('.py') and not f.startswith('__'))]
        if other_files:
            print(f"Altri file trovati: {len(other_files)}")
            for other_file in other_files:
                print(f"  - {other_file}")
        
        print("=== Fine diagnostica ===\n")
    
    def _load_plugin_from_file(self, filepath):
        """Carica un plugin da un file Python"""
        plugin_name = os.path.splitext(os.path.basename(filepath))[0]
        spec = importlib.util.spec_from_file_location(plugin_name, filepath)
        
        if spec is None:
            raise ImportError(f"Impossibile caricare il plugin da {filepath}")
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[plugin_name] = module
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            raise ImportError(f"Errore durante l'esecuzione del modulo {plugin_name}: {e}")
        
        # Cerca tutte le classi che ereditano da PluginBase
        for name, obj in module.__dict__.items():
            if (isinstance(obj, type) and 
                issubclass(obj, PluginBase) and 
                obj is not PluginBase):
                
                try:
                    plugin_instance = obj()
                    plugin_id = plugin_instance.get_id()
                    
                    if plugin_id in self.plugins:
                        raise ValueError(f"Plugin ID {plugin_id} già esistente")
                    
                    self.plugins[plugin_id] = plugin_instance
                    print(f"Plugin caricato: {plugin_id}")
                    return
                
                except Exception as e:
                    raise RuntimeError(f"Errore durante l'inizializzazione del plugin {name}: {e}")
        
        raise RuntimeError(f"Nessuna classe Plugin valida trovata in {filepath}")
    
    def _load_config(self):
        """Carica la configurazione dei plugin dal file JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.plugin_configs = json.load(f)
            else:
                self.plugin_configs = {}
        except Exception as e:
            print(f"Errore nel caricamento della configurazione dei plugin: {e}")
            self.plugin_configs = {}
    
    def _save_config(self):
        """Salva la configurazione dei plugin nel file JSON"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.plugin_configs, f, indent=4)
        except Exception as e:
            print(f"Errore nel salvataggio della configurazione dei plugin: {e}")
    
    def load_plugins(self):
        """Carica tutti i plugin dalla directory plugins"""
        print(f"\n=== Caricamento plugin ===")
        
        # Esegui diagnostica
        self.diagnose_plugins_directory()
        
        if not os.path.exists(self.plugins_dir):
            os.makedirs(self.plugins_dir, exist_ok=True)
            print(f"Directory plugin creata: {self.plugins_dir}")
            return
        
        # Svuota le liste di plugin e hook
        self.plugins = {}
        self.hooks = {}
        
        # Carica tutti i file Python nella directory plugins
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    filepath = os.path.join(self.plugins_dir, filename)
                    self._load_plugin_from_file(filepath)
                except Exception as e:
                    print(f"Errore nel caricamento del plugin {filename}: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Registra gli hook di tutti i plugin
        for plugin_id, plugin in self.plugins.items():
            self._register_plugin_hooks(plugin_id, plugin)
        
        print(f"=== Caricamento completato: {len(self.plugins)} plugin ===\n")

    def _register_plugin_hooks(self, plugin_id, plugin):
        """Registra gli hook di un plugin"""
        hooks = plugin.get_hooks()
        for hook_name, methods in hooks.items():
            if hook_name not in self.hooks:
                self.hooks[hook_name] = []
            
            for method in methods:
                self.hooks[hook_name].append((plugin_id, method))
    
    def get_plugin_config(self, plugin_id):
        """Ritorna la configurazione di un plugin"""
        return self.plugin_configs.get(plugin_id, {})
    
    def save_plugin_config(self, plugin_id, config):
        """Salva la configurazione di un plugin"""
        self.plugin_configs[plugin_id] = config
        self._save_config()
    
    def call_hook(self, hook_name, *args, **kwargs):
        """Esegue tutti i gestori registrati per un hook"""
        results = []
        
        if hook_name in self.hooks:
            for plugin_id, method in self.hooks[hook_name]:
                try:
                    # Controlla se il plugin è abilitato
                    plugin_config = self.get_plugin_config(plugin_id) or {}
                    if not plugin_config.get("enabled", True):
                    # Plugin disabilitato, salta
                        continue
                
                    # Passa la configurazione del plugin come argomento
                    plugin_config = self.get_plugin_config(plugin_id) or {}
                    kwargs['plugin_config'] = self.get_plugin_config(plugin_id)
                    result = method(*args, **kwargs)
                    
                    # Se il risultato è una lista di SyntaxError, aggiungi la categoria
                    if result and isinstance(result, list) and all(isinstance(err, SyntaxError) for err in result):
                        plugin = self.plugins.get(plugin_id)
                        if plugin:
                            plugin_name = plugin.get_name()
                            for err in result:
                                if not hasattr(err, 'category') or not err.category or err.category == "Generico":
                                    err.category = plugin_name
                    
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    print(f"Errore nell'esecuzione dell'hook {hook_name} del plugin {plugin_id}: {e}")
        
        return results

class PHPAnalyzer:
    def __init__(self):
        self.errors = []
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_plugins()
        
    def analyze_file(self, filepath: str) -> List[SyntaxError]:
        """Analizza un singolo file PHP"""
        self.errors = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Esegui controlli base
            #self._check_php_tags(lines)
            #self._check_quotes(lines)
            #self._check_semicolons(lines)
            #self._check_function_syntax(lines)
            #self._check_array_syntax(lines)
            #self._check_variable_syntax(lines)
            
            # Esegui controlli tramite plugin
            plugin_errors = self.plugin_manager.call_hook('syntax_check', filepath=filepath, lines=lines)
            for error_list in plugin_errors:
                self.errors.extend(error_list)
            
        except Exception as e:
            print(f"Errore durante l'analisi del file {filepath}: {e}")
            
        return self.errors
    
    def _is_in_html_block(self, lines: List[str], line_num: int) -> bool:
        """Verifica se una linea è all'interno di un blocco HTML (dopo ?>)"""
        in_php = True
        for i in range(line_num):
            if '<?php' in lines[i] or '<?' in lines[i]:
                in_php = True
            elif '?>' in lines[i]:
                in_php = False
        return not in_php
    
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
    
    def _check_brackets(self, lines: List[str]):
        """Controlla parentesi, graffe e quadre"""
        
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
                    self.errors.append(SyntaxError(
                        line_number, 
                        lines[line_number-1].strip() if line_number <= len(lines) else "", 
                        "Parentesi chiusa senza apertura",
                        f"Trovata '{char}' senza corrispondente apertura",
                        f"Verifica se manca una '{list(brackets.keys())[list(brackets.values()).index(char)]}' prima"
                    ))
                else:
                    opening, open_line, open_col = stack.pop()
                    if brackets[opening] != char:
                        self.errors.append(SyntaxError(
                            line_number, 
                            lines[line_number-1].strip() if line_number <= len(lines) else "", 
                            "Parentesi non corrispondente",
                            f"Atteso '{brackets[opening]}' ma trovato '{char}'",
                            f"Sostituisci '{char}' con '{brackets[opening]}'"
                        ))
        
        # Controlla parentesi non chiuse
        while stack:
            opening, line_num, col = stack.pop()
            self.errors.append(SyntaxError(
                line_num, 
                lines[line_num-1].strip() if line_num <= len(lines) else "", 
                "Parentesi non chiusa",
                f"'{opening}' aperta ma mai chiusa",
                f"Aggiungi '{brackets[opening]}' alla fine del blocco"
            ))
    
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
    
    def _check_semicolons(self, lines: List[str]):
        """Controlla i punti e virgola mancanti"""
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
                
            # Verifica se stiamo dentro echo/print di HTML multilinea
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
                self.errors.append(SyntaxError(
                    i, stripped, "Punto e virgola mancante",
                    "La linea dovrebbe terminare con ;",
                    "Aggiungi ';' alla fine della riga"
                ))
    
    def _check_quotes(self, lines: List[str]):
        """Controlla virgolette non chiuse - versione migliorata per gestire stringhe multilinea"""
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
                    self.errors.append(SyntaxError(
                        i, line.strip(), 
                        f"Virgoletta {quote_type} non chiusa",
                        f"La stringa iniziata con {string_char} non è stata chiusa",
                        f"Verifica se manca una {string_char} alla fine della stringa"
                    ))
    
    def _check_php_tags(self, lines: List[str]):
        """Controlla i tag PHP"""
        php_open = False
        open_line = 0
        
        for i, line in enumerate(lines, 1):
            if '<?php' in line or '<?' in lines[i-1]:
                if php_open:
                    self.errors.append(SyntaxError(
                        i, line.strip(), "Tag PHP già aperto",
                        "Trovato un nuovo tag di apertura PHP senza chiudere il precedente",
                        "Aggiungi '?>' prima di questo tag o rimuovi questo tag"
                    ))
                php_open = True
                open_line = i
            
            if '?>' in line:
                if not php_open:
                    self.errors.append(SyntaxError(
                        i, line.strip(), "Tag PHP chiuso senza apertura",
                        "Trovato '?>' senza corrispondente '<?php' o '<?'",
                        "Rimuovi '?>' o aggiungi '<?php' prima"
                    ))
                php_open = False
    
    def _check_function_syntax(self, lines: List[str]):
        """Controlla la sintassi delle funzioni"""
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
                        self.errors.append(SyntaxError(
                            i, line.strip(), "Sintassi funzione errata",
                            "La dichiarazione della funzione non segue il pattern corretto",
                            "Usa: function nomeFunzione(parametri) {"
                        ))
    
    def _check_array_syntax(self, lines: List[str]):
        """Controlla la sintassi degli array"""
        for i, line in enumerate(lines, 1):
            # Se siamo in un blocco HTML, salta
            if self._is_in_html_block(lines, i - 1):
                continue
                
            # Ignora commenti
            in_single_comment, in_multi_comment = self._is_in_comment(lines, i)
            if in_single_comment or in_multi_comment:
                continue
                
            # Controlla virgole negli array
            if 'array(' in line or '[' in line:
                # Cerca pattern di elementi array senza virgola
                if re.search(r'["\'\w]\s+["\'\w]', line):
                    # Verifica che non sia dentro una stringa o un commento
                    match = re.search(r'["\'\w]\s+["\'\w]', line)
                    if match and not self._is_in_string(line, match.start()):
                        self.errors.append(SyntaxError(
                            i, line.strip(), "Virgola mancante in array",
                            "Possibile virgola mancante tra elementi dell'array",
                            "Aggiungi ',' tra gli elementi dell'array"
                        ))
    
    def _check_variable_syntax(self, lines: List[str]):
        """Controlla la sintassi delle variabili"""
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
                                self.errors.append(SyntaxError(
                                    i, line.strip(), "Variabile senza $",
                                    f"La variabile '{word}' non ha il simbolo $",
                                    f"Cambia '{word}' in '${word}'"
                                ))
    def fix_file(self, filepath: str, errors: List[SyntaxError]) -> bool:
        """Corregge automaticamente gli errori nel file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Tieni traccia se sono state apportate modifiche
            modifiche_effettuate = False
            
            # Ordina gli errori per linea (dal basso verso l'alto per evitare offset)
            errors.sort(key=lambda x: x.line_number, reverse=True)
            
            for error in errors:
                line_idx = error.line_number - 1
                if line_idx < 0 or line_idx >= len(lines):
                    continue  # Ignora errori con numeri di riga invalidi
                    
                line = lines[line_idx]
                
                # Correggi gli errori in base al tipo
                if error.error_type == "Punto e virgola mancante":
                    if not line.strip().endswith(';'):
                        lines[line_idx] = line.rstrip() + ';\n'
                        modifiche_effettuate = True
                
                elif error.error_type == "Variabile senza $":
                    var_match = re.search(r"La variabile '(\w+)'", error.description)
                    if var_match:
                        var_name = var_match.group(1)
                        # Assicurati di sostituire solo la variabile e non parti di altre parole
                        pattern = r'\b' + re.escape(var_name) + r'\b(?!\$)'
                        new_line = re.sub(pattern, f'${var_name}', line)
                        if new_line != line:
                            lines[line_idx] = new_line
                            modifiche_effettuate = True
                
                elif error.error_type == "Virgoletta singola non chiusa" or error.error_type == "Virgoletta doppia non chiusa":
                    # Determina il tipo di virgoletta
                    quote_type = "'" if "singola" in error.error_type else '"'
                    if line.count(quote_type) % 2 == 1:  # Se c'è un numero dispari di virgolette
                        lines[line_idx] = line.rstrip() + quote_type + ";\n"
                        modifiche_effettuate = True
                
                elif error.error_type == "Virgola mancante in array":
                    # Cerca due elementi adiacenti senza virgola
                    match = re.search(r'(["\'\w])\s+(["\'\w])', line)
                    if match:
                        pos = match.start() + 1
                        lines[line_idx] = line[:pos] + ',' + line[pos:]
                        modifiche_effettuate = True
                
                elif error.error_type == "Parentesi non chiusa":
                    bracket_match = re.search(r"'(.)'", error.description)
                    if bracket_match:
                        opening_bracket = bracket_match.group(1)
                        closing_bracket = {'(': ')', '{': '}', '[': ']'}.get(opening_bracket)
                        if closing_bracket:
                            lines[line_idx] = line.rstrip() + closing_bracket + "\n"
                            modifiche_effettuate = True
                
                # Aggiungi altri tipi di errori qui...
            
            # Scrivi il file corretto solo se sono state apportate modifiche
            if modifiche_effettuate:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.writelines(lines)
                return True
            else:
                print(f"Nessuna correzione disponibile per gli errori trovati in {filepath}")
                return False
                
        except Exception as e:
            print(f"Errore durante la correzione del file: {e}")
            return False

        
class PHPAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PHP Syntax Analyzer")
        self.root.geometry("900x700")
        
        self.analyzer = PHPAnalyzer()
        self.current_file = None
        self.current_errors = []
        
        self.create_widgets()
    
    def diagnose_plugins(self):
        """Esegue la diagnostica dei plugin"""
        self.analyzer.plugin_manager.diagnose_plugins_directory()
        messagebox.showinfo("Diagnostica", "Diagnostica completa. Controlla la console per i dettagli.")
    
    def show_plugin_manager(self):
        """Mostra la finestra di gestione dei plugin"""
        manager_window = tk.Toplevel(self.root)
        manager_window.title("Gestione Plugin")
        manager_window.geometry("600x500")
        
        # Frame principale
        main_frame = ttk.Frame(manager_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Il resto del tuo codice per questo metodo...
    
    def _toggle_plugin(self, plugin_id):
        """Abilita o disabilita un plugin"""
        enabled = self.plugin_enabled[plugin_id].get()
        print(f"Plugin {plugin_id} {'abilitato' if enabled else 'disabilitato'}")
        # Qui potresti salvare lo stato dei plugin in una configurazione
        
    def create_widgets(self):
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurazione del peso delle righe e colonne
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Frame per i controlli file/directory
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Nella funzione create_widgets, aggiungi questo pulsante al control_frame
        ttk.Button(control_frame, text="Gestione Plugin", command=self.show_plugin_manager).grid(row=0, column=6, padx=5)
        
        # Pulsanti per selezionare file/directory
        ttk.Button(control_frame, text="Seleziona File PHP", command=self.select_file).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="Seleziona Directory", command=self.select_directory).grid(row=0, column=1, padx=5)
        
        # Checkbox per analisi ricorsiva
        self.recursive_var = tk.BooleanVar()
        ttk.Checkbutton(control_frame, text="Analisi ricorsiva", variable=self.recursive_var).grid(row=0, column=2, padx=5)
        
        # Pulsante di analisi
        ttk.Button(control_frame, text="Analizza", command=self.analyze).grid(row=0, column=3, padx=5)
        
        # Pulsante di ricarica plugin
        ttk.Button(control_frame, text="Ricarica Plugin", command=self.reload_plugins).grid(row=0, column=4, padx=5)
        
        
        # Label per mostrare il file/directory corrente
        self.current_path_var = tk.StringVar(value="Nessun file/directory selezionato")
        ttk.Label(main_frame, textvariable=self.current_path_var).grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Area principale per visualizzare gli errori
        self.error_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=100, height=30)
        self.error_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tag per la formattazione del testo (aggiungi questa riga insieme alle altre tag già presenti)
        self.error_text.tag_configure("category_header", foreground="dark blue", font=("TkDefaultFont", 10, "bold"))
        
        # Tag per la formattazione del testo
        self.error_text.tag_configure("error", foreground="red")
        self.error_text.tag_configure("suggestion", foreground="green")
        self.error_text.tag_configure("info", foreground="blue")
        self.error_text.tag_configure("filename", foreground="purple", font=("TkDefaultFont", 11, "bold"))
        
        # Frame per i pulsanti di azione
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Pulsanti di azione
        ttk.Button(action_frame, text="Correggi Errori", command=self.fix_errors).grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="Salva Report", command=self.save_report).grid(row=0, column=1, padx=5)
        ttk.Button(action_frame, text="Pulisci", command=self.clear_output).grid(row=0, column=2, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Menu bar
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        # Menu File
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Seleziona File", command=self.select_file)
        file_menu.add_command(label="Seleziona Directory", command=self.select_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self.root.quit)
        
        # Menu Plugin
        plugin_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Plugin", menu=plugin_menu)
        plugin_menu.add_command(label="Ricarica Plugin", command=self.reload_plugins)
        plugin_menu.add_separator()
        
        # Aggiungi tutti i plugin al menu
        for plugin_id, plugin in self.analyzer.plugin_manager.plugins.items():
            plugin_menu.add_command(
                label=f"{plugin.get_name()} - {plugin.get_version()}",
                command=lambda pid=plugin_id: self.configure_plugin(pid)
            )
        
        # Chiamata agli hook ui_extension
        self.analyzer.plugin_manager.call_hook('ui_extension', gui=self)
    
    def reload_plugins(self):
        """Ricarica tutti i plugin"""
        self.analyzer.plugin_manager.load_plugins()
        messagebox.showinfo("Plugin", f"Caricati {len(self.analyzer.plugin_manager.plugins)} plugin")
        
        # Aggiorna l'interfaccia per riflettere i nuovi plugin
        self.root.destroy()
        root = tk.Tk()
        app = PHPAnalyzerGUI(root)
        root.mainloop()
    
    def configure_plugin(self, plugin_id):
        """Mostra la finestra di configurazione di un plugin"""
        plugin = self.analyzer.plugin_manager.plugins.get(plugin_id)
        if not plugin:
            return
        
        config_window = tk.Toplevel(self.root)
        config_window.title(f"Configurazione {plugin.get_name()}")
        config_window.geometry("500x400")
        
        ttk.Label(config_window, text=f"Plugin: {plugin.get_name()} (ID: {plugin_id})").pack(pady=10)
        ttk.Label(config_window, text=f"Descrizione: {plugin.get_description()}").pack(pady=5)
        ttk.Label(config_window, text=f"Versione: {plugin.get_version()}").pack(pady=5)
        ttk.Label(config_window, text=f"Autore: {plugin.get_author()}").pack(pady=5)
        
        # Visualizza gli hook implementati
        hooks_text = "Hook implementati:\n"
        plugin_hooks = plugin.get_hooks()
        for hook_name, methods in plugin_hooks.items():
            for method in methods:
                hooks_text += f"- {hook_name}: {method.__name__}\n"
        
        ttk.Label(config_window, text=hooks_text).pack(pady=10)

    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Seleziona file PHP",
            filetypes=[("PHP files", "*.php"), ("All files", "*.*")]
        )
        if filename:
            self.current_file = filename
            self.current_path_var.set(f"File: {filename}")
            pass
            
    def select_directory(self):
        directory = filedialog.askdirectory(title="Seleziona directory")
        if directory:
            self.current_file = directory
            self.current_path_var.set(f"Directory: {directory}")
            pass
            
    def analyze(self):
        if not self.current_file:
            messagebox.showwarning("Attenzione", "Seleziona prima un file o una directory")
            return
        
        self.clear_output()
        self.status_var.set("Analisi in corso...")
        
        # Esegui l'analisi in un thread separato
        thread = threading.Thread(target=self.run_analysis)
        thread.daemon = True
        thread.start()

        
    def run_analysis(self):
        try:
            files_to_analyze = []
            
            if os.path.isfile(self.current_file):
                if self.current_file.endswith('.php'):
                    files_to_analyze.append(self.current_file)
            elif os.path.isdir(self.current_file):
                if self.recursive_var.get():
                    for root, dirs, files in os.walk(self.current_file):
                        for file in files:
                            if file.endswith('.php'):
                                files_to_analyze.append(os.path.join(root, file))
                else:
                    for file in os.listdir(self.current_file):
                        if file.endswith('.php'):
                            files_to_analyze.append(os.path.join(self.current_file, file))
            
            if not files_to_analyze:
                self.root.after(0, lambda: messagebox.showinfo("Info", "Nessun file PHP trovato"))
                self.root.after(0, lambda: self.status_var.set("Pronto"))
                return
            
            total_errors = 0
            self.current_errors = []
            
            for filepath in files_to_analyze:
                errors = self.analyzer.analyze_file(filepath)
                if errors:
                    self.current_errors.extend([(filepath, error) for error in errors])
                    total_errors += len(errors)
                    self.root.after(0, lambda fp=filepath, err=errors: self.display_file_errors(fp, err))
                else:
                    self.root.after(0, lambda fp=filepath: self.display_no_errors(fp))
            
            status_message = f"Analisi completata. Files: {len(files_to_analyze)}, Errori: {total_errors}"
            self.root.after(0, lambda: self.status_var.set(status_message))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Errore", f"Errore durante l'analisi: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Errore durante l'analisi"))
    
    def display_file_errors(self, filepath, errors):
        self.error_text.insert(tk.END, f"\n{'='*80}\n", "filename")
        self.error_text.insert(tk.END, f"File: {filepath}\n", "filename")
        self.error_text.insert(tk.END, f"{'='*80}\n\n", "filename")
    
        # Raggruppa errori per categoria
        errors_by_category = {}
        for error in errors:
            category = getattr(error, 'category', "Generico")
            if category not in errors_by_category:
                errors_by_category[category] = []
            errors_by_category[category].append(error)
    
        # Tag per le categorie se non esistono già
        if not hasattr(self.error_text, 'category_tags_created'):
            self.error_text.tag_configure("category_header", foreground="dark blue", font=("TkDefaultFont", 10, "bold"))
            self.error_text.category_tags_created = True
    
        # Mostra errori raggruppati per categoria
        for category, category_errors in errors_by_category.items():
            self.error_text.insert(tk.END, f"\n== {category} ({len(category_errors)}) ==\n", "category_header")
        
            for error in category_errors:
                self.error_text.insert(tk.END, f"Riga {error.line_number}: ", "error")
                self.error_text.insert(tk.END, f"{error.error_type}\n", "error")
                self.error_text.insert(tk.END, f"   Codice: {error.line_content}\n")
                self.error_text.insert(tk.END, f"   Problema: {error.description}\n", "info")
                self.error_text.insert(tk.END, f"   Suggerimento: {error.suggestion}\n\n", "suggestion")
    
        # Aggiungi una riga vuota alla fine
        self.error_text.insert(tk.END, "\n")

    def display_no_errors(self, filepath):
        self.error_text.insert(tk.END, f"\n✓ Nessun errore trovato in: {filepath}\n", "suggestion")
    
    def fix_errors(self):
        if not self.current_errors:
            messagebox.showinfo("Info", "Nessun errore da correggere")
            return
    
        if messagebox.askyesno("Conferma", "Vuoi correggere automaticamente gli errori trovati?"):
            fixed_files = set()
            errors_fixed = 0
            errors_by_file = {}
        
            for filepath, error in self.current_errors:
                if filepath not in errors_by_file:
                    errors_by_file[filepath] = []
                errors_by_file[filepath].append(error)
        
            for filepath, errors in errors_by_file.items():
                if self.analyzer.fix_file(filepath, errors):
                    fixed_files.add(filepath)
                    errors_fixed += len(errors)
        
            if fixed_files:
                messagebox.showinfo("Successo", f"Corretti {errors_fixed} errori in {len(fixed_files)} file")
                self.analyze()  # Rianalizza dopo la correzione
            else:
                messagebox.showwarning("Attenzione", "Nessun file è stato corretto.\n"
                                  "Potrebbero essere necessarie correzioni manuali o gli errori non sono supportati per la correzione automatica.")
            
    def save_report(self):
        if not self.error_text.get("1.0", tk.END).strip():
            messagebox.showwarning("Attenzione", "Nessun report da salvare")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(self.error_text.get("1.0", tk.END))
                messagebox.showinfo("Successo", "Report salvato con successo")
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante il salvataggio: {str(e)}")
        pass
        
    def clear_output(self):
        self.error_text.delete("1.0", tk.END)
        self.current_errors = []
        pass
        
def main():
    root = tk.Tk()
    app = PHPAnalyzerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()