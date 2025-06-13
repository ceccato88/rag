# manage_production_users.py

import json
import hashlib
from datetime import datetime
from pathlib import Path
import sys
import shutil

class ProductionUserManager:
    """Gerenciador de usuários para o sistema RAG de produção"""
    
    def __init__(self, users_file="production_users.json"):
        self.users_file = Path(users_file)
        self.users = self.load_users()
        self.salt = "streamlit_rag_production_2025"  # Mesmo salt da versão de produção
        
        # Permissões disponíveis
        self.available_permissions = [
            "extract",      # Extração de dados
            "stats",        # Estatísticas do sistema
            "clear_all",    # Limpar dados de outros usuários
            "manage_users", # Gerenciar outros usuários
            "admin"         # Acesso administrativo completo
        ]
        
        # Perfis pré-definidos com permissões
        self.role_permissions = {
            "Admin": ["extract", "stats", "clear_all", "manage_users", "admin"],
            "Pesquisador": ["extract", "stats"],
            "Demonstração": [],
            "Estudante": ["extract"],
            "Professor": ["extract", "stats"],
            "Convidado": []
        }
    
    def load_users(self):
        """Carrega usuários do arquivo"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Erro ao carregar usuários: {e}")
                return {}
        return {}
    
    def save_users(self):
        """Salva usuários no arquivo"""
        try:
            # Backup do arquivo atual
            if self.users_file.exists():
                backup_file = self.users_file.with_suffix('.json.backup')
                shutil.copy2(self.users_file, backup_file)
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar usuários: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Cria hash da senha com salt (compatível com produção)"""
        return hashlib.sha256((password + self.salt).encode()).hexdigest()
    
    def add_user(self, username: str, name: str, password: str, role: str = "Pesquisador", 
                 organization: str = "", custom_permissions: list = None):
        """Adiciona novo usuário"""
        if username in self.users:
            return False, "Usuário já existe!"
        
        if len(username) < 3:
            return False, "Nome de usuário deve ter pelo menos 3 caracteres!"
        
        if len(password) < 4:
            return False, "Senha deve ter pelo menos 4 caracteres!"
        
        # Define permissões baseadas no perfil ou customizadas
        if custom_permissions is not None:
            permissions = [p for p in custom_permissions if p in self.available_permissions]
        else:
            permissions = self.role_permissions.get(role, [])
        
        self.users[username] = {
            "password_hash": self.hash_password(password),
            "name": name,
            "role": role,
            "organization": organization,
            "permissions": permissions,
            "created_at": datetime.now().isoformat(),
            "last_login": "",
            "total_conversations": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "extractions_count": 0,
            "active": True,
            "notes": ""
        }
        
        if self.save_users():
            return True, f"Usuário '{username}' criado com sucesso!"
        else:
            return False, "Erro ao salvar usuário!"
    
    def update_user(self, username: str, **kwargs):
        """Atualiza informações do usuário"""
        if username not in self.users:
            return False, "Usuário não encontrado!"
        
        # Campos que podem ser atualizados
        allowed_fields = ['name', 'role', 'organization', 'active', 'notes']
        
        for field, value in kwargs.items():
            if field in allowed_fields:
                self.users[username][field] = value
            elif field == 'password':
                self.users[username]['password_hash'] = self.hash_password(value)
            elif field == 'permissions':
                # Valida permissões
                valid_permissions = [p for p in value if p in self.available_permissions]
                self.users[username]['permissions'] = valid_permissions
            elif field == 'role':
                # Atualiza permissões baseadas no novo perfil
                self.users[username]['role'] = value
                if value in self.role_permissions:
                    self.users[username]['permissions'] = self.role_permissions[value]
        
        self.users[username]['updated_at'] = datetime.now().isoformat()
        
        if self.save_users():
            return True, f"Usuário '{username}' atualizado com sucesso!"
        else:
            return False, "Erro ao atualizar usuário!"
    
    def remove_user(self, username: str):
        """Remove usuário"""
        if username not in self.users:
            return False, "Usuário não encontrado!"
        
        # Não permite remover se for o último admin
        if self.users[username].get('role') == 'Admin':
            admin_count = sum(1 for user in self.users.values() 
                            if user.get('role') == 'Admin' and user.get('active', True))
            if admin_count <= 1:
                return False, "Não é possível remover o último administrador!"
        
        del self.users[username]
        
        if self.save_users():
            # Remove também os dados do usuário
            user_dir = Path(f"production_users/{username}")
            if user_dir.exists():
                try:
                    shutil.rmtree(user_dir)
                    print(f"📁 Dados do usuário removidos: {user_dir}")
                except Exception as e:
                    print(f"⚠️ Erro ao remover dados: {e}")
            
            return True, f"Usuário '{username}' removido com sucesso!"
        else:
            return False, "Erro ao remover usuário!"
    
    def list_users(self, show_inactive=False):
        """Lista todos os usuários"""
        if not self.users:
            print("📋 Nenhum usuário cadastrado.")
            return
        
        users_to_show = self.users
        if not show_inactive:
            users_to_show = {k: v for k, v in self.users.items() if v.get('active', True)}
        
        print("📋 USUÁRIOS CADASTRADOS (SISTEMA DE PRODUÇÃO):")
        print("=" * 100)
        print(f"{'Username':<15} {'Nome':<25} {'Perfil':<15} {'Organização':<20} {'Permissões':<15} {'Status':<8}")
        print("-" * 100)
        
        for username, info in users_to_show.items():
            status = "Ativo" if info.get('active', True) else "Inativo"
            permissions_str = str(len(info.get('permissions', [])))
            org = info.get('organization', 'N/A')[:19]  # Trunca se muito longo
            
            print(f"{username:<15} {info['name']:<25} {info['role']:<15} {org:<20} {permissions_str:<15} {status:<8}")
        
        total_shown = len(users_to_show)
        total_all = len(self.users)
        
        if show_inactive:
            print(f"\nTotal: {total_all} usuários")
        else:
            print(f"\nAtivos: {total_shown} | Total: {total_all} usuários")
            if total_all > total_shown:
                print("💡 Use --include-inactive para ver usuários inativos")
    
    def get_user_details(self, username: str):
        """Mostra detalhes de um usuário específico"""
        if username not in self.users:
            print(f"❌ Usuário '{username}' não encontrado!")
            return
        
        user = self.users[username]
        print(f"\n👤 DETALHES DO USUÁRIO: {username}")
        print("=" * 60)
        print(f"Nome: {user['name']}")
        print(f"Perfil: {user['role']}")
        print(f"Organização: {user.get('organization', 'N/A')}")
        print(f"Status: {'Ativo' if user.get('active', True) else 'Inativo'}")
        print(f"Criado em: {user['created_at']}")
        print(f"Último login: {user.get('last_login', 'Nunca')}")
        
        # Permissões
        permissions = user.get('permissions', [])
        print(f"Permissões ({len(permissions)}): {', '.join(permissions) if permissions else 'Nenhuma'}")
        
        # Estatísticas de uso
        print(f"\n📊 Estatísticas de Uso:")
        print(f"  Conversas totais: {user.get('total_conversations', 0)}")
        print(f"  Consultas bem-sucedidas: {user.get('successful_queries', 0)}")
        print(f"  Consultas falhadas: {user.get('failed_queries', 0)}")
        print(f"  Extrações realizadas: {user.get('extractions_count', 0)}")
        
        # Taxa de sucesso
        total_queries = user.get('successful_queries', 0) + user.get('failed_queries', 0)
        if total_queries > 0:
            success_rate = (user.get('successful_queries', 0) / total_queries) * 100
            print(f"  Taxa de sucesso: {success_rate:.1f}%")
        
        # Notas
        if user.get('notes'):
            print(f"\n📝 Notas: {user['notes']}")
        
        # Verifica dados salvos
        user_dir = Path(f"production_users/{username}")
        if user_dir.exists():
            memory_file = user_dir / "chat_history.json"
            stats_file = user_dir / "user_stats.json"
            
            print(f"\n💾 Dados Salvos:")
            
            if memory_file.exists():
                try:
                    with open(memory_file, 'r') as f:
                        data = json.load(f)
                        print(f"  Histórico: {data.get('total_messages', 0)} mensagens")
                        print(f"  Última atualização: {data.get('last_updated', 'N/A')}")
                except:
                    print("  Histórico: Erro ao ler")
            else:
                print("  Histórico: Nenhum")
            
            if stats_file.exists():
                try:
                    with open(stats_file, 'r') as f:
                        stats = json.load(f)
                        print(f"  Primeira atividade: {stats.get('first_login', 'N/A')}")
                        print(f"  Última atividade: {stats.get('last_activity', 'N/A')}")
                except:
                    print("  Estatísticas: Erro ao ler")
        else:
            print(f"\n💾 Dados Salvos: Nenhum")

