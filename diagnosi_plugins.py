#!/usr/bin/env python3
"""
Script di diagnosi per i plugin
"""
import os
import sys
import importlib.util

# Assicurati che il percorso corrente sia nel sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importa PluginBase
from analizzatore import PluginBase

print(f"Tipo di PluginBase: {type(PluginBase)}")
print(f"PluginBase path: {PluginBase.__module__}")

# Definisci un metodo simile a _load_plugin_from_file
def carica_plugin(filepath):
    print(f"Tentativo di caricamento plugin da: {filepath}")
    plugin_name = os.path.splitext(os.path.basename(filepath))[0]
    print(f"Nome del plugin: {plugin_name}")
    
    spec = importlib.util.spec_from_file_location(plugin_name, filepath)
    if spec is None:
        print(f"Impossibile ottenere spec per {filepath}")
        return None
        
    module = importlib.util.module_from_spec(spec)
    sys.modules[plugin_name] = module
    
    try:
        spec.loader.exec_module(module)
        print(f"Modulo {plugin_name} eseguito con successo")
    except Exception as e:
        print(f"Errore durante l'esecuzione del modulo: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Cerca tutte le classi che ereditano da PluginBase
    print(f"Contenuto del modulo {plugin_name}:")
    for name, obj in module.__dict__.items():
        print(f"  - {name}: {type(obj)}")
        if isinstance(obj, type):
            print(f"    - È una classe")
            try:
                if issubclass(obj, PluginBase):
                    print(f"      - È una sottoclasse di PluginBase")
                    if obj is not PluginBase:
                        print(f"        - Non è PluginBase stesso")
                        # Tenta di istanziare la classe
                        try:
                            plugin_instance = obj()
                            print(f"Plugin istanziato: {plugin_instance}")
                            print(f"Plugin ID: {plugin_instance.get_id()}")
                            print(f"Plugin hooks: {plugin_instance.get_hooks()}")
                            return plugin_instance
                        except Exception as e:
                            print(f"Errore nell'istanziazione del plugin: {e}")
            except TypeError:
                print(f"      - Non può essere confrontato con PluginBase")
    
    print(f"Nessun plugin valido trovato in {filepath}")
    return None

# Carica i plugin dalla directory plugins
plugins_dir = os.path.join(current_dir, "plugins")
plugins = {}

print(f"Scansione della directory: {plugins_dir}")
for filename in os.listdir(plugins_dir):
    if filename.endswith(".py") and not filename.startswith("__"):
        filepath = os.path.join(plugins_dir, filename)
        print(f"\nAnalisi del file: {filename}")
        plugin_instance = carica_plugin(filepath)
        if plugin_instance:
            plugin_id = plugin_instance.get_id()
            plugins[plugin_id] = plugin_instance
            print(f"Plugin aggiunto: {plugin_id}")

print(f"\nPlugin caricati con successo: {len(plugins)}")
for plugin_id, plugin in plugins.items():
    print(f"  - {plugin_id}: {plugin.get_name()} ({plugin.get_version()})")