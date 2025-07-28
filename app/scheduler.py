from datetime import datetime, timedelta
from app.extensions import db
from app.models.message import Message
import logging
import os

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Arquivo para controlar a última limpeza
CLEANUP_LOG_FILE = 'last_cleanup.txt'

def get_last_cleanup_date():
    """
    Obtém a data da última limpeza do arquivo de controle
    """
    try:
        if os.path.exists(CLEANUP_LOG_FILE):
            with open(CLEANUP_LOG_FILE, 'r') as f:
                date_str = f.read().strip()
                return datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception as e:
        logger.error(f"Erro ao ler data da última limpeza: {str(e)}")
    return None

def set_last_cleanup_date():
    """
    Define a data atual como última limpeza
    """
    try:
        with open(CLEANUP_LOG_FILE, 'w') as f:
            f.write(datetime.now().strftime('%Y-%m-%d'))
    except Exception as e:
        logger.error(f"Erro ao salvar data da última limpeza: {str(e)}")

def should_run_cleanup():
    """
    Verifica se a limpeza deve ser executada hoje
    """
    last_cleanup = get_last_cleanup_date()
    today = datetime.now().date()
    
    # Se nunca foi executada ou se foi executada em um dia diferente
    return last_cleanup is None or last_cleanup != today

def cleanup_old_messages():
    """
    Remove mensagens antigas (mais de 20 dias) do banco de dados
    """
    try:
        # Verificar se já foi executada hoje
        if not should_run_cleanup():
            return
        
        # Calcular data limite (20 dias atrás)
        cutoff_date = datetime.now() - timedelta(days=20)
        
        # Buscar mensagens antigas
        old_messages = Message.query.filter(
            Message.created_at < cutoff_date
        ).all()
        
        # Contar quantas serão removidas
        count = len(old_messages)
        
        if count > 0:
            # Remover mensagens antigas
            for message in old_messages:
                db.session.delete(message)
            
            db.session.commit()
            logger.info(f"Limpeza automática: {count} mensagens antigas removidas")
        else:
            logger.info("Limpeza automática: Nenhuma mensagem antiga encontrada")
        
        # Marcar que foi executada hoje
        set_last_cleanup_date()
            
    except Exception as e:
        logger.error(f"Erro na limpeza automática de mensagens: {str(e)}")
        db.session.rollback()

def check_and_cleanup():
    """
    Função chamada no primeiro acesso do dia para verificar e executar limpeza
    """
    try:
        if should_run_cleanup():
            cleanup_old_messages()
    except Exception as e:
        logger.error(f"Erro ao verificar limpeza: {str(e)}")

# Funções mantidas para compatibilidade (não usadas mais)
def init_scheduler():
    """
    Função mantida para compatibilidade (não usada)
    """
    logger.info("Scheduler não é mais necessário - usando limpeza no primeiro acesso")
    return None

def start_scheduler():
    """
    Função mantida para compatibilidade (não usada)
    """
    logger.info("Scheduler não é mais necessário - usando limpeza no primeiro acesso")
    return None

def stop_scheduler():
    """
    Função mantida para compatibilidade (não usada)
    """
    logger.info("Scheduler não é mais necessário") 