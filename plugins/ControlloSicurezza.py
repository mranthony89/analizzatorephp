#!/usr/bin/env python3
"""
Plugin per il controllo della sicurezza per PHP Analyzer
Identifica potenziali vulnerabilità di sicurezza nel codice PHP
"""
from typing import List, Dict

try:
    from analizzatore import PluginBase, SyntaxError
except ImportError:
    # Definizione di fallback per IDE
    class PluginBase:
        def get_id(self): pass
        def get_name(self): pass
        def get_description(self): pass
        def get_version(self): pass
        def get_author(self): pass
        def get_hooks(self): pass

    class SyntaxError:
        def __init__(self, line_number, line_content, error_type, description, suggestion):
            self.line_number = line_number
            self.line_content = line_content
            self.error_type = error_type
            self.description = description
            self.suggestion = suggestion

class SicurezzaPlugin(PluginBase):
    """
    Plugin per il controllo delle vulnerabilità di sicurezza nel codice PHP
    """
    
    def get_id(self):
        return "sicurezza_checker"
        
    def get_name(self):
        return "Controllo Sicurezza"
        
    def get_description(self):
        return "Identifica potenziali vulnerabilità di sicurezza nel codice PHP"
        
    def get_version(self):
        return "1.0.0"
        
    def get_author(self):
        return "Proietti House & Claude"
        
    def get_hooks(self):
        return {
            'syntax_check': [self.check_sicurezza]
        }
    
    def get_config_defaults(self):
        return {
            "check_sql_injection": True,
            "check_xss": True,
            "check_file_inclusion": True,
            "check_command_injection": True,
            "exclude_patterns": ["*/vendor/*", "*/tests/*"]
        }
    
    def check_sicurezza(self, filepath: str, lines: List[str], plugin_config: Dict = None, **kwargs) -> List[SyntaxError]:
        """
        Controlla vulnerabilità di sicurezza in un file PHP
        
        Args:
            filepath: Il percorso del file PHP
            lines: Le linee del file
            plugin_config: La configurazione del plugin
            
        Returns:
            Una lista di errori trovati
        """
        errors = []
        config = plugin_config or self.get_config_defaults()
        
        # Controlla se il file deve essere escluso
        if self._should_exclude_file(filepath, config):
            return errors
        
        # Controlla SQL Injection
        if config.get("check_sql_injection", True):
            errors.extend(self._check_sql_injection(lines))
        
        # Controlla XSS
        if config.get("check_xss", True):
            errors.extend(self._check_xss(lines))
        
        # Controlla File Inclusion
        if config.get("check_file_inclusion", True):
            errors.extend(self._check_file_inclusion(lines))
        
        # Controlla Command Injection
        if config.get("check_command_injection", True):
            errors.extend(self._check_command_injection(lines))
        
        return errors
    
    def _should_exclude_file(self, filepath: str, config: Dict) -> bool:
        """Verifica se il file deve essere escluso dall'analisi"""
        import fnmatch
        exclude_patterns = config.get("exclude_patterns", [])
        
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(filepath, pattern):
                return True
        return False
    
    def _check_sql_injection(self, lines: List[str]) -> List[SyntaxError]:
        """Controlla possibili vulnerabilità di SQL Injection"""
        errors = []
        
        # Pattern per rilevare possibili SQL Injection
        dangerous_patterns = [
            (r'mysqli_query\s*\(\s*[^,]+\s*,\s*\$[^)]*\s*\)', "Uso diretto di variabili in query SQL"),
            (r'mysql_query\s*\(\s*\$[^)]*\s*\)', "Uso diretto di variabili in query SQL"),
            (r'PDO.*->query\s*\(\s*\$[^)]*\s*\)', "Uso diretto di variabili in query PDO"),
            (r'SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*\s*=\s*\$', "Query SQL con potenziale vulnerabilità"),
            (r'INSERT\s+INTO\s+.*\s+VALUES\s*\(\s*.*\$', "Query SQL con potenziale vulnerabilità"),
            (r'UPDATE\s+.*\s+SET\s+.*\s*=\s*\$', "Query SQL con potenziale vulnerabilità")
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in dangerous_patterns:
                if re.search(pattern, line):
                    errors.append(SyntaxError(
                        i, line.strip(),
                        "Rischio SQL Injection",
                        description,
                        "Usa prepared statements o escape/sanitizza i dati con mysqli_real_escape_string o PDO::prepare"
                    ))
        
        return errors
    
    def _check_xss(self, lines: List[str]) -> List[SyntaxError]:
        """Controlla possibili vulnerabilità XSS"""
        errors = []
        
        # Pattern per rilevare possibili XSS
        dangerous_patterns = [
            (r'echo\s+\$_POST', "Output diretto di dati POST"),
            (r'echo\s+\$_GET', "Output diretto di dati GET"),
            (r'echo\s+\$_REQUEST', "Output diretto di dati REQUEST"),
            (r'echo\s+\$_COOKIE', "Output diretto di dati COOKIE"),
            (r'echo\s+\$_SERVER', "Output diretto di dati SERVER"),
            (r'echo\s+\$.*\[', "Output diretto di array senza sanitizzazione"),
            (r'print\s+\$_', "Output diretto di superglobale PHP"),
            (r'<\?=\s*\$_', "Output diretto tramite short tag")
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in dangerous_patterns:
                if re.search(pattern, line):
                    errors.append(SyntaxError(
                        i, line.strip(),
                        "Rischio XSS",
                        description,
                        "Usa htmlspecialchars o htmlentities per sanitizzare l'output"
                    ))
        
        return errors
    
    def _check_file_inclusion(self, lines: List[str]) -> List[SyntaxError]:
        """Controlla possibili vulnerabilità di Local/Remote File Inclusion"""
        errors = []
        
        dangerous_patterns = [
            (r'include\s*\(\s*\$', "Include dinamico da variabile"),
            (r'include_once\s*\(\s*\$', "Include_once dinamico da variabile"),
            (r'require\s*\(\s*\$', "Require dinamico da variabile"),
            (r'require_once\s*\(\s*\$', "Require_once dinamico da variabile"),
            (r'file_get_contents\s*\(\s*\$', "File get contents da variabile")
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in dangerous_patterns:
                if re.search(pattern, line):
                    errors.append(SyntaxError(
                        i, line.strip(),
                        "Rischio File Inclusion",
                        description,
                        "Valida e filtra il percorso del file prima di includerlo"
                    ))
        
        return errors
    
    def _check_command_injection(self, lines: List[str]) -> List[SyntaxError]:
        """Controlla possibili vulnerabilità di Command Injection"""
        errors = []
        
        dangerous_patterns = [
            (r'system\s*\(\s*\$', "Esecuzione di comando da variabile"),
            (r'exec\s*\(\s*\$', "Esecuzione di comando da variabile"),
            (r'shell_exec\s*\(\s*\$', "Esecuzione di comando da variabile"),
            (r'passthru\s*\(\s*\$', "Esecuzione di comando da variabile"),
            (r'eval\s*\(\s*\$', "Eval di codice da variabile"),
            (r'popen\s*\(\s*\$', "Apertura pipe da variabile"),
            (r'proc_open\s*\(\s*\$', "Apertura processo da variabile")
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, description in dangerous_patterns:
                if re.search(pattern, line):
                    errors.append(SyntaxError(
                        i, line.strip(),
                        "Rischio Command Injection",
                        description,
                        "Evita di eseguire comandi da input utente o sanitizza con escapeshellarg/escapeshellcmd"
                    ))
        
        return errors