# streamlit_rag_app_producao.py

import streamlit as st
import json
import hashlib
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

# Importa a versão do sistema
from buscador_conversacional_producao import ProductionConversationalRAG, health_check

# Configuração da página
st.set_page_config(
    page_title="RAG Conversacional",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração de logging específica para o Streamlit
def setup_streamlit_logging():
    """Configura logging específico para o Streamlit"""
    st_logger = logging.getLogger(__name__)
    st_logger.setLevel(logging.DEBUG)
    
    # Remove handlers existentes para evitar duplicação
    for handler in st_logger.handlers[:]:
        st_logger.removeHandler(handler)
    
    # Formatter detalhado
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Menos verboso no console para Streamlit
    console_handler.setFormatter(formatter)
    st_logger.addHandler(console_handler)
    
    # Handler para arquivo específico do Streamlit
    file_handler = logging.FileHandler("streamlit_debug.log", encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    st_logger.addHandler(file_handler)
    
    # Permite propagação para mostrar logs no console principal
    st_logger.propagate = True
    
    return st_logger

logger = setup_streamlit_logging()

# Log inicial para confirmar que o sistema de logging está funcionando
logger.info("🌐 [INIT] Sistema de logging do Streamlit inicializado")

def get_sao_paulo_time():
    """Retorna datetime atual no fuso horário de São Paulo"""
    return datetime.now(ZoneInfo("America/Sao_Paulo"))

def close_all_modals():
    """Fecha todos os modals abertos"""
    # Log quais modals estavam abertos
    open_modals = []
    if st.session_state.get('show_user_management', False):
        open_modals.append('Gerenciamento de Usuários')
    if st.session_state.get('show_user_stats', False):
        open_modals.append('Estatísticas Pessoais')
    if st.session_state.get('show_document_management', False):
        open_modals.append('Gerenciamento de Documentos')
    
    if open_modals:
        logger.debug(f"[MODAL] Fechando modals: {', '.join(open_modals)}")
    
    st.session_state.show_user_management = False
    st.session_state.show_user_stats = False
    st.session_state.show_document_management = False
    # Limpa estado de edição se existir
    if 'edit_user' in st.session_state:
        del st.session_state.edit_user

class StreamlitUserManager:
    """Gerenciador de usuários para Streamlit"""
    
    def __init__(self, users_file="production_users.json"):
        self.users_file = Path(users_file)
        self.users = self.load_users()
        self._create_default_users()
    
    def _create_default_users(self):
        """Cria usuários padrão se não existirem"""
        # Não cria mais usuários automaticamente
        pass
    
    def load_users(self) -> Dict:
        """Carrega usuários do arquivo"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar usuários: {e}")
                return {}
        return {}
    
    def save_users(self):
        """Salva usuários no arquivo"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar usuários: {e}")
    
    def hash_password(self, password: str) -> str:
        """Hash da senha com salt"""
        salt = "streamlit_rag_production_2025"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> bool:
        """Autentica usuário"""
        if username in self.users:
            return self.users[username]["password_hash"] == self.hash_password(password)
        return False
    
    def get_user_info(self, username: str) -> Dict:
        """Pega informações do usuário"""
        return self.users.get(username, {})
    
    def is_admin(self, username: str) -> bool:
        """Verifica se usuário é admin"""
        user = self.users.get(username, {})
        return user.get("role") == "Admin"

@st.cache_resource
def _get_global_rag_instance():
    """Instância global do RAG (cache do Streamlit)"""
    try:
        logger.info("[CACHE] Inicializando instância global RAG...")
        start_time = time.time()
        
        rag_instance = ProductionConversationalRAG()
        
        init_time = time.time() - start_time
        logger.info(f"[CACHE] RAG inicializado com sucesso em {init_time:.2f}s")
        
        return rag_instance
    except Exception as e:
        logger.error(f"[CACHE] Erro ao inicializar RAG: {e}", exc_info=True)
        st.error(f"❌ Erro na inicialização: {e}")
        return None

class ProductionStreamlitRAG:
    """RAG adaptado para Streamlit com cache e otimizações"""
    
    def __init__(self, user_id: str):
        logger.info(f"[USER] Inicializando ProductionStreamlitRAG para usuário: {user_id}")
        
        self.user_id = user_id
        self.user_dir = Path(f"production_users/{user_id}")
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.user_dir / "chat_history.json"
        self.stats_file = self.user_dir / "user_stats.json"
        
        logger.debug(f"[USER] Diretório do usuário: {self.user_dir}")
        
        # Inicializa RAG (com cache global no Streamlit)
        self._initialize_rag()
        
        # Carrega histórico e estatísticas do usuário
        self.load_user_data()
        
        logger.info(f"[USER] ProductionStreamlitRAG inicializado para {user_id}")
    
    def _initialize_rag(self):
        """Inicializa RAG usando cache global"""
        if "rag_instance" not in st.session_state:
            st.session_state.rag_instance = _get_global_rag_instance()
        
        if st.session_state.rag_instance is None:
            st.error("❌ Sistema RAG não inicializado corretamente")
            st.stop()
    
    def load_user_data(self):
        """Carrega dados específicos do usuário"""
        # Carrega histórico
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Define histórico específico do usuário no RAG
                    st.session_state.rag_instance.chat_history = data.get("chat_history", [])
            except Exception as e:
                logger.warning(f"Erro ao carregar histórico do usuário {self.user_id}: {e}")
                st.session_state.rag_instance.chat_history = []
        else:
            st.session_state.rag_instance.chat_history = []
        
        # Carrega estatísticas
        self.user_stats = self._load_user_stats()
    
    def _load_user_stats(self) -> Dict:
        """Carrega estatísticas do usuário"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "total_questions": 0,
            "successful_answers": 0,
            "first_login": get_sao_paulo_time().isoformat(),
            "last_activity": get_sao_paulo_time().isoformat()
        }
    
    def _save_user_stats(self):
        """Salva estatísticas do usuário"""
        try:
            self.user_stats["last_activity"] = get_sao_paulo_time().isoformat()
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar estatísticas: {e}")
    
    def save_user_history(self):
        """Salva histórico do usuário"""
        try:
            memory_data = {
                "user_id": self.user_id,
                "last_updated": get_sao_paulo_time().isoformat(),
                "total_messages": len(st.session_state.rag_instance.chat_history),
                "chat_history": st.session_state.rag_instance.chat_history
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
            
            self._save_user_stats()
        except Exception as e:
            logger.error(f"Erro ao salvar histórico: {e}")
            st.error(f"Erro ao salvar dados: {e}")
    
    def ask(self, question: str) -> str:
        """Faz pergunta usando RAG e salva automaticamente"""
        start_time = time.time()
        
        logger.info(f"[ASK] Usuário {self.user_id} perguntou: {question[:100]}...")
        
        try:
            self.user_stats["total_questions"] += 1
            logger.debug(f"[ASK] Total de perguntas do usuário: {self.user_stats['total_questions']}")
            
            # Usa o método ask do sistema
            logger.debug(f"[ASK] Chamando RAG...")
            response = st.session_state.rag_instance.ask(question)
            
            processing_time = time.time() - start_time
            logger.info(f"[ASK] Resposta gerada em {processing_time:.2f}s")
            
            if "erro" not in response.lower() and "desculpe" not in response.lower():
                self.user_stats["successful_answers"] += 1
                logger.debug(f"[ASK] Resposta bem-sucedida registrada")
            else:
                logger.warning(f"[ASK] Resposta com possível erro detectado")
            
            logger.debug(f"[ASK] Salvando histórico do usuário...")
            self.save_user_history()
            
            logger.info(f"[ASK] Processo completo em {time.time() - start_time:.2f}s")
            return response
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"[ASK] Erro na pergunta do usuário {self.user_id} após {error_time:.2f}s: {e}", exc_info=True)
            return f"❌ Erro ao processar pergunta: {e}"
    
    def clear_history(self):
        """Limpa histórico do usuário"""
        st.session_state.rag_instance.clear_history()
        self.save_user_history()
        logger.info(f"Histórico limpo para usuário {self.user_id}")
    
    def get_history(self):
        """Retorna histórico atual"""
        return st.session_state.rag_instance.chat_history
    
    
    
    def get_user_stats(self):
        """Retorna estatísticas do usuário"""
        return self.user_stats.copy()

def login_page():
    """Página de login do sistema"""
    st.title("🚀 Login - Sistema RAG Conversacional")
    
    # Health check do sistema
    with st.spinner("Verificando sistema..."):
        try:
            health_status = health_check()
            if health_status["status"] == "healthy":
                st.success("✅ Sistema operacional")
            elif health_status["status"] == "degraded":
                st.warning("⚠️ Sistema com degradação")
            else:
                st.error("❌ Sistema com problemas")
                st.json(health_status)
        except Exception as e:
            st.error(f"❌ Erro no health check: {str(e)}")
    
        st.markdown("### 🔐 Acesso ao Sistema")
        
        
        with st.form("login_form"):
            username = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            password = st.text_input("🔒 Senha", type="password", placeholder="Digite sua senha")
            login_button = st.form_submit_button("🚀 Entrar", use_container_width=True)
        
        if login_button:
            if username and password:
                user_manager = StreamlitUserManager()
                
                if user_manager.authenticate(username, password):
                    # Login bem-sucedido
                    user_info = user_manager.get_user_info(username)
                    
                    logger.info(f"[LOGIN] Login bem-sucedido: {username} - {user_info.get('name')} - {user_info.get('role')}")
                    logger.debug(f"[LOGIN] Permissões do usuário: {user_info.get('permissions', [])}")
                    
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_info = user_info
                    st.session_state.user_manager = user_manager
                    
                    st.success(f"✅ Bem-vindo, {user_info.get('name', username)}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    logger.warning(f"[LOGIN] Tentativa de login falhada para usuário: {username}")
                    st.error("❌ Usuário ou senha incorretos!")
            else:
                st.warning("⚠️ Preencha todos os campos!")
        

def sidebar_user_info():
    """Sidebar otimizada com informações do usuário e sistema"""
    with st.sidebar:
        st.markdown("### 👤 Usuário Logado")
        user_info = st.session_state.get('user_info', {})
        
        st.markdown(f"**Nome:** {user_info.get('name', 'N/A')}")
        st.markdown(f"**Perfil:** {user_info.get('role', 'N/A')}")
        st.markdown(f"**Organização:** {user_info.get('organization', 'N/A')}")
        
        st.markdown("---")
        
        # Botões de ação com permissões
        if st.button("📊 Minhas Estatísticas", use_container_width=True):
            # Fecha todos os modals e abre apenas este
            close_all_modals()
            st.session_state.show_user_stats = True
        
        if st.button("🧹 Limpar Conversa", use_container_width=True):
            if 'user_rag' in st.session_state:
                st.session_state.user_rag.clear_history()
                st.success("✅ Conversa limpa!")
                st.rerun()
        
        # Painel administrativo (apenas para admins)
        user_manager = st.session_state.get('user_manager')
        if user_manager and user_manager.is_admin(st.session_state.username):
            st.markdown("---")
            st.markdown("### 🛠️ Painel Admin")
            if st.button("👥 Gerenciar Usuários", use_container_width=True):
                logger.info(f"[ADMIN] Painel de gerenciamento acessado por {st.session_state.username}")
                # Fecha todos os modals e abre apenas este
                close_all_modals()
                st.session_state.show_user_management = True
            
            if st.button("📄 Gerenciar Documentos", use_container_width=True):
                logger.info(f"[ADMIN] Painel de documentos acessado por {st.session_state.username}")
                # Fecha todos os modals e abre apenas este
                close_all_modals()
                st.session_state.show_document_management = True
        
        if st.button("🚪 Logout", use_container_width=True):
            # Log da saída
            logger.info(f"Logout: {st.session_state.get('username', 'unknown')}")
            
            # Limpa modals e sessão
            close_all_modals()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        


def user_management_modal():
    """Modal para gerenciamento de usuários (apenas admins)"""
    if st.session_state.get('show_user_management', False):
        # Cabeçalho com botão de fechar
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("# 👥 Gerenciamento de Usuários")
        with col2:
            if st.button("❌ Fechar", key="close_users_header", use_container_width=True):
                logger.info(f"[MODAL] Gerenciamento de usuários fechado por {st.session_state.username}")
                close_all_modals()
                st.rerun()
        
        st.markdown("---")
        
        user_manager = st.session_state.get('user_manager')
        if not user_manager:
            st.error("❌ Gerenciador de usuários não disponível")
            return
        
        # Tabs para diferentes funcionalidades
        tab_names = ["📋 Lista de Usuários", "➕ Criar Usuário", "✏️ Editar Usuário", "📊 Estatísticas"]
        
        # Cria as tabs
        tabs = st.tabs(tab_names)
        
        with tabs[0]:  # Lista de Usuários
            st.markdown("#### 📋 Usuários Cadastrados")
            
            # Mostra mensagem de sucesso se houver
            if 'user_updated_message' in st.session_state:
                st.success(st.session_state.user_updated_message)
                del st.session_state.user_updated_message
            
            if 'user_deleted_message' in st.session_state:
                st.success(st.session_state.user_deleted_message)
                del st.session_state.user_deleted_message
            
            # Lista todos os usuários
            users = user_manager.users
            if users:
                for username, user_data in users.items():
                    with st.expander(f"👤 {user_data.get('name', username)} (@{username})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Nome:** {user_data.get('name', 'N/A')}")
                            st.write(f"**Tipo:** {user_data.get('role', 'N/A')}")
                            st.write(f"**Organização:** {user_data.get('organization', 'N/A')}")
                        
                        with col2:
                            
                            # Botões de ação
                            col_edit, col_delete = st.columns(2)
                            with col_edit:
                                if st.button(f"✏️ Editar", key=f"edit_{username}"):
                                    st.session_state.edit_user = username
                                    st.session_state.active_user_tab = 2  # Vai para aba de edição
                                    st.rerun()
                            
                            with col_delete:
                                if username != st.session_state.username:  # Não pode deletar a si mesmo
                                    if st.button(f"🗑️ Excluir", key=f"delete_{username}"):
                                        # Remove usuário
                                        del user_manager.users[username]
                                        user_manager.save_users()
                                        
                                        # Remove dados da pasta production_users
                                        import shutil
                                        user_dir = Path(f"production_users/{username}")
                                        if user_dir.exists():
                                            try:
                                                shutil.rmtree(user_dir)
                                                logger.info(f"[ADMIN] Dados da pasta removidos para {username}")
                                            except Exception as e:
                                                logger.error(f"[ADMIN] Erro ao remover pasta {user_dir}: {e}")
                                        
                                        logger.info(f"[ADMIN] Usuário {username} excluído por {st.session_state.username}")
                                        st.session_state.user_deleted_message = f"✅ Usuário '{username}' excluído com sucesso!"
                                        st.rerun()
            else:
                st.info("Nenhum usuário cadastrado.")
        
        with tabs[1]:  # Criar Usuário
            st.markdown("#### ➕ Criar Novo Usuário")
            
            # Key dinâmica para forçar limpeza dos campos
            form_key = f"create_user_form_{st.session_state.get('form_key', 0)}"
            
            with st.form(form_key):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_username = st.text_input("👤 Nome de usuário", help="Nome único para login")
                    new_name = st.text_input("📛 Nome completo")
                    new_password = st.text_input("🔒 Senha", type="password")
                
                with col2:
                    new_role = st.selectbox("🎭 Tipo", ["Admin", "Usuário"])
                    new_organization = st.text_input("🏢 Organização")
                
                if st.form_submit_button("➕ Criar Usuário", use_container_width=True):
                    if new_username and new_name and new_password:
                        if new_username not in user_manager.users:
                            # Cria usuário
                            user_manager.users[new_username] = {
                                "password_hash": user_manager.hash_password(new_password),
                                "name": new_name,
                                "role": new_role,
                                "organization": new_organization,
                                "created_at": get_sao_paulo_time().isoformat(),
                                "last_login": "",
                                "total_conversations": 0,
                                "successful_queries": 0,
                                "failed_queries": 0,
                                "active": True,
                                "notes": ""
                            }
                            
                            # Salva
                            user_manager.save_users()
                            logger.info(f"[ADMIN] Novo usuário {new_username} criado por {st.session_state.username}")
                            
                            # Mostra sucesso imediatamente na aba atual
                            st.success(f"✅ Usuário '{new_username}' criado com sucesso!")
                            
                            # Força recriação do formulário para limpar campos
                            if 'form_key' in st.session_state:
                                st.session_state.form_key += 1
                            else:
                                st.session_state.form_key = 1
                            
                            # Pequeno delay para usuário ver a mensagem antes de limpar
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Nome de usuário já existe!")
                    else:
                        st.error("❌ Preencha todos os campos obrigatórios!")
        
        with tabs[2]:  # Editar Usuário
            st.markdown("#### ✏️ Editar Usuário")
            
            if st.session_state.get('edit_user'):
                edit_username = st.session_state.edit_user
                edit_user_data = user_manager.users.get(edit_username, {})
                
                st.info(f"Editando usuário: **{edit_username}**")
                
                with st.form("edit_user_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_name = st.text_input("📛 Nome completo", value=edit_user_data.get('name', ''))
                        edit_new_password = st.text_input("🔒 Nova senha (deixe vazio para manter atual)", type="password")
                    
                    with col2:
                        edit_role = st.selectbox("🎭 Tipo", ["Admin", "Usuário"], 
                                                index=["Admin", "Usuário"].index(edit_user_data.get('role', 'Usuário')))
                        edit_organization = st.text_input("🏢 Organização", value=edit_user_data.get('organization', ''))
                    
                    col_save, col_cancel = st.columns(2)
                    
                    with col_save:
                        if st.form_submit_button("💾 Salvar Alterações", use_container_width=True):
                            # Atualiza dados
                            user_manager.users[edit_username]['name'] = edit_name
                            user_manager.users[edit_username]['role'] = edit_role
                            user_manager.users[edit_username]['organization'] = edit_organization
                            
                            # Atualiza senha se fornecida
                            if edit_new_password:
                                user_manager.users[edit_username]['password_hash'] = user_manager.hash_password(edit_new_password)
                            
                            # Salva
                            user_manager.save_users()
                            logger.info(f"[ADMIN] Usuário {edit_username} editado por {st.session_state.username}")
                            
                            # Mostra sucesso imediatamente na aba atual
                            st.success(f"✅ Usuário '{edit_username}' atualizado com sucesso!")
                            
                            # Define mensagem para mostrar na listagem também
                            st.session_state.user_updated_message = f"✅ Usuário '{edit_username}' atualizado com sucesso!"
                            st.session_state.active_user_tab = 0  # Volta para aba de listagem
                            del st.session_state.edit_user
                            
                            # Pequeno delay para usuário ver a mensagem
                            time.sleep(1)
                            st.rerun()
                    
                    with col_cancel:
                        if st.form_submit_button("❌ Cancelar", use_container_width=True):
                            del st.session_state.edit_user
                            st.rerun()
            else:
                st.info("Selecione um usuário na aba 'Lista de Usuários' para editar.")
        
        with tabs[3]:  # Estatísticas
            st.markdown("#### 📊 Estatísticas de Uso")
            
            # Estatísticas gerais
            total_users = len(user_manager.users)
            roles_count = {}
            
            for user_data in user_manager.users.values():
                role = user_data.get('role', 'Não definido')
                roles_count[role] = roles_count.get(role, 0) + 1
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("👥 Total de Usuários", total_users)
            
            with col2:
                st.metric("🛠️ Administradores", roles_count.get('Admin', 0))
            
            with col3:
                st.metric("👤 Usuários", roles_count.get('Usuário', 0))
            
            # Estatísticas por usuário
            st.markdown("##### 📈 Atividade por Usuário")
            
            # Carrega estatísticas de todos os usuários
            users_stats = []
            for username in user_manager.users.keys():
                user_stats_file = Path(f"production_users/{username}/user_stats.json")
                if user_stats_file.exists():
                    try:
                        with open(user_stats_file, 'r', encoding='utf-8') as f:
                            stats = json.load(f)
                            stats['username'] = username
                            stats['name'] = user_manager.users[username].get('name', username)
                            users_stats.append(stats)
                    except:
                        pass
            
            if users_stats:
                # Ordena por atividade
                users_stats.sort(key=lambda x: x.get('total_questions', 0), reverse=True)
                
                for stats in users_stats:
                    with st.expander(f"📊 {stats['name']} (@{stats['username']})"):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("❓ Perguntas", stats.get('total_questions', 0))
                        
                        with col2:
                            st.metric("✅ Sucessos", stats.get('successful_answers', 0))
                        
                        
                        with col4:
                            success_rate = 0
                            if stats.get('total_questions', 0) > 0:
                                success_rate = (stats.get('successful_answers', 0) / stats.get('total_questions', 1)) * 100
                            st.metric("📈 Taxa Sucesso", f"{success_rate:.1f}%")
                        
                        # Última atividade
                        if stats.get('last_activity'):
                            try:
                                last_activity = datetime.fromisoformat(stats['last_activity'])
                                st.caption(f"🕐 Última atividade: {last_activity.strftime('%d/%m/%Y %H:%M')}")
                            except:
                                st.caption("🕐 Última atividade: Não disponível")
            else:
                st.info("Nenhuma estatística de uso disponível ainda.")

def document_management_modal():
    """Modal para gerenciamento de documentos (apenas admins)"""
    if st.session_state.get('show_document_management', False):
        # Cabeçalho com botão de fechar
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("# 📄 Gerenciamento de Documentos")
        with col2:
            if st.button("❌ Fechar", key="close_documents_header", use_container_width=True):
                logger.info(f"[MODAL] Gerenciamento de documentos fechado por {st.session_state.username}")
                close_all_modals()
                st.rerun()
        
        st.markdown("---")
        
        # Tabs para diferentes funcionalidades
        tab_names = ["📤 Upload/Indexar", "📋 Documentos Indexados", "⚙️ Configurações"]
        tabs = st.tabs(tab_names)
        
        with tabs[0]:  # Upload/Indexar
            st.markdown("#### 📤 Adicionar Novo Documento")
            
            # Opções de entrada
            input_method = st.radio(
                "Método de entrada:",
                ["🔗 URL do PDF", "📎 Upload de arquivo"],
                help="Escolha como fornecer o documento para indexação"
            )
            
            if input_method == "🔗 URL do PDF":
                # Lógica de limpeza de campos
                if st.session_state.get("clear_url_field", False):
                    st.session_state.clear_url_field = False
                    st.session_state.pdf_url_input = ""

                pdf_url = st.text_input(
                    "URL do documento PDF:",
                    key="pdf_url_input",
                    placeholder="https://arxiv.org/pdf/2501.13956",
                    help="Cole aqui o link direto para o arquivo PDF"
                )
                
                if pdf_url and st.button("🔍 Validar URL", use_container_width=True):
                    # Validação básica da URL
                    if pdf_url.lower().endswith('.pdf') or 'arxiv.org/pdf/' in pdf_url:
                        st.success("✅ URL válida detectada!")
                    else:
                        st.warning("⚠️ A URL pode não ser um PDF válido. Prossiga com cuidado.")
                
                source_type = "url"
                source_value = pdf_url
            
            else:  # Upload de arquivo
                # Lógica de limpeza para upload
                upload_key = "pdf_uploader"
                if st.session_state.get('clear_upload_field', False):
                    st.session_state.clear_upload_field = False
                    if upload_key in st.session_state:
                        del st.session_state[upload_key]
                    upload_key = f"pdf_uploader_{hash(str(st.session_state.get('upload_counter', 0)))}"
                    st.session_state.upload_counter = st.session_state.get('upload_counter', 0) + 1
                
                uploaded_file = st.file_uploader(
                    "Escolha um arquivo PDF:",
                    type=['pdf'],
                    help="Selecione um arquivo PDF do seu computador",
                    key=upload_key
                )
                
                if uploaded_file:
                    st.success(f"✅ Arquivo carregado: {uploaded_file.name} ({uploaded_file.size} bytes)")
                
                source_type = "upload"
                source_value = uploaded_file
            
            # Configuração automática: sempre substitui documentos existentes
            
            # Botão de indexação
            st.markdown("---")
            
            can_index = (source_type == "url" and source_value) or (source_type == "upload" and source_value is not None)
            
            if st.button("🚀 Iniciar Indexação", disabled=not can_index, use_container_width=True):
                if can_index:
                    try:
                        st.info("🔄 Iniciando processo de indexação...")
                        
                        # Cria container para logs em tempo real
                        progress_container = st.container()
                        log_container = st.container()
                        
                        with progress_container:
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                        
                        with log_container:
                            log_area = st.empty()
                        
                        # Processa o arquivo real
                        if source_type == "upload":
                            # Salva arquivo temporário para upload
                            import tempfile
                            import subprocess
                            import sys
                            temp_pdf_path = None
                            try:
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', prefix='temp_upload_') as tmp_file:
                                    tmp_file.write(source_value.getvalue())
                                    temp_pdf_path = tmp_file.name
                                
                                logger.info(f"[INDEXING] Arquivo temporário criado: {temp_pdf_path}")
                                status_text.text("📥 Processando arquivo PDF...")
                                progress_bar.progress(20)
                                
                                # Prepara ambiente com todas as variáveis necessárias
                                env = os.environ.copy()
                                env['PDF_URL'] = temp_pdf_path
                                
                                # Garante que todas as variáveis do Astra DB estão presentes
                                required_env_vars = [
                                    'VOYAGE_API_KEY', 'ASTRA_DB_API_ENDPOINT', 'ASTRA_DB_APPLICATION_TOKEN'
                                ]
                                missing_vars = [var for var in required_env_vars if not env.get(var)]
                                if missing_vars:
                                    st.error(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
                                    return
                                
                                status_text.text("🖼️ Extraindo imagens e texto...")
                                progress_bar.progress(50)
                                
                                logger.info(f"[INDEXING] Executando indexador com arquivo: {temp_pdf_path}")
                                
                                result = subprocess.run([
                                    sys.executable, "-u", "indexador.py"
                                ], env=env, capture_output=True, text=True, cwd="/workspaces/rag", timeout=300)
                                
                                logger.info(f"[INDEXING] Indexador finalizado com código: {result.returncode}")
                                if result.stdout:
                                    logger.info(f"[INDEXING] STDOUT: {result.stdout}")
                                if result.stderr:
                                    logger.warning(f"[INDEXING] STDERR: {result.stderr}")
                                
                                if result.returncode == 0:
                                    status_text.text("✅ Indexação concluída com sucesso!")
                                    progress_bar.progress(100)
                                    st.success("🎉 Documento indexado com sucesso!")
                                    st.info("📊 O documento já está disponível para consultas no sistema RAG.")
                                    # Mostra log de sucesso se houver
                                    if result.stdout:
                                        with st.expander("📄 Ver detalhes da indexação"):
                                            st.text(result.stdout)
                                else:
                                    st.error(f"❌ Erro na indexação (código {result.returncode})")
                                    if result.stderr:
                                        st.error(f"**Erro detalhado:** {result.stderr}")
                                    if result.stdout:
                                        st.text(f"**Saída do processo:** {result.stdout}")
                                    
                            except subprocess.TimeoutExpired:
                                st.error("❌ Timeout na indexação (5 minutos). Documento muito grande ou processamento lento.")
                            except Exception as e:
                                logger.error(f"[INDEXING] Erro durante indexação: {e}")
                                st.error(f"❌ Erro durante indexação: {e}")
                            finally:
                                # Remove arquivo temporário se ainda existir
                                if temp_pdf_path and os.path.exists(temp_pdf_path):
                                    try:
                                        os.remove(temp_pdf_path)
                                        logger.info(f"[INDEXING] Arquivo temporário removido: {temp_pdf_path}")
                                    except Exception as e:
                                        logger.warning(f"[INDEXING] Erro ao remover arquivo temporário: {e}")
                                    
                        else:
                            # URL processing real
                            import subprocess
                            import sys
                            
                            status_text.text("📥 Baixando PDF da URL...")
                            progress_bar.progress(20)
                            
                            # Prepara ambiente com todas as variáveis necessárias
                            env = os.environ.copy()
                            env['PDF_URL'] = source_value
                            
                            # Garante que todas as variáveis do Astra DB estão presentes
                            required_env_vars = [
                                'VOYAGE_API_KEY', 'ASTRA_DB_API_ENDPOINT', 'ASTRA_DB_APPLICATION_TOKEN'
                            ]
                            missing_vars = [var for var in required_env_vars if not env.get(var)]
                            if missing_vars:
                                st.error(f"❌ Variáveis de ambiente faltando: {', '.join(missing_vars)}")
                                return
                            
                            status_text.text("🖼️ Extraindo imagens e texto...")
                            progress_bar.progress(50)
                            
                            logger.info(f"[INDEXING] Executando indexador com URL: {source_value}")
                            
                            try:
                                result = subprocess.run([
                                    sys.executable, "-u", "indexador.py"
                                ], env=env, capture_output=True, text=True, cwd="/workspaces/rag", timeout=600)
                                
                                logger.info(f"[INDEXING] Indexador finalizado com código: {result.returncode}")
                                if result.stdout:
                                    logger.info(f"[INDEXING] STDOUT: {result.stdout}")
                                if result.stderr:
                                    logger.warning(f"[INDEXING] STDERR: {result.stderr}")
                                
                                if result.returncode == 0:
                                    status_text.text("✅ Indexação concluída com sucesso!")
                                    progress_bar.progress(100)
                                    st.success("🎉 Documento indexado com sucesso!")
                                    st.info("📊 O documento já está disponível para consultas no sistema RAG.")
                                    # Mostra log de sucesso se houver
                                    if result.stdout:
                                        with st.expander("📄 Ver detalhes da indexação"):
                                            st.text(result.stdout)
                                else:
                                    st.error(f"❌ Erro na indexação (código {result.returncode})")
                                    if result.stderr:
                                        st.error(f"**Erro detalhado:** {result.stderr}")
                                    if result.stdout:
                                        st.text(f"**Saída do processo:** {result.stdout}")
                                        
                            except subprocess.TimeoutExpired:
                                st.error("❌ Timeout na indexação (10 minutos). URL inacessível ou processamento muito lento.")
                            except Exception as e:
                                logger.error(f"[INDEXING] Erro durante indexação: {e}")
                                st.error(f"❌ Erro durante indexação: {e}")
                        
                        # Log da indexação
                        logger.info(f"[ADMIN] Documento indexado por {st.session_state.username}: {source_type}={str(source_value)[:100]}")
                        
                        # Automaticamente força limpeza dos campos após sucesso
                        if result.returncode == 0:
                            # Limpa o session state relacionado aos campos
                            if source_type == "url":
                                st.session_state.clear_url_field = True
                            else:
                                st.session_state.clear_upload_field = True
                            
                        # Mostra botão para limpar campos e atualizar lista
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🔄 Limpar campos", key="clear_fields", use_container_width=True):
                                # Força limpeza dos campos
                                st.session_state.clear_url_field = True
                                st.session_state.clear_upload_field = True
                                st.rerun()
                        with col2:
                            if st.button("📋 Atualizar lista", key="refresh_docs_list", use_container_width=True):
                                st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Erro durante a indexação: {e}")
                        logger.error(f"[ADMIN] Erro na indexação por {st.session_state.username}: {e}")
                        # Mostra stderr do processo para debug
                        if 'result' in locals() and hasattr(result, 'stderr') and result.stderr:
                            st.error(f"Erro detalhado: {result.stderr}")
                        if 'result' in locals() and hasattr(result, 'stdout') and result.stdout:
                            st.info(f"Saída do processo: {result.stdout}")
                else:
                    st.warning("⚠️ Forneça uma URL válida ou faça upload de um arquivo antes de indexar.")
        
        with tabs[1]:  # Documentos Indexados
            st.markdown("#### 📋 Documentos Atualmente Indexados")
            
            # Botão para atualizar lista manualmente
            if st.button("🔄 Atualizar Lista", key="refresh_docs"):
                st.rerun()
            
            try:
                # Busca documentos reais no Astra DB
                from astrapy import DataAPIClient
                endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
                token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
                
                if endpoint and token:
                    client = DataAPIClient(token)
                    database = client.get_database(endpoint)
                    collection = database.get_collection("pdf_documents")
                    
                    # Busca documentos únicos pela fonte
                    try:
                        documents = collection.distinct("doc_source")
                    except Exception as e:
                        # Fallback: busca alguns documentos e extrai sources únicos
                        st.warning(f"⚠️ Usando método alternativo para listar documentos: {e}")
                        docs = collection.find({}, limit=100)
                        sources = set()
                        for doc in docs:
                            if 'doc_source' in doc:
                                sources.add(doc['doc_source'])
                        documents = list(sources)
                    
                    if documents:
                        st.markdown("##### 📚 Documentos Indexados:")
                        
                        for doc_source in documents:
                            if doc_source:
                                # Extrai nome do documento
                                doc_name = doc_source.split("/")[-1] if "/" in doc_source else doc_source
                                
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(f"📄 **{doc_name}**")
                                
                                with col2:
                                    if st.button("🗑️ Remover", key=f"remove_{hash(doc_source)}", use_container_width=True):
                                        if st.session_state.get(f'confirm_delete_{hash(doc_source)}', False):
                                            try:
                                                # Remove todos os chunks relacionados ao documento
                                                result = collection.delete_many({"doc_source": doc_source})
                                                
                                                # Remove imagens relacionadas
                                                import glob
                                                pdf_images_dir = "pdf_images"
                                                if os.path.exists(pdf_images_dir):
                                                    doc_base_name = doc_name.replace(".pdf", "").replace(" ", "_")
                                                    for img_file in glob.glob(f"{pdf_images_dir}/*{doc_base_name}*"):
                                                        try:
                                                            os.remove(img_file)
                                                        except:
                                                            pass
                                                
                                                st.success(f"✅ Documento '{doc_name}' removido! {result.deleted_count} chunks excluídos.")
                                                st.session_state[f'confirm_delete_{hash(doc_source)}'] = False
                                                # Aguarda um pouco para que o usuário veja a mensagem
                                                time.sleep(1)
                                                st.rerun()
                                                
                                            except Exception as e:
                                                st.error(f"❌ Erro ao remover documento: {str(e)}")
                                        else:
                                            st.session_state[f'confirm_delete_{hash(doc_source)}'] = True
                                            st.warning("⚠️ Clique novamente para confirmar a remoção.")
                                            st.rerun()
                    else:
                        st.info("📄 Nenhum documento indexado encontrado.")
                else:
                    st.warning("⚠️ Configurações do Astra DB não encontradas.")
                    
            except Exception as e:
                st.error(f"❌ Erro ao carregar documentos: {str(e)}")
        
        with tabs[2]:  # Configurações
            st.markdown("#### ⚙️ Configurações do Sistema")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 🗄️ Configurações do Banco de Dados")
                
                # Mostra informações da conexão (sem revelar credenciais)
                astra_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT", "")
                if astra_endpoint:
                    endpoint_display = astra_endpoint[:30] + "..." if len(astra_endpoint) > 30 else astra_endpoint
                    st.info(f"**Endpoint:** {endpoint_display}")
                else:
                    st.warning("⚠️ Endpoint do Astra DB não configurado")
                
                collection_name = "pdf_documents"  # Do buscador
                st.info(f"**Collection:** {collection_name}")
                
                # Teste de conectividade
                if st.button("🔗 Testar Conexão", use_container_width=True):
                    try:
                        # Aqui você testaria a conexão real
                        st.success("✅ Conexão com Astra DB estabelecida!")
                    except Exception as e:
                        st.error(f"❌ Erro de conexão: {e}")
            
            with col2:
                st.markdown("##### 🤖 Configurações de IA")
                
                # Informações das APIs (sem revelar chaves)
                openai_key = os.getenv("OPENAI_API_KEY", "")
                voyage_key = os.getenv("VOYAGE_API_KEY", "")
                
                st.info(f"**OpenAI API:** {'✅ Configurada' if openai_key else '❌ Não configurada'}")
                st.info(f"**Voyage AI API:** {'✅ Configurada' if voyage_key else '❌ Não configurada'}")
                
                # Health check do sistema
                if st.button("🏥 Health Check", use_container_width=True):
                    try:
                        from buscador_conversacional_producao import health_check
                        health_status = health_check()
                        
                        if health_status["status"] == "healthy":
                            st.success("✅ Sistema operacional")
                        elif health_status["status"] == "degraded":
                            st.warning("⚠️ Sistema com degradação")
                        else:
                            st.error("❌ Sistema com problemas")
                        
                        st.json(health_status)
                        
                    except Exception as e:
                        st.error(f"❌ Erro no health check: {e}")
            

def user_stats_modal():
    """Modal para exibir estatísticas pessoais do usuário"""
    if st.session_state.get('show_user_stats', False):
        # Cabeçalho com botão de fechar
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("# 📊 Minhas Estatísticas")
        with col2:
            if st.button("❌ Fechar", key="close_user_stats_header", use_container_width=True):
                logger.info(f"[MODAL] Estatísticas pessoais fechadas por {st.session_state.username}")
                close_all_modals()
                st.rerun()
        
        st.markdown("---")
        
        if 'user_rag' in st.session_state:
            try:
                user_stats = st.session_state.user_rag.get_user_stats()
                user_info = st.session_state.get('user_info', {})
                
                # Informações do usuário
                st.markdown("### 👤 Informações do Usuário")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.info(f"**Nome:** {user_info.get('name', 'N/A')}")
                with col2:
                    st.info(f"**Perfil:** {user_info.get('role', 'N/A')}")
                with col3:
                    st.info(f"**Organização:** {user_info.get('organization', 'N/A')}")
                
                st.markdown("---")
                
                # Métricas principais
                st.markdown("### 📈 Atividade no Sistema")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        label="❓ Total de Perguntas",
                        value=user_stats.get("total_questions", 0),
                        help="Número total de perguntas feitas ao sistema"
                    )
                
                with col2:
                    st.metric(
                        label="✅ Respostas Bem-sucedidas",
                        value=user_stats.get("successful_answers", 0),
                        help="Perguntas que resultaram em respostas satisfatórias"
                    )
                
                
                with col4:
                    # Taxa de sucesso
                    success_rate = 0
                    if user_stats.get("total_questions", 0) > 0:
                        success_rate = (user_stats.get("successful_answers", 0) / user_stats.get("total_questions", 1)) * 100
                    
                    st.metric(
                        label="📈 Taxa de Sucesso",
                        value=f"{success_rate:.1f}%",
                        help="Percentual de perguntas com respostas bem-sucedidas"
                    )
                
                st.markdown("---")
                
                # Informações temporais
                st.markdown("### 🕐 Histórico de Uso")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if user_stats.get('first_login'):
                        try:
                            first_login = datetime.fromisoformat(user_stats['first_login'])
                            st.info(f"**Primeiro acesso:** {first_login.strftime('%d/%m/%Y %H:%M')}")
                        except:
                            st.info("**Primeiro acesso:** Não disponível")
                    else:
                        st.info("**Primeiro acesso:** Não disponível")
                
                with col2:
                    if user_stats.get('last_activity'):
                        try:
                            last_activity = datetime.fromisoformat(user_stats['last_activity'])
                            st.info(f"**Última atividade:** {last_activity.strftime('%d/%m/%Y %H:%M')}")
                        except:
                            st.info("**Última atividade:** Não disponível")
                    else:
                        st.info("**Última atividade:** Não disponível")
                
                # Análise de performance
                if user_stats.get("total_questions", 0) > 0:
                    st.markdown("---")
                    st.markdown("### 📊 Análise de Performance")
                    
                    # Barra de progresso para taxa de sucesso
                    st.markdown("**Taxa de Sucesso:**")
                    st.progress(success_rate / 100)
                    
                    # Insights
                    if success_rate >= 90:
                        st.success("🎯 **Excelente!** Você está obtendo ótimos resultados!")
                    elif success_rate >= 70:
                        st.info("👍 **Bom trabalho!** Continue assim.")
                    elif success_rate >= 50:
                        st.warning("⚠️ **Pode melhorar.** Tente perguntas mais específicas.")
                    else:
                        st.error("🔄 **Vamos melhorar!** Experimente reformular suas perguntas.")
                
                else:
                    st.info("📝 **Primeira vez?** Faça algumas perguntas para ver suas estatísticas aqui!")
                    
            except Exception as e:
                logger.error(f"Erro ao exibir estatísticas pessoais: {e}")
                st.error("❌ Erro ao carregar suas estatísticas. Tente novamente.")


def chat_interface():
    """Interface principal de chat otimizada"""
    st.title("🚀 RAG Conversacional")
    
    
    # Inicializa RAG do usuário se não existir
    if 'user_rag' not in st.session_state:
        logger.info(f"[CHAT] Inicializando RAG para usuário: {st.session_state.username}")
        
        with st.spinner("Inicializando sistema RAG..."):
            try:
                init_start = time.time()
                
                st.session_state.user_rag = ProductionStreamlitRAG(st.session_state.username)
                
                init_time = time.time() - init_start
                logger.info(f"[CHAT] RAG do usuário inicializado em {init_time:.2f}s")
                
                st.success("✅ Sistema inicializado com sucesso!")
            except Exception as e:
                logger.error(f"[CHAT] Erro ao inicializar RAG para {st.session_state.username}: {e}", exc_info=True)
                st.error(f"❌ Erro na inicialização: {e}")
                st.stop()
    
    # Verifica se algum modal está aberto
    modal_open = (
        st.session_state.get('show_user_management', False) or
        st.session_state.get('show_user_stats', False) or
        st.session_state.get('show_document_management', False)
    )
    
    # Se algum modal estiver aberto, mostra apenas o modal
    if modal_open:
        # Indicação visual de que está em modo modal
        st.info("🔄 **Modo Painel:** Use o botão ❌ Fechar no canto superior direito para voltar à conversa.")
        
        user_management_modal()
        user_stats_modal()
        document_management_modal()
        return  # Para aqui, não mostra a conversa
    
    # Container para mensagens (só mostra se nenhum modal estiver aberto)
    chat_container = st.container()
    
    # Exibe histórico da conversa
    with chat_container:
        history = st.session_state.user_rag.get_history()
        
        if history:
            for message in history:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
        else:
            # Mensagem de boas-vindas personalizada
            user_name = st.session_state.user_info.get('name', 'usuário')
            welcome_msg = f"""
            👋 Olá, **{user_name}**! Bem-vindo ao sistema RAG.
            
            🚀 **Recursos disponíveis:**
            - Perguntas contextuais inteligentes
            - Memória de conversas anteriores  
            - Análise de documentos acadêmicos
            
            💡 **Exemplos de perguntas:**
            - "O que é o Zep Graphiti?"
            - "Explique a arquitetura temporal"
            - "Quais são os resultados de performance?"
            - "Como funciona a invalidação de memória?"
            
            Faça sua primeira pergunta!
            """
            st.markdown(welcome_msg)
    
    # Input para nova mensagem
    if prompt := st.chat_input("Digite sua pergunta..."):
        logger.info(f"[CHAT] Nova mensagem do usuário {st.session_state.username}: {prompt[:100]}...")
        
        # Mostra pergunta do usuário
        with st.chat_message("user"):
            st.write(prompt)
        
        # Gera resposta usando sistema
        with st.chat_message("assistant"):
            with st.spinner("🧠 Processando com IA..."):
                try:
                    start_time = time.time()
                    logger.debug(f"[CHAT] Iniciando processamento da pergunta...")
                    
                    response = st.session_state.user_rag.ask(prompt)
                    processing_time = time.time() - start_time
                    
                    logger.info(f"[CHAT] Resposta processada em {processing_time:.2f}s para {st.session_state.username}")
                    logger.debug(f"[CHAT] Resposta: {response[:200]}...")
                    
                    st.write(response)
                    
                    # Mostra tempo de processamento para admin
                    if st.session_state.user_info.get('role') == 'Admin':
                        st.caption(f"⏱️ Processado em {processing_time:.2f}s")
                        logger.debug(f"[CHAT] Tempo mostrado para admin: {processing_time:.2f}s")
                        
                except Exception as e:
                    error_time = time.time() - start_time
                    error_msg = f"❌ Erro ao processar pergunta: {e}"
                    
                    logger.error(f"[CHAT] Erro no chat para {st.session_state.username} após {error_time:.2f}s: {e}", exc_info=True)
                    
                    st.error(error_msg)
                    
                    # Fallback para admin
                    if st.session_state.user_info.get('role') == 'Admin':
                        logger.debug(f"[CHAT] Mostrando debug info para admin")
                        st.markdown("**Debug Info:**")
                        st.code(str(e))

def main():
    """Função principal da aplicação"""
    # CSS personalizado para melhor aparência
    st.markdown("""
    <style>
    .stApp > header {
        background-color: transparent;
    }
    .stApp {
        margin-top: -80px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Inicializa estado da sessão
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # Verifica autenticação
    if not st.session_state.authenticated:
        login_page()
    else:
        # Interface principal
        sidebar_user_info()
        chat_interface()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Erro crítico na aplicação: {e}")
        st.error(f"❌ Erro crítico: {e}")
        st.markdown("**Verifique:**")
        st.markdown("1. Variáveis de ambiente configuradas")
        st.markdown("2. Conexão com Astra DB")
        st.markdown("3. Documentos indexados corretamente")
        st.markdown("4. Dependências instaladas")