def show_menu():
    """Mostra menu principal"""
    print("\n🚀 GERENCIADOR DE USUÁRIOS - SISTEMA RAG PRODUÇÃO")
    print("=" * 60)
    print("1. 👤 Adicionar usuário")
    print("2. 📋 Listar usuários")
    print("3. 🔍 Detalhes do usuário")
    print("4. ✏️  Editar usuário")
    print("5. 🔒 Alterar senha")
    print("6. 🔑 Gerenciar permissões")
    print("7. ❌ Remover usuário")
    print("8. 📊 Estatísticas")
    print("9. 🔧 Ferramentas")
    print("10. 🚪 Sair")
    print("-" * 60)

def add_user_interactive(manager):
    """Adiciona usuário interativamente"""
    print("\n👤 ADICIONAR NOVO USUÁRIO")
    print("-" * 40)
    
    username = input("Username (login): ").strip()
    name = input("Nome completo: ").strip()
    password = input("Senha: ").strip()
    
    print(f"\nPerfis disponíveis:")
    roles = list(manager.role_permissions.keys())
    for i, role in enumerate(roles, 1):
        perms = manager.role_permissions[role]
        print(f"{i}. {role} ({len(perms)} permissões)")
    
    role_choice = input(f"Escolha o perfil (1-{len(roles)}): ").strip()
    try:
        role = roles[int(role_choice) - 1]
    except (ValueError, IndexError):
        role = "Pesquisador"
        print(f"⚠️ Opção inválida, usando perfil padrão: {role}")
    
    organization = input("Organização (opcional): ").strip()
    
    # Opção de personalizar permissões
    custom_perms = input("\nPersonalizar permissões? (s/n): ").strip().lower()
    permissions = None
    
    if custom_perms == 's':
        print(f"\nPermissões disponíveis:")
        for i, perm in enumerate(manager.available_permissions, 1):
            print(f"{i}. {perm}")
        
        perm_input = input("Digite os números das permissões (ex: 1,3,5): ").strip()
        if perm_input:
            try:
                perm_indices = [int(x.strip()) - 1 for x in perm_input.split(',')]
                permissions = [manager.available_permissions[i] for i in perm_indices 
                             if 0 <= i < len(manager.available_permissions)]
            except:
                print("⚠️ Formato inválido, usando permissões do perfil")
    
    success, message = manager.add_user(username, name, password, role, organization, permissions)
    
    if success:
        print(f"✅ {message}")
        
        # Mostra resumo do usuário criado
        user = manager.users[username]
        print(f"\n📋 Resumo do usuário criado:")
        print(f"  Username: {username}")
        print(f"  Nome: {name}")
        print(f"  Perfil: {role}")
        print(f"  Permissões: {', '.join(user['permissions']) if user['permissions'] else 'Nenhuma'}")
    else:
        print(f"❌ {message}")

