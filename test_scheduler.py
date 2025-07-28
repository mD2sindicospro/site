#!/usr/bin/env python3
"""
Script para testar a funcionalidade de limpeza automática de mensagens
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.message import Message
from app.scheduler import cleanup_old_messages, should_run_cleanup, get_last_cleanup_date
from datetime import datetime, timedelta

def test_cleanup():
    """Testa a funcionalidade de limpeza automática"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testando Limpeza Automática de Mensagens")
        print("=" * 50)
        
        # Verificar status da limpeza
        last_cleanup = get_last_cleanup_date()
        should_run = should_run_cleanup()
        
        print(f"📅 Última limpeza: {last_cleanup or 'Nunca executada'}")
        print(f"🔄 Deve executar hoje: {'Sim' if should_run else 'Não'}")
        
        # Verificar mensagens existentes
        total_messages = Message.query.count()
        print(f"📊 Total de mensagens no banco: {total_messages}")
        
        # Verificar mensagens antigas
        cutoff_date = datetime.now() - timedelta(days=20)
        old_messages = Message.query.filter(
            Message.created_at < cutoff_date
        ).count()
        print(f"📅 Mensagens com mais de 20 dias: {old_messages}")
        
        if should_run and old_messages > 0:
            print(f"🧹 Executando limpeza automática...")
            cleanup_old_messages()
            
            # Verificar resultado
            new_total = Message.query.count()
            print(f"✅ Limpeza concluída! Mensagens restantes: {new_total}")
            print(f"🗑️  Mensagens removidas: {total_messages - new_total}")
        elif not should_run:
            print("✅ Limpeza já foi executada hoje")
        else:
            print("✅ Nenhuma mensagem antiga encontrada para limpeza")
        
        print("\n📋 Informações do Sistema:")
        print("   • Execução: No primeiro acesso do dia")
        print("   • Critério: Mensagens com mais de 20 dias")
        print("   • Controle: Arquivo last_cleanup.txt")
        print("   • Logs: Registrados no log da aplicação")
        print("   • Segurança: Apenas mensagens antigas são removidas")

if __name__ == "__main__":
    test_cleanup() 