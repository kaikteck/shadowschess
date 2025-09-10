import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyDVvBockK-W45GKypKz7JuxxFSVeSdE6w4"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure for external access
app.config['SERVER_NAME'] = None
app.config['APPLICATION_ROOT'] = '/'

# Add cache control headers
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

# configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///shadows.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# initialize the app with the extension
db.init_app(app)

with app.app_context():
    import models
    db.create_all()

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/teoria', methods=['GET', 'POST'])
def teoria():
    if request.method == 'POST':
        teoria_content = request.form.get('teoria_content', '')
        session['teoria_content'] = teoria_content
        flash('Teoria salva com sucesso!', 'success')
        return redirect(url_for('teoria'))

    teoria_content = session.get('teoria_content', '')
    return render_template('teoria.html', teoria_content=teoria_content)

@app.route('/exemplos', methods=['GET', 'POST'])
def exemplos():
    if request.method == 'POST':
        nome = request.form.get('nome')
        situacao = request.form.get('situacao')
        peca_sombra = request.form.get('peca_sombra')
        resultado = request.form.get('resultado')

        if nome and situacao and peca_sombra and resultado:
            exemplo = models.Exemplo(
                nome=nome,
                situacao=situacao,
                peca_sombra=peca_sombra,
                resultado=resultado
            )
            db.session.add(exemplo)
            db.session.commit()
            flash('Exemplo adicionado com sucesso!', 'success')
        else:
            flash('Por favor, preencha todos os campos.', 'error')

        return redirect(url_for('exemplos'))

    exemplos = models.Exemplo.query.all()
    return render_template('exemplos.html', exemplos=exemplos)

@app.route('/conceitos')
def conceitos():
    return render_template('conceitos.html')

@app.route('/fundamentos')
def fundamentos():
    return render_template('fundamentos.html')

@app.route('/exercicios_fundamentos')
def exercicios_fundamentos():
    return render_template('exercicios_fundamentos.html')

@app.route('/exercicios_conceitos')
def exercicios_conceitos():
    return render_template('exercicios_conceitos.html')

@app.route('/delete_exemplo/<int:id>')
def delete_exemplo(id):
    exemplo = models.Exemplo.query.get_or_404(id)
    db.session.delete(exemplo)
    db.session.commit()
    flash('Exemplo removido com sucesso!', 'success')
    return redirect(url_for('exemplos'))

@app.route('/exercicios')
def exercicios():
    # Verificar se é nível ranking 5000
    nivel = request.args.get('nivel', '')
    
    if nivel == 'ranking5000':
        # Mostrar apenas exercícios ranking 5000
        exercicios = models.ExercicioTatico.query.filter_by(dificuldade='Ranking 5000').order_by(models.ExercicioTatico.pontos.desc()).all()
        
        # Se não existem, inicializar automaticamente
        if not exercicios:
            inicializar_exercicios_ranking5000()
            exercicios = models.ExercicioTatico.query.filter_by(dificuldade='Ranking 5000').order_by(models.ExercicioTatico.pontos.desc()).all()
        
        return render_template('exercicios.html', exercicios=exercicios, nivel_ultra=True)
    else:
        # Mostrar exercícios normais (excluir ranking 5000)
        exercicios = models.ExercicioTatico.query.filter(models.ExercicioTatico.dificuldade != 'Ranking 5000').order_by(models.ExercicioTatico.dificuldade, models.ExercicioTatico.created_at).all()
        return render_template('exercicios.html', exercicios=exercicios, nivel_ultra=False)

@app.route('/exercicios/resolver/<int:id>')
def resolver_exercicio(id):
    exercicio = models.ExercicioTatico.query.get_or_404(id)
    return render_template('resolver_exercicio.html', exercicio=exercicio)

def normalize_move(move):
    """Normaliza a notação de movimento para comparação"""
    if not move:
        return ""
    
    # Remover espaços e converter para minúsculas
    normalized = move.strip().lower()
    
    # Remover símbolos especiais comuns (+, #, !, ?, etc.)
    symbols_to_remove = ['+', '#', '!', '?', '=']
    for symbol in symbols_to_remove:
        normalized = normalized.replace(symbol, '')
    
    # Remover caracteres de captura (x) para comparação mais flexível
    normalized = normalized.replace('x', '')
    
    return normalized

