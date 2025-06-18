#!/usr/bin/env python3
"""
🔐 RECOMENDAÇÕES DE SEGURANÇA - Implementação de Autenticação JWT + API Keys

Este arquivo contém exemplos de como implementar autenticação nas APIs RAG.
"""

import os
import jwt
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
from functools import wraps

# ═══════════════════════════════════════════════════════════════════════════════
# 1. CONFIGURAÇÕES DE SEGURANÇA
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityConfig:
    """Configurações de segurança centralizadas"""
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # API Key Configuration
    API_KEY_LENGTH = 32
    API_KEY_PREFIX = "rag_"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hora
    
    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
    
    # Redis for rate limiting and session management
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. MODELOS DE DADOS DE AUTENTICAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

class User(BaseModel):
    """Modelo de usuário"""
    user_id: str
    username: str
    email: str
    role: str  # "admin", "user", "readonly"
    api_key: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

class LoginRequest(BaseModel):
    """Request de login"""
    username: str
    password: str

class JWTTokenResponse(BaseModel):
    """Response com token JWT"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    role: str

class APIKeyRequest(BaseModel):
    """Request para geração de API Key"""
    description: str
    expires_days: Optional[int] = None

class APIKeyResponse(BaseModel):
    """Response com API Key"""
    api_key: str
    description: str
    expires_at: Optional[datetime] = None
    created_at: datetime

# ═══════════════════════════════════════════════════════════════════════════════
# 3. SISTEMA DE AUTENTICAÇÃO JWT
# ═══════════════════════════════════════════════════════════════════════════════

class JWTAuthenticator:
    """Sistema de autenticação JWT"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
    
    def create_token(self, user: User) -> Dict[str, any]:
        """Cria token JWT para usuário"""
        
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(hours=self.config.JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        token = jwt.encode(payload, self.config.JWT_SECRET_KEY, algorithm=self.config.JWT_ALGORITHM)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": self.config.JWT_EXPIRATION_HOURS * 3600,
            "user_id": user.user_id,
            "role": user.role
        }
    
    def verify_token(self, token: str) -> Dict[str, any]:
        """Verifica e decodifica token JWT"""
        
        try:
            payload = jwt.decode(
                token, 
                self.config.JWT_SECRET_KEY, 
                algorithms=[self.config.JWT_ALGORITHM]
            )
            
            # Verificar se é token de acesso
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Token inválido")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Token inválido")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. SISTEMA DE API KEYS
# ═══════════════════════════════════════════════════════════════════════════════

class APIKeyManager:
    """Gerenciador de API Keys"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
    
    def generate_api_key(self, user_id: str, description: str = "") -> str:
        """Gera nova API key"""
        
        # Gerar key aleatória
        timestamp = str(int(time.time()))
        data = f"{user_id}:{timestamp}:{description}"
        hash_key = hashlib.sha256(data.encode()).hexdigest()
        
        api_key = f"{self.config.API_KEY_PREFIX}{hash_key[:self.config.API_KEY_LENGTH]}"
        
        # Em produção, salvar no banco de dados com:
        # - api_key (hash)
        # - user_id
        # - description
        # - created_at
        # - expires_at
        # - is_active
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, any]]:
        """Verifica API key e retorna dados do usuário"""
        
        # Em produção, consultar banco de dados
        # Por enquanto, validação simples
        if not api_key.startswith(self.config.API_KEY_PREFIX):
            return None
        
        # Simulação - em produção buscar no DB
        return {
            "user_id": "api_user",
            "username": "API User",
            "role": "user",
            "api_key": api_key
        }

# ═══════════════════════════════════════════════════════════════════════════════
# 5. RATE LIMITING
# ═══════════════════════════════════════════════════════════════════════════════

class RateLimiter:
    """Sistema de rate limiting"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        # Em produção, usar Redis
        self.redis_client = None  # redis.Redis.from_url(config.REDIS_URL)
        self.memory_store = {}  # Fallback para desenvolvimento
    
    def is_allowed(self, key: str, limit: int = None, window: int = None) -> bool:
        """Verifica se requisição está dentro do limite"""
        
        limit = limit or self.config.RATE_LIMIT_REQUESTS
        window = window or self.config.RATE_LIMIT_WINDOW
        
        current_time = int(time.time())
        window_start = current_time - window
        
        # Em produção, usar Redis com sliding window
        # Por simplicidade, usar memória local
        if key not in self.memory_store:
            self.memory_store[key] = []
        
        # Remover requisições antigas
        self.memory_store[key] = [
            req_time for req_time in self.memory_store[key] 
            if req_time > window_start
        ]
        
        # Verificar limite
        if len(self.memory_store[key]) >= limit:
            return False
        
        # Adicionar requisição atual
        self.memory_store[key].append(current_time)
        return True
    
    def get_remaining_requests(self, key: str) -> int:
        """Retorna número de requisições restantes"""
        current_count = len(self.memory_store.get(key, []))
        return max(0, self.config.RATE_LIMIT_REQUESTS - current_count)

# ═══════════════════════════════════════════════════════════════════════════════
# 6. MIDDLEWARES DE SEGURANÇA
# ═══════════════════════════════════════════════════════════════════════════════

# Configuração de segurança global
security_config = SecurityConfig()
jwt_auth = JWTAuthenticator(security_config)
api_key_manager = APIKeyManager(security_config)
rate_limiter = RateLimiter(security_config)

