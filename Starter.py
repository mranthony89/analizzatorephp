#!/usr/bin/env python3
"""
Analizzatore per i plugin
"""
import os
import sys
import importlib.util
import tkinter as tk

# Importa PluginBase da analizzatore
from analizzatore import PluginBase, PHPAnalyzerGUI, PHPAnalyzer

def main():
    # Stampa informazioni sulla classe PluginBase
    print(f"Tipo di PluginBase: {type(PluginBase)}")
    print(f"Path del modulo PluginBase: {PluginBase.__module__}")

    # Ottieni il percorso assoluto del progetto
    project_dir = os.path.dirname(os.path.abspath(__file__))
    plugins_dir = os.path.join(project_dir, "plugins")
    
    # Inizializza l'analyzer con il percorso corretto
    analyzer = PHPAnalyzer()
    
    # Sostituisci il plugin_manager per usare il percorso corretto
    from analizzatore import PluginManager
    plugin_manager = PluginManager(plugins_dir)
    plugin_manager.load_plugins()
    analyzer.plugin_manager = plugin_manager
    
    print(f"\nPlugins caricati dall'analyzer: {len(analyzer.plugin_manager.plugins)}")
    for plugin_id, plugin in analyzer.plugin_manager.plugins.items():
        print(f"  - {plugin_id}: {plugin.get_name()}")

    # Crea e avvia l'interfaccia grafica
    root = tk.Tk()
    app = PHPAnalyzerGUI(root)
    app.analyzer = analyzer  # Usa l'analyzer con i plugin caricati
    root.mainloop()

if __name__ == "__main__":
    main()