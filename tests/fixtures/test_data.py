"""Fixtures específicas para dados de teste."""

import json
import tempfile
from pathlib import Path
from PIL import Image


# Dados de teste para perguntas do evaluator
SAMPLE_TEST_QUESTIONS = [
    {
        "id": "ml_basics_001",
        "question": "What is machine learning and how does it differ from traditional programming?",
        "expected_pages": [1, 2, 5],
        "expected_keywords": ["machine learning", "traditional programming", "algorithm", "data"],
        "category": "conceptual",
        "difficulty": "easy",
        "ground_truth": "Machine learning is a method where computers learn patterns from data rather than being explicitly programmed."
    },
    {
        "id": "nn_architecture_002", 
        "question": "Explain the architecture of a deep neural network and its key components.",
        "expected_pages": [8, 9, 12],
        "expected_keywords": ["neural network", "layers", "weights", "activation", "backpropagation"],
        "category": "technical",
        "difficulty": "hard",
        "ground_truth": "Deep neural networks consist of multiple layers with neurons, weights, and activation functions."
    },
    {
        "id": "gradient_descent_003",
        "question": "How does gradient descent optimization work in neural networks?",
        "expected_pages": [15, 16],
        "expected_keywords": ["gradient descent", "optimization", "learning rate", "convergence"],
        "category": "technical", 
        "difficulty": "medium",
        "ground_truth": "Gradient descent iteratively adjusts parameters to minimize the loss function."
    },
    {
        "id": "overfitting_004",
        "question": "What is overfitting and how can it be prevented?",
        "expected_pages": [20, 21, 22],
        "expected_keywords": ["overfitting", "regularization", "validation", "generalization"],
        "category": "conceptual",
        "difficulty": "medium"
    },
    {
        "id": "transformer_005",
        "question": "Describe the attention mechanism in transformer models.",
        "expected_pages": [25, 26, 27],
        "expected_keywords": ["attention", "transformer", "self-attention", "queries", "keys", "values"],
        "category": "technical",
        "difficulty": "hard"
    }
]

# Dados de teste para documentos
SAMPLE_DOCUMENTS = [
    {
        "id": "doc_page_1",
        "page_num": 1,
        "markdown_text": """
# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence (AI) that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves.

## Traditional Programming vs Machine Learning

In traditional programming, we write specific instructions for the computer to follow. In machine learning, we provide data and let the algorithm find patterns.

Key differences:
- Traditional: Rules + Data → Answers  
- ML: Data + Answers → Rules
        """,
        "image_path": "/test/images/page_1.png",
        "doc_source": "ml_textbook.pdf"
    },
    {
        "id": "doc_page_2", 
        "page_num": 2,
        "markdown_text": """
# Types of Machine Learning

There are three main types of machine learning:

## 1. Supervised Learning
Uses labeled training data to learn a mapping function from inputs to outputs.

## 2. Unsupervised Learning  
Finds hidden patterns in data without labeled examples.

## 3. Reinforcement Learning
Learns through interaction with an environment using rewards and penalties.
        """,
        "image_path": "/test/images/page_2.png", 
        "doc_source": "ml_textbook.pdf"
    },
    {
        "id": "doc_page_8",
        "page_num": 8,
        "markdown_text": """
# Neural Network Architecture

A neural network consists of layers of interconnected nodes (neurons). Each connection has an associated weight that determines the importance of the input.

## Key Components:
- **Input Layer**: Receives the initial data
- **Hidden Layers**: Process the information  
- **Output Layer**: Produces the final result
- **Weights**: Parameters that control signal strength
- **Biases**: Allow shifting of activation functions
        """,
        "image_path": "/test/images/page_8.png",
        "doc_source": "ml_textbook.pdf"
    }
]

# Embeddings de exemplo (simulados)
SAMPLE_EMBEDDINGS = {
    "machine learning": [0.1, 0.2, 0.3] + [0.0] * 1021,
    "neural network": [0.2, 0.1, 0.4] + [0.0] * 1021, 
    "gradient descent": [0.3, 0.4, 0.1] + [0.0] * 1021,
    "overfitting": [0.1, 0.3, 0.2] + [0.0] * 1021
}

# Respostas RAG simuladas
SAMPLE_RAG_RESPONSES = {
    "what is machine learning": {
        "answer": "Machine learning is a subset of artificial intelligence that enables systems to automatically learn and improve from experience without being explicitly programmed. It differs from traditional programming in that instead of writing specific rules, we provide data and let algorithms find patterns.",
        "pages_used": [1, 2],
        "query_transformed": "machine learning definition and traditional programming comparison",
        "confidence": 0.92
    },
    "neural network architecture": {
        "answer": "A neural network consists of layers of interconnected nodes called neurons. The key components include an input layer that receives data, hidden layers that process information, an output layer that produces results, weights that control signal strength, and biases that allow shifting of activation functions.",
        "pages_used": [8, 9],
        "query_transformed": "neural network structure and components",
        "confidence": 0.88
    },
    "gradient descent": {
        "answer": "Gradient descent is an optimization algorithm that iteratively adjusts neural network parameters to minimize the loss function. It calculates gradients and moves in the direction that reduces error, with the learning rate controlling the step size.",
        "pages_used": [15, 16],
        "query_transformed": "gradient descent optimization algorithm",
        "confidence": 0.85
    }
}

def create_test_pdf_content():
    """Cria conteúdo simulado de PDF para testes."""
    return {
        "metadata": {
            "title": "Machine Learning Fundamentals",
            "author": "Test Author",
            "pages": 30,
            "created": "2024-01-01"
        },
        "pages": [
            {
                "page_number": i + 1,
                "text": f"This is page {i + 1} content with machine learning concepts.",
                "has_images": i % 3 == 0,  # Algumas páginas têm imagens
                "word_count": 150 + (i * 10)
            }
            for i in range(30)
        ]
    }

def create_test_image(size=(100, 100), color="red"):
    """Cria uma imagem de teste."""
    return Image.new('RGB', size, color=color)

def create_test_config():
    """Cria configuração de teste."""
    return {
        "embedding_dim": 1024,
        "max_tokens": 32000,
        "batch_size": 10,
        "concurrency": 2,
        "timeout": 5,
        "retry_attempts": 1
    }

def save_test_data_to_file(data, file_path):
    """Salva dados de teste em arquivo JSON."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_test_data_from_file(file_path):
    """Carrega dados de teste de arquivo JSON."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_evaluation_dataset_file(temp_dir):
    """Cria arquivo de dataset de avaliação para testes."""
    dataset_path = Path(temp_dir) / "test_evaluation_dataset.json"
    save_test_data_to_file(SAMPLE_TEST_QUESTIONS, dataset_path)
    return str(dataset_path)

def create_mock_vector_search_results():
    """Cria resultados simulados de busca vetorial."""
    return [
        {
            "_id": "doc_1",
            "page_num": 1,
            "markdown_text": "Machine learning is a powerful technique...",
            "doc_source": "ml_paper.pdf",
            "$similarity": 0.95
        },
        {
            "_id": "doc_2", 
            "page_num": 8,
            "markdown_text": "Neural networks consist of multiple layers...",
            "doc_source": "ml_paper.pdf",
            "$similarity": 0.87
        },
        {
            "_id": "doc_3",
            "page_num": 15,
            "markdown_text": "Gradient descent optimization works by...",
            "doc_source": "ml_paper.pdf", 
            "$similarity": 0.82
        }
    ]

def create_mock_rerank_results():
    """Cria resultados simulados de re-ranking."""
    return [
        {"index": 0, "relevance_score": 0.92},
        {"index": 2, "relevance_score": 0.88},
        {"index": 1, "relevance_score": 0.75}
    ]
