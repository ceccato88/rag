"""
Prompts estruturados para o padrão ReAct.
Substitui o sistema "thinking" do Anthropic por prompts organizados.
"""

from typing import Dict, Any, List


class ReActPrompts:
    """Coleção de prompts estruturados para o padrão ReAct."""
    
    @staticmethod
    def initial_fact_gathering(task: str, context: str = "") -> str:
        """Prompt para coleta inicial de fatos."""
        return f"""Abaixo apresento uma solicitação do usuário e contexto potencialmente relevante para ajudar a resolvê-la.

Com base na solicitação do usuário, use o contexto para responder à seguinte pesquisa da melhor forma possível.

Aqui está a solicitação do usuário:

```
{task}
```

Aqui está o contexto:

=== Início do Contexto ===

{context}

=== Fim do Contexto ===

Aqui está a pesquisa:

1. Liste quaisquer fatos ou números específicos que sejam DADOS com base na solicitação. É possível que não haja nenhum.
2. Liste quaisquer fatos que sejam lembrados da memória, seu conhecimento ou suposições bem fundamentadas, etc.

Ao responder esta pesquisa, lembre-se de que os fatos geralmente serão detalhes específicos.
Forneça quantos fatos puder, mesmo que pareçam triviais ou sem importância."""

    @staticmethod
    def planning(task: str, team_capabilities: str, facts: str) -> str:
        """Prompt para criação de plano."""
        return f"""Para abordar a solicitação do usuário, montamos a seguinte equipe de especialistas:

{team_capabilities}

Com base na equipe disponível e nos fatos conhecidos e desconhecidos, crie um plano conciso em tópicos para como abordaremos a solicitação do usuário.

Fatos conhecidos:
{facts}

Lembre-se, não há exigência de envolver todos os membros da equipe no plano. Alguns membros da equipe podem não ser relevantes para a solicitação do usuário.

O plano deve ser:
- Específico e acionável
- Organizado em etapas lógicas
- Focado no objetivo final
- Realista com os recursos disponíveis"""

    @staticmethod
    def execution(task: str, team_capabilities: str, context: str, facts: str, plan: str) -> str:
        """Prompt para execução do plano."""
        return f"""Estamos trabalhando para abordar a seguinte solicitação do usuário:

```
{task}
```

Para responder a esta solicitação, montamos a seguinte equipe:

{team_capabilities}

Aqui está o contexto a considerar:

=== Início do Contexto ===

{context}

=== Fim do Contexto ===

Aqui estão os fatos a considerar:

{facts}

Aqui está o plano a seguir da melhor forma possível:

{plan}

Execute o próximo passo do plano de forma precisa e detalhada. Se uma ação específica for necessária, execute-a usando as ferramentas disponíveis."""

    @staticmethod
    def validation(task: str, team_capabilities: str) -> str:
        """Prompt para validação do progresso."""
        return f"""Estamos trabalhando na seguinte solicitação do usuário:

```
{task}
```

E montamos a seguinte equipe:

{team_capabilities}

Para fazer progresso na solicitação, responda às seguintes perguntas, incluindo o raciocínio necessário:

- O suficiente do plano foi executado para completar com sucesso a solicitação original do usuário? Isso inclui a execução de tarefas planejadas e o fornecimento de todas as informações solicitadas.
- Estamos em um loop onde estamos repetindo as mesmas solicitações e/ou obtendo as mesmas respostas? Loops podem abranger várias rodadas e podem incluir ações repetidas.
- Qual é a próxima instrução ou pergunta para fazer progresso na solicitação? Formule como se estivesse falando diretamente e inclua qualquer informação específica necessária.

Forneça suas respostas em formato JSON estruturado:
{{
    "is_request_completed": {{
        "reason": "Explicação detalhada",
        "answer": true/false
    }},
    "is_in_loop": {{
        "reason": "Explicação detalhada", 
        "answer": true/false
    }},
    "next_instruction_or_question": {{
        "reason": "Explicação detalhada",
        "answer": "Próxima ação específica"
    }}
}}"""

    @staticmethod
    def update_facts(task: str, context: str, original_facts: str) -> str:
        """Prompt para atualização de fatos."""
        return f"""Abaixo apresento uma solicitação do usuário e contexto potencialmente relevante no histórico de conversação para ajudar a resolvê-la.

Com base na solicitação, atualize a folha de fatos para incluir qualquer coisa nova que aprendemos que seja relevante para a solicitação.
Exemplos de edições podem incluir, mas não se limitam a, adicionar novas suposições, mover suposições para fatos verificados se apropriado, etc.
Atualizações podem ser feitas em qualquer seção da folha de fatos, e mais de uma seção pode ser editada.
Este é um bom momento para atualizar fatos lembrados, então adicione ou atualize pelo menos uma suposição bem fundamentada.
Não remova nenhum fato a menos que você tenha informações suficientes para fazê-lo com confiança.

Aqui está a solicitação do usuário:

```
{task}
```

Aqui está o contexto original:

=== Início do Contexto ===

{context}

=== Fim do Contexto ===

Aqui está a folha de fatos original:

{original_facts}

Pesquisa atualizada:

1. Liste quaisquer fatos ou números específicos que sejam DADOS com base na solicitação. É possível que não haja nenhum.
2. Liste quaisquer fatos que sejam lembrados da memória, seu conhecimento ou suposições bem fundamentadas, etc.

Ao responder esta pesquisa, lembre-se de que os fatos geralmente serão detalhes específicos.
Forneça quantos fatos puder, mesmo que pareçam triviais ou sem importância."""

    @staticmethod
    def update_plan(team_capabilities: str, what_went_wrong: str = "") -> str:
        """Prompt para atualização do plano."""
        return f"""Explique brevemente o que deu errado na última execução (a causa raiz da falha), e então elabore um novo plano que tome medidas e/ou inclua dicas para superar desafios anteriores e evitar repetir os mesmos erros.

{f"Problema identificado: {what_went_wrong}" if what_went_wrong else ""}

Como antes, o novo plano deve ser conciso e expresso em forma de tópicos, e considerar a seguinte equipe disponível:

{team_capabilities}

O novo plano deve:
- Abordar especificamente os problemas anteriores
- Incluir medidas preventivas contra falhas
- Ser mais robusto e detalhado
- Manter o foco no objetivo original"""

    @staticmethod
    def final_result(task: str) -> str:
        """Prompt para resultado final."""
        return f"""Estamos trabalhando na seguinte solicitação do usuário:

```
{task}
```

Completamos a tarefa.

As mensagens acima contêm a conversa que ocorreu para completar a tarefa.

Com base nas informações coletadas, forneça a resposta final à solicitação original.
A resposta deve ser formulada como se você estivesse falando com o usuário.

A resposta final deve:
- Ser completa e abordar todos os aspectos da solicitação
- Ser clara e bem estruturada
- Incluir todos os detalhes relevantes descobertos durante o processo
- Ser apresentada de forma profissional e útil"""

    @staticmethod
    def reasoning_reflection(reasoning_history: List[Dict[str, Any]]) -> str:
        """Prompt para reflexão sobre o processo de raciocínio."""
        history_summary = "\n".join([
            f"- {step.get('step_type', 'unknown')}: {step.get('content', 'N/A')}"
            for step in reasoning_history
        ])
        
        return f"""Analise o seguinte histórico de raciocínio e forneça uma reflexão sobre a qualidade do processo:

Histórico de passos:
{history_summary}

Avalie:
1. Eficiência do processo (foram dados passos desnecessários?)
2. Completude da análise (algum aspecto importante foi perdido?)
3. Qualidade do raciocínio (as conexões lógicas fazem sentido?)
4. Oportunidades de melhoria (como o processo poderia ser otimizado?)

Forneça feedback construtivo para melhorar futuras execuções."""