@app.route('/exercicios/verificar', methods=['POST'])
def verificar_exercicio():
    try:
        data = request.get_json()
        exercicio_id = data.get('exercicio_id')
        lance_usuario = data.get('lance')
        
        exercicio = models.ExercicioTatico.query.get_or_404(exercicio_id)
        
        # Normalizar ambos os movimentos para comparação flexível
        lance_normalizado = normalize_move(lance_usuario)
        melhor_lance_normalizado = normalize_move(exercicio.melhor_lance)
        
        # Verificar se o lance está correto (comparação flexível)
        correto = lance_normalizado == melhor_lance_normalizado
        
        # Se não der match exato, tentar variações comuns
        if not correto:
            # Verificar se contém o movimento correto
            correto = (melhor_lance_normalizado in lance_normalizado or 
                      lance_normalizado in melhor_lance_normalizado)
        
        if correto:
            response = {
                'correto': True,
                'pontos': exercicio.pontos,
                'explicacao': exercicio.explicacao_solucao,
                'tipo_tatica': exercicio.tipo_tatica
            }
        else:
            response = {
                'correto': False,
                'dica': exercicio.dica,
                'melhor_lance': exercicio.melhor_lance
            }
            
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Erro ao verificar exercício: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/exercicios/resposta_inimigo', methods=['POST'])
def resposta_inimigo():
    try:
        data = request.get_json()
        posicao_atual = data.get('posicao')
        lance_usuario = data.get('lance')
        tipo_tatica = data.get('tipo_tatica', '')
        
        # Contexto especializado para análise tática
        context = f"""
        Você é o "Rei do Mate", especialista em xadrez e na estratégia "In the Shadows".
        
        SITUAÇÃO ATUAL:
        - Usuário jogou: {lance_usuario}
        - Tipo de tática em questão: {tipo_tatica}
        - Posição atual do tabuleiro: {posicao_atual}
        
        RESPONDA COMO UM ADVERSÁRIO EXPERIENTE:
        - Analise o lance do usuário
        - Explique qual seria sua resposta como adversário
        - Mencione se o lance criou uma ameaça real
        - Seja direto e técnico
        - Máximo 3 frases
        """
        
        prompt = f"{context}\n\nAnálise tática:"
        
        response = model.generate_content(prompt)
        ai_response = response.text
        
        return jsonify({
            'resposta': ai_response,
            'tipo': 'analise_tatica'
        })
        
    except Exception as e:
        logging.error(f"Erro na resposta do adversário: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/reflexoes')
def reflexoes():
    return render_template('reflexoes.html')

@app.route('/inicializar_exercicios')
def inicializar_exercicios():
    """Rota para inicializar exercicios basicos no banco de dados"""
    try:
        # Verificar se ja existem exercicios
        if models.ExercicioTatico.query.count() > 0:
            return jsonify({'message': 'Exercicios ja existem no banco'})
        
        # EXERCICIOS TATICOS GERAIS - versao simples
        exercicios = []
        
        exercicios.append(models.ExercicioTatico(
            titulo='Pin Basico',
            descricao='Torre crava cavalo que defende o rei',
            posicao_inicial='{"a1":"wR","b1":"wN","c1":"wB","d1":"wQ","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","b2":"wP","c2":"wP","d2":"wP","f2":"wP","g2":"wP","h2":"wP","e4":"wP","d5":"wR","a8":"bR","b8":"bN","c8":"bB","d8":"bQ","e8":"bK","f8":"bB","h8":"bR","a7":"bP","b7":"bP","c7":"bP","d7":"bP","f7":"bP","g7":"bP","h7":"bP","e5":"bP","e6":"bN","g8":"bN"}',
            melhor_lance='Re5',
            tipo_tatica='Pin',
            dificuldade='Iniciante',
            pontos=12,
            dica='A torre pode criar uma linha de ataque.',
            explicacao_solucao='Re5 crava o cavalo na coluna e, impedindo sua movimentacao.',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Fork com Cavalo',
            descricao='Ataque duplo contra rei e dama',
            posicao_inicial='{"a1":"wR","b1":"wN","c1":"wB","d1":"wQ","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wN","e4":"wP","a8":"bR","b8":"bN","c8":"bB","d8":"bQ","e8":"bK","f8":"bB","g8":"bN","h8":"bR","a7":"bP","b7":"bP","f7":"bP","g7":"bP","h7":"bP","d5":"bP","c6":"bQ","e6":"bP"}',
            melhor_lance='Ne6+',
            tipo_tatica='Fork',
            dificuldade='Iniciante',
            pontos=15,
            dica='O cavalo pode atacar duas pecas simultaneamente.',
            explicacao_solucao='Ne6+ ataca rei e dama ao mesmo tempo.',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Deflexao da Torre',
            descricao='Force a torre a abandonar a defesa',
            posicao_inicial='{"a1":"wK","h1":"wR","e1":"wQ","e8":"bK","e7":"bR","f7":"bP","g7":"bP","h7":"bP"}',
            melhor_lance='Qe5+',
            tipo_tatica='Deflexao',
            dificuldade='Intermediario',
            pontos=20,
            dica='Force a torre a sair da defesa com xeque.',
            explicacao_solucao='Qe5+ obriga torre a se mover e abandona defesa.',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Ataque Descoberto',
            descricao='Bispo revela ataque da torre',
            posicao_inicial='{"a1":"wK","c1":"wB","d1":"wR","e8":"bK","e6":"bQ","f7":"bP","g7":"bP","h7":"bP"}',
            melhor_lance='Be3+',
            tipo_tatica='Descoberta',
            dificuldade='Intermediario',
            pontos=18,
            dica='Mova o bispo revelando ataque da torre.',
            explicacao_solucao='Be3+ revela xeque da torre e ataca dama.',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Sacrificio de Dama',
            descricao='Ofereca a dama para mate forcado',
            posicao_inicial='{"a1":"wK","d1":"wQ","h1":"wR","e8":"bK","f8":"bR","g8":"bN","f7":"bP","g7":"bP","h7":"bP"}',
            melhor_lance='Qd8+',
            tipo_tatica='Sacrificio',
            dificuldade='Avancado',
            pontos=25,
            dica='Sacrifique a dama para conseguir mate.',
            explicacao_solucao='Qd8+ forca Rxd8 e depois Rxd8 e mate.',
            jogadas_necessarias=2
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Cravada Absoluta',
            descricao='Bispo crava torre na diagonal do rei',
            posicao_inicial='{"a1":"wR","b1":"wN","c1":"wB","d1":"wQ","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","b2":"wP","c2":"wP","d2":"wP","f2":"wP","g2":"wP","h2":"wP","e4":"wP","a8":"bR","b8":"bN","c8":"bB","d8":"bQ","e8":"bK","f8":"bB","g8":"bN","h8":"bR","a7":"bP","b7":"bP","c7":"bP","d7":"bP","f7":"bP","g7":"bP","h7":"bP","e5":"bR","d6":"bP","f6":"bP"}',
            melhor_lance='Bb5',
            tipo_tatica='Pin',
            dificuldade='Intermediario',
            pontos=18,
            dica='Diagonal perfeita para cravada absoluta.',
            explicacao_solucao='Bb5 crava torre que nao pode se mover.',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Garfo de Peao',
            descricao='Peao ataca duas pecas pesadas simultaneamente',
            posicao_inicial='{"a1":"wR","b1":"wN","c1":"wB","d1":"wQ","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wP","e4":"wP","a8":"bR","b8":"bN","c8":"bB","d8":"bQ","e8":"bK","f8":"bB","g8":"bN","h8":"bR","a7":"bP","b7":"bP","f7":"bP","g7":"bP","h7":"bP","c5":"bQ","e5":"bR","d6":"bP"}',
            melhor_lance='d5',
            tipo_tatica='Fork',
            dificuldade='Intermediario',
            pontos=16,
            dica='O peao pode ser muito poderoso em ataques duplos.',
            explicacao_solucao='d5 ataca dama e torre ao mesmo tempo.',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Xeque Descoberto Duplo',
            descricao='Cavalo revela xeque e ataca simultaneamente',
            posicao_inicial='{"a1":"wK","b1":"wR","d3":"wN","e8":"bK","c5":"bQ","f7":"bP","g7":"bP","h7":"bP"}',
            melhor_lance='Ne5+',
            tipo_tatica='Descoberta',
            dificuldade='Avancado',
            pontos=22,
            dica='Cavalo pode dar xeque e atacar dama ao mesmo tempo.',
            explicacao_solucao='Ne5+ da xeque descoberto e ataca dama.',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Deflexao do Bispo',
            descricao='Remova o defensor da diagonal critica',
            posicao_inicial='{"a1":"wK","c1":"wQ","e3":"bB","f2":"bP","h2":"bK","g1":"wR"}',
            melhor_lance='Qc8+',
            tipo_tatica='Deflexao',
            dificuldade='Avancado',
            pontos=25,
            dica='Ataque o rei para deflexionar o bispo.',
            explicacao_solucao='Qc8+ forca bispo sair e permite Rg8#.',
            jogadas_necessarias=2
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Sacrificio de Torre',
            descricao='Torre se sacrifica para abrir linhas decisivas',
            posicao_inicial='{"a1":"wK","a8":"wR","e1":"wQ","g1":"wB","h8":"bK","g8":"bR","h7":"bP","g7":"bP","f7":"bP"}',
            melhor_lance='Rxg8+',
            tipo_tatica='Sacrificio',
            dificuldade='Intermediario',
            pontos=20,
            dica='Sacrifique torre para abrir coluna h.',
            explicacao_solucao='Rxg8+ Hxg8 e Qh1 e mate.',
            jogadas_necessarias=2
        ))
        
        # EXERCICIOS IN THE SHADOWS - versao simples
        exercicios.append(models.ExercicioTatico(
            titulo='Torre nas Sombras',
            descricao='Peca oculta decide a partida',
            posicao_inicial='{"a1":"wK","a8":"wR","b1":"wN","c1":"wB","e1":"wQ","h8":"bK","h7":"bP","g7":"bP","f7":"bP","e7":"bQ","d7":"bR","c6":"bN"}',
            melhor_lance='Nc3',
            tipo_tatica='In the Shadows',
            dificuldade='Avancado',
            pontos=35,
            dica='O cavalo aparentemente passivo revela linha mortal.',
            explicacao_solucao='Nc3 parece passivo mas revela ataque da torre!',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Bispo Fantasma',
            descricao='Estrategia In the Shadows - peca escondida ataca',
            posicao_inicial='{"a1":"wK","c1":"wB","e1":"wQ","g1":"wN","h1":"wR","a8":"bK","c8":"bB","d8":"bQ","e8":"bR","f8":"bB","g8":"bN","h8":"bR","d4":"wP","e5":"bP","f6":"bN","c6":"bQ"}',
            melhor_lance='Nf5',
            tipo_tatica='In the Shadows',
            dificuldade='Avancado',
            pontos=40,
            dica='Movimento de cavalo revela bispo oculto decisivo.',
            explicacao_solucao='Nf5 libera diagonal do bispo atacando dama!',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Dama Sombria',
            descricao='Sacrificio revela peca oculta devastadora',
            posicao_inicial='{"a1":"wK","b1":"wQ","c1":"wB","h1":"wR","a8":"bK","c8":"bR","d8":"bQ","e8":"bB","f8":"bN","g8":"bR","h8":"bN","e5":"wN","f6":"bP","g6":"bP","h6":"bP","c6":"bN","d6":"bP"}',
            melhor_lance='Nxd6+',
            tipo_tatica='In the Shadows',
            dificuldade='Expert',
            pontos=50,
            dica='Sacrificio do cavalo revela a dama escondida.',
            explicacao_solucao='Nxd6+ sacrifica cavalo mas revela ataque devastador da dama!',
            jogadas_necessarias=2
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Cavalo Oculto Letal',
            descricao='Movimento aparentemente defensivo esconde ataque mortal',
            posicao_inicial='{"a1":"wK","b3":"wN","c2":"wB","d1":"wQ","h1":"wR","a8":"bK","b8":"bQ","c8":"bR","d8":"bB","f8":"bN","g8":"bR","h8":"bN","e4":"bP","f7":"bP","g7":"bP","h7":"bP"}',
            melhor_lance='Nd4',
            tipo_tatica='In the Shadows',
            dificuldade='Avancado',
            pontos=45,
            dica='Cavalo move-se silenciosamente mas revela linha do bispo.',
            explicacao_solucao='Nd4 parece neutro mas libera Bh8# atraves da diagonal!',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Torre Invisivel',
            descricao='Peao move e revela torre escondida ha varias jogadas',
            posicao_inicial='{"a1":"wK","a4":"wR","b2":"wP","e1":"wQ","g1":"wB","h1":"wN","a8":"bK","b8":"bQ","c8":"bR","d8":"bB","e8":"bR","f8":"bN","g8":"bN","h8":"bR","b7":"bP","c7":"bP","d7":"bP"}',
            melhor_lance='b4',
            tipo_tatica='In the Shadows',
            dificuldade='Expert',
            pontos=55,
            dica='O peao simples esconde uma torre que espera ha tempo.',
            explicacao_solucao='b4 libera a4-a8 e torre da mate em Ra8#!',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Dama Espectral',
            descricao='Recuo tatico revela dama que estava nas sombras',
            posicao_inicial='{"a1":"wK","c3":"wQ","e3":"wB","g1":"wN","h1":"wR","a8":"bK","b8":"bR","c8":"bQ","d8":"bB","e8":"bR","f8":"bN","g8":"bN","h8":"bR","d5":"bP","e6":"bP","f7":"bP","g7":"bP","h7":"bP"}',
            melhor_lance='Bd2',
            tipo_tatica='In the Shadows',
            dificuldade='Expert',
            pontos=48,
            dica='Bispo recua mas revela linha mortal da dama.',
            explicacao_solucao='Bd2 parece recuo mas libera Qc8# - mate inevitavel!',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Rei Sombrio',
            descricao='O proprio rei move e revela peca oculta decisiva',
            posicao_inicial='{"a2":"wK","b1":"wQ","c1":"wR","d1":"wB","e1":"wN","f1":"wR","g1":"wB","h1":"wN","a8":"bK","b8":"bQ","c8":"bR","d8":"bB","e8":"bR","f8":"bN","g8":"bN","h8":"bR","d4":"bP","e5":"bP","f6":"bP"}',
            melhor_lance='Ka3',
            tipo_tatica='In the Shadows',
            dificuldade='Master',
            pontos=60,
            dica='O rei move estrategicamente revelando linha da torre.',
            explicacao_solucao='Ka3 libera Rc8# - o rei escondeu a torre decisiva!',
            jogadas_necessarias=1
        ))
        
        # EXERCICIOS DE AVALIACAO DE POSICAO
        exercicios.append(models.ExercicioTatico(
            titulo='Quem esta melhor?',
            descricao='Avalie esta posicao e determine quem tem vantagem',
            posicao_inicial='{"a1":"wR","e1":"wK","h1":"wR","c1":"wB","g1":"wN","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wP","e4":"wP","a8":"bR","e8":"bK","h8":"bR","f8":"bB","b8":"bN","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","d5":"bP","e5":"bP"}',
            melhor_lance='f3',
            tipo_tatica='Avaliacao',
            dificuldade='Intermediario',
            pontos=15,
            dica='Analise espacos, desenvolvimento e estrutura de peoes.',
            explicacao_solucao='Posicao equilibrada, f3 prepara Be3 melhorando a posicao.',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Vantagem Posicional',
            descricao='Identifique o principal fator posicional nesta posicao',
            posicao_inicial='{"a1":"wR","e1":"wK","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","c4":"wB","e4":"wP","f4":"wP","a8":"bR","e8":"bK","a7":"bP","b7":"bP","c7":"bP","e6":"bP","f7":"bP","g7":"bP","h7":"bP","d6":"bB"}',
            melhor_lance='Bd5',
            tipo_tatica='Avaliacao',
            dificuldade='Avancado',
            pontos=20,
            dica='Procure pela peca mais ativa que pode ser centralizada.',
            explicacao_solucao='Bd5 centraliza o bispo dominando o tabuleiro.',
            jogadas_necessarias=1
        ))
        
        # EXERCICIOS DE ABERTURA
        exercicios.append(models.ExercicioTatico(
            titulo='Abertura Italiana',
            descricao='Complete o desenvolvimento classico da abertura italiana',
            posicao_inicial='{"a1":"wR","b1":"wN","c1":"wB","d1":"wQ","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","e4":"wP","c4":"wB","f3":"wN","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","e5":"bP","c5":"bB","f6":"bN","a8":"bR","b8":"bN","c8":"bB","d8":"bQ","e8":"bK","f8":"bB","g8":"bN","h8":"bR"}',
            melhor_lance='d3',
            tipo_tatica='Abertura',
            dificuldade='Intermediario',
            pontos=12,
            dica='Controle o centro com peoes e prepare o roque.',
            explicacao_solucao='d3 apoia e4 e prepara desenvolvimento harmonioso.',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Defesa Francesa',
            descricao='Encontre o melhor plano para as pretas na defesa francesa',
            posicao_inicial='{"a1":"wR","b1":"wN","c1":"wB","d1":"wQ","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wP","e5":"wP","a7":"bP","b7":"bP","c7":"bP","d7":"bP","f7":"bP","g7":"bP","h7":"bP","e6":"bP","a8":"bR","b8":"bN","c8":"bB","d8":"bQ","e8":"bK","f8":"bB","g8":"bN","h8":"bR"}',
            melhor_lance='c5',
            tipo_tatica='Abertura',
            dificuldade='Avancado',
            pontos=18,
            dica='Ataque o centro branco pela lateral.',
            explicacao_solucao='c5 pressiona d4 seguindo principios da francesa.',
            jogadas_necessarias=1
        ))
        
        # EXERCICIOS DE FINAIS
        exercicios.append(models.ExercicioTatico(
            titulo='Final Rei e Peao',
            descricao='Conduza este final basico para a vitoria',
            posicao_inicial='{"e5":"wK","e4":"wP","e7":"bK","b6":"bP","g6":"bP","h7":"bP"}',
            melhor_lance='Kd6',
            tipo_tatica='Final',
            dificuldade='Iniciante',
            pontos=10,
            dica='O rei deve liderar o avanco do peao.',
            explicacao_solucao='Kd6 apoia o peao e impede o rei negro, garantindo a promocao.',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Torre vs Peoes',
            descricao='Use a torre para parar os peoes conectados',
            posicao_inicial='{"a1":"wK","h1":"wR","a7":"wP","b7":"wP","e8":"bK","e4":"bP","f4":"bP","g7":"bP","h7":"bP"}',
            melhor_lance='Re1',
            tipo_tatica='Final',
            dificuldade='Intermediario',
            pontos=16,
            dica='Posicione a torre atras dos peoes.',
            explicacao_solucao='Re1 para os peoes conectados, controlando a coluna e.',
            jogadas_necessarias=1
        ))
        
        # EXERCICIOS DE ESTRATEGIA
        exercicios.append(models.ExercicioTatico(
            titulo='Casa Fraca',
            descricao='Identifique e ocupe a melhor casa para seu cavalo',
            posicao_inicial='{"a1":"wR","e1":"wK","f1":"wR","g1":"wN","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wP","e5":"wN","a8":"bR","e8":"bK","f8":"bR","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","d5":"bP","f6":"bP"}',
            melhor_lance='Nd7',
            tipo_tatica='Estrategia',
            dificuldade='Avancado',
            pontos=22,
            dica='Procure uma casa central bem protegida.',
            explicacao_solucao='Nd7 ocupa casa dominante no campo inimigo.',
            jogadas_necessarias=1
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Estrutura de Peoes',
            descricao='Melhore sua estrutura atacando a cadeia inimiga',
            posicao_inicial='{"a1":"wR","e1":"wK","h1":"wR","a2":"wP","b3":"wP","c2":"wP","d4":"wP","f2":"wP","g2":"wP","h2":"wP","a8":"bR","e8":"bK","h8":"bR","a7":"bP","b7":"bP","c6":"bP","d5":"bP","f7":"bP","g7":"bP","h7":"bP"}',
            melhor_lance='c4',
            tipo_tatica='Estrategia',
            dificuldade='Intermediario',
            pontos=14,
            dica='Ataque a base da cadeia de peoes.',
            explicacao_solucao='c4 quebra a estrutura preta em c6-d5.',
            jogadas_necessarias=1
        ))
        
        # EXERCICIOS DE CALCULO
        exercicios.append(models.ExercicioTatico(
            titulo='Calculo de Variantes',
            descricao='Analise todas as continuacoes possivel nesta posicao',
            posicao_inicial='{"a1":"wR","e1":"wK","h1":"wR","c1":"wB","f3":"wN","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","e4":"wP","a8":"bR","e8":"bK","h8":"bR","c8":"bB","f6":"bN","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","e5":"bP"}',
            melhor_lance='Ng5',
            tipo_tatica='Calculo',
            dificuldade='Avancado',
            pontos=25,
            dica='Considere todas as respostas do adversario.',
            explicacao_solucao='Ng5 cria multiplas ameacas que o negro nao pode parar todas.',
            jogadas_necessarias=2
        ))
        
        exercicios.append(models.ExercicioTatico(
            titulo='Forcando Sequencias',
            descricao='Encontre a sequencia forzada que leva vantagem',
            posicao_inicial='{"a1":"wK","d1":"wQ","h1":"wR","e8":"bK","f8":"bR","f7":"bP","g7":"bP","h7":"bP","a7":"bP","b7":"bP","c7":"bP","d7":"bP","e7":"bP"}',
            melhor_lance='Qd8+',
            tipo_tatica='Calculo',
            dificuldade='Avancado',
            pontos=30,
            dica='Comece com xeque e calcule ate o fim.',
            explicacao_solucao='Qd8+ Rxd8 Rxd8# e mate em 3 lances.',
            jogadas_necessarias=3
        ))
        
        for ex in exercicios:
            db.session.add(ex)
        
        db.session.commit()
        
        return jsonify({'message': f'Criados {len(exercicios)} exercicios com sucesso!'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao inicializar exercicios: {str(e)}")
        return jsonify({'error': f'Erro: {str(e)}'}), 500

@app.route('/limpar_exercicios')
def limpar_exercicios():
    """Rota para limpar todos os exercícios do banco de dados"""
    try:
        models.ExercicioTatico.query.delete()
        db.session.commit()
        return jsonify({'message': 'Exercícios limpos com sucesso!'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao limpar exercícios: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/inicializar_exercicios_ranking5000')
def inicializar_exercicios_ranking5000():
    """Exercicios Ranking 5000 - Alem da Compreensao Humana"""
    try:
        # Limpar exercicios ranking 5000 existentes primeiro
        models.ExercicioTatico.query.filter_by(dificuldade='Ranking 5000').delete()
        db.session.commit()
        
        exercicios_ultra = []
        
        # Exercicios baseados no texto do usuario: "Alem da compreensao humana"
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='O Eco das Sombras',
            descricao='Encontre sequencia de 4 lances onde cada movimento ecoa o anterior, forcando mate. Visualize 16 posicoes simultaneamente.',
            posicao_inicial='{"a1":"wR","c1":"wB","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wQ","e4":"wP","c6":"wN","a8":"bR","c8":"bB","e8":"bK","f8":"bB","g8":"bN","h8":"bR","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","d5":"bQ","e5":"bP"}',
            melhor_lance='Qxd5+',
            tipo_tatica='Calculo Multidimensional',
            dificuldade='Ranking 5000',
            pontos=2500,
            dica='Primeiro lance ecoa nos seguintes. Ondas de pressao se amplificam.',
            explicacao_solucao='Qxd5+ Kf8 forcado, Qf7+ Ke8 forcado, Qe6+ Kf8 forcado, Qf7# mate final.',
            jogadas_necessarias=4
        ))
        
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='Danca dos Cavalos Impossivel',
            descricao='Dois cavalos em sincronizacao perfeita criam armadilha forcando mate em 5 lances com 8 variantes principais.',
            posicao_inicial='{"b1":"wN","e1":"wK","g1":"wN","a1":"wR","h1":"wR","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wP","e4":"wP","b8":"bN","e8":"bK","g8":"bN","a8":"bR","h8":"bR","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","d5":"bP","e5":"bP"}',
            melhor_lance='Nc3',
            tipo_tatica='Coordenacao Transcendental',
            dificuldade='Ranking 5000',
            pontos=3000,
            dica='Cavalos dancam em harmonia. Apenas mentes transcendentais veem a armadilha.',
            explicacao_solucao='Nc3 prepara Nd5 e Ne4 simultaneamente, criando rede que forca mate.',
            jogadas_necessarias=5
        ))
        
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='Sacrificio da Eternidade',
            descricao='Sacrifique peca mais valiosa em posicao aparentemente absurda, mas que leva a mate forcado em 3 lances.',
            posicao_inicial='{"a1":"wR","e1":"wK","f1":"wR","c1":"wB","d1":"wQ","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","e4":"wP","h4":"wP","a8":"bR","e8":"bK","h8":"bR","c8":"bB","d8":"bQ","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","e5":"bP","g6":"bP"}',
            melhor_lance='Qh5+',
            tipo_tatica='Sacrificio Transcendental',
            dificuldade='Ranking 5000',
            pontos=2800,
            dica='Dama deve morrer para vitoria nascer. Desafia logica xadrezistica conhecida.',
            explicacao_solucao='Qh5+ gxh5 forcado, Rxf7+ Kxf7, Re7# mate inevitavel.',
            jogadas_necessarias=3
        ))
        
        # Calculos mentais sem tabuleiro
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='Cidade das Pecas Invisiveis',
            descricao='OLHOS FECHADOS: Visualize posicao e calcule 12 lances mantendo todas 64 casas na memoria simultaneamente.',
            posicao_inicial='{"mental":"posicao_complexa","cavalo":"f3","bispo":"c5","dama":"d1","rei":"e8"}',
            melhor_lance='Mental: Ng5',
            tipo_tatica='Visualizacao Absoluta',
            dificuldade='Ranking 5000',
            pontos=3500,
            dica='Execute sem ver tabuleiro. Mantenha TODAS as 64 casas na mente.',
            explicacao_solucao='Ng5 inicia sequencia que culmina em mate forcado 12 lances adiante.',
            jogadas_necessarias=12
        ))
        
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='Arquitetura de Variantes',
            descricao='Calcule mentalmente 5 linhas de jogo diferentes simultaneamente, mantendo todas posicoes na memoria por 10 minutos.',
            posicao_inicial='{"mental":"meio_jogo","tensoes":"multiplas_simultaneas"}',
            melhor_lance='Mental: Multiplas linhas',
            tipo_tatica='Processamento Paralelo',
            dificuldade='Ranking 5000',
            pontos=4000,
            dica='Mente processa 5 partidas simultaneamente. Humanos nao conseguem.',
            explicacao_solucao='5 linhas convergem para vitoria, provando mesmo resultado por caminhos diferentes.',
            jogadas_necessarias=8
        ))
        
        # Desafios de percepcao de erros sutis
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='O Erro que Ninguem Ve',
            descricao='Posicao parece equilibrada, mas tem erro sutil que apenas 1 em 10.000 mestres detecta. Encontre erro oculto.',
            posicao_inicial='{"a1":"wR","c1":"wB","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","b2":"wP","c2":"wP","d2":"wQ","e2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wP","a8":"bR","c8":"bB","e8":"bK","f8":"bB","g8":"bN","h8":"bR","a7":"bP","b7":"bP","c7":"bP","d7":"bQ","e7":"bP","f7":"bP","g7":"bP","h7":"bP","d5":"bP"}',
            melhor_lance='Qd3',
            tipo_tatica='Percepcao Ultra-Agucada',
            dificuldade='Ranking 5000',
            pontos=3200,
            dica='Erro escondido na estrutura. Nao e ameaca obvia, mas vulnerabilidade microscopica.',
            explicacao_solucao='Qd3 explora fragilidade da casa c4 indefesa ha 3 lances, criando pressao invisivel.',
            jogadas_necessarias=1
        ))
        
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='A Fissura no Tempo',
            descricao='Posicao parece solida mas ha janela de 1 lance onde tudo desmorona. Se nao encontrar agora, oportunidade se perde.',
            posicao_inicial='{"a1":"wR","b1":"wN","e1":"wK","f1":"wR","c1":"wB","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","e4":"wP","g4":"wP","a8":"bR","b8":"bN","e8":"bK","h8":"bR","f8":"bB","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","e5":"bP","g6":"bP"}',
            melhor_lance='g5',
            tipo_tatica='Timing Critico',
            dificuldade='Ranking 5000',
            pontos=2900,
            dica='Existe apenas 1 momento onde vitoria e possivel. Este e o momento.',
            explicacao_solucao='g5 quebra estrutura preta no momento exato, criando avalanche de fraquezas.',
            jogadas_necessarias=1
        ))
        
        # Oportunidades ocultas - lances absurdos que funcionam
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='A Loucura que Vence',
            descricao='Lance parece suicidio completo. Jogador humano rejeitaria instantaneamente. Mas e a unica vitoria possivel.',
            posicao_inicial='{"a1":"wR","e1":"wK","h1":"wR","d1":"wQ","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","e4":"wP","d4":"wP","a8":"bR","e8":"bK","h8":"bR","d8":"bQ","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","e5":"bP","d5":"bP"}',
            melhor_lance='Kf1',
            tipo_tatica='Paradoxo Absoluto',
            dificuldade='Ranking 5000',
            pontos=3800,
            dica='Movimento vai contra TODOS principios do xadrez. Genial de forma que humanos nao processam.',
            explicacao_solucao='Kf1 prepara armadilha profunda que leva 15 lances para manifestar, mas garante vitoria.',
            jogadas_necessarias=1
        ))
        
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='O Retrocesso da Vitoria',
            descricao='Mova peca para TRAS quando toda logica diz para avancar. Movimento quebra leis do progresso mas cria vitoria.',
            posicao_inicial='{"a1":"wR","c1":"wB","e1":"wK","g1":"wN","h1":"wR","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wQ","e4":"wP","f5":"wB","a8":"bR","c8":"bB","e8":"bK","g8":"bN","h8":"bR","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","d5":"bQ","e5":"bP"}',
            melhor_lance='Bf4',
            tipo_tatica='Regressao Genial',
            dificuldade='Ranking 5000',
            pontos=3400,
            dica='Va para tras para conquistar o futuro. Conceito transcende logica linear humana.',
            explicacao_solucao='Bf4 recua para criar bateria devastadora com dama, forcando mate em 6 lances.',
            jogadas_necessarias=1
        ))
        
        # Treinos de finais transcendentais
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='Final dos 64 Futuros',
            descricao='Final tem 64 desfechos diferentes dependendo de micro-variacoes. Deve calcular TODOS simultaneamente.',
            posicao_inicial='{"a1":"wK","h1":"wR","a8":"bK","b7":"bP","c6":"bP"}',
            melhor_lance='Kd2',
            tipo_tatica='Final Multiversal',
            dificuldade='Ranking 5000',
            pontos=4500,
            dica='Cada casa que rei escolhe cria realidade diferente. Deve dominar todas realidades.',
            explicacao_solucao='Kd2 e unica jogada que vence em TODOS os 64 cenarios possiveis, controlando espaco-tempo.',
            jogadas_necessarias=1
        ))
        
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='Zugzwang Dimensional',
            descricao='Crie posicao onde adversario esta em zugzwang em 8 dimensoes diferentes simultaneamente.',
            posicao_inicial='{"a1":"wK","b1":"wR","h8":"bK","a7":"bR","g7":"bP"}',
            melhor_lance='Rb8+',
            tipo_tatica='Zugzwang Absoluto',
            dificuldade='Ranking 5000',
            pontos=3900,
            dica='Forca adversario a piorar posicao em multiplas dimensoes simultaneamente.',
            explicacao_solucao='Rb8+ forca Ka7 e cada resposta possivel piora posicao preta exponencialmente.',
            jogadas_necessarias=1
        ))
        
        # Desafios de visao e memoria
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='Snapshot Quantico',
            descricao='OLHE posicao por 3 segundos. Feche olhos e reconstrua PERFEITAMENTE todas 32 pecas apos 5 minutos.',
            posicao_inicial='{"a1":"wR","b1":"wN","c1":"wB","d1":"wQ","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wP","e4":"wP","b5":"wP","c6":"wN","a8":"bR","c8":"bB","d8":"bQ","e8":"bK","f8":"bB","g8":"bN","h8":"bR","a7":"bP","b7":"bP","c7":"bP","e7":"bP","f7":"bP","g7":"bP","h7":"bP","d5":"bP","e5":"bN"}',
            melhor_lance='Memoria Perfeita',
            tipo_tatica='Fotografia Mental',
            dificuldade='Ranking 5000',
            pontos=5000,
            dica='Mente funciona como camera quantica, capturando informacao alem da capacidade humana.',
            explicacao_solucao='Reconstrucao 100% precisa de todas posicoes apos tempo determinado. Erro = falha completa.',
            jogadas_necessarias=1
        ))
        
        
        # Exercicios finais mais simples para completar a lista
        exercicios_ultra.append(models.ExercicioTatico(
            titulo='A Singularidade Final',
            descricao='Exercicio final onde todas tecnicas se fundem numa jogada que transcende categorias conhecidas.',
            posicao_inicial='{"a1":"wK","h8":"bK","d4":"wQ","e7":"bQ"}',
            melhor_lance='Qd8+',
            tipo_tatica='Singularidade',
            dificuldade='Ranking 5000',
            pontos=10000,
            dica='Lance nao pode ser explicado por teoria conhecida. E transcendencia pura.',
            explicacao_solucao='Solucao esta alem das palavras. Apenas quem alcancou singularidade compreende.',
            jogadas_necessarias=1
        ))
        
        # Adicionar um por vez ao banco para evitar erros
        count = 0
        for ex in exercicios_ultra:
            try:
                db.session.add(ex)
                db.session.commit()
                count += 1
            except Exception as e:
                db.session.rollback()
                logging.warning(f"Erro ao adicionar exercicio {ex.titulo}: {str(e)}")
                continue
        
        return jsonify({'message': f'Criados {count} exercicios RANKING 5000 - Alem da Compreensao Humana!'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao criar exercicios ranking 5000: {str(e)}")
        return jsonify({'error': f'Erro: {str(e)}'}), 500

@app.route('/adicionar_exercicios_variados')
def adicionar_exercicios_variados():
    """Adiciona exercícios variados além de puzzles táticos"""
    try:
        # Verificar se exercicios variados ja existem
        exercicios_variados = models.ExercicioTatico.query.filter(
            models.ExercicioTatico.tipo_tatica.in_(['Abertura', 'Final', 'Estrategia', 'Calculo', 'Avaliacao'])
        ).count()
        
        if exercicios_variados > 0:
            return jsonify({'message': 'Exercicios variados ja existem no banco'})
        
        novos_exercicios = []
        
        # EXERCICIOS DE ABERTURA
        novos_exercicios.append(models.ExercicioTatico(
            titulo='Gambito da Rainha Aceito',
            descricao='Como recuperar o peao sacrificado na abertura',
            posicao_inicial='{"a1":"wR","b1":"wN","c1":"wB","d1":"wQ","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","b2":"wP","e2":"wP","f2":"wP","g2":"wP","h2":"wP","c4":"bP","d4":"wP","a7":"bP","b7":"bP","c7":"bP","d7":"bP","e7":"bP","f7":"bP","g7":"bP","h7":"bP","a8":"bR","b8":"bN","c8":"bB","d8":"bQ","e8":"bK","f8":"bB","g8":"bN","h8":"bR"}',
            melhor_lance='e3',
            tipo_tatica='Abertura',
            dificuldade='Intermediario',
            pontos=15,
            dica='Desenvolva e prepare a recuperacao do peao.',
            explicacao_solucao='e3 prepara Bxc4 para recuperar o peao.',
            jogadas_necessarias=1
        ))
        
        novos_exercicios.append(models.ExercicioTatico(
            titulo='Defesa Siciliana - Dragão',
            descricao='Encontre o melhor desenvolvimento para as pretas',
            posicao_inicial='{"a1":"wR","b1":"wN","c1":"wB","d1":"wQ","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wN","e4":"wP","c5":"bP","d6":"bP","g6":"bP","a7":"bP","b7":"bP","e7":"bP","f7":"bP","h7":"bP","a8":"bR","b8":"bN","c8":"bB","d8":"bQ","e8":"bK","f8":"bB","g8":"bN","h8":"bR"}',
            melhor_lance='Bg7',
            tipo_tatica='Abertura',
            dificuldade='Avancado',
            pontos=20,
            dica='Fianchetto do bispo para controlar a diagonal longa.',
            explicacao_solucao='Bg7 ativa o bispo na diagonal longa a1-h8.',
            jogadas_necessarias=1
        ))
        
        # EXERCICIOS DE FINAIS
        novos_exercicios.append(models.ExercicioTatico(
            titulo='Final Rei e Peão',
            descricao='Promova o peao para ganhar o final',
            posicao_inicial='{"e1":"wK","e5":"wP","e8":"bK"}',
            melhor_lance='Kd6',
            tipo_tatica='Final',
            dificuldade='Iniciante',
            pontos=12,
            dica='O rei deve apoiar o avanco do peao.',
            explicacao_solucao='Kd6 apoia o peao e impede o rei preto.',
            jogadas_necessarias=1
        ))
        
        novos_exercicios.append(models.ExercicioTatico(
            titulo='Final Torre vs Peões',
            descricao='Use a torre para parar os peoes conectados',
            posicao_inicial='{"a1":"wK","h1":"wR","e8":"bK","e4":"bP","f4":"bP"}',
            melhor_lance='Re1',
            tipo_tatica='Final',
            dificuldade='Intermediario',
            pontos=18,
            dica='Posicione a torre atras dos peoes.',
            explicacao_solucao='Re1 controla a coluna e para os peoes.',
            jogadas_necessarias=1
        ))
        
        # EXERCICIOS DE ESTRATEGIA
        novos_exercicios.append(models.ExercicioTatico(
            titulo='Controle de Casa Fraca',
            descricao='Ocupe a casa fraca no campo inimigo',
            posicao_inicial='{"a1":"wR","e1":"wK","f1":"wR","g1":"wN","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wP","e5":"wN","a8":"bR","e8":"bK","f8":"bR","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","d5":"bP","f6":"bP"}',
            melhor_lance='Nd7',
            tipo_tatica='Estrategia',
            dificuldade='Avancado',
            pontos=22,
            dica='O cavalo pode ocupar uma excelente casa.',
            explicacao_solucao='Nd7 ocupa a casa forte e controla pontos-chave.',
            jogadas_necessarias=1
        ))
        
        novos_exercicios.append(models.ExercicioTatico(
            titulo='Estrutura de Peões',
            descricao='Melhore sua estrutura de peões',
            posicao_inicial='{"a1":"wR","e1":"wK","h1":"wR","a2":"wP","b3":"wP","c2":"wP","d4":"wP","f2":"wP","g2":"wP","h2":"wP","a8":"bR","e8":"bK","h8":"bR","a7":"bP","b7":"bP","c6":"bP","d5":"bP","f7":"bP","g7":"bP","h7":"bP"}',
            melhor_lance='c4',
            tipo_tatica='Estrategia',
            dificuldade='Intermediario',
            pontos=16,
            dica='Ataque a cadeia de peoes na base.',
            explicacao_solucao='c4 pressiona a base da cadeia inimiga.',
            jogadas_necessarias=1
        ))
        
        # EXERCICIOS DE CALCULO
        novos_exercicios.append(models.ExercicioTatico(
            titulo='Sequência Forçada',
            descricao='Calcule a sequencia de xeques forcados',
            posicao_inicial='{"a1":"wK","d1":"wQ","h1":"wR","e8":"bK","f8":"bR","f7":"bP","g7":"bP","h7":"bP","a7":"bP","b7":"bP","c7":"bP","d7":"bP","e7":"bP"}',
            melhor_lance='Qd8+',
            tipo_tatica='Calculo',
            dificuldade='Avancado',
            pontos=25,
            dica='Inicie com xeque forcado.',
            explicacao_solucao='Qd8+ Rxd8 Rxd8# e mate forcado.',
            jogadas_necessarias=3
        ))
        
        novos_exercicios.append(models.ExercicioTatico(
            titulo='Variantes Múltiplas',
            descricao='Analise todas as respostas possiveis',
            posicao_inicial='{"a1":"wR","e1":"wK","h1":"wR","c1":"wB","f3":"wN","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","e4":"wP","a8":"bR","e8":"bK","h8":"bR","c8":"bB","f6":"bN","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","e5":"bP"}',
            melhor_lance='Ng5',
            tipo_tatica='Calculo',
            dificuldade='Avancado',
            pontos=23,
            dica='Considere todas as respostas do adversario.',
            explicacao_solucao='Ng5 cria multiplas ameacas simultaneas.',
            jogadas_necessarias=2
        ))
        
        # EXERCICIOS DE AVALIACAO DE POSICAO
        novos_exercicios.append(models.ExercicioTatico(
            titulo='Quem está Melhor?',
            descricao='Avalie corretamente a posição',
            posicao_inicial='{"a1":"wR","e1":"wK","h1":"wR","c1":"wB","g1":"wN","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wP","e4":"wP","a8":"bR","e8":"bK","h8":"bR","f8":"bB","b8":"bN","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","d5":"bP","e5":"bP"}',
            melhor_lance='f3',
            tipo_tatica='Avaliacao',
            dificuldade='Intermediario',
            pontos=14,
            dica='Pense em desenvolvimento e espaco.',
            explicacao_solucao='f3 prepara Be3 e melhora a posicao.',
            jogadas_necessarias=1
        ))
        
        novos_exercicios.append(models.ExercicioTatico(
            titulo='Fatores Posicionais',
            descricao='Identifique o fator posicional mais importante',
            posicao_inicial='{"a1":"wR","e1":"wK","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","c4":"wB","e4":"wP","f4":"wP","a8":"bR","e8":"bK","a7":"bP","b7":"bP","c7":"bP","e6":"bP","f7":"bP","g7":"bP","h7":"bP","d6":"bB"}',
            melhor_lance='Bd5',
            tipo_tatica='Avaliacao',
            dificuldade='Avancado',
            pontos=19,
            dica='Centralize a peca mais ativa.',
            explicacao_solucao='Bd5 domina o centro e pressiona f7.',
            jogadas_necessarias=1
        ))
        
        # Adicionar exercicios In the Shadows variados
        novos_exercicios.append(models.ExercicioTatico(
            titulo='Sombra da Abertura',
            descricao='Use uma jogada aparentemente normal para preparar uma armadilha',
            posicao_inicial='{"a1":"wR","b1":"wN","c1":"wB","d1":"wQ","e1":"wK","f1":"wB","g1":"wN","h1":"wR","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wP","e4":"wP","c5":"bP","d6":"bP","a7":"bP","b7":"bP","e7":"bP","f7":"bP","g7":"bP","h7":"bP","a8":"bR","b8":"bN","c8":"bB","d8":"bQ","e8":"bK","f8":"bB","g8":"bN","h8":"bR"}',
            melhor_lance='h3',
            tipo_tatica='In the Shadows',
            dificuldade='Avancado',
            pontos=30,
            dica='Este lance parece perda de tempo, mas esconde uma armadilha.',
            explicacao_solucao='h3 prepara g4-g5 com ataque devastador se o adversario nao perceber.',
            jogadas_necessarias=1
        ))
        
        novos_exercicios.append(models.ExercicioTatico(
            titulo='Torre Passiva Mortal',
            descricao='A torre parece inutil, mas e a chave da vitoria',
            posicao_inicial='{"a1":"wR","e1":"wK","h1":"wR","b1":"wN","f3":"wN","a2":"wP","b2":"wP","c2":"wP","f2":"wP","g2":"wP","h2":"wP","d4":"wP","e4":"wP","a8":"bR","e8":"bK","f8":"bR","g8":"bN","a7":"bP","b7":"bP","c7":"bP","f7":"bP","g7":"bP","h7":"bP","d6":"bP","e5":"bP"}',
            melhor_lance='Ra3',
            tipo_tatica='In the Shadows',
            dificuldade='Avancado',
            pontos=35,
            dica='A torre em a1 parece fora de jogo, mas pode decidir a partida.',
            explicacao_solucao='Ra3-h3 criara mate inevitavel na ala do rei.',
            jogadas_necessarias=2
        ))
        
        # Adicionar todos ao banco
        for ex in novos_exercicios:
            db.session.add(ex)
        
        db.session.commit()
        
        return jsonify({'message': f'Adicionados {len(novos_exercicios)} exercicios variados com sucesso!'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao adicionar exercicios variados: {str(e)}")
        return jsonify({'error': f'Erro: {str(e)}'}), 500

@app.route('/recriar_banco')
def recriar_banco():
    """Rota para recriar a estrutura do banco de dados"""
    try:
        # Dropar e recriar todas as tabelas
        db.drop_all()
        db.create_all()
        return jsonify({'message': 'Banco de dados recriado com sucesso!'})
        
    except Exception as e:
        logging.error(f"Erro ao recriar banco: {str(e)}")
        return jsonify({'error': f'Erro: {str(e)}'}), 500

@app.route('/chat/send', methods=['POST'])
def chat_send():
    try:
        # Verificar se a requisição é JSON
        if not request.is_json:
            return jsonify({'error': 'Requisição deve ser JSON'}), 400
            
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400
            
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Mensagem vazia'}), 400

        # Contexto específico para xadrez e estratégia "In the Shadows"
        context = """
        Você é o "Rei do Mate", um assistente de xadrez especializado na estratégia "In the Shadows".
        
        REGRAS DE RESPOSTA:
        - Seja CLARO, CURTO e OBJETIVO
        - Evite floreios, metáforas ou introduções desnecessárias
        - Se alguém disser "olá", responda apenas "oi" ou "olá"
        - Foque apenas no que foi perguntado
        - Use português brasileiro
        - Máximo 2-3 frases por resposta
        """

        prompt = f"{context}\n\nUsuário: {user_message}\n\nRei do Mate:"

        response = model.generate_content(prompt)
        ai_response = response.text

        return jsonify({'response': ai_response})

    except Exception as e:
        logging.error(f"Erro no chat: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/taticas/analise', methods=['POST'])
def analise_tatica():
    try:
        data = request.get_json()
        tipo_tatica = data.get('tipo_tatica')
        situacao = data.get('situacao')
        
        if not tipo_tatica or not situacao:
            return jsonify({'error': 'Tipo de tática e situação são obrigatórios'}), 400
        
        # Contexto especializado para análise tática como adversario
        context = f"""
        Você é um ADVERSARIO EXPERIENTE em xadrez analisando uma tática.
        
        SITUAÇÃO:
        - Tática aplicada: {tipo_tatica}
        - Descrição: {situacao}
        
        RESPONDA COMO UM ADVERSARIO QUE:
        - Identifica a ameaça imediatamente
        - Explica como defenderia ou contra-atacaria
        - Menciona possíveis armadilhas do oponente
        - É direto e técnico
        - Máximo 3 frases
        - Foco na DEFESA e CONTRA-ATAQUE
        
        EXEMPLO de resposta: "Essa cravada é perigosa, mas posso quebrá-la com h6 expulsando o bispo. Se ele insistir, sacrifico a qualidade mas mantenho iniciativa no centro."
        """
        
        prompt = f"{context}\n\nAdversário experiente responde:"
        
        response = model.generate_content(prompt)
        ai_response = response.text
        
        return jsonify({
            'resposta': ai_response,
            'tipo': 'analise_defensiva',
            'tatica_analisada': tipo_tatica
        })
        
    except Exception as e:
        logging.error(f"Erro na análise tática: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/conceitos/exemplo', methods=['POST'])
def exemplo_pratico_conceito():
    try:
        data = request.get_json()
        conceito = data.get('conceito')
        cenario = data.get('cenario')
        
        if not conceito or not cenario:
            return jsonify({'error': 'Conceito e cenário são obrigatórios'}), 400
        
        # Contexto para gerar exemplos práticos educativos
        context = f"""
        Você é um PROFESSOR DE XADREZ explicando conceitos com exemplos práticos.
        
        CONCEITO: {conceito}
        CENARIO: {cenario}
        
        GERE UMA EXPLICAÇÃO PRÁTICA:
        - Use linguagem clara e didática
        - Explique COMO reconhecer o conceito
        - Mostre QUANDO aplicar
        - Dê dicas práticas
        - Conecte com outros conceitos
        - Máximo 150 palavras
        
        RESPONDA APENAS EM FORMATO JSON:
        {{
            "explicacao": "explicação didática do conceito",
            "dicas": ["dica 1", "dica 2", "dica 3"],
            "conceitos_relacionados": ["conceito 1", "conceito 2"]
        }}
        """
        
        prompt = f"{context}\n\nProfessor responde:"
        
        response = model.generate_content(prompt)
        ai_text = response.text.strip()
        
        # Tentar extrair JSON da resposta
        try:
            import json
            # Procurar por JSON na resposta
            start = ai_text.find('{')
            end = ai_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = ai_text[start:end]
                ai_data = json.loads(json_str)
            else:
                raise ValueError("JSON não encontrado")
        except:
            # Fallback caso o JSON não seja parseado
            ai_data = {
                "explicacao": f"O conceito {conceito} é fundamental no xadrez. {cenario} Este é um exemplo clássico que demonstra a importância da compreensão posicional.",
                "dicas": [
                    f"Observe quando {conceito.lower()} aparecer em suas partidas",
                    "Pratique reconhecendo este padrão",
                    "Conecte com sua estratégia geral"
                ],
                "conceitos_relacionados": ["Estrategia", "Tatica"]
            }
        
        return jsonify(ai_data)
        
    except Exception as e:
        logging.error(f"Erro no exemplo prático: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/shadows/practice', methods=['POST'])
def practice_shadow_scenario():
    try:
        data = request.get_json()
        scenario = data.get('scenario')
        description = data.get('description')
        
        if not scenario or not description:
            return jsonify({'error': 'Cenario e descricao sao obrigatorios'}), 400
        
        # Contexto especializado para treino de cenários "In the Shadows"
        context = f"""
        Você é um MESTRE DE XADREZ especializado na estratégia "In the Shadows" - deceptiva e sutil.
        
        CENARIO: {scenario}
        SITUACAO: {description}
        
        CRIE UM EXERCICIO PRATICO:
        - Explique os SINAIS para reconhecer esta oportunidade
        - Mostre a SEQUENCIA de movimentos
        - Alerte para ARMADILHAS comuns
        - Dê dicas de TIMING
        - Mencione CONTRA-JOGOS do oponente
        - Máximo 200 palavras, linguagem prática
        
        RESPONDA APENAS EM FORMATO JSON:
        {{
            "preparacao": "como preparar o cenário",
            "execucao": "sequencia de movimentos chave",
            "sinais": ["sinal 1", "sinal 2", "sinal 3"],
            "armadilhas": ["armadilha 1", "armadilha 2"],
            "timing": "quando executar"
        }}
        """
        
        prompt = f"{context}\n\nMestre responde:"
        
        response = model.generate_content(prompt)
        ai_text = response.text.strip()
        
        # Tentar extrair JSON da resposta
        try:
            import json
            start = ai_text.find('{')
            end = ai_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = ai_text[start:end]
                ai_data = json.loads(json_str)
            else:
                raise ValueError("JSON não encontrado")
        except:
            # Fallback
            ai_data = {
                "preparacao": f"Para executar {scenario}, prepare as peças em posições aparentemente passivas.",
                "execucao": "Aguarde o momento ideal e execute a sequência decisiva.",
                "sinais": ["Oponente focado em outra área", "Suas peças coordenadas", "Momento tático favorável"],
                "armadilhas": ["Não revelar intenções muito cedo", "Cuidado com contra-ataques"],
                "timing": "Execute quando o oponente estiver distraiído com outras ameaças"
            }
        
        return jsonify(ai_data)
        
    except Exception as e:
        logging.error(f"Erro no treino de cenário: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/shadows/analyze', methods=['POST'])
def analyze_shadow_scenario():
    try:
        data = request.get_json()
        scenario = data.get('scenario')
        analysis_focus = data.get('analysis_focus')
        
        if not scenario or not analysis_focus:
            return jsonify({'error': 'Cenário e foco de análise são obrigatórios'}), 400
        
        # Contexto para análise técnica profunda
        context = f"""
        Você é um ANALISTA DE XADREZ especializado em estratégias sutis "In the Shadows".
        
        CENARIO: {scenario}
        FOCO: {analysis_focus}
        
        GERE UMA ANALISE TECNICA:
        - PRINCIPIOS estratégicos envolvidos
        - PADROES posicionais típicos
        - ERROS comuns a evitar
        - VARIANTES principais
        - APLICACAO em diferentes aberturas
        - Linguagem técnica mas acessível
        
        RESPONDA APENAS EM FORMATO JSON:
        {{
            "principios": ["princípio 1", "princípio 2"],
            "padroes": "padrões posicionais chave",
            "erros_comuns": ["erro 1", "erro 2"],
            "aplicacoes": ["abertura 1", "abertura 2"],
            "dificuldade": "iniciante/intermediário/avançado"
        }}
        """
        
        prompt = f"{context}\n\nAnalista responde:"
        
        response = model.generate_content(prompt)
        ai_text = response.text.strip()
        
        # Tentar extrair JSON da resposta
        try:
            import json
            start = ai_text.find('{')
            end = ai_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = ai_text[start:end]
                ai_data = json.loads(json_str)
            else:
                raise ValueError("JSON não encontrado")
        except:
            # Fallback
            ai_data = {
                "principios": ["Deceptividade", "Coordenação sutil"],
                "padroes": f"O padrão {scenario} envolve posicionamento enganoso seguido de ativação súbita.",
                "erros_comuns": ["Revelar intenções muito cedo", "Não aguardar momento ideal"],
                "aplicacoes": ["Gambito da Rainha", "Defesa Siciliana"],
                "dificuldade": "intermediário"
            }
        
        return jsonify(ai_data)
        
    except Exception as e:
        logging.error(f"Erro na análise do cenário: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

if __name__ == '__main__':
    # Production ready setup
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)