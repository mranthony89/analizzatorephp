#!/usr/bin/env python3
"""
Plugin per la gestione dei plugin per PHP Analyzer
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json

try:
    from analizzatore import PluginBase
except ImportError:
    # Definizione di fallback per IDE
    class PluginBase:
        def get_id(self): pass
        def get_hooks(self): pass

class PluginManagerPlugin(PluginBase):
    """
    Plugin per la gestione dei plugin dell'analizzatore PHP
    """
    
    def get_id(self):
        return "plugin_manager_plugin"
        
    def get_name(self):
        return "Gestione Plugin"
        
    def get_description(self):
        return "Fornisce un'interfaccia per gestire i plugin dell'analizzatore"
        
    def get_author(self):
        return "Proietti House & Claude"
        
    def get_version(self):
        return "1.0.0"
        
    def get_hooks(self):
        return {
            'ui_extension': [self.add_plugin_manager_button]
        }
    
    def get_config_defaults(self):
        return {
            "preferred_plugins_dir": "./plugins"
        }
    
    def add_plugin_manager_button(self, gui, **kwargs):
        """Aggiunge un pulsante per il gestore plugin all'interfaccia"""
        # Aggiungi un pulsante nella barra degli strumenti
        control_frame = gui.root.winfo_children()[0].winfo_children()[0]
        plugin_mgr_button = ttk.Button(
            control_frame, 
            text="Gestione Plugin", 
            command=lambda: self.show_plugin_manager(gui)
        )
        plugin_mgr_button.grid(row=0, column=6, padx=5)
    
    def show_plugin_manager(self, gui):
        """Mostra la finestra di gestione dei plugin"""
        manager_window = tk.Toplevel(gui.root)
        manager_window.title("Gestione Plugin")
        manager_window.geometry("750x550")
        
        # Frame principale
        main_frame = ttk.Frame(manager_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crea un notebook con schede
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scheda per la lista dei plugin
        plugins_frame = ttk.Frame(notebook)
        notebook.add(plugins_frame, text="Plugin Disponibili")
        
        # Crea una treeview per mostrare i plugin
        columns = ("id", "nome", "versione", "autore", "stato")
        tree = ttk.Treeview(plugins_frame, columns=columns, show="headings")
        
        # Configura le intestazioni
        tree.heading("id", text="ID")
        tree.heading("nome", text="Nome")
        tree.heading("versione", text="Versione")
        tree.heading("autore", text="Autore")
        tree.heading("stato", text="Stato")
        
        # Configura le colonne
        tree.column("id", width=120)
        tree.column("nome", width=180)
        tree.column("versione", width=80)
        tree.column("autore", width=150)
        tree.column("stato", width=100)
        
        # Aggiungi scrollbar
        scrollbar = ttk.Scrollbar(plugins_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        # Imposta la griglia
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        plugins_frame.columnconfigure(0, weight=1)
        plugins_frame.rowconfigure(0, weight=1)
        
        # Frame per i dettagli del plugin
        details_frame = ttk.LabelFrame(plugins_frame, text="Dettagli Plugin")
        details_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Campi per i dettagli
        ttk.Label(details_frame, text="Descrizione:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        description_var = tk.StringVar()
        ttk.Label(details_frame, textvariable=description_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(details_frame, text="Hook:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        hooks_var = tk.StringVar()
        ttk.Label(details_frame, textvariable=hooks_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(details_frame, text="Dipendenze:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        deps_var = tk.StringVar()
        ttk.Label(details_frame, textvariable=deps_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Frame per i controlli
        control_frame = ttk.Frame(plugins_frame)
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Pulsanti di azione
        ttk.Button(
            control_frame, 
            text="Abilita", 
            command=lambda: self._toggle_plugin(gui, tree, True, 
                                               description_var, hooks_var, deps_var)
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Disabilita", 
            command=lambda: self._toggle_plugin(gui, tree, False,
                                                description_var, hooks_var, deps_var)
        ).grid(row=0, column=1, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Configura", 
            command=lambda: self._configure_plugin(gui, tree)
        ).grid(row=0, column=2, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Ricarica Plugin", 
            command=lambda: self._reload_plugins(gui, tree,
                                                description_var, hooks_var, deps_var)
        ).grid(row=0, column=3, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Diagnostica", 
            command=lambda: self._diagnose_plugins(gui)
        ).grid(row=0, column=4, padx=5)
        
        # Scheda per la configurazione generale
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configurazione")
        
        ttk.Label(config_frame, text="Directory Plugin:").grid(row=0, column=0, sticky=tk.W, pady=10)
        plugins_dir_var = tk.StringVar(value=gui.analyzer.plugin_manager.plugins_dir)
        dir_entry = ttk.Entry(config_frame, textvariable=plugins_dir_var, width=50)
        dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(
            config_frame, 
            text="Sfoglia", 
            command=lambda: self._browse_plugins_dir(plugins_dir_var)
        ).grid(row=0, column=2, padx=5, pady=10)
        
        ttk.Button(
            config_frame, 
            text="Salva Configurazione", 
            command=lambda: self._save_plugins_dir(gui, plugins_dir_var)
        ).grid(row=1, column=1, pady=10)
        
        # Popola la treeview con i plugin
        self._populate_plugin_tree(gui, tree)
        
        # Evento di selezione nella treeview
        tree.bind("<<TreeviewSelect>>", lambda e: self._on_tree_select(
            tree, gui, description_var, hooks_var, deps_var))
        
        # Metti lo stato iniziale - nessun plugin selezionato
        description_var.set("")
        hooks_var.set("")
        deps_var.set("")
    
    def _populate_plugin_tree(self, gui, tree):
        """Popola la treeview con i plugin disponibili"""
        # Pulisci prima la treeview
        for item in tree.get_children():
            tree.delete(item)
            
        # Aggiungi i plugin alla treeview
        for plugin_id, plugin in gui.analyzer.plugin_manager.plugins.items():
            # Verifica se c'è una configurazione per questo plugin
            config = gui.analyzer.plugin_manager.get_plugin_config(plugin_id)
            enabled = config.get("enabled", True)
            
            # Aggiungi alla treeview
            tree.insert("", tk.END, values=(
                plugin_id,
                plugin.get_name(),
                plugin.get_version(),
                plugin.get_author(),
                "Abilitato" if enabled else "Disabilitato"
            ))
    
    def _on_tree_select(self, tree, gui, desc_var, hooks_var, deps_var):
        """Gestisce l'evento di selezione nella treeview"""
        selection = tree.selection()
        if not selection:
            desc_var.set("")
            hooks_var.set("")
            deps_var.set("")
            return
            
        # Ottieni l'ID del plugin selezionato
        item = selection[0]
        plugin_id = tree.item(item, "values")[0]
        
        # Ottieni il plugin
        plugin = gui.analyzer.plugin_manager.plugins.get(plugin_id)
        if not plugin:
            return
            
        # Aggiorna le variabili di testo
        desc_var.set(plugin.get_description())
        
        # Formatta gli hook
        hooks = plugin.get_hooks()
        if hooks:
            hooks_text = ", ".join(hooks.keys())
        else:
            hooks_text = "Nessuno"
        hooks_var.set(hooks_text)
        
        # Formatta le dipendenze
        deps = plugin.get_dependencies()
        if deps:
            deps_text = ", ".join(deps)
        else:
            deps_text = "Nessuna"
        deps_var.set(deps_text)
    
    def _toggle_plugin(self, gui, tree, enable, desc_var, hooks_var, deps_var):
        """Abilita o disabilita il plugin selezionato"""
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Selezione", "Seleziona prima un plugin")
            return
        
        # Ottieni l'ID del plugin selezionato
        item = selection[0]
        plugin_id = tree.item(item, "values")[0]
        
        # Aggiorna lo stato
        config = gui.analyzer.plugin_manager.get_plugin_config(plugin_id) or {}
        config["enabled"] = enable
        gui.analyzer.plugin_manager.save_plugin_config(plugin_id, config)
        
        # Aggiorna la treeview
        tree.item(item, values=(
            plugin_id,
            gui.analyzer.plugin_manager.plugins[plugin_id].get_name(),
            gui.analyzer.plugin_manager.plugins[plugin_id].get_version(),
            gui.analyzer.plugin_manager.plugins[plugin_id].get_author(),
            "Abilitato" if enable else "Disabilitato"
        ))
        
        # Aggiorna anche le variabili di testo in caso di modifiche
        self._on_tree_select(tree, gui, desc_var, hooks_var, deps_var)
        
        messagebox.showinfo("Stato Plugin", 
                        f"Plugin {plugin_id} {'abilitato' if enable else 'disabilitato'} con successo")
    
    def _configure_plugin(self, gui, tree):
        """Apre una finestra per configurare il plugin selezionato"""
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Selezione", "Seleziona prima un plugin")
            return
        
        # Ottieni l'ID del plugin selezionato
        item = selection[0]
        plugin_id = tree.item(item, "values")[0]
        
        # Ottieni il plugin
        plugin = gui.analyzer.plugin_manager.plugins.get(plugin_id)
        if not plugin:
            return
            
        # Ottieni la configurazione attuale
        current_config = gui.analyzer.plugin_manager.get_plugin_config(plugin_id) or {}
        
        # Ottieni la configurazione predefinita
        default_config = plugin.get_config_defaults()
        
        # Crea una finestra di configurazione
        config_window = tk.Toplevel(gui.root)
        config_window.title(f"Configurazione: {plugin.get_name()}")
        config_window.geometry("600x400")
        
        # Frame principale
        main_frame = ttk.Frame(config_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Nome e descrizione in alto
        ttk.Label(main_frame, text=f"Plugin: {plugin.get_name()}", font=("TkDefaultFont", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        ttk.Label(main_frame, text=f"Descrizione: {plugin.get_description()}").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Mostra la configurazione come JSON modificabile
        ttk.Label(main_frame, text="Configurazione JSON:").grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        # Unisci la configurazione predefinita con quella attuale
        merged_config = {**default_config, **current_config}
        
        # Crea un editor di testo per il JSON
        config_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=70, height=15)
        config_text.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        config_text.insert("1.0", json.dumps(merged_config, indent=4))
        
        # Frame per i pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Pulsanti
        ttk.Button(
            button_frame, 
            text="Salva Configurazione", 
            command=lambda: self._save_plugin_config(
                gui, plugin_id, config_text, config_window)
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Ripristina Predefiniti", 
            command=lambda: config_text.delete("1.0", tk.END) or 
                            config_text.insert("1.0", json.dumps(default_config, indent=4))
        ).grid(row=0, column=1, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Annulla", 
            command=config_window.destroy
        ).grid(row=0, column=2, padx=5)
        
        # Configura i pesi delle righe e colonne
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
    
    def _save_plugin_config(self, gui, plugin_id, config_text, window):
        """Salva la configurazione di un plugin"""
        try:
            # Ottieni il testo JSON dalla casella di testo
            config_json = config_text.get("1.0", tk.END)
            
            # Converti in dizionario
            config = json.loads(config_json)
            
            # Salva la configurazione
            gui.analyzer.plugin_manager.save_plugin_config(plugin_id, config)
            
            messagebox.showinfo("Configurazione", "Configurazione salvata con successo")
            window.destroy()
            
        except json.JSONDecodeError as e:
            messagebox.showerror("Errore JSON", f"Formato JSON non valido: {str(e)}")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il salvataggio: {str(e)}")
    
    def _reload_plugins(self, gui, tree, desc_var, hooks_var, deps_var):
        """Ricarica tutti i plugin"""
        try:
            gui.analyzer.plugin_manager.load_plugins()
            messagebox.showinfo("Plugin", f"Caricati {len(gui.analyzer.plugin_manager.plugins)} plugin")
            
            # Aggiorna la treeview
            self._populate_plugin_tree(gui, tree)
            
            # Resetta le variabili di dettaglio
            desc_var.set("")
            hooks_var.set("")
            deps_var.set("")
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il ricaricamento: {str(e)}")
    
    def _diagnose_plugins(self, gui):
        """Esegue la diagnostica dei plugin"""
        gui.analyzer.plugin_manager.diagnose_plugins_directory()
        messagebox.showinfo("Diagnostica", "Diagnostica completata. Controlla la console per i dettagli.")
    
    def _browse_plugins_dir(self, string_var):
        """Permette di selezionare la directory dei plugin"""
        directory = filedialog.askdirectory(
            title="Seleziona la directory dei plugin",
            initialdir=string_var.get()
        )
        if directory:
            string_var.set(directory)
    
    def _save_plugins_dir(self, gui, string_var):
        """Salva la directory dei plugin nella configurazione"""
        new_dir = string_var.get()
        
        if not os.path.exists(new_dir):
            if messagebox.askyesno("Directory non esistente", 
                                   "La directory selezionata non esiste. Vuoi crearla?"):
                try:
                    os.makedirs(new_dir, exist_ok=True)
                except Exception as e:
                    messagebox.showerror("Errore", f"Impossibile creare la directory: {str(e)}")
                    return
            else:
                return
        
        # Salva la directory nella configurazione del plugin
        config = gui.analyzer.plugin_manager.get_plugin_config(self.get_id()) or {}
        config["preferred_plugins_dir"] = new_dir
        gui.analyzer.plugin_manager.save_plugin_config(self.get_id(), config)
        
        # Aggiorna la directory nel plugin manager
        # Nota: per applicare effettivamente questa modifica potrebbe essere necessario riavviare l'applicazione
        messagebox.showinfo("Configurazione", 
                           "Directory plugin aggiornata. Potrebbe essere necessario riavviare l'applicazione.")