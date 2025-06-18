#!/usr/bin/env python3
"""
🚀 SISTEMA RAG MULTI-AGENTE - ARQUIVO PRINCIPAL

Este é o arquivo principal para usar o sistema multi-agente em produção.
Execute: python main_multiagent.py
"""

import asyncio
import sys
from pathlib import Path

# Configurar caminhos
sys.path.append('multi-agent-researcher/src')
sys.path.append('/workspaces/rag')

# Carregar configurações
from dotenv import load_dotenv, find_dotenv
env_file = find_dotenv()
if env_file:
    load_dotenv(env_file)
    print(f"✅ Configurações carregadas de: {env_file}")

from researcher.agents.openai_lead import OpenAILeadResearcher, OpenAILeadConfig
from researcher.agents.base import AgentContext


class MultiAgentRAGSystem:
    """Sistema RAG Multi-Agente Principal."""
    
    def __init__(self):
        """Inicializar o sistema."""
        self.config = OpenAILeadConfig.from_env()
        self.agent = OpenAILeadResearcher(
            agent_id="production-rag-system",
            name="Sistema RAG Multi-Agente",
            config=self.config
        )
        
    async def ask(self, question: str, objective: str = None, constraints: list = None, streaming: bool = True) -> str:
        """
        Fazer uma pergunta ao sistema multi-agente, mostrando raciocínio em tempo real se streaming=True.
        
        Args:
            question: Pergunta do usuário
            objective: Objetivo da pesquisa (opcional)
            constraints: Restrições da pesquisa (opcional)
            streaming: Exibir raciocínio em tempo real (padrão: True)
            
        Returns:
            Resposta do sistema
        """
        from time import sleep
        import asyncio
        
        # Criar contexto
        context = AgentContext(
            query=question,
            objective=objective or f"Responder: {question}",
            constraints=constraints or []
        )
        
        print(f"🤖 Processando: {question}")
        print(f"🎯 Objetivo: {context.objective}")
        if constraints:
            print(f"⚠️  Restrições: {', '.join(constraints)}")
        print()
        
        # Executar sistema multi-agente com streaming
        task = asyncio.create_task(self.agent.run(context))
        last_len = 0
        print("🧠 Raciocínio em tempo real:")
        while not task.done():
            if hasattr(self.agent, 'reasoner'):
                trace = self.agent.reasoner.reasoning_history
                for step in trace[last_len:]:
                    print(f"  [{step.step_type.upper()}] {step.content}")
                    if step.observations:
                        print(f"     💡 {step.observations}")
                    if step.next_action:
                        print(f"     ➡️  Próxima ação: {step.next_action}")
                last_len = len(trace)
            await asyncio.sleep(0.5)
        result = await task
        # Print any final steps
        if hasattr(self.agent, 'reasoner'):
            trace = self.agent.reasoner.reasoning_history
            for step in trace[last_len:]:
                print(f"  [{step.step_type.upper()}] {step.content}")
                if step.observations:
                    print(f"     💡 {step.observations}")
                if step.next_action:
                    print(f"     ➡️  Próxima ação: {step.next_action}")
        print()
        return result.output
    
    def get_reasoning_trace(self) -> list:
        """Obter o trace de raciocínio da última execução."""
        if hasattr(self.agent, 'reasoner'):
            return self.agent.reasoner.reasoning_history
        return []
    
    def show_stats(self):
        """Mostrar estatísticas do sistema."""
        print(f"📊 Configuração do Sistema:")
        print(f"  • Modelo: {self.config.model}")
        print(f"  • Max subagentes: {self.config.max_subagents}")
        print(f"  • Execução paralela: {self.config.parallel_execution}")
        print(f"  • Decomposição LLM: {self.config.use_llm_decomposition}")
        print(f"  • Timeout: {self.config.subagent_timeout}s")