def edit_user_interactive(manager):
    """Edita usuário interativamente"""
    print("\n✏️ EDITAR USUÁRIO")
    print("-" * 30)
    
    username = input("Username para editar: ").strip()
    
    if username not in manager.users:
        print("❌ Usuário não encontrado!")
        return
    
    user = manager.users[username]
    print(f"\nDados atuais de '{username}':")
    print(f"Nome: {user['name']}")
    print(f"Perfil: {user['role']}")
    print(f"Organização: {user.get('organization', 'N/A')}")
    print(f"Status: {'Ativo' if user.get('active', True) else 'Inativo'}")
    print(f"Permissões: {', '.join(user.get('permissions', []))}")
    print(f"Notas: {user.get('notes', 'Nenhuma')}")
    
    print("\nDeixe em branco para manter o valor atual:")
    
    new_name = input(f"Novo nome [{user['name']}]: ").strip()
    
    # Perfis
    print(f"\nPerfis disponíveis:")
    roles = list(manager.role_permissions.keys())
    for i, role in enumerate(roles, 1):
        print(f"{i}. {role}")
    
    current_role_idx = roles.index(user['role']) + 1 if user['role'] in roles else 0
    new_role_input = input(f"Novo perfil [{current_role_idx}={user['role']}]: ").strip()
    
    new_org = input(f"Nova organização [{user.get('organization', 'N/A')}]: ").strip()
    
    new_notes = input(f"Novas notas [{user.get('notes', 'Nenhuma')}]: ").strip()
    
    status_input = input("Ativo? (s/n) [atual: {}]: ".format('s' if user.get('active', True) else 'n')).strip().lower()
    
    # Prepara atualizações
    updates = {}
    
    if new_name:
        updates['name'] = new_name
    
    if new_role_input:
        try:
            role_idx = int(new_role_input) - 1
            if 0 <= role_idx < len(roles):
                updates['role'] = roles[role_idx]
        except ValueError:
            pass
    
    if new_org:
        updates['organization'] = new_org
    
    if new_notes:
        updates['notes'] = new_notes
    
    if status_input in ['s', 'n']:
        updates['active'] = status_input == 's'
    
    if updates:
        success, message = manager.update_user(username, **updates)
        print(f"✅ {message}" if success else f"❌ {message}")
    else:
        print("ℹ️ Nenhuma alteração feita.")

