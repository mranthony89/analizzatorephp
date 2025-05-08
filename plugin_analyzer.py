#!/usr/bin/env python3
"""
Analizzatore per i plugin
"""
import os
import sys
import importlib.util

# Importa PluginBase da analizzatore
from analizzatore import PluginBase, PHPAnalyzerGUI, PHPAnalyzer

# Stampa informazioni sulla classe PluginBase
print(f"Tipo di PluginBase: {type(PluginBase)}")
print(f"Path del modulo PluginBase: {PluginBase.__module__}")

# Verifica se esistono plugin funzionanti nel sistema
analyzer = PHPAnalyzer()
plugin_manager = analyzer.plugin_manager

print(f"\nPlugins caricati dall'analyzer: {len(plugin_manager.plugins)}")
for plugin_id, plugin in plugin_manager.plugins.items():
    print(f"  - {plugin_id}: {plugin.get_name()}")

# Carica manualmente un plugin
print("\nTentativo di caricamento manuale di plugin_base.py:")
filepath = os.path.join("plugins", "plugin_base.py")
if os.path.exists(filepath):
    # Ottieni il nome del modulo
    plugin_name = os.path.splitext(os.path.basename(filepath))[0]
    print(f"Nome del plugin: {plugin_name}")
    
    try:
        # Importa il modulo
        spec = importlib.util.spec_from_file_location(plugin_name, filepath)
        if spec is None:
            print(f"Impossibile ottenere spec per {filepath}")
        else:
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)
            print(f"Modulo {plugin_name} eseguito")
            
            # Cerca classi che ereditano da PluginBase
            print("Classi nel modulo:")
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type):
                    print(f"  - {name} (tipo: {type(obj)})")
                    try:
                        if issubclass(obj, PluginBase):
                            print(f"    - È sottoclasse di PluginBase")
                            if obj is not PluginBase:
                                print(f"    - Non è PluginBase stesso")
                                # Instanzia il plugin
                                try:
                                    plugin_instance = obj()
                                    plugin_id = plugin_instance.get_id()
                                    print(f"    - Istanziazione riuscita: {plugin_id}")
                                    
                                    # Confronta con le classi esistenti nel modulo
                                    print("\nConfrontando con le classi nel __dict__ del modulo:")
                                    for name, cls in module.__dict__.items():
                                        if isinstance(cls, type):
                                            print(f"  - {name}: {issubclass(cls, PluginBase) if isinstance(cls, type) else 'non è una classe'}")
                                    
                                except Exception as e:
                                    print(f"    - Errore nell'istanziazione: {e}")
                    except TypeError:
                        print(f"    - Non può essere confrontato con PluginBase")
    except Exception as e:
        print(f"Errore durante l'importazione: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"Il file {filepath} non esiste")

# Prova a creare un plugin direttamente qui
class PluginTest(PluginBase):
    def get_id(self):
        return "plugin_test"
    def get_name(self):
        return "Plugin Test"
    def get_description(self):
        return "Plugin di test"
    def get_version(self):
        return "1.0.0"
    def get_author(self):
        return "Test"
    def get_hooks(self):
        return {}

# Verifica se PluginTest è una sottoclasse valida
print(f"\nVerifica di PluginTest:")
print(f"PluginTest è classe: {isinstance(PluginTest, type)}")
print(f"PluginTest è sottoclasse di PluginBase: {issubclass(PluginTest, PluginBase)}")
print(f"PluginTest è PluginBase stesso: {PluginTest is PluginBase}")

# Prova a istanziare PluginTest
test_instance = PluginTest()
print(f"Istanza di PluginTest creata: {test_instance}")
print(f"ID: {test_instance.get_id()}")