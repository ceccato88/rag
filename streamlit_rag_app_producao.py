# streamlit_rag_app_producao.py

import streamlit as st
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
import time
from typing import Dict, Any, Optional

# Importa a versão de produção
from buscador_conversacional_producao import ProductionConversationalRAG, health_check

# Configuração da página
st.set_page_config(
    page_title="RAG Conversacional - Produção",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração de logging para Streamlit
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - Streamlit - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class StreamlitUserManager:
    """Gerenciador de usuários para Streamlit (versão produção)"""
    
    def __init__(self, users_file="production_users.json"):
        self.users_file = Path(users_file)
        self.users = self.load_users()
        self._create_default_users()
    
    def _create_default_users(self):
        """Cria usuários padrão se não existirem"""
        default_users = {
            "admin": {
                "password_hash": self.hash_password("admin123"),
                "name": "Administrador",
                "role": "Admin",
                "organization": "Sistema",
                "permissions": ["extract", "stats", "clear_all"]
            },
            "pesquisador": {
                "password_hash": self.hash_password("pesquisa123"),
                "name": "Dr. Pesquisador",
                "role": "Pesquisador",
                "organization": "Universidade",
                "permissions": ["extract", "stats"]
            },
            "demo": {
                "password_hash": self.hash_password("demo123"),
                "name": "Usuário Demo",
                "role": "Demonstração",
                "organization": "Demo",
                "permissions": []
            }
        }
        
        # Adiciona usuários que não existem
        updated = False
        for username, user_data in default_users.items():
            if username not in self.users:
                self.users[username] = user_data
                updated = True
        
        if updated:
            self.save_users()
    
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
    
    def has_permission(self, username: str, permission: str) -> bool:
        """Verifica se usuário tem permissão específica"""
        user = self.users.get(username, {})
        return permission in user.get("permissions", [])

class ProductionStreamlitRAG:
    """RAG de produção adaptado para Streamlit com cache e otimizações"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.user_dir = Path(f"production_users/{user_id}")
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.user_dir / "chat_history.json"
        self.stats_file = self.user_dir / "user_stats.json"
        
        # Inicializa RAG de produção (com cache global no Streamlit)
        self._initialize_rag()
        
        # Carrega histórico e estatísticas do usuário
        self.load_user_data()
    
    @st.cache_resource
    def _get_global_rag_instance():
        """Instância global do RAG (cache do Streamlit)"""
        try:
            logger.info("Inicializando instância global RAG de produção...")
            return ProductionConversationalRAG()
        except Exception as e:
            logger.error(f"Erro ao inicializar RAG: {e}")
            st.error(f"❌ Erro na inicialização: {e}")
            return None
    
    def _initialize_rag(self):
        """Inicializa RAG usando cache global"""
        if "rag_instance" not in st.session_state:
            st.session_state.rag_instance = self._get_global_rag_instance()
        
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
            "extraction_count": 0,
            "first_login": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
    
    def _save_user_stats(self):
        """Salva estatísticas do usuário"""
        try:
            self.user_stats["last_activity"] = datetime.now().isoformat()
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar estatísticas: {e}")
    
    def save_user_history(self):
        """Salva histórico do usuário"""
        try:
            memory_data = {
                "user_id": self.user_id,
                "last_updated": datetime.now().isoformat(),
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
        """Faz pergunta usando RAG de produção e salva automaticamente"""
        try:
            self.user_stats["total_questions"] += 1
            
            # Usa o método ask da versão de produção
            response = st.session_state.rag_instance.ask(question)
            
            if "erro" not in response.lower() and "desculpe" not in response.lower():
                self.user_stats["successful_answers"] += 1
            
            self.save_user_history()
            return response
            
        except Exception as e:
            logger.error(f"Erro na pergunta do usuário {self.user_id}: {e}")
            return f"❌ Erro ao processar pergunta: {e}"
    
    def clear_history(self):
        """Limpa histórico do usuário"""
        st.session_state.rag_instance.clear_history()
        self.save_user_history()
        logger.info(f"Histórico limpo para usuário {self.user_id}")
    
    def get_history(self):
        """Retorna histórico atual"""
        return st.session_state.rag_instance.chat_history
    
    def extract_data(self, template: dict, document_filter: Optional[str] = None):
        """Extrai dados estruturados usando RAG de produção"""
        try:
            self.user_stats["extraction_count"] += 1
            self._save_user_stats()
            
            return st.session_state.rag_instance.extract_structured_data(template, document_filter)
        except Exception as e:
            logger.error(f"Erro na extração para usuário {self.user_id}: {e}")
            return {
                "status": "error",
                "message": f"Erro na extração: {e}"
            }
    
    def get_system_stats(self):
        """Obtém estatísticas do sistema"""
        try:
            return st.session_state.rag_instance.get_system_stats()
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {"error": str(e)}
    
    def get_user_stats(self):
        """Retorna estatísticas do usuário"""
        return self.user_stats.copy()

def login_page():
    """Página de login com informações da versão de produção"""
    st.title("🚀 Login - Sistema RAG Conversacional (Produção)")
    
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
            st.error(f"❌ Erro no health check: {e}")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Acesso ao Sistema")
        
        # Credentials de demonstração
        with st.expander("👀 Credenciais de Demonstração"):
            st.markdown("""
            **Usuários disponíveis:**
            - **admin** / admin123 (Administrador completo)
            - **pesquisador** / pesquisa123 (Pesquisador)
            - **demo** / demo123 (Demonstração básica)
            """)
        
        with st.form("login_form"):
            username = st.text_input("👤 Usuário", placeholder="Digite seu usuário")
            password = st.text_input("🔒 Senha", type="password", placeholder="Digite sua senha")
            login_button = st.form_submit_button("🚀 Entrar", use_container_width=True)
        
        if login_button:
            if username and password:
                user_manager = StreamlitUserManager()
                
                if user_manager.authenticate(username, password):
                    # Login bem-sucedido
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_info = user_manager.get_user_info(username)
                    st.session_state.user_manager = user_manager
                    
                    logger.info(f"Login bem-sucedido: {username}")
                    st.success(f"✅ Bem-vindo, {st.session_state.user_info.get('name', username)}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos!")
                    logger.warning(f"Tentativa de login falhada: {username}")
            else:
                st.warning("⚠️ Preencha todos os campos!")
        
        # Informações do sistema de produção
        st.markdown("---")
        st.markdown("### 📋 Sistema de Produção")
        st.info("""
        **🚀 Recursos de Produção Ativos:**
        - 🧠 Query transformer inteligente com cache
        - 🔄 Fallbacks automáticos robustos
        - 📊 Logging estruturado e monitoramento
        - ⚡ Otimizações de performance
        - 🛡️ Validação de ambiente e segurança
        - 💾 Memória persistente por usuário
        - 📈 Estatísticas detalhadas de uso
        """)

def sidebar_user_info():
    """Sidebar otimizada com informações do usuário e sistema"""
    with st.sidebar:
        st.markdown("### 👤 Usuário Logado")
        user_info = st.session_state.get('user_info', {})
        
        st.markdown(f"**Nome:** {user_info.get('name', 'N/A')}")
        st.markdown(f"**Perfil:** {user_info.get('role', 'N/A')}")
        st.markdown(f"**Organização:** {user_info.get('organization', 'N/A')}")
        
        # Estatísticas do usuário
        if 'user_rag' in st.session_state:
            try:
                user_stats = st.session_state.user_rag.get_user_stats()
                st.markdown("### 📊 Suas Estatísticas")
                st.metric("Perguntas", user_stats.get("total_questions", 0))
                st.metric("Respostas bem-sucedidas", user_stats.get("successful_answers", 0))
                st.metric("Extrações realizadas", user_stats.get("extraction_count", 0))
                
                # Taxa de sucesso
                if user_stats.get("total_questions", 0) > 0:
                    success_rate = (user_stats.get("successful_answers", 0) / user_stats.get("total_questions", 1)) * 100
                    st.metric("Taxa de sucesso", f"{success_rate:.1f}%")
            except Exception as e:
                logger.error(f"Erro ao exibir estatísticas: {e}")
        
        st.markdown("---")
        
        # Botões de ação com permissões
        if st.button("🧹 Limpar Conversa", use_container_width=True):
            if 'user_rag' in st.session_state:
                st.session_state.user_rag.clear_history()
                st.success("✅ Conversa limpa!")
                st.rerun()
        
        # Extração de dados (com permissão)
        user_manager = st.session_state.get('user_manager')
        if user_manager and user_manager.has_permission(st.session_state.username, "extract"):
            if st.button("📊 Extrair Dados", use_container_width=True):
                st.session_state.show_extraction = True
        
        # Estatísticas do sistema (com permissão)
        if user_manager and user_manager.has_permission(st.session_state.username, "stats"):
            if st.button("📈 Estatísticas Sistema", use_container_width=True):
                st.session_state.show_system_stats = True
        
        if st.button("🚪 Logout", use_container_width=True):
            # Log da saída
            logger.info(f"Logout: {st.session_state.get('username', 'unknown')}")
            
            # Limpa sessão
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📚 Recursos Disponíveis")
        st.markdown("""
        **🔍 Consultas Inteligentes:**
        - Perguntas naturais contextuais
        - Referências a conversas anteriores
        - Análise de tabelas e figuras
        - Seguimento automático de tópicos
        
        **🚀 Otimizações de Produção:**
        - Cache de transformações
        - Fallbacks automáticos
        - Verificação de relevância
        - Logging detalhado
        """)

def system_stats_modal():
    """Modal para exibir estatísticas do sistema"""
    if st.session_state.get('show_system_stats', False):
        st.markdown("### 📈 Estatísticas do Sistema")
        
        if 'user_rag' in st.session_state:
            with st.spinner("Coletando estatísticas..."):
                try:
                    stats = st.session_state.user_rag.get_system_stats()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🗃️ Sistema")
                        st.json({
                            "Status": stats.get("system_health", "unknown"),
                            "Database": stats.get("database_status", "unknown"),
                            "Histórico atual": stats.get("chat_history_length", 0)
                        })
                    
                    with col2:
                        st.markdown("#### 🧠 Query Transformer")
                        transformer_stats = stats.get("transformer_stats", {})
                        st.json({
                            "Cache size": transformer_stats.get("cache_size", 0),
                            "Cache hits": transformer_stats.get("cache_hits", 0),
                            "LLM calls": transformer_stats.get("llm_calls", 0)
                        })
                    
                    # Health check atual
                    st.markdown("#### 🏥 Health Check")
                    try:
                        health_status = health_check()
                        
                        status_color = {
                            "healthy": "🟢",
                            "degraded": "🟡", 
                            "error": "🔴"
                        }.get(health_status["status"], "⚪")
                        
                        st.markdown(f"{status_color} **Status:** {health_status['status']}")
                        st.json(health_status)
                        
                    except Exception as e:
                        st.error(f"Erro no health check: {e}")
                        
                except Exception as e:
                    st.error(f"Erro ao coletar estatísticas: {e}")
        
        if st.button("❌ Fechar Estatísticas", use_container_width=True):
            st.session_state.show_system_stats = False
            st.rerun()

def extraction_modal():
    """Modal para extração de dados com templates otimizados"""
    if st.session_state.get('show_extraction', False):
        st.markdown("### 📊 Extração de Dados Estruturados")
        
        # Templates específicos para documentos acadêmicos
        templates = {
            "📄 Informações do Paper": {
                "title": "",
                "authors": [],
                "abstract": "",
                "year": "",
                "venue": "",
                "keywords": []
            },
            "🔬 Metodologia Técnica": {
                "approach_name": "",
                "algorithms": [],
                "datasets_used": [],
                "evaluation_metrics": [],
                "baseline_comparisons": []
            },
            "📊 Resultados e Performance": {
                "best_performance": "",
                "performance_metrics": {},
                "tables_referenced": [],
                "key_findings": [],
                "limitations": []
            },
            "🏗️ Arquitetura Zep/Graphiti": {
                "architecture_components": [],
                "temporal_features": [],
                "invalidation_mechanisms": [],
                "memory_management": "",
                "performance_optimizations": []
            },
            "🔧 Implementação": {
                "programming_languages": [],
                "frameworks_used": [],
                "hardware_requirements": "",
                "software_dependencies": [],
                "installation_steps": []
            },
            "🎛️ Personalizado": {}
        }
        
        template_choice = st.selectbox("📋 Escolha um template:", list(templates.keys()))
        
        # Filtro por documento (se disponível)
        doc_filter = st.text_input(
            "📁 Filtrar por documento (opcional):", 
            placeholder="Ex: 2501_13956",
            help="Deixe vazio para buscar em todos os documentos"
        )
        
        if template_choice == "🎛️ Personalizado":
            custom_template = st.text_area(
                "Template JSON personalizado:",
                value='{\n  "campo1": "",\n  "campo2": [],\n  "campo3": {}\n}',
                height=200,
                help="Use arrays [] para listas e {} para objetos"
            )
            try:
                template = json.loads(custom_template)
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON inválido: {e}")
                return
        else:
            template = templates[template_choice]
            st.markdown("**Template selecionado:**")
            st.json(template)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 Extrair Dados", use_container_width=True):
                if 'user_rag' in st.session_state:
                    with st.spinner("Extraindo dados usando IA..."):
                        try:
                            result = st.session_state.user_rag.extract_data(
                                template, 
                                doc_filter if doc_filter.strip() else None
                            )
                            
                            if result.get("status") == "success":
                                st.success("✅ Dados extraídos com sucesso!")
                                
                                # Exibe dados extraídos
                                st.markdown("#### 📋 Dados Extraídos:")
                                st.json(result["data"])
                                
                                # Informações adicionais
                                st.info(f"📊 Páginas analisadas: {result.get('pages_analyzed', 'N/A')}")
                                
                                # Opções de download
                                json_str = json.dumps(result["data"], indent=2, ensure_ascii=False)
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                filename = f"extracao_{template_choice.replace('🎛️ ', '').replace('📄 ', '').replace(' ', '_')}_{timestamp}.json"
                                
                                st.download_button(
                                    "💾 Baixar JSON",
                                    json_str,
                                    file_name=filename,
                                    mime="application/json",
                                    use_container_width=True
                                )
                                
                            else:
                                st.error(f"❌ Erro na extração: {result.get('message', 'Erro desconhecido')}")
                                
                        except Exception as e:
                            st.error(f"❌ Erro durante extração: {e}")
                            logger.error(f"Erro na extração: {e}")
        
        with col2:
            if st.button("🔄 Limpar Template", use_container_width=True):
                st.rerun()
        
        with col3:
            if st.button("❌ Fechar", use_container_width=True):
                st.session_state.show_extraction = False
                st.rerun()

def chat_interface():
    """Interface principal de chat otimizada para produção"""
    st.title("🚀 RAG Conversacional - Produção")
    
    # Badge de status de produção
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        st.markdown('<div style="text-align: center;"><span style="background-color: #28a745; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px;">🚀 PRODUÇÃO</span></div>', unsafe_allow_html=True)
    
    # Inicializa RAG do usuário se não existir
    if 'user_rag' not in st.session_state:
        with st.spinner("Inicializando sistema RAG de produção..."):
            try:
                st.session_state.user_rag = ProductionStreamlitRAG(st.session_state.username)
                st.success("✅ Sistema inicializado com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro na inicialização: {e}")
                logger.error(f"Erro ao inicializar RAG para {st.session_state.username}: {e}")
                st.stop()
    
    # Modals
    extraction_modal()
    system_stats_modal()
    
    # Container para mensagens
    chat_container = st.container()
    
    # Exibe histórico da conversa
    with chat_container:
        history = st.session_state.user_rag.get_history()
        
        if history:
            for i, message in enumerate(history):
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
            👋 Olá, **{user_name}**! Bem-vindo ao sistema RAG de produção.
            
            🚀 **Recursos disponíveis:**
            - Perguntas contextuais inteligentes
            - Memória de conversas anteriores  
            - Análise de documentos acadêmicos
            - Extração de dados estruturados
            
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
        # Mostra pergunta do usuário
        with st.chat_message("user"):
            st.write(prompt)
        
        # Gera resposta usando sistema de produção
        with st.chat_message("assistant"):
            with st.spinner("🧠 Processando com IA..."):
                try:
                    start_time = time.time()
                    response = st.session_state.user_rag.ask(prompt)
                    processing_time = time.time() - start_time
                    
                    st.write(response)
                    
                    # Mostra tempo de processamento para admin
                    if st.session_state.user_info.get('role') == 'Admin':
                        st.caption(f"⏱️ Processado em {processing_time:.2f}s")
                        
                except Exception as e:
                    error_msg = f"❌ Erro ao processar pergunta: {e}"
                    st.error(error_msg)
                    logger.error(f"Erro no chat para {st.session_state.username}: {e}")
                    
                    # Fallback para admin
                    if st.session_state.user_info.get('role') == 'Admin':
                        st.markdown("**Debug Info:**")
                        st.code(str(e))

def main():
    """Função principal da aplicação de produção"""
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
        # Interface principal de produção
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