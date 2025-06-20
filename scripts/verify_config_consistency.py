#!/usr/bin/env python3
"""
Script para verificar consistência da configuração do sistema RAG.
Uso: python scripts/verify_config_consistency.py
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Adicionar diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from src.core.config import SystemConfig
    from src.core.constants import *
except ImportError as e:
    print(f"❌ Erro ao importar configurações: {e}")
    sys.exit(1)

class ConfigConsistencyChecker:
    """Verificador de consistência de configuração."""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.issues = []
        self.warnings = []
        
    def check_hardcoded_values(self) -> List[str]:
        """Verifica valores hardcoded no código."""
        issues = []
        
        # Padrões suspeitos
        suspicious_patterns = [
            (r'\btemperature\s*=\s*0\.\d+', 'Temperatura hardcoded'),
            (r'\bmax_tokens\s*=\s*\d+', 'max_tokens hardcoded'),
            (r'model\s*=\s*["\']gpt-', 'Modelo hardcoded'),
            (r'model\s*=\s*["\']voyage-', 'Modelo de embedding hardcoded'),
            (r'os\.getenv\s*\(\s*["\'][A-Z_]+["\']', 'Uso direto de os.getenv'),
        ]
        
        # Arquivos que são legítimos para ter os.getenv e valores hardcoded
        legitimate_files = {
            'src/core/config.py',     # Arquivo principal de configuração
            'api/core/config.py',     # Arquivo de configuração da API
            'src/core/constants.py',  # Arquivo de constantes
            'src/utils/env_validation.py',  # Utilitário de validação
        }
        
        # Buscar em arquivos Python
        for py_file in self.root_dir.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            
            # Converter para caminho relativo
            rel_path = str(py_file.relative_to(self.root_dir))
            
            # Pular arquivos legítimos e exemplos
            if rel_path in legitimate_files or rel_path.startswith('exemplo/'):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                for pattern, description in suspicious_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        for match in matches:
                            # Pular matches que estão sendo usados corretamente
                            if description == 'max_tokens hardcoded' and ('config.rag.' in content or 'TOKEN_LIMITS' in content):
                                continue
                            if description == 'Temperatura hardcoded' and ('config.rag.' in content or 'PROCESSING_CONFIG' in content):
                                continue
                            issues.append(f"{rel_path}: {description} - '{match}'")
            except Exception as e:
                self.warnings.append(f"Não foi possível ler {py_file}: {e}")
        
        return issues
    
    def check_env_alignment(self) -> List[str]:
        """Verifica alinhamento entre .env.example e constants.py."""
        issues = []
        
        env_file = self.root_dir / ".env.example"
        if not env_file.exists():
            issues.append(".env.example não encontrado")
            return issues
        
        # Extrair variáveis do .env.example
        env_vars = set()
        try:
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    var_name = line.split('=')[0]
                    env_vars.add(var_name)
        except Exception as e:
            issues.append(f"Erro ao ler .env.example: {e}")
            return issues
        
        # Verificar se todas as variáveis estão nas constantes ou enhanced_config
        constants_file = self.root_dir / "src" / "core" / "constants.py"
        enhanced_config_file = self.root_dir / "multi-agent-researcher" / "src" / "researcher" / "enhanced" / "enhanced_config.py"
        
        constants_content = ""
        enhanced_config_content = ""
        
        if constants_file.exists():
            try:
                constants_content = constants_file.read_text()
            except Exception as e:
                issues.append(f"Erro ao ler constants.py: {e}")
                
        if enhanced_config_file.exists():
            try:
                enhanced_config_content = enhanced_config_file.read_text()
            except Exception as e:
                issues.append(f"Erro ao ler enhanced_config.py: {e}")
        
        # Verificar se variáveis estão em qualquer um dos arquivos
        for var in env_vars:
            if (var not in constants_content and 
                var not in enhanced_config_content and
                not var.startswith('MAX_CANDIDATES_')):  # Estas estão no enhanced_config
                issues.append(f"Variável {var} do .env.example não encontrada em constants.py ou enhanced_config.py")
        
        return issues
    
    def check_config_integration(self) -> List[str]:
        """Verifica se configurações estão integradas no config.py."""
        issues = []
        
        try:
            config = SystemConfig()
            # Testar se as principais configurações são carregáveis
            essential_configs = [
                ('config.rag.llm_model', 'Modelo LLM'),
                ('config.rag.temperature', 'Temperatura'),
                ('config.rag.max_tokens', 'Max tokens'),
                ('config.multiagent.max_subagents', 'Max subagents'),
                ('config.security.enable_rate_limiting', 'Rate limiting'),
            ]
            
            for attr_path, description in essential_configs:
                try:
                    # Navegar pelos atributos
                    obj = config
                    for attr in attr_path.split('.')[1:]:  # Pular 'config'
                        obj = getattr(obj, attr)
                except AttributeError:
                    issues.append(f"Configuração essencial não encontrada: {description} ({attr_path})")
                    
        except Exception as e:
            issues.append(f"Erro ao carregar SystemConfig: {e}")
        
        return issues
    
    def check_variable_tracking(self) -> List[str]:
        """Verifica se VARIABLE_TRACKING.md existe e está atualizado."""
        issues = []
        
        tracking_file = self.root_dir / "VARIABLE_TRACKING.md"
        if not tracking_file.exists():
            issues.append("VARIABLE_TRACKING.md não encontrado")
            return issues
        
        try:
            content = tracking_file.read_text()
            
            # Verificar se status indica conclusão
            if "**Status**: ✅ CONCLUÍDO" not in content:
                self.warnings.append("VARIABLE_TRACKING.md pode não estar atualizado")
            
            # Verificar se tem as 77 variáveis (atualizado após melhorias)
            if "77/77 (100%)" not in content:
                self.warnings.append("VARIABLE_TRACKING.md pode não ter todas as variáveis")
                
        except Exception as e:
            issues.append(f"Erro ao ler VARIABLE_TRACKING.md: {e}")
        
        return issues
    
    def run_all_checks(self) -> Tuple[bool, Dict[str, List[str]]]:
        """Executa todas as verificações."""
        results = {
            'hardcoded_values': self.check_hardcoded_values(),
            'env_alignment': self.check_env_alignment(),
            'config_integration': self.check_config_integration(),
            'variable_tracking': self.check_variable_tracking(),
        }
        
        # Determinar se passou
        total_issues = sum(len(issues) for issues in results.values())
        passed = total_issues == 0
        
        return passed, results

def main():
    """Função principal."""
    print("🔍 Verificando consistência da configuração do sistema RAG...\n")
    
    checker = ConfigConsistencyChecker()
    passed, results = checker.run_all_checks()
    
    # Mostrar resultados
    for check_name, issues in results.items():
        check_display = check_name.replace('_', ' ').title()
        if issues:
            print(f"❌ {check_display}:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i:2d}. {issue}")
            print(f"   📊 Total: {len(issues)} problemas encontrados")
            print()
        else:
            print(f"✅ {check_display}: OK")
    
    # Mostrar warnings
    if checker.warnings:
        print("\n⚠️  Avisos:")
        for warning in checker.warnings:
            print(f"   • {warning}")
    
    # Resultado final
    print(f"\n{'='*50}")
    if passed:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("   Sistema de configuração está consistente.")
    else:
        total_issues = sum(len(issues) for issues in results.values())
        print(f"❌ ENCONTRADOS {total_issues} PROBLEMAS!")
        print("   Verifique e corrija os problemas listados acima.")
        print("   Consulte BOAS_PRATICAS_CONFIGURACAO.md para orientações.")
    
    print(f"{'='*50}")
    
    # Exit code
    sys.exit(0 if passed else 1)

if __name__ == "__main__":
    main()