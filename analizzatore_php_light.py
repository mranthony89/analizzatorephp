#!/usr/bin/env python3
"""
PHP Syntax Analyzer con Interfaccia Grafica e Sistema di Plugin
Analizza file PHP per trovare errori comuni di sintassi
"""

import os
import re
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import List, Dict, Tuple, Optional, Any, Callable
from dataclasses import dataclass
import threading
import importlib.util
import json
import time
import hashlib
import traceback

@dataclass
class SyntaxError:
    """Classe per rappresentare un errore di sintassi"""
    line_number: int
    line_content: str
    error_type: str
    description: str
    suggestion: str

class PluginBase:
    """Classe base per i plugin dell'analizzatore PHP"""
    def get_id(self):
        """Restituisce l'identificativo unico del plugin"""
        return self.__class__.__name__
    
    def get_name(self):
        """Restituisce il nome descrittivo del plugin"""
        return self.__class__.__name__
    
    def get_description(self):
        """Restituisce la descrizione del plugin"""
        return ""
    
    def get_version(self):
        """Restituisce la versione del plugin"""
        return "1.0.0"
    
    def get_author(self):
        """Restituisce l'autore del plugin"""
        return "Unknown"
    
    def get_hooks(self):
        """Restituisce un dizionario degli hook implementati dal plugin"""
        return {}
    
    def get_dependencies(self):
        """Restituisce una lista di ID di plugin da cui dipende"""
        return []
    
    def get_config_defaults(self):
        """Restituisce le configurazioni predefinite del plugin"""
        return {}

