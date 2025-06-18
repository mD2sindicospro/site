"""
Módulo de traduções para mapear textos internos (em inglês) para textos exibidos ao usuário (em português).
"""

STATUS_TRANSLATIONS = {
    'pending': 'Pendente',
    'in_progress': 'Em Andamento',
    'completed': 'Concluída',
    'cancelled': 'Cancelada',
    'correction': 'Correção',
    'approved': 'Realizada',
    'not_completed': 'Não Realizada',
    'overdue': 'Atrasada',
    'finalizada': 'Finalizada',
    'realizada': 'Realizada',
    'correção': 'Correção',
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
        str: Nome da classe CSS
    """
    return f'badge-status-{status.replace(" ", "-").lower()}' 