def manage_permissions_interactive(manager):
    """Gerencia permissões do usuário"""
    print("\n🔑 GERENCIAR PERMISSÕES")
    print("-" * 30)
    
    username = input("Username: ").strip()
    
    if username not in manager.users:
        print("❌ Usuário não encontrado!")
        return
    
    user = manager.users[username]
    current_perms = user.get('permissions', [])
    
    print(f"\nPermissões atuais de '{username}':")
    if current_perms:
        for i, perm in enumerate(current_perms, 1):
            print(f"  {i}. {perm}")
    else:
        print("  Nenhuma permissão")
    
    print(f"\nPermissões disponíveis:")
    for i, perm in enumerate(manager.available_permissions, 1):
        status = "✓" if perm in current_perms else " "
        print(f"  {i}. [{status}] {perm}")
    
    print(f"\nOpções:")
    print("1. Adicionar permissões")
    print("2. Remover permissões")
    print("3. Definir permissões do perfil")
    print("4. Limpar todas as permissões")
    
    choice = input("Escolha (1-4): ").strip()
    
    if choice == "1":
        # Adicionar
        available = [p for p in manager.available_permissions if p not in current_perms]
        if not available:
            print("✅ Usuário já tem todas as permissões!")
            return
        
        print("Permissões para adicionar:")
        for i, perm in enumerate(available, 1):
            print(f"  {i}. {perm}")
        
        selections = input("Digite os números (ex: 1,3): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selections.split(',')]
            to_add = [available[i] for i in indices if 0 <= i < len(available)]
            new_perms = current_perms + to_add
        except:
            print("❌ Formato inválido!")
            return
    
    elif choice == "2":
        # Remover
        if not current_perms:
            print("ℹ️ Usuário não tem permissões para remover!")
            return
        
        selections = input("Digite os números para remover (ex: 1,3): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selections.split(',')]
            to_remove = [current_perms[i] for i in indices if 0 <= i < len(current_perms)]
            new_perms = [p for p in current_perms if p not in to_remove]
        except:
            print("❌ Formato inválido!")
            return
    
    elif choice == "3":
        # Usar permissões do perfil
        role = user['role']
        new_perms = manager.role_permissions.get(role, [])
        print(f"Aplicando permissões do perfil '{role}': {', '.join(new_perms) if new_perms else 'Nenhuma'}")
    
    elif choice == "4":
        # Limpar todas
        new_perms = []
        print("Removendo todas as permissões...")
    
    else:
        print("❌ Opção inválida!")
        return
    
    success, message = manager.update_user(username, permissions=new_perms)
    print(f"✅ {message}" if success else f"❌ {message}")

def change_password_interactive(manager):
    """Altera senha do usuário"""
    print("\n🔒 ALTERAR SENHA")
    print("-" * 20)
    
    username = input("Username: ").strip()
    
    if username not in manager.users:
        print("❌ Usuário não encontrado!")
        return
    
    print(f"Alterando senha para: {manager.users[username]['name']}")
    new_password = input("Nova senha: ").strip()
    
    if len(new_password) < 4:
        print("❌ Senha deve ter pelo menos 4 caracteres!")
        return
    
    confirm_password = input("Confirme a nova senha: ").strip()
    
    if new_password != confirm_password:
        print("❌ Senhas não coincidem!")
        return
    
    success, message = manager.update_user(username, password=new_password)
    print(f"✅ {message}" if success else f"❌ {message}")

def show_statistics(manager):
    """Mostra estatísticas do sistema"""
    print("\n📊 ESTATÍSTICAS DO SISTEMA DE PRODUÇÃO")
    print("=" * 50)
    
    if not manager.users:
        print("Nenhum usuário cadastrado.")
        return
    
    total_users = len(manager.users)
    active_users = sum(1 for user in manager.users.values() if user.get('active', True))
    
    # Conta por perfil
    roles = {}
    permissions_count = {}
    for user in manager.users.values():
        role = user['role']
        roles[role] = roles.get(role, 0) + 1
        
        for perm in user.get('permissions', []):
            permissions_count[perm] = permissions_count.get(perm, 0) + 1
    
    print(f"📈 Usuários:")
    print(f"  Total: {total_users}")
    print(f"  Ativos: {active_users}")
    print(f"  Inativos: {total_users - active_users}")
    
    print(f"\n👥 Por perfil:")
    for role, count in sorted(roles.items()):
        print(f"  {role}: {count}")
    
    print(f"\n🔑 Permissões mais usadas:")
    for perm, count in sorted(permissions_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {perm}: {count} usuários")
    
    # Estatísticas de uso
    total_conversations = sum(u.get('total_conversations', 0) for u in manager.users.values())
    total_extractions = sum(u.get('extractions_count', 0) for u in manager.users.values())
    
    print(f"\n💬 Uso do sistema:")
    print(f"  Total de conversas: {total_conversations}")
    print(f"  Total de extrações: {total_extractions}")
    
    # Verifica diretórios de usuários
    users_with_data = 0
    total_messages = 0
    
    for username in manager.users:
        user_dir = Path(f"production_users/{username}")
        if user_dir.exists():
            memory_file = user_dir / "chat_history.json"
            if memory_file.exists():
                users_with_data += 1
                try:
                    with open(memory_file, 'r') as f:
                        data = json.load(f)
                        total_messages += data.get('total_messages', 0)
                except:
                    pass
    
    print(f"\n💾 Dados salvos:")
    print(f"  Usuários com dados: {users_with_data}")
    print(f"  Total de mensagens: {total_messages}")
    
    # Usuários mais ativos
    if total_conversations > 0:
        print(f"\n🏆 Usuários mais ativos:")
        active_users_list = [(username, user.get('total_conversations', 0)) 
                           for username, user in manager.users.items() 
                           if user.get('total_conversations', 0) > 0]
        active_users_list.sort(key=lambda x: x[1], reverse=True)
        
        for username, conversations in active_users_list[:5]:
            print(f"  {username}: {conversations} conversas")

def tools_menu(manager):
    """Menu de ferramentas"""
    print("\n🔧 FERRAMENTAS")
    print("-" * 20)
    print("1. Backup dos usuários")
    print("2. Limpar dados de usuário")
    print("3. Resetar estatísticas")
    print("4. Migrar da versão antiga")
    print("5. Voltar")
    
    choice = input("Escolha (1-5): ").strip()
    
    if choice == "1":
        # Backup
        backup_file = f"production_users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            shutil.copy2(manager.users_file, backup_file)
            print(f"✅ Backup criado: {backup_file}")
        except Exception as e:
            print(f"❌ Erro no backup: {e}")
    
    elif choice == "2":
        # Limpar dados de usuário
        username = input("Username para limpar dados: ").strip()
        if username not in manager.users:
            print("❌ Usuário não encontrado!")
            return
        
        confirm = input(f"⚠️ Confirma limpeza dos dados de '{username}'? (CONFIRMAR): ").strip()
        if confirm == "CONFIRMAR":
            user_dir = Path(f"production_users/{username}")
            if user_dir.exists():
                try:
                    shutil.rmtree(user_dir)
                    print(f"✅ Dados removidos: {user_dir}")
                except Exception as e:
                    print(f"❌ Erro: {e}")
            else:
                print("ℹ️ Usuário não possui dados salvos")
    
    elif choice == "3":
        # Resetar estatísticas
        username = input("Username para resetar estatísticas (ou 'todos'): ").strip()
        
        if username == "todos":
            confirm = input("⚠️ Resetar estatísticas de TODOS os usuários? (CONFIRMAR): ").strip()
            if confirm == "CONFIRMAR":
                for user in manager.users.values():
                    user['total_conversations'] = 0
                    user['successful_queries'] = 0
                    user['failed_queries'] = 0
                    user['extractions_count'] = 0
                
                if manager.save_users():
                    print("✅ Estatísticas resetadas para todos os usuários!")
                else:
                    print("❌ Erro ao salvar!")
        
        elif username in manager.users:
            manager.users[username].update({
                'total_conversations': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'extractions_count': 0
            })
            
            if manager.save_users():
                print(f"✅ Estatísticas resetadas para '{username}'!")
            else:
                print("❌ Erro ao salvar!")
        else:
            print("❌ Usuário não encontrado!")
    
    elif choice == "4":
        # Migração da versão antiga
        old_file = "streamlit_users.json"
        if Path(old_file).exists():
            print(f"📁 Encontrado arquivo antigo: {old_file}")
            migrate = input("Migrar usuários? (s/n): ").strip().lower()
            
            if migrate == 's':
                try:
                    with open(old_file, 'r') as f:
                        old_users = json.load(f)
                    
                    migrated = 0
                    for username, old_user in old_users.items():
                        if username not in manager.users:
                            # Converte formato antigo para novo
                            # Mapeia roles antigos para novos
                            role_mapping = {
                                "researcher": "Pesquisador",
                                "student": "Estudante", 
                                "professor": "Professor",
                                "admin": "Admin"
                            }
                            
                            old_role = old_user.get("role", "researcher")
                            new_role = role_mapping.get(old_role, "Pesquisador")
                            
                            new_user = {
                                "password_hash": old_user.get("password_hash", ""),
                                "name": old_user.get("name", username),
                                "role": new_role,
                                "organization": old_user.get("organization", ""),
                                "permissions": manager.role_permissions.get(new_role, []),
                                "created_at": old_user.get("created_at", datetime.now().isoformat()),
                                "last_login": old_user.get("last_login", ""),
                                "total_conversations": old_user.get("total_conversations", 0),
                                "successful_queries": 0,
                                "failed_queries": 0,
                                "extractions_count": 0,
                                "active": old_user.get("active", True),
                                "notes": f"Migrado de {old_file}"
                            }
                            
                            manager.users[username] = new_user
                            migrated += 1
                    
                    if manager.save_users():
                        print(f"✅ {migrated} usuários migrados com sucesso!")
                        
                        # Pergunta se quer fazer backup do arquivo antigo
                        backup = input("Fazer backup do arquivo antigo? (s/n): ").strip().lower()
                        if backup == 's':
                            backup_name = f"streamlit_users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            shutil.copy2(old_file, backup_name)
                            print(f"📁 Backup criado: {backup_name}")
                    else:
                        print("❌ Erro ao salvar usuários migrados!")
                        
                except Exception as e:
                    print(f"❌ Erro na migração: {e}")
        else:
            print(f"ℹ️ Arquivo antigo não encontrado: {old_file}")

def main():
    """Função principal"""
    manager = ProductionUserManager()
    
    # Cria usuários padrão se não existirem
    if not manager.users:
        print("🏗️ Criando usuários padrão...")
        
        default_users = [
            ("admin", "Administrador", "admin123", "Admin", "Sistema"),
            ("pesquisador", "Dr. Pesquisador", "pesquisa123", "Pesquisador", "Universidade"),
            ("demo", "Usuário Demo", "demo123", "Demonstração", "Demo")
        ]
        
        for username, name, password, role, org in default_users:
            success, message = manager.add_user(username, name, password, role, org)
            if success:
                print(f"✅ {message}")
            else:
                print(f"⚠️ {message}")
    
    # Modo não-interativo para automação
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            show_inactive = "--include-inactive" in sys.argv
            manager.list_users(show_inactive)
        
        elif command == "add" and len(sys.argv) >= 5:
            username, name, password = sys.argv[2:5]
            role = sys.argv[5] if len(sys.argv) > 5 else "Pesquisador"
            organization = sys.argv[6] if len(sys.argv) > 6 else ""
            
            success, message = manager.add_user(username, name, password, role, organization)
            print(message)
        
        elif command == "remove" and len(sys.argv) >= 3:
            username = sys.argv[2]
            success, message = manager.remove_user(username)
            print(message)
        
        elif command == "details" and len(sys.argv) >= 3:
            username = sys.argv[2]
            manager.get_user_details(username)
        
        elif command == "password" and len(sys.argv) >= 4:
            username, new_password = sys.argv[2:4]
            success, message = manager.update_user(username, password=new_password)
            print(message)
        
        elif command == "stats":
            show_statistics(manager)
        
        elif command == "backup":
            backup_file = f"production_users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            try:
                shutil.copy2(manager.users_file, backup_file)
                print(f"✅ Backup criado: {backup_file}")
            except Exception as e:
                print(f"❌ Erro no backup: {e}")
        
        elif command == "help":
            print("🚀 GERENCIADOR DE USUÁRIOS RAG PRODUÇÃO")
            print("\nComandos disponíveis:")
            print("  list [--include-inactive]  - Lista usuários")
            print("  add <user> <nome> <senha> [role] [org] - Adiciona usuário")
            print("  remove <user>              - Remove usuário")
            print("  details <user>             - Detalhes do usuário")
            print("  password <user> <senha>    - Altera senha")
            print("  stats                      - Estatísticas")
            print("  backup                     - Backup dos usuários")
            print("  help                       - Esta ajuda")
            print("\nPerfis disponíveis: Admin, Pesquisador, Demonstração, Estudante, Professor, Convidado")
            print("\nExemplos:")
            print("  python manage_production_users.py add joao 'João Silva' senha123 Pesquisador 'UFMG'")
            print("  python manage_production_users.py list --include-inactive")
            print("  python manage_production_users.py details admin")
        
        else:
            print("❌ Comando inválido! Use 'help' para ver comandos disponíveis.")
        
        return
    
    # Modo interativo
    while True:
        show_menu()
        choice = input("\nEscolha uma opção (1-10): ").strip()
        
        if choice == "1":
            add_user_interactive(manager)
        
        elif choice == "2":
            show_inactive = input("\nIncluir usuários inativos? (s/n): ").strip().lower() == 's'
            manager.list_users(show_inactive)
        
        elif choice == "3":
            username = input("\nUsername para ver detalhes: ").strip()
            manager.get_user_details(username)
        
        elif choice == "4":
            edit_user_interactive(manager)
        
        elif choice == "5":
            change_password_interactive(manager)
        
        elif choice == "6":
            manage_permissions_interactive(manager)
        
        elif choice == "7":
            username = input("\nUsername para remover: ").strip()
            
            if username in manager.users:
                user_info = manager.users[username]
                print(f"\n⚠️ ATENÇÃO: Você está prestes a remover:")
                print(f"   Usuário: {username}")
                print(f"   Nome: {user_info['name']}")
                print(f"   Perfil: {user_info['role']}")
                print(f"   Organização: {user_info.get('organization', 'N/A')}")
                
                confirm = input(f"\nPara confirmar, digite 'REMOVER {username}': ").strip()
                
                if confirm == f"REMOVER {username}":
                    success, message = manager.remove_user(username)
                    print(f"✅ {message}" if success else f"❌ {message}")
                else:
                    print("❌ Remoção cancelada.")
            else:
                print("❌ Usuário não encontrado!")
        
        elif choice == "8":
            show_statistics(manager)
        
        elif choice == "9":
            tools_menu(manager)
        
        elif choice == "10":
            print("\n👋 Até logo!")
            print("🚀 Sistema RAG de Produção - Usuários gerenciados com sucesso!")
            break
        
        else:
            print("❌ Opção inválida!")
        
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Operação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        sys.exit(1)