async def modo_interativo():
    """Modo interativo para testar o sistema."""
    
    print("🚀 SISTEMA RAG MULTI-AGENTE - MODO INTERATIVO")
    print("="*60)
    print("Digite suas perguntas ou 'sair' para terminar")
    print("Comandos: /help, /stats, /trace, /sair")
    print()
    
    # Inicializar sistema
    sistema = MultiAgentRAGSystem()
    sistema.show_stats()
    print()
    
    while True:
        try:
            pergunta = input("❓ Sua pergunta: ").strip()
            
            if pergunta.lower() in ['sair', 'exit', 'quit']:
                print("👋 Até logo!")
                break
                
            elif pergunta == '/help':
                print("📋 Comandos disponíveis:")
                print("  • /stats  - Mostrar configuração do sistema")
                print("  • /trace  - Mostrar raciocínio da última consulta")
                print("  • /sair   - Sair do programa")
                print()
                continue
                
            elif pergunta == '/stats':
                sistema.show_stats()
                print()
                continue
                
            elif pergunta == '/trace':
                trace = sistema.get_reasoning_trace()
                if trace:
                    print("🧠 Raciocínio da última consulta:")
                    for i, step in enumerate(trace, 1):
                        print(f"{i}. [{step.step_type.upper()}] {step.content}")
                else:
                    print("⚠️ Nenhum trace disponível")
                print()
                continue
                
            elif not pergunta:
                continue
            
            print("⏳ Processando...")
            print()
            
            # Executar pergunta
            resposta = await sistema.ask(pergunta)
            
            print("🤖 Resposta:")
            print("="*50)
            print(resposta)
            print("="*50)
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Saindo...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")
            print()


async def modo_demonstracao():
    """Modo demonstração com perguntas pré-definidas."""
    
    print("🎭 MODO DEMONSTRAÇÃO")
    print("="*30)
    
    sistema = MultiAgentRAGSystem()
    
    # Perguntas de exemplo
    perguntas_demo = [
        {
            "pergunta": "O que é Zep e como funciona?",
            "objetivo": "Entender o conceito e arquitetura do Zep",
            "restricoes": ["Foco em aspectos técnicos"]
        },
        {
            "pergunta": "Quais são as vantagens dos grafos de conhecimento?",
            "objetivo": "Compreender benefícios dos knowledge graphs",
            "restricoes": ["Incluir exemplos práticos"]
        }
    ]
    
    for i, demo in enumerate(perguntas_demo, 1):
        print(f"🎯 Demo {i}/{len(perguntas_demo)}")
        print("-"*40)
        
        resposta = await sistema.ask(
            demo["pergunta"], 
            demo["objetivo"], 
            demo["restricoes"]
        )
        
        print("🤖 Resposta:")
        # Mostrar apenas preview
        linhas = resposta.split('\n')[:10]
        for linha in linhas:
            if linha.strip():
                print(linha)
        if len(resposta.split('\n')) > 10:
            print("...")
        
        print()
        
        # Mostrar trace resumido
        trace = sistema.get_reasoning_trace()
        if trace:
            print("🧠 Passos do raciocínio:")
            for step in trace[-3:]:  # Últimos 3 passos
                print(f"  • {step.step_type}: {step.content[:80]}...")
        
        print("\n" + "="*50 + "\n")


async def main():
    """Função principal."""
    
    print("🚀 SISTEMA RAG MULTI-AGENTE")
    print("="*40)
    print()
    print("Escolha o modo de execução:")
    print("1. Modo Interativo")
    print("2. Modo Demonstração")
    print("3. Sair")
    print()
    
    try:
        escolha = input("Sua escolha (1-3): ").strip()
        
        if escolha == "1":
            await modo_interativo()
        elif escolha == "2":
            await modo_demonstracao()
        elif escolha == "3":
            print("👋 Até logo!")
        else:
            print("❌ Opção inválida")
            
    except KeyboardInterrupt:
        print("\n👋 Saindo...")


if __name__ == "__main__":
    """
    ESTE É O ARQUIVO PRINCIPAL DO SISTEMA MULTI-AGENTE!
    
    Execute: python main_multiagent.py
    
    O sistema vai:
    1. Carregar configurações do .env
    2. Inicializar OpenAI Lead Agent + ReAct reasoning
    3. Permitir fazer perguntas
    4. Mostrar todo o processo de raciocínio
    5. Retornar respostas baseadas em documentos reais
    """
    asyncio.run(main())
