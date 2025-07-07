from app import create_app
from app.extensions import db
from app.models.activity import Activity

def update_status_to_standard():
    # Atualizar 'realizada' para 'done'
    atividades_realizada = Activity.query.filter_by(status='realizada').all()
    for atividade in atividades_realizada:
        atividade.status = 'done'
    
    # Atualizar 'approved' para 'done'
    atividades_approved = Activity.query.filter_by(status='approved').all()
    for atividade in atividades_approved:
        atividade.status = 'done'
    
    # Atualizar 'finalizada' para 'done'
    atividades_finalizada = Activity.query.filter_by(status='finalizada').all()
    for atividade in atividades_finalizada:
        atividade.status = 'done'
    
    # Atualizar 'aprovada' para 'done'
    atividades_aprovada = Activity.query.filter_by(status='aprovada').all()
    for atividade in atividades_aprovada:
        atividade.status = 'done'
    
    # Atualizar 'correção' para 'correction'
    atividades_correcao = Activity.query.filter_by(status='correção').all()
    for atividade in atividades_correcao:
        atividade.status = 'correction'
    
    # Commit das mudanças
    db.session.commit()
    
    print(f"Atualizadas {len(atividades_realizada)} atividades de 'realizada' para 'done'.")
    print(f"Atualizadas {len(atividades_approved)} atividades de 'approved' para 'done'.")
    print(f"Atualizadas {len(atividades_finalizada)} atividades de 'finalizada' para 'done'.")
    print(f"Atualizadas {len(atividades_aprovada)} atividades de 'aprovada' para 'done'.")
    print(f"Atualizadas {len(atividades_correcao)} atividades de 'correção' para 'correction'.")
    
    # Verificar se ainda existem status não padronizados
    status_nao_padronizados = Activity.query.filter(
        Activity.status.in_(['realizada', 'approved', 'finalizada', 'aprovada', 'correção'])
    ).all()
    
    if status_nao_padronizados:
        print(f"ATENÇÃO: Ainda existem {len(status_nao_padronizados)} atividades com status não padronizados!")
    else:
        print("Todos os status estão padronizados!")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        update_status_to_standard() 