# FastAPI Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, any]:
    """Dependency para autenticação JWT"""
    
    token = credentials.credentials
    return jwt_auth.verify_token(token)

async def get_api_key_user(request: Request) -> Optional[Dict[str, any]]:
    """Dependency para autenticação via API Key"""
    
    # Verificar header X-API-Key
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    
    return api_key_manager.verify_api_key(api_key)

async def authenticate_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, any]:
    """Dependency unificada para autenticação (JWT ou API Key)"""
    
    # Tentar autenticação via API Key primeiro
    api_user = await get_api_key_user(request)
    if api_user:
        return api_user
    
    # Tentar autenticação via JWT
    if credentials:
        return jwt_auth.verify_token(credentials.credentials)
    
    raise HTTPException(
        status_code=401,
        detail="Autenticação requerida. Use JWT Bearer token ou X-API-Key header."
    )

def require_role(required_roles: List[str]):
    """Decorator para exigir roles específicas"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obter usuário atual dos kwargs
            current_user = kwargs.get('current_user')
            if not current_user or current_user.get('role') not in required_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Acesso negado. Roles requeridas: {required_roles}"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def check_rate_limit(request: Request):
    """Middleware para verificar rate limiting"""
    
    # Usar IP + User ID se autenticado
    client_ip = request.client.host
    user_key = f"rate_limit:{client_ip}"
    
    # Se autenticado, usar user_id
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = jwt_auth.verify_token(token)
            user_key = f"rate_limit:user:{payload['user_id']}"
    except:
        pass  # Usar IP se não conseguir autenticar
    
    if not rate_limiter.is_allowed(user_key):
        raise HTTPException(
            status_code=429,
            detail="Rate limit excedido. Tente novamente mais tarde.",
            headers={"Retry-After": str(security_config.RATE_LIMIT_WINDOW)}
        )

# ═══════════════════════════════════════════════════════════════════════════════
# 7. EXEMPLO DE APLICAÇÃO COM SEGURANÇA
# ═══════════════════════════════════════════════════════════════════════════════

def create_secure_app() -> FastAPI:
    """Cria aplicação FastAPI com segurança implementada"""
    
    app = FastAPI(
        title="RAG API - Segura",
        description="API RAG com autenticação JWT e API Keys",
        version="1.0.0"
    )
    
    # CORS restritivo
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_config.ALLOWED_ORIGINS,  # Origens específicas
        allow_credentials=True,
        allow_methods=["GET", "POST"],  # Métodos específicos
        allow_headers=["*"],
    )
    
    # Endpoints de autenticação
    @app.post("/auth/login", response_model=JWTTokenResponse)
    async def login(login_data: LoginRequest):
        """Login com username/password"""
        
        # Em produção, verificar credenciais no banco
        if login_data.username == "admin" and login_data.password == "secret":
            user = User(
                user_id="1",
                username="admin",
                email="admin@example.com",
                role="admin",
                created_at=datetime.utcnow()
            )
            return jwt_auth.create_token(user)
        
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    @app.post("/auth/api-key", response_model=APIKeyResponse)
    async def create_api_key(
        api_key_data: APIKeyRequest,
        current_user: Dict = Depends(get_current_user)
    ):
        """Gera nova API key para usuário autenticado"""
        
        api_key = api_key_manager.generate_api_key(
            current_user["user_id"], 
            api_key_data.description
        )
        
        return APIKeyResponse(
            api_key=api_key,
            description=api_key_data.description,
            created_at=datetime.utcnow()
        )
    
    # Endpoints protegidos
    @app.post("/search")
    async def secure_search(
        query_data: dict,
        request: Request,
        current_user: Dict = Depends(authenticate_user)
    ):
        """Endpoint de busca protegido"""
        
        # Verificar rate limiting
        await check_rate_limit(request)
        
        # Lógica de busca aqui
        return {
            "message": "Busca realizada com sucesso",
            "user": current_user["username"],
            "query": query_data
        }
    
    @app.get("/admin/metrics")
    async def admin_metrics(current_user: Dict = Depends(get_current_user)):
        """Endpoint administrativo"""
        
        if current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Acesso negado")
        
        return {"metrics": "dados administrativos"}
    
    return app

# ═══════════════════════════════════════════════════════════════════════════════
# 8. IMPLEMENTAÇÃO PARA AS APIs EXISTENTES
# ═══════════════════════════════════════════════════════════════════════════════

"""
EXEMPLO DE COMO MODIFICAR api_simple.py:

# Adicionar no topo do arquivo
from security_recommendations import (
    authenticate_user, check_rate_limit, require_role,
    security_config, SecurityConfig
)

# Modificar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=security_config.ALLOWED_ORIGINS,  # Não mais ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Proteger endpoint principal
@app.post("/search", response_model=SimpleRAGResponse)
async def simple_rag_search(
    query_data: SimpleRAGQuery,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(authenticate_user),  # ADICIONAR
    state: APIState = Depends(check_api_ready)
):
    # Verificar rate limiting
    await check_rate_limit(request)  # ADICIONAR
    
    # Resto do código permanece igual...

# Proteger endpoints administrativos
@app.get("/config", response_model=Dict[str, Any])
async def get_config(
    current_user: Dict = Depends(authenticate_user),  # ADICIONAR
    state: APIState = Depends(check_api_ready)
):
    # Verificar se é admin
    if current_user["role"] not in ["admin", "user"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Resto do código...
"""

if __name__ == "__main__":
    # Exemplo de uso
    app = create_secure_app()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)