#!/usr/bin/env python3
"""
Plugin di diagnostica per il PHP Analyzer
"""
import os
import tkinter as tk
from tkinter import ttk, scrolledtext

try:
    from analizzatore import PluginBase
except ImportError:
    # Definizione di fallback per IDE
    class PluginBase:
        def get_id(self): pass
        def get_hooks(self): pass

class DiagnosticsPlugin(PluginBase):
    """
    Plugin di diagnostica per mostrare informazioni sul sistema dei plugin
    """
    
    def get_id(self):
        return "diagnostics_plugin"
        
    def get_name(self):
        return "Diagnostica Plugin"
        
    def get_description(self):
        return "Mostra informazioni di diagnostica sul sistema dei plugin"
        
    def get_author(self):
        return "Proietti House & Claude"
        
    def get_version(self):
        return "1.0.0"
        
    def get_hooks(self):
        return {
            'ui_extension': [self.add_diagnostics_button]
        }
    
    def add_diagnostics_button(self, gui, **kwargs):
        """Aggiunge un pulsante per le diagnostiche all'interfaccia"""
        # Aggiungi un pulsante nella barra degli strumenti
        control_frame = gui.root.winfo_children()[0].winfo_children()[0]
        diag_button = ttk.Button(control_frame, text="Diagnostica", command=lambda: self.show_diagnostics(gui))
        diag_button.grid(row=0, column=7, padx=5)
    
    def show_diagnostics(self, gui):
        """Mostra una finestra con informazioni di diagnostica"""
        diag_window = tk.Toplevel(gui.root)
        diag_window.title("Diagnostica Plugin")
        diag_window.geometry("700x500")
        
        # Crea notebook per le schede
        notebook = ttk.Notebook(diag_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scheda per info generale
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="Informazioni Generali")
        
        # Scheda per i plugin
        plugins_frame = ttk.Frame(notebook)
        notebook.add(plugins_frame, text="Plugin Caricati")
        
        # Scheda per i file nella cartella plugins
        files_frame = ttk.Frame(notebook)
        notebook.add(files_frame, text="File nella cartella plugins")
        
        # Popola la scheda generale
        self._populate_general_info(general_frame, gui)
        
        # Popola la scheda plugin
        self._populate_plugins_info(plugins_frame, gui)
        
        # Popola la scheda file
        self._populate_files_info(files_frame)
    
    def _populate_general_info(self, frame, gui):
        """Popola la scheda con informazioni generali"""
        info_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text.insert(tk.END, "=== Informazioni di Sistema ===\n\n")
        
        # Info sulla directory corrente
        info_text.insert(tk.END, f"Directory di lavoro: {os.getcwd()}\n")
        info_text.insert(tk.END, f"Directory plugins: {os.path.join(os.getcwd(), 'plugins')}\n\n")
        
        # Info sul Python path
        info_text.insert(tk.END, "=== Python Path ===\n")
        import sys
        for path in sys.path:
            info_text.insert(tk.END, f"- {path}\n")
        
        info_text.insert(tk.END, "\n=== Informazioni sull'analizzatore ===\n")
        info_text.insert(tk.END, f"Plugin caricati: {len(gui.analyzer.plugin_manager.plugins)}\n")
        
        # Info sugli hook registrati
        info_text.insert(tk.END, "\n=== Hook registrati ===\n")
        for hook_name, handlers in gui.analyzer.plugin_manager.hooks.items():
            info_text.insert(tk.END, f"Hook '{hook_name}': {len(handlers)} handler(s)\n")
            for plugin_id, method in handlers:
                info_text.insert(tk.END, f"  - {plugin_id}.{method.__name__}\n")
        
        info_text.config(state=tk.DISABLED)  # Rendi di sola lettura
    
    def _populate_plugins_info(self, frame, gui):
        """Popola la scheda con informazioni sui plugin caricati"""
        info_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text.insert(tk.END, "=== Plugin caricati ===\n\n")
        
        if not gui.analyzer.plugin_manager.plugins:
            info_text.insert(tk.END, "Nessun plugin caricato!\n\n")
            info_text.insert(tk.END, "Possibili cause:\n")
            info_text.insert(tk.END, "1. La cartella 'plugins' non esiste o è vuota\n")
            info_text.insert(tk.END, "2. I file plugin non contengono classi che ereditano da PluginBase\n")
            info_text.insert(tk.END, "3. Ci sono errori di sintassi nei file plugin\n")
            info_text.insert(tk.END, "4. I plugin hanno dipendenze non soddisfatte\n\n")
            info_text.insert(tk.END, "Consulta la scheda 'File nella cartella plugins' per ulteriori informazioni.")
        else:
            for plugin_id, plugin in gui.analyzer.plugin_manager.plugins.items():
                info_text.insert(tk.END, f"Plugin: {plugin.get_name()} (ID: {plugin_id})\n")
                info_text.insert(tk.END, f"Descrizione: {plugin.get_description()}\n")
                info_text.insert(tk.END, f"Versione: {plugin.get_version()}\n")
                info_text.insert(tk.END, f"Autore: {plugin.get_author()}\n")
                
                # Mostra gli hook implementati
                hooks = plugin.get_hooks()
                if hooks:
                    info_text.insert(tk.END, "Hook implementati:\n")
                    for hook_name, methods in hooks.items():
                        for method in methods:
                            info_text.insert(tk.END, f"  - {hook_name}: {method.__name__}\n")
                else:
                    info_text.insert(tk.END, "Nessun hook implementato!\n")
                
                # Mostra le dipendenze
                deps = plugin.get_dependencies()
                if deps:
                    info_text.insert(tk.END, "Dipendenze:\n")
                    for dep in deps:
                        info_text.insert(tk.END, f"  - {dep}\n")
                
                info_text.insert(tk.END, "\n" + "-" * 50 + "\n\n")
        
        info_text.config(state=tk.DISABLED)  # Rendi di sola lettura
    
    def _populate_files_info(self, frame):
        """Popola la scheda con informazioni sui file nella cartella plugins"""
        info_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        plugins_dir = os.path.join(os.getcwd(), 'plugins')
        
        info_text.insert(tk.END, f"=== File nella cartella {plugins_dir} ===\n\n")
        
        if not os.path.exists(plugins_dir):
            info_text.insert(tk.END, f"La cartella 'plugins' non esiste! Dovrebbe essere in: {plugins_dir}\n")
            info_text.insert(tk.END, "Assicurati di creare questa cartella per i tuoi plugin.")
            return
        
        files = os.listdir(plugins_dir)
        
        if not files:
            info_text.insert(tk.END, "La cartella 'plugins' è vuota. Nessun file trovato.\n")
            return
        
        python_files = [f for f in files if f.endswith('.py') and not f.startswith('__')]
        other_files = [f for f in files if not (f.endswith('.py') and not f.startswith('__'))]
        
        if python_files:
            info_text.insert(tk.END, "File Python trovati:\n")
            for i, file in enumerate(python_files, 1):
                file_path = os.path.join(plugins_dir, file)
                file_size = os.path.getsize(file_path)
                file_mod = os.path.getmtime(file_path)
                import time
                mod_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_mod))
                
                info_text.insert(tk.END, f"{i}. {file}\n")
                info_text.insert(tk.END, f"   - Dimensione: {file_size} byte\n")
                info_text.insert(tk.END, f"   - Ultima modifica: {mod_time}\n")
                
                # Analizza il contenuto del file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Controlla se il file importa PluginBase
                    if "PluginBase" in content:
                        info_text.insert(tk.END, f"   - Importa PluginBase: Sì\n")
                    else:
                        info_text.insert(tk.END, f"   - Importa PluginBase: No (problema!)\n")
                    
                    # Controlla se ha classi che ereditano da PluginBase
                    if "class" in content and "(PluginBase)" in content:
                        info_text.insert(tk.END, f"   - Classe che eredita da PluginBase: Sì\n")
                    else:
                        info_text.insert(tk.END, f"   - Classe che eredita da PluginBase: No (problema!)\n")
                    
                    # Controlla se implementa get_hooks
                    if "def get_hooks" in content:
                        info_text.insert(tk.END, f"   - Implementa get_hooks: Sì\n")
                    else:
                        info_text.insert(tk.END, f"   - Implementa get_hooks: No (problema!)\n")
                    
                except Exception as e:
                    info_text.insert(tk.END, f"   - Errore nell'analisi del file: {str(e)}\n")
                
                info_text.insert(tk.END, "\n")
        else:
            info_text.insert(tk.END, "Nessun file Python valido trovato nella cartella 'plugins'.\n\n")
        
        if other_files:
            info_text.insert(tk.END, "Altri file e cartelle trovati:\n")
            for i, file in enumerate(other_files, 1):
                info_text.insert(tk.END, f"{i}. {file}\n")
        
        info_text.config(state=tk.DISABLED)  # Rendi di sola lettura