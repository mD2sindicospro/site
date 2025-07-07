"""
Módulo de traduções para mapear textos internos (em inglês) para textos exibidos ao usuário (em português).
"""

STATUS_TRANSLATIONS = {
    'pending': 'Pendente',
    'in_progress': 'Em Andamento',
    'completed': 'Em Verificação',
    'correction': 'Correção',
    'not_completed': 'Não Realizada',
    'overdue': 'Atrasada',
    'done': 'Realizada',
    'cancelled': 'Cancelada',
}

def translate_status(status):
    """
    Traduz o status interno para o texto em português.
    
    Args:
        status (str): Status interno em inglês
        
    Returns:
        str: Status traduzido para português
    """
    return STATUS_TRANSLATIONS.get(status, status)

def get_status_class(status):
    """
    Retorna a classe CSS correspondente ao status.
    
    Args:
        status (str): Status interno em inglês
        
    Returns:
        str: Classe CSS para o badge
    """
    if status == "in_progress":
        return "badge-status-in-progress"
    return f'badge-status-{status.lower().replace("_", "-")}' 