class PluginManager:
    """Gestisce il caricamento e l'esecuzione dei plugin per l'analizzatore PHP"""
    def __init__(self):
        self.plugins = {}
        self.hooks = {
            'pre_analyze': [],     # Eseguito prima dell'analisi
            'post_analyze': [],    # Eseguito dopo l'analisi
            'syntax_check': [],    # Controlli sintattici
            'semantic_check': [],  # Controlli semantici
            'fix_error': [],       # Correzione errori
            'ui_extension': [],    # Estensioni UI
            'cache_invalidate': [] # Controllo invalidazione cache
        }
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Carica la configurazione dei plugin"""
        config_path = "plugin_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Errore nel caricamento della configurazione: {str(e)}")
                self.config = {}
    
    def save_config(self):
        """Salva la configurazione dei plugin"""
        config_path = "plugin_config.json"
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Errore nel salvataggio della configurazione: {str(e)}")
    
    def get_plugin_config(self, plugin_id):
        """Ottiene la configurazione per un plugin specifico"""
        if plugin_id not in self.config:
            self.config[plugin_id] = {}
        return self.config[plugin_id]
    
    def set_plugin_config(self, plugin_id, config_data):
        """Imposta la configurazione per un plugin specifico"""
        self.config[plugin_id] = config_data
        self.save_config()
    
    def register_plugin(self, plugin_instance):
        """Registra un nuovo plugin"""
        plugin_id = plugin_instance.get_id()
        if plugin_id in self.plugins:
            print(f"Attenzione: Plugin '{plugin_id}' già registrato, verrà sovrascritto")
        
        # Verifica dipendenze
        dependencies = plugin_instance.get_dependencies()
        for dep_id in dependencies:
            if dep_id not in self.plugins:
                print(f"Attenzione: Plugin '{plugin_id}' dipende da '{dep_id}' che non è caricato")
                return False
        
        # Carica configurazione di default se non esiste
        if plugin_id not in self.config:
            self.config[plugin_id] = plugin_instance.get_config_defaults()
        
        self.plugins[plugin_id] = plugin_instance
        
        # Registra i metodi del plugin negli hook appropriati
        for hook_name, methods in plugin_instance.get_hooks().items():
            if hook_name in self.hooks:
                for method in methods:
                    self.hooks[hook_name].append((plugin_id, method))
            else:
                print(f"Attenzione: Hook '{hook_name}' non supportato nel plugin '{plugin_id}'")
        
        return True
    
    def execute_hook(self, hook_name, *args, **kwargs):
        """Esegue tutti i metodi registrati per un determinato hook"""
        results = []
        for plugin_id, method in self.hooks.get(hook_name, []):
            try:
                # Passa la configurazione del plugin
                kwargs['plugin_config'] = self.get_plugin_config(plugin_id)
                result = method(*args, **kwargs)
                if result is not None:
                    results.append(result)
            except Exception as e:
                print(f"Errore nell'esecuzione del plugin '{plugin_id}': {str(e)}")
                traceback.print_exc()
        return results
    
    def load_plugins_from_directory(self, directory):
        """Carica plugin da una directory"""
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print(f"Creata directory plugin: {directory}")
            except Exception as e:
                print(f"Impossibile creare directory plugin: {str(e)}")
            return
        
        # Prima carica i plugin senza dipendenze
        plugin_files = [f for f in os.listdir(directory) if f.endswith('.py') and not f.startswith('__')]
        loaded_plugins = set()
        
        while plugin_files:
            loaded_count = 0
            remaining_files = []
            
            for filename in plugin_files:
                try:
                    module_path = os.path.join(directory, filename)
                    spec = importlib.util.spec_from_file_location("plugin", module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Cerca la classe del plugin nel modulo
                    plugin_classes = []
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, PluginBase) and attr != PluginBase:
                            plugin_classes.append(attr)
                    
                    if not plugin_classes:
                        print(f"Nessuna classe plugin trovata in {filename}")
                        continue
                    
                    # Registra i plugin
                    all_deps_loaded = True
                    for plugin_class in plugin_classes:
                        plugin_instance = plugin_class()
                        deps = plugin_instance.get_dependencies()
                        
                        if all(dep in loaded_plugins for dep in deps):
                            if self.register_plugin(plugin_instance):
                                loaded_plugins.add(plugin_instance.get_id())
                                loaded_count += 1
                                print(f"Plugin caricato: {plugin_instance.get_id()} (v{plugin_instance.get_version()})")
                        else:
                            all_deps_loaded = False
                    
                    if not all_deps_loaded:
                        remaining_files.append(filename)
                        
                except Exception as e:
                    print(f"Errore nel caricamento del plugin {filename}: {str(e)}")
                    traceback.print_exc()
            
            # Se nessun plugin è stato caricato in questo ciclo, rompi il loop
            if loaded_count == 0 and remaining_files == plugin_files:
                for filename in remaining_files:
                    print(f"Impossibile caricare {filename} - dipendenze non soddisfatte")
                break
            
            plugin_files = remaining_files
        
        # Salva la configurazione aggiornata
        self.save_config()

class CacheManager:
    """Gestisce la cache dei risultati dell'analisi"""
    def __init__(self, cache_dir=".cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir)
            except Exception as e:
                print(f"Impossibile creare directory cache: {str(e)}")
                self.cache_dir = None
    
    def get_cache_path(self, filepath):
        """Ottiene il percorso del file cache per un filepath"""
        if not self.cache_dir:
            return None
        
        file_hash = hashlib.md5(filepath.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{file_hash}.json")
    
    def is_cache_valid(self, filepath, plugin_manager):
        """Controlla se la cache è valida per un filepath"""
        if not self.cache_dir:
            return False
        
        cache_path = self.get_cache_path(filepath)
        if not os.path.exists(cache_path):
            return False
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Controlla timestamp e hash del file
            file_mtime = os.path.getmtime(filepath)
            if file_mtime > cache_data.get('timestamp', 0):
                return False
            
            # Calcola hash del file
            with open(filepath, 'rb') as f:
                file_content = f.read()
                current_hash = hashlib.md5(file_content).hexdigest()
            
            if current_hash != cache_data.get('file_hash', ''):
                return False
            
            # Chiedi a tutti i plugin se la cache è valida
            cache_valid = True
            invalidate_results = plugin_manager.execute_hook('cache_invalidate', filepath=filepath, cache_data=cache_data)
            for result in invalidate_results:
                if result is False:
                    cache_valid = False
                    break
            
            return cache_valid
            
        except Exception as e:
            print(f"Errore nella verifica della cache: {str(e)}")
            return False
    
    def get_cached_results(self, filepath):
        """Ottiene i risultati in cache per un filepath"""
        if not self.cache_dir:
            return None
        
        cache_path = self.get_cache_path(filepath)
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Deserializza gli errori
            errors = []
            for error_data in cache_data.get('errors', []):
                errors.append(SyntaxError(
                    line_number=error_data['line_number'],
                    line_content=error_data['line_content'],
                    error_type=error_data['error_type'],
                    description=error_data['description'],
                    suggestion=error_data['suggestion']
                ))
            
            return errors
            
        except Exception as e:
            print(f"Errore nel recupero della cache: {str(e)}")
            return None
    
    def save_results_to_cache(self, filepath, errors):
        """Salva i risultati in cache per un filepath"""
        if not self.cache_dir:
            return False
        
        cache_path = self.get_cache_path(filepath)
        
        try:
            # Calcola hash del file
            with open(filepath, 'rb') as f:
                file_content = f.read()
                file_hash = hashlib.md5(file_content).hexdigest()
            
            # Serializza gli errori
            error_data = []
            for error in errors:
                error_data.append({
                    'line_number': error.line_number,
                    'line_content': error.line_content,
                    'error_type': error.error_type,
                    'description': error.description,
                    'suggestion': error.suggestion
                })
            
            cache_data = {
                'timestamp': time.time(),
                'file_hash': file_hash,
                'errors': error_data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=4)
            
            return True
            
        except Exception as e:
            print(f"Errore nel salvataggio della cache: {str(e)}")
            return False

class PHPAnalyzer:
    def __init__(self):
        self.errors = []
        self.plugin_manager = PluginManager()
        self.cache_manager = CacheManager()
        
        # Carica i plugin dalla directory
        self.plugin_manager.load_plugins_from_directory("plugins")
    
    def analyze_file(self, filepath: str) -> List[SyntaxError]:
        """Analizza un singolo file PHP"""
        self.errors = []
        
        # Controlla la cache
        if self.cache_manager.is_cache_valid(filepath, self.plugin_manager):
            cached_errors = self.cache_manager.get_cached_results(filepath)
            if cached_errors is not None:
                self.errors = cached_errors
                return self.errors
        
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Esegui hook pre_analyze
            self.plugin_manager.execute_hook('pre_analyze', filepath=filepath, lines=lines)
            
            # Controlli di sintassi di base
            # Nota: _check_brackets è stato spostato in un plugin
            self._check_semicolons(lines)
            self._check_quotes(lines)
            self._check_php_tags(lines)
            self._check_function_syntax(lines)
            self._check_array_syntax(lines)
            self._check_variable_syntax(lines)
            
            # Esegui hook syntax_check per controlli di sintassi avanzati
            syntax_results = self.plugin_manager.execute_hook('syntax_check', filepath=filepath, lines=lines)
            for errors in syntax_results:
                if errors:
                    self.errors.extend(errors)
            
            # Esegui hook semantic_check per analisi semantica
            semantic_results = self.plugin_manager.execute_hook('semantic_check', filepath=filepath, lines=lines)
            for errors in semantic_results:
                if errors:
                    self.errors.extend(errors)
            
            # Esegui hook post_analyze
            self.plugin_manager.execute_hook('post_analyze', filepath=filepath, lines=lines, errors=self.errors)
            
            # Salva i risultati in cache
            self.cache_manager.save_results_to_cache(filepath, self.errors)
            
        except Exception as e:
            print(f"Errore durante l'analisi del file {filepath}: {e}")
            traceback.print_exc()
            
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
    
    # Nota: il metodo _check_brackets è stato rimosso perché spostato nel plugin syntax_checker_brackets.py
    
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
            if '<?php' in line or '<?' in line:
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
            
            # Ordina gli errori per linea (dal basso verso l'alto per evitare offset)
            errors.sort(key=lambda x: x.line_number, reverse=True)
            
            for error in errors:
                line_idx = error.line_number - 1
                if line_idx < len(lines):
                    line = lines[line_idx]
                    
                    # Applica correzioni base
                    if error.error_type == "Punto e virgola mancante":
                        lines[line_idx] = line.rstrip() + ';\n'
                    
                    elif error.error_type == "Variabile senza $":
                        # Trova il nome della variabile dall'errore
                        var_match = re.search(r"La variabile '(\w+)'", error.description)
                        if var_match:
                            var_name = var_match.group(1)
                            lines[line_idx] = line.replace(var_name, f'${var_name}')
                    
                    # Esegui hook fix_error per correzioni avanzate
                    fix_results = self.plugin_manager.execute_hook(
                        'fix_error', 
                        error=error, 
                        lines=lines, 
                        line_idx=line_idx, 
                        filepath=filepath
                    )
                    
                    for result in fix_results:
                        if result:
                            break  # Se un plugin ha corretto l'errore, passiamo al successivo
            
            # Scrivi il file corretto
            with open(filepath, 'w', encoding='utf-8') as file:
                file.writelines(lines)
            
            return True
            
        except Exception as e:
            print(f"Errore durante la correzione del file: {e}")
            return False

class PHPAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PHP Syntax Analyzer")
        self.root.geometry("1000x700")
        
        self.analyzer = PHPAnalyzer()
        self.current_file = None
        self.current_errors = []
        self.filter_options = {}
        
        self.create_widgets()
        
        # Carica le estensioni UI dai plugin
        self.analyzer.plugin_manager.execute_hook('ui_extension', gui=self)
    
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
        control_frame.columnconfigure(5, weight=1)  # La colonna dei filtri si espande
        
        # Pulsanti per selezionare file/directory
        ttk.Button(control_frame, text="Seleziona File PHP", command=self.select_file).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="Seleziona Directory", command=self.select_directory).grid(row=0, column=1, padx=5)
        
        # Checkbox per analisi ricorsiva
        self.recursive_var = tk.BooleanVar()
        ttk.Checkbutton(control_frame, text="Analisi ricorsiva", variable=self.recursive_var).grid(row=0, column=2, padx=5)
        
        # Pulsante di analisi
        ttk.Button(control_frame, text="Analizza", command=self.analyze).grid(row=0, column=3, padx=5)
        
        # Dropdowns per filtri (verranno popolati dai plugin)
        self.filter_frame = ttk.Frame(control_frame)
        self.filter_frame.grid(row=0, column=5, sticky=(tk.E))
        
        # Frame per la configurazione
        config_button = ttk.Button(control_frame, text="Config", command=self.show_config)
        config_button.grid(row=0, column=4, padx=5)
        
        # Label per mostrare il file/directory corrente
        self.current_path_var = tk.StringVar(value="Nessun file/directory selezionato")
        ttk.Label(main_frame, textvariable=self.current_path_var).grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Frame principale con pannello split
        self.paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame per albero file (opzionale, verrà popolato da plugin)
        self.tree_frame = ttk.Frame(self.paned_window, width=200)
        self.paned_window.add(self.tree_frame, weight=1)
        
        # Frame per l'output degli errori
        self.output_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.output_frame, weight=3)
        
        # Area di testo per errori
        self.error_text = scrolledtext.ScrolledText(self.output_frame, wrap=tk.WORD, width=80, height=30)
        self.error_text.pack(fill=tk.BOTH, expand=True)
        
        # Tag per la formattazione del testo
        self.error_text.tag_configure("error", foreground="red")
        self.error_text.tag_configure("suggestion", foreground="green")
        self.error_text.tag_configure("info", foreground="blue")
        self.error_text.tag_configure("filename", foreground="purple", font=("TkDefaultFont", 11, "bold"))
        
        # Area per anteprima codice (opzionale, verrà popolata da plugin)
        self.preview_frame = ttk.Frame(main_frame)
        self.preview_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        self.preview_frame.grid_remove()  # Nascosto finché non viene usato da un plugin
        
        # Frame per i pulsanti di azione
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Pulsanti di azione
        ttk.Button(action_frame, text="Correggi Errori", command=self.fix_errors).grid(row=0, column=0, padx=5)
        ttk.Button(action_frame, text="Salva Report", command=self.save_report).grid(row=0, column=1, padx=5)
        ttk.Button(action_frame, text="Pulisci", command=self.clear_output).grid(row=0, column=2, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Seleziona file PHP",
            filetypes=[("PHP files", "*.php"), ("All files", "*.*")]
        )
        if filename:
            self.current_file = filename
            self.current_path_var.set(f"File: {filename}")
    
    def select_directory(self):
        directory = filedialog.askdirectory(title="Seleziona directory")
        if directory:
            self.current_file = directory
            self.current_path_var.set(f"Directory: {directory}")
    
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
            
            # Aggiorna l'UI con il numero totale di file
            self.root.after(0, lambda: self.status_var.set(f"Analisi in corso... 0/{len(files_to_analyze)} file"))
            
            for i, filepath in enumerate(files_to_analyze):
                errors = self.analyzer.analyze_file(filepath)
                
                # Aggiorna l'UI con il progresso
                progress_msg = f"Analisi in corso... {i+1}/{len(files_to_analyze)} file"
                self.root.after(0, lambda m=progress_msg: self.status_var.set(m))
                
                if errors:
                    # Applica filtri se presenti
                    filtered_errors = self.apply_filters(errors)
                    
                    self.current_errors.extend([(filepath, error) for error in filtered_errors])
                    total_errors += len(filtered_errors)
                    
                    if filtered_errors:  # Mostra risultati solo se ci sono errori dopo il filtro
                        self.root.after(0, lambda fp=filepath, err=filtered_errors: self.display_file_errors(fp, err))
                else:
                    self.root.after(0, lambda fp=filepath: self.display_no_errors(fp))
            
            status_message = f"Analisi completata. Files: {len(files_to_analyze)}, Errori: {total_errors}"
            self.root.after(0, lambda: self.status_var.set(status_message))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Errore", f"Errore durante l'analisi: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Errore durante l'analisi"))
            traceback.print_exc()
    
    def apply_filters(self, errors):
        """Applica i filtri agli errori"""
        # Se non ci sono filtri attivi, restituisci tutti gli errori
        if not self.filter_options:
            return errors
        
        filtered_errors = []
        for error in errors:
            include = True
            
            # Applica ogni filtro attivo
            for filter_name, filter_value in self.filter_options.items():
                if filter_name == 'error_type' and filter_value and error.error_type != filter_value:
                    include = False
                    break
                # Aggiungi altri filtri qui...
            
            if include:
                filtered_errors.append(error)
        
        return filtered_errors
    
    def add_filter(self, name, options, default=None):
        """Aggiunge un nuovo filtro all'interfaccia"""
        # Crea una variabile per il filtro
        var = tk.StringVar(value=default if default else "")
        
        # Crea un dropdown
        filter_label = ttk.Label(self.filter_frame, text=f"{name}:")
        filter_label.pack(side=tk.LEFT, padx=(10, 2))
        
        filter_combo = ttk.Combobox(self.filter_frame, textvariable=var, values=options, width=15)
        filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Aggiorna filtri quando cambia il valore
        def on_filter_change(*args):
            if var.get():
                self.filter_options[name] = var.get()
            else:
                if name in self.filter_options:
                    del self.filter_options[name]
            
            # Se siamo già in analisi, non riapplicare i filtri
            if self.status_var.get().startswith("Analisi in corso"):
                return
                
            # Riapplica i filtri agli errori correnti
            if self.current_errors:
                self.clear_output()
                errors_by_file = {}
                
                for filepath, error in self.current_errors:
                    if filepath not in errors_by_file:
                        errors_by_file[filepath] = []
                    errors_by_file[filepath].append(error)
                
                for filepath, errors in errors_by_file.items():
                    filtered = self.apply_filters(errors)
                    if filtered:
                        self.display_file_errors(filepath, filtered)
                    else:
                        self.display_no_errors(filepath)
        
        var.trace("w", on_filter_change)
        
        return var
    
    def display_file_errors(self, filepath, errors):
        self.error_text.insert(tk.END, f"\n{'='*80}\n", "filename")
        self.error_text.insert(tk.END, f"File: {filepath}\n", "filename")
        self.error_text.insert(tk.END, f"{'='*80}\n\n", "filename")
        
        for error in errors:
            self.error_text.insert(tk.END, f"Riga {error.line_number}: ", "error")
            self.error_text.insert(tk.END, f"{error.error_type}\n", "error")
            self.error_text.insert(tk.END, f"   Codice: {error.line_content}\n")
            self.error_text.insert(tk.END, f"   Problema: {error.description}\n", "info")
            self.error_text.insert(tk.END, f"   Suggerimento: {error.suggestion}\n\n", "suggestion")
    
    def display_no_errors(self, filepath):
        self.error_text.insert(tk.END, f"\n✓ Nessun errore trovato in: {filepath}\n", "suggestion")
    
    def fix_errors(self):
        if not self.current_errors:
            messagebox.showinfo("Info", "Nessun errore da correggere")
            return
        
        if messagebox.askyesno("Conferma", "Vuoi correggere automaticamente gli errori trovati?"):
            fixed_files = set()
            errors_by_file = {}
            
            for filepath, error in self.current_errors:
                if filepath not in errors_by_file:
                    errors_by_file[filepath] = []
                errors_by_file[filepath].append(error)
            
            for filepath, errors in errors_by_file.items():
                if self.analyzer.fix_file(filepath, errors):
                    fixed_files.add(filepath)
            
            if fixed_files:
                messagebox.showinfo("Successo", f"Corretti {len(fixed_files)} file")
                self.analyze()  # Rianalizza dopo la correzione
            else:
                messagebox.showwarning("Attenzione", "Nessun file è stato corretto")
    
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
    
    def clear_output(self):
        self.error_text.delete("1.0", tk.END)
    
    def show_code_preview(self, filepath, line_number, num_lines=5):
        """Mostra un'anteprima del codice intorno alla linea dell'errore"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
            start_line = max(0, line_number - num_lines - 1)
            end_line = min(len(lines), line_number + num_lines)
            
            # Crea finestra di preview se non esiste
            if not hasattr(self, 'preview_text'):
                self.preview_frame.grid()  # Mostra il frame
                self.preview_text = scrolledtext.ScrolledText(self.preview_frame, height=10, width=80)
                self.preview_text.pack(fill=tk.BOTH, expand=True)
                self.preview_text.tag_configure("error_line", background="#ffdddd")
                self.preview_text.tag_configure("line_num", foreground="#666666")
            
            # Pulisci e aggiorna il testo
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert(tk.END, f"Preview del file: {filepath} (riga {line_number})\n\n")
            
            for i in range(start_line, end_line):
                line_tag = "error_line" if i == line_number - 1 else ""
                self.preview_text.insert(tk.END, f"{i+1}: ", "line_num")
                self.preview_text.insert(tk.END, lines[i], line_tag)
                if not lines[i].endswith('\n'):
                    self.preview_text.insert(tk.END, '\n')
                    
        except Exception as e:
            print(f"Errore nella preview del codice: {str(e)}")
            if hasattr(self, 'preview_text'):
                self.preview_text.delete("1.0", tk.END)
                self.preview_text.insert(tk.END, f"Errore nella preview del file: {str(e)}")
    
    def show_config(self):
        """Mostra la finestra di configurazione dei plugin"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Configurazione Plugin")
        config_window.geometry("600x400")
        
        notebook = ttk.Notebook(config_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Crea una tab per ogni plugin
        for plugin_id, plugin in self.analyzer.plugin_manager.plugins.items():
            plugin_frame = ttk.Frame(notebook)
            notebook.add(plugin_frame, text=plugin.get_name())
            
            # Aggiungi descrizione del plugin
            desc_label = ttk.Label(
                plugin_frame, 
                text=f"Descrizione: {plugin.get_description()}\nVersione: {plugin.get_version()}\nAutore: {plugin.get_author()}"
            )
            desc_label.pack(pady=10, padx=10, anchor=tk.W)
            
            # Aggiungi separatore
            ttk.Separator(plugin_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
            
            # Ottieni configurazione del plugin
            config = self.analyzer.plugin_manager.get_plugin_config(plugin_id)
            
            # Crea campi di input per ogni opzione di configurazione
            config_items = {}
            
            # Ottieni configurazioni di default
            defaults = plugin.get_config_defaults()
            
            # Frame per configurazioni
            options_frame = ttk.Frame(plugin_frame)
            options_frame.pack(fill=tk.BOTH, expand=True, padx=10)
            
            # Se non ci sono opzioni, mostra un messaggio
            if not defaults:
                ttk.Label(options_frame, text="Nessuna opzione di configurazione disponibile").pack(pady=20)
            
            # Altrimenti, crea controlli per ogni opzione
            row = 0
            for key, default in defaults.items():
                ttk.Label(options_frame, text=key).grid(row=row, column=0, sticky=tk.W, pady=5)
                
                # Crea il controllo appropriato in base al tipo
                if isinstance(default, bool):
                    var = tk.BooleanVar(value=config.get(key, default))
                    ttk.Checkbutton(options_frame, variable=var).grid(row=row, column=1, sticky=tk.W)
                    config_items[key] = var
                elif isinstance(default, int):
                    var = tk.IntVar(value=config.get(key, default))
                    ttk.Entry(options_frame, textvariable=var, width=10).grid(row=row, column=1, sticky=tk.W)
                    config_items[key] = var
                elif isinstance(default, list):
                    current = config.get(key, default)
                    if default and isinstance(default[0], str):  # Lista di stringhe
                        var = tk.StringVar(value=current[0] if current else "")
                        ttk.Combobox(options_frame, textvariable=var, values=default).grid(row=row, column=1, sticky=tk.W)
                        config_items[key] = var
                else:  # Stringa o altro
                    var = tk.StringVar(value=config.get(key, default))
                    ttk.Entry(options_frame, textvariable=var, width=30).grid(row=row, column=1, sticky=tk.W)
                    config_items[key] = var
                
                row += 1
            
            # Aggiungi pulsanti per salvare/annullare
            btn_frame = ttk.Frame(plugin_frame)
            btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
            
            def save_config(plugin_id=plugin_id, config_items=config_items):
                new_config = {}
                for key, var in config_items.items():
                    new_config[key] = var.get()
                self.analyzer.plugin_manager.set_plugin_config(plugin_id, new_config)
                messagebox.showinfo("Configurazione", "Configurazione salvata con successo")
            
            ttk.Button(btn_frame, text="Salva", command=save_config).pack(side=tk.RIGHT, padx=5)
            ttk.Button(btn_frame, text="Annulla", command=config_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def add_tree_view(self, parent_item=None, path=None):
        """Aggiunge una vista ad albero per i file e directory"""
        if not hasattr(self, 'tree_view'):
            # Crea il treeview se non esiste
            self.tree_view = ttk.Treeview(self.tree_frame)
            self.tree_view.pack(fill=tk.BOTH, expand=True)
            
            # Aggiungi scrollbar
            tree_scroll = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree_view.yview)
            tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            self.tree_view.configure(yscrollcommand=tree_scroll.set)
            
            # Configura colonne
            self.tree_view["columns"] = ("errors")
            self.tree_view.column("#0", width=200, minwidth=200)
            self.tree_view.column("errors", width=50, minwidth=50)
            
            self.tree_view.heading("#0", text="File/Directory")
            self.tree_view.heading("errors", text="Errori")
            
            # Binding per la selezione
            self.tree_view.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # Se path non è specificato, usa current_file
        if path is None:
            path = self.current_file
        
        # Se è la prima chiamata, cancella l'albero
        if parent_item is None:
            for item in self.tree_view.get_children():
                self.tree_view.delete(item)
        
        # Popola l'albero
        if os.path.isfile(path):
            # Aggiungi file singolo
            item = self.tree_view.insert(
                parent_item, 
                'end', 
                text=os.path.basename(path), 
                values=(self._count_errors_in_file(path),)
            )
            self.tree_view.item(item, tags=(path,))
        elif os.path.isdir(path):
            # Aggiungi directory
            dir_item = self.tree_view.insert(
                parent_item, 
                'end', 
                text=os.path.basename(path) or path, 
                values=("")
            )
            self.tree_view.item(dir_item, tags=(path,))
            
            # Aggiungi i file nella directory
            try:
                for item in sorted(os.listdir(path)):
                    item_path = os.path.join(path, item)
                    if os.path.isfile(item_path) and item.endswith('.php'):
                        file_item = self.tree_view.insert(
                            dir_item, 
                            'end', 
                            text=item, 
                            values=(self._count_errors_in_file(item_path),)
                        )
                        self.tree_view.item(file_item, tags=(item_path,))
                    elif os.path.isdir(item_path) and self.recursive_var.get():
                        # Per le directory, chiamata ricorsiva
                        self.add_tree_view(dir_item, item_path)
            except Exception as e:
                print(f"Errore nell'aggiunta all'albero: {str(e)}")
    
    def _count_errors_in_file(self, filepath):
        """Conta gli errori in un file"""
        count = 0
        for f, error in self.current_errors:
            if f == filepath:
                count += 1
        return count if count > 0 else ""
    
    def on_tree_select(self, event):
        """Gestisce la selezione nel treeview"""
        selection = self.tree_view.selection()
        if selection:
            item = selection[0]
            filepath = self.tree_view.item(item, "tags")[0]
            
            # Filtra gli errori per questo file
            file_errors = []
            for f, error in self.current_errors:
                if f == filepath:
                    file_errors.append(error)
            
            # Mostra gli errori
            self.clear_output()
            if file_errors:
                self.display_file_errors(filepath, file_errors)
            else:
                self.display_no_errors(filepath)

def main():
    # Crea la directory plugins se non esiste
    os.makedirs("plugins", exist_ok=True)
    
    root = tk.Tk()
    app = PHPAnalyzerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
