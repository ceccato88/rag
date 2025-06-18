#!/usr/bin/env python3
"""
Teste básico do sistema RAG conforme README
"""

from search import SimpleRAG

def teste_basico():
    """Testa funcionalidade básica do RAG"""
    print("🔍 Iniciando teste do sistema RAG...")
    
    try:
        # Inicializar o sistema RAG
        rag = SimpleRAG()
        print("✅ Sistema RAG inicializado com sucesso")
        
        # Fazer uma pergunta simples
        pergunta = "O que é Zep e como funciona?"
        print(f"\n❓ Pergunta: {pergunta}")
        
        # Obter resposta
        print("🤖 Processando...")
        resultado = rag.search(pergunta)
        
        print("\n💬 Resposta:")
        print(resultado)
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    sucesso = teste_basico()
    if sucesso:
        print("\n✅ Teste concluído com sucesso!")
    else:
        print("\n❌ Teste falhou!")
