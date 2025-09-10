from app import db
from datetime import datetime

class Exemplo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    situacao = db.Column(db.Text, nullable=False)
    peca_sombra = db.Column(db.String(200), nullable=False)
    resultado = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Exemplo {self.nome}>'

class ExercicioTatico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    posicao_inicial = db.Column(db.Text, nullable=False)  # JSON da posição do tabuleiro
    melhor_lance = db.Column(db.String(10), nullable=False)  # e.g., "e4-e5"
    tipo_tatica = db.Column(db.String(50), nullable=False)  # Pin, Fork, etc
    dificuldade = db.Column(db.String(20), nullable=False)  # Iniciante, Intermediário, Avançado
    pontos = db.Column(db.Integer, default=10)
    dica = db.Column(db.Text, nullable=True)
    explicacao_solucao = db.Column(db.Text, nullable=False)
    jogadas_necessarias = db.Column(db.Integer, default=1)  # Quantas jogadas para resolver
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ExercicioTatico {self.titulo}>'
