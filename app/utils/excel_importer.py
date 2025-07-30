import pandas as pd
from datetime import datetime
from app.models.activity import Activity
from app.models.property import Property
from app.models.user import User
from app.extensions import db
import logging

logger = logging.getLogger(__name__)

class ActivityExcelImporter:
    """Classe para importar atividades de arquivos Excel"""
    
    REQUIRED_COLUMNS = ['titulo', 'descricao', 'condominio', 'responsavel', 'data_entrega']
    
    def __init__(self):
        self.errors = []
        self.success_count = 0
        self.total_rows = 0
        self.successful_imports = []
        self.failed_imports = []
    
    def validate_excel_file(self, file_path):
        """Valida se o arquivo Excel tem a estrutura correta"""
        try:
            df = pd.read_excel(file_path)
            
            # Verifica se todas as colunas obrigatórias estão presentes
            missing_columns = []
            for col in self.REQUIRED_COLUMNS:
                if col not in df.columns:
                    missing_columns.append(col)
            
            if missing_columns:
                self.errors.append(f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}")
                return False
            
            # Verifica se há dados no arquivo
            if df.empty:
                self.errors.append("O arquivo está vazio")
                return False
            
            self.total_rows = len(df)
            return True
            
        except Exception as e:
            self.errors.append(f"Erro ao ler arquivo Excel: {str(e)}")
            return False
    
    def find_property_by_name(self, property_name):
        """Encontra uma propriedade pelo nome"""
        return Property.query.filter(
            Property.name.ilike(f"%{property_name}%"),
            Property.is_active == True
        ).first()
    
    def find_user_by_name(self, user_name):
        """Encontra um usuário pelo nome"""
        return User.query.filter(
            User.name.ilike(f"%{user_name}%"),
            User.is_active == True
        ).first()
    
    def parse_date(self, date_value):
        """Converte diferentes formatos de data para datetime.date"""
        if pd.isna(date_value):
            return None
        
        if isinstance(date_value, str):
            # Primeiro tenta DD/MM/AAAA (formato brasileiro)
            try:
                return datetime.strptime(date_value, '%d/%m/%Y').date()
            except ValueError:
                # Depois tenta AAAA-MM-DD (formato ISO)
                try:
                    return datetime.strptime(date_value, '%Y-%m-%d').date()
                except ValueError:
                    return None
        
        if isinstance(date_value, datetime):
            return date_value.date()
        
        return None
    
    def import_activities(self, file_path, created_by_id):
        """Importa atividades do arquivo Excel"""
        if not self.validate_excel_file(file_path):
            return False
        
        df = pd.read_excel(file_path)
        
        for index, row in df.iterrows():
            try:
                # Extrai dados da linha
                title = str(row['titulo']).strip()
                description = str(row['descricao']).strip()
                property_name = str(row['condominio']).strip()
                responsible_name = str(row['responsavel']).strip()
                delivery_date_str = row['data_entrega']
                
                # Validações básicas
                if not title or len(title) < 3:
                    error_msg = f"Título muito curto ou vazio"
                    self.errors.append(f"Linha {index + 2}: {error_msg}")
                    self.failed_imports.append({
                        'linha': index + 2,
                        'titulo': title,
                        'condominio': property_name,
                        'responsavel': responsible_name,
                        'data_entrega': str(delivery_date_str),
                        'erro': error_msg
                    })
                    continue
                
                if not description or len(description) < 10:
                    error_msg = f"Descrição muito curta ou vazia"
                    self.errors.append(f"Linha {index + 2}: {error_msg}")
                    self.failed_imports.append({
                        'linha': index + 2,
                        'titulo': title,
                        'condominio': property_name,
                        'responsavel': responsible_name,
                        'data_entrega': str(delivery_date_str),
                        'erro': error_msg
                    })
                    continue
                
                # Encontra propriedade
                property_obj = self.find_property_by_name(property_name)
                if not property_obj:
                    error_msg = f"Condomínio '{property_name}' não encontrado"
                    self.errors.append(f"Linha {index + 2}: {error_msg}")
                    self.failed_imports.append({
                        'linha': index + 2,
                        'titulo': title,
                        'condominio': property_name,
                        'responsavel': responsible_name,
                        'data_entrega': str(delivery_date_str),
                        'erro': error_msg
                    })
                    continue
                
                # Encontra responsável
                responsible_obj = self.find_user_by_name(responsible_name)
                if not responsible_obj:
                    error_msg = f"Responsável '{responsible_name}' não encontrado"
                    self.errors.append(f"Linha {index + 2}: {error_msg}")
                    self.failed_imports.append({
                        'linha': index + 2,
                        'titulo': title,
                        'condominio': property_name,
                        'responsavel': responsible_name,
                        'data_entrega': str(delivery_date_str),
                        'erro': error_msg
                    })
                    continue
                
                # Processa data de entrega
                delivery_date = self.parse_date(delivery_date_str)
                if not delivery_date:
                    error_msg = f"Data de entrega inválida"
                    self.errors.append(f"Linha {index + 2}: {error_msg}")
                    self.failed_imports.append({
                        'linha': index + 2,
                        'titulo': title,
                        'condominio': property_name,
                        'responsavel': responsible_name,
                        'data_entrega': str(delivery_date_str),
                        'erro': error_msg
                    })
                    continue
                
                # Define status inicial como "em andamento"
                hoje = datetime.now().date()
                status_inicial = 'in_progress'
                if delivery_date < hoje:
                    status_inicial = 'overdue'
                
                # Cria a atividade
                activity = Activity(
                    title=title,
                    description=description,
                    property_id=property_obj.id,
                    responsible_id=responsible_obj.id,
                    delivery_date=delivery_date,
                    status=status_inicial,
                    created_by_id=created_by_id
                )
                
                db.session.add(activity)
                self.success_count += 1
                
                # Registra atividade importada com sucesso
                self.successful_imports.append({
                    'linha': index + 2,
                    'titulo': title,
                    'condominio': property_obj.name,
                    'responsavel': responsible_obj.name,
                    'data_entrega': delivery_date.strftime('%d/%m/%Y'),
                    'status': status_inicial
                })
                
            except Exception as e:
                error_msg = f"Erro inesperado - {str(e)}"
                self.errors.append(f"Linha {index + 2}: {error_msg}")
                self.failed_imports.append({
                    'linha': index + 2,
                    'titulo': title if 'title' in locals() else 'N/A',
                    'condominio': property_name if 'property_name' in locals() else 'N/A',
                    'responsavel': responsible_name if 'responsible_name' in locals() else 'N/A',
                    'data_entrega': str(delivery_date_str) if 'delivery_date_str' in locals() else 'N/A',
                    'erro': error_msg
                })
                continue
        
        # Commit das atividades criadas
        if self.success_count > 0:
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                self.errors.append(f"Erro ao salvar atividades no banco: {str(e)}")
                return False
        
        return True
    
    def get_summary(self):
        """Retorna um resumo da importação"""
        return {
            'total_rows': self.total_rows,
            'success_count': self.success_count,
            'error_count': len(self.errors),
            'errors': self.errors,
            'successful_imports': self.successful_imports,
            'failed_imports': self.failed_imports
        }
    
    def create_template_excel(self, output_path):
        """Cria um arquivo Excel de exemplo com a estrutura correta"""
        template_data = {
            'titulo': ['Limpeza da área comum', 'Manutenção do elevador', 'Verificação do sistema de incêndio'],
            'descricao': [
                'Realizar limpeza completa da área comum incluindo corredores e hall de entrada',
                'Verificar funcionamento do elevador e realizar manutenção preventiva',
                'Testar sistema de incêndio e verificar extintores'
            ],
            'condominio': ['Residencial Exemplo', 'Residencial Exemplo', 'Residencial Exemplo'],
            'responsavel': ['João Silva', 'Maria Santos', 'Pedro Oliveira'],
            'data_entrega': ['31/12/2024', '31/12/2024', '31/12/2024']
        }
        
        df = pd.DataFrame(template_data)
        df.to_excel(output_path, index=False)
        return output_path 