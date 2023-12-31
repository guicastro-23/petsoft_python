from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask import request, redirect, url_for
from datetime import datetime
from sqlalchemy import func
import re
from flask import jsonify
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from flask_migrate import Migrate
from math import ceil

ITEMS_PER_PAGE = 10


# Hash the password with a shorter length
hashed_password = generate_password_hash('your_password', method='pbkdf2:sha256', salt_length=8)



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Guilherme1234@127.0.0.1/petsoft'
app.config['SECRET_KEY'] = 'chave_secreta'  
db = SQLAlchemy(app)
migrate = Migrate(app, db)

def format_currency(value):
    return f"R$ {value:,.2f}".replace('.', ',')


# Registro do filtro para o Jinja2
app.jinja_env.filters['format_currency'] = format_currency


class Cliente(db.Model):
    idCliente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(80), nullable=False)
    logradouro = db.Column(db.String(80), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    tipo_endereco = db.Column(db.String(20))
    numero_endereco = db.Column(db.Integer)

class Animal(db.Model):
    id_an = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(80), nullable=False)
    data_nasc = db.Column(db.Date)
    pelagem = db.Column(db.String(20))
    porte = db.Column(db.String(10))
    agressivo = db.Column(db.Boolean)
    obs = db.Column(db.String(100))
    tipo_animal = db.Column(db.String(10), nullable=True)
    

    # Chave estrangeira referenciando a tabela Cliente
    Cliente_idCliente = db.Column(db.Integer, db.ForeignKey('cliente.idCliente'), nullable=False)

    # Relacionamento com o Cliente
    cliente = db.relationship('Cliente', backref=db.backref('animais', lazy=True))



class Usuario(db.Model):
    id_us = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login = db.Column(db.String(100), nullable=False)
    senha = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    
    def set_password(self, password):
     self.senha = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.senha, password)

class Servico(db.Model):
    id_ser = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo = db.Column(db.String(20))
    valor = db.Column(db.Float)



class OrdemDeServico(db.Model):
    id_os = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo_servico = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.String(45), nullable=False)
    valorTotal = db.Column(db.Float, nullable=False)
    data_in = db.Column(db.Date)
    Usuario_id_us = db.Column(db.Integer, db.ForeignKey('usuario.id_us'), nullable=True)
    Cliente_idCliente = db.Column(db.Integer, db.ForeignKey('cliente.idCliente'), nullable=False)
    Animal_id_an = db.Column(db.Integer, db.ForeignKey('animal.id_an'), nullable=False)
    Animal_Cliente_idCliente = db.Column(db.Integer, nullable=True)
   # servico_id = db.Column(db.Integer,db.ForeignKey('servico.id_ser'),nullable=False)
    
    cliente = db.relationship('Cliente', foreign_keys=[Cliente_idCliente])
    animal = db.relationship('Animal', foreign_keys=[Animal_id_an])
    #servico = db.relationship('Servico', foreign_keys=[servico_id])


#class OrdemServicoServico(db.Model):
  #  _tablename_ = 'ordem_servico_servico'

  #  ordem_de_servico_id = db.Column(db.Integer, db.ForeignKey('ordem_de_servico.id_os'), primary_key=True)
  #  servico_tipo = db.Column(db.String(20), db.ForeignKey('servico.tipo'), primary_key=True)

    # Relacionamentos com as outras tabelas
   # ordem_de_servico = db.relationship('OrdemDeServico')
   # servico = db.relationship('Servico')

    
ITEMS_PER_PAGE = 10


# Rotas

# Rotas
@app.route('/')
def redirecionar_para_login():
   return redirect(url_for('login'))

@app.route('/index')
def home():
    return render_template('index.html')
# ------------------------------Rotas de cliente ---------------------------------------
@app.route('/lista_clientes', methods=['GET'])
def lista_clientes():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('searchTerm', '')

    if search_term:
        # Filtra e ordena clientes pelo nome ou telefone em ordem alfabética
        query = Cliente.query.filter(
            Cliente.nome.ilike(f'%{search_term}%') | 
            Cliente.telefone.ilike(f'%{search_term}%')
        ).order_by(Cliente.nome)
    else:
        # Ordena todos os clientes pelo nome em ordem alfabética
        query = Cliente.query.order_by(Cliente.nome)

    pagination = query.paginate(page=page, per_page=10, error_out=False)
    clientes = pagination.items
    total_pages = pagination.pages

    return render_template('lista_clientes.html', clientes=clientes, total_pages=total_pages, current_page=page)


@app.route('/clientes', methods=['GET', 'POST'])
def listar_clientes():
    if request.method == 'GET':
        clientes = Cliente.query.all()
        return render_template('clientes.html', clientes=clientes)
    elif request.method == 'POST':
        nome_cliente = request.form['nome_cliente'].capitalize()
        telefone_cliente = request.form['telefone_cliente']
        endereco_cliente = request.form['endereco_cliente'].title()  # Converte a primeira letra de cada palavra para maiúscula
        tipo_endereco_cliente = request.form['tipo_endereco_cliente']
        numero_endereco_cliente = request.form['numero_endereco_cliente']

        # Validar o número de telefone
        telefone_regex = r"\([0-9]{2}\) [0-9]{4,5}-[0-9]{4}"
        if not re.match(telefone_regex, telefone_cliente):
            flash('Informe um número de telefone no formato (XX) XXXXX-XXXX.', 'error')
            return redirect(url_for('listar_clientes'))

        novo_cliente = Cliente(
            nome=nome_cliente,
            telefone=telefone_cliente,
            logradouro=endereco_cliente,
            tipo_endereco=tipo_endereco_cliente,
            numero_endereco=int(numero_endereco_cliente)  # Converta para inteiro
        )

        db.session.add(novo_cliente)
        try:
            db.session.commit()
            flash('Cliente adicionado com sucesso.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Erro ao adicionar cliente.', 'error')

        return redirect(url_for('lista_clientes'))
    
@app.route('/clientes/editar/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == 'POST':
        nome_cliente = request.form['nome_cliente'].title()  # Converte a primeira letra de cada palavra para maiúscula
        telefone_cliente = request.form['telefone_cliente']
        endereco_cliente = request.form['endereco_cliente'].title()  # Converte a primeira letra de cada palavra para maiúscula
        tipo_endereco_cliente = request.form['tipo_endereco_cliente']
        numero_endereco_cliente = int(request.form['numero_endereco_cliente'])

        # Validar o número de telefone
        telefone_regex = r"\([0-9]{2}\) [0-9]{4,5}-[0-9]{4}"
        if not re.match(telefone_regex, telefone_cliente):
            flash('Informe um número de telefone no formato (XX) XXXXX-XXXX.', 'error')
            return redirect(url_for('editar_cliente', cliente_id=cliente_id))

        # Atualizar dados do cliente
        cliente.nome = nome_cliente
        cliente.telefone = telefone_cliente
        cliente.logradouro = endereco_cliente
        cliente.tipo_endereco = tipo_endereco_cliente
        cliente.numero_endereco = numero_endereco_cliente

        db.session.commit()
        flash('Alterações salvas com sucesso!', 'success')
        return redirect(url_for('lista_clientes'))

    return render_template('editar_cliente.html', cliente=cliente)


@app.route('/excluir_cliente/<int:cliente_id>', methods=['GET', 'POST'])
def excluir_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)

    # Verifica se o cliente possui animais associados
    if cliente.animais:  # Supondo que 'animais' seja o relacionamento definido no modelo Cliente
        flash('Não é possível excluir um cliente que possui animais associados.', 'error')
        return redirect(url_for('lista_clientes'))

    db.session.delete(cliente)
    try:
        db.session.commit()
        flash('Cliente excluído com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir cliente: {e}', 'error')
    
    return redirect(url_for('lista_clientes'))


#------------------ fim da rota de cliente -------------------------------

#---------- Rotas Animais ---------------------------------------------------------------------
    
#19/12

@app.route('/animais', methods=['GET', 'POST'])
def listar_animais():
    animais = Animal.query.all()
    clientes = Cliente.query.all()
    errors = []

    if request.method == 'POST':
        # Obter os dados do formulário
        nome_animal = request.form.get('nome_animal')
        cliente_id = request.form.get('cliente_animal')
        data_nasc = request.form.get('data_nasc_animal')
        pelagem = request.form.get('pelagem_animal')
        porte = request.form.get('porte_animal')
        agressivo = request.form.get('agressivo_animal') == 'True' # Verificar se a caixa de seleção agressivo está marcada
        obs = request.form.get('observacoes_animal')
        tipo_animal = request.form.get('tipo_animal')
        nome_animal = nome_animal.capitalize()

        if tipo_animal not in ['Cachorro', 'Gato']:
            flash('Por favor, selecione se é um Cachorro ou um Gato.', 'error')
        # Validar o nome do animal usando expressão regular
        elif not re.match(r"^[A-Za-zÀ-ú ]+$", nome_animal):
            flash('O nome do animal deve conter apenas letras e espaços.', 'error')
        # Validation for animal name starting with an uppercase letter
        elif not nome_animal[0].isupper():
            flash('O nome do animal deve iniciar com letra maiúscula.', 'error')
        # Validation for selecting "Tipo de Pelagem" (coat type)
        elif not pelagem:
            flash('Selecione um tipo de pelagem para o animal.', 'error')
        # Validation for selecting "Porte" (size)
        elif not porte:
            flash('Selecione um porte para o animal.', 'error')
        else:
            # Verificar se o cliente existe
            cliente = Cliente.query.get(cliente_id)
            if cliente is None:
                flash('Cliente não encontrado.', 'error')
            else:
                # Verificar se o animal já existe para o mesmo cliente
                existing_animal = Animal.query.filter_by(nome=nome_animal, Cliente_idCliente=cliente_id).first()
                if existing_animal:
                    flash('Esse cliente já possui um animal com o mesmo nome.', 'error')
                else:
                    try:
                        data_nasc = datetime.strptime(data_nasc, '%Y-%m-%d')
                    except ValueError:
                        flash('Data de nascimento inválida.', 'error')
                    else:
                        # Obter a data atual como um objeto datetime
                        data_atual = datetime.now()

                        # Verificar se a data de nascimento é no futuro
                        if data_nasc > data_atual:
                            flash('A data de nascimento não pode ser no futuro.', 'error')
                        else:
                            # Se todas as verificações passarem, criar o novo animal
                            novo_animal = Animal(
                                nome=nome_animal,
                                data_nasc=data_nasc,
                                Cliente_idCliente=cliente_id,
                                pelagem=pelagem,
                                porte=porte,
                                agressivo=agressivo,
                                obs=obs,
                                tipo_animal=tipo_animal
                            )

                            db.session.add(novo_animal)

                            try:
                                db.session.commit()
                                flash('Animal adicionado com sucesso.', 'success')
                            except Exception as e:
                                db.session.rollback()
                                flash(f'Erro ao adicionar o animal: {str(e)}', 'error')
                            return redirect(url_for('lista_animais'))
    return render_template('animais.html', animais=animais, clientes=clientes)

@app.route('/lista_animais', methods=['GET'])
def lista_animais():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('searchTerm', '')

    query = Animal.query.order_by(Animal.nome)  # Ordena animais pelo nome em ordem alfabética

    if search_term:
        # Filtrar animais pelo nome, espécie ou nome do tutor
        query = query.join(Cliente).filter(
            Animal.nome.ilike(f'%{search_term}%') |
            Animal.tipo_animal.ilike(f'%{search_term}%') |
            Cliente.nome.ilike(f'%{search_term}%')
        ).order_by(Animal.nome)  # Mantém a ordenação após a filtragem

    pagination = query.paginate(page=page, per_page=ITEMS_PER_PAGE, error_out=False)
    animais = pagination.items
    total_pages = pagination.pages

    return render_template('lista_animais.html', animais=animais, total_pages=total_pages, current_page=page)

# Editar Animal
@app.route('/editar_animal/<int:animal_id>', methods=['GET', 'POST'])
def editar_animal(animal_id):
    # Lógica para obter os dados do animal com o ID fornecido
    animal = Animal.query.get_or_404(animal_id)

    if request.method == 'POST':
        # Lógica para processar os dados do formulário de edição
        nome_animal = request.form['nome_animal']
        tipo_animal = request.form['tipo_animal']
        data_nasc_animal = request.form['data_nasc_animal']

        if tipo_animal not in ['Cachorro', 'Gato']:
            flash('Por favor, selecione se é um Cachorro ou um Gato.', 'error')
        else:
            # Validar o nome do animal usando expressão regular
            if not re.match(r"^[A-Za-zÀ-ú ]+$", nome_animal):
                flash('O nome do animal deve conter apenas letras e espaços.', 'error')
            else:
                try:
                    data_nasc_animal = datetime.strptime(data_nasc_animal, '%Y-%m-%d')
                except ValueError:
                    flash('Data de nascimento inválida.', 'error')
                else:
                    # Obter a data atual como um objeto datetime
                    data_atual = datetime.now()

                    # Verificar se a data de nascimento é no futuro
                    if data_nasc_animal > data_atual:
                        flash('A data de nascimento não pode ser no futuro.', 'error')
                    else:
                        # Agora você pode atualizar os dados do animal no banco de dados
                        nome_animal = nome_animal.capitalize()
                        animal.nome = nome_animal
                        animal.tipo_animal = tipo_animal
                        animal.data_nasc = data_nasc_animal
                        animal.agressivo = request.form.get('agressivo_animal') == 'True'
                        animal.porte = request.form['porte_animal']
                        animal.pelagem = request.form['pelagem_animal']
                        animal.obs = request.form['observacoes_animal']
                        

                        # Atualiza os dados no banco de dados
                        db.session.commit()

                        flash('Alterações salvas com sucesso!', 'success')
                        return redirect(url_for('lista_animais'))  # Redireciona para a lista de animais após a edição

    # Renderize a página de edição com os dados do animal
    return render_template('editar_animal.html', animal=animal)

@app.route('/excluir_animal/<int:animal_id>', methods=['GET', 'POST'])
def excluir_animal(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    
    db.session.delete(animal)
    db.session.commit()
    
    flash(' Animal excluido com sucesso.', 'sucess')
    return redirect(url_for('lista_animais'))

#--------------------- Fim das 

@app.route('/agendamento')
def listar_agendamento():
    agendamento = OrdemDeServico.query.all()
    return render_template('agendamento.html', agendamento=agendamento)

# Rota para a página "Nova Ordem"
@app.route('/nova_ordem', methods=['GET', 'POST'])
def nova_ordem():
    if request.method == 'POST':
        # Obtenha os dados do formulário
        tipo_servico = request.form['tipo_servico']
        descricao = request.form['descricao']
        valorTotal = float(request.form['valor_total'])
        data_in = request.form['data_ordem']
        cliente_id = int(request.form['cliente_animal'])
        animal_id = int(request.form['animal'])

 # Obtenha o valor do serviço com base no tipo de serviço selecionado
        servico = Servico.query.filter_by(tipo=tipo_servico).first()
        valorTotal = servico.valor if servico else 0.0

        # Crie uma nova ordem de serviço
        nova_ordem = OrdemDeServico(
            tipo_servico=tipo_servico,
            descricao=descricao,
            valorTotal=valorTotal,
            data_in=data_in,
            Cliente_idCliente=cliente_id,
            Animal_id_an=animal_id
        )

        # Adicione a ordem de serviço ao banco de dados
        db.session.add(nova_ordem)
        db.session.commit()

        # Redirecione para a página de listagem de ordens de serviço ou outra página relevante
        return redirect(url_for('nova_ordem'))

    # Se o método for GET, simplesmente renderize o formulário
    clientes = Cliente.query.all()
    animais = Animal.query.all()
    
    # Obtenha os tipos de serviço disponíveis do banco de dados
    tipos_servico = [servico.tipo for servico in Servico.query.all()]
    
    return render_template('nova_ordem.html', clientes=clientes, animais=animais, tipos_servico=tipos_servico)

@app.route('/obter_valor_servico', methods=['GET'])
def obter_valor_servico():
    tipo_servico = request.args.get('tipo_servico')
    
    # Consulte o banco de dados para obter o valor do serviço com base no tipo
    servico = Servico.query.filter_by(tipo=tipo_servico).first()
    
    # Verifique se o serviço foi encontrado
    if servico:
        valor_servico = servico.valor
    else:
        valor_servico = 0.0

    # Converta o valor para uma string JSON para enviar de volta ao cliente
    resposta = {'valor_servico': valor_servico}
    
    # Use a função jsonify para converter a resposta em JSON
    return jsonify(resposta)


#------------------- fi da  Rota de Ordens --------------------------------------------

@app.route('/eventos', methods=['GET'])
def obter_eventos():
    ordens = OrdemDeServico.query.all()
    eventos = []

    for ordem in ordens:
        eventos.append({
            'title': ordem.tipo,
            'start': ordem.data_in.isoformat(),
            'url': url_for('detalhes_ordem', ordem_id=ordem.id_os)  # Substitua 'detalhes_ordem' pela rota correta
        })

    return jsonify(eventos)

@app.route('/get_ordens_servico')
def get_ordens_servico():
    # Obtenha as ordens de serviço no período especificado
    start = request.args.get('start')
    end = request.args.get('end')

    # Consulta ao banco de dados para buscar as ordens de serviço
    ordens_servico = OrdemDeServico.query.filter(OrdemDeServico.data_in.between(start, end)).all()

    # Transforma os dados em um formato adequado para o calendário
    events = [{
        'id_os': ordem_servico.id_os,
        'descricao': ordem_servico.descricao,
        'data_in': ordem_servico.data_in.isoformat()  # Formato ISO para compatibilidade com o calendário
    } for ordem_servico in ordens_servico]

    return jsonify(events)

@app.route('/buscar_clientes_por_nome')
def buscar_clientes_por_nome():
    nome = request.args.get('nome', '').strip()
    if len(nome) > 0:
        # Adjust the query according to your database schema
        clients = Cliente.query.filter(Cliente.nome.ilike(f'{nome}%')).all()
        client_list = [{'idCliente': client.idCliente, 'nome': client.nome} for client in clients]
        return jsonify({'clientes': client_list})
    
    return jsonify({'clientes': []})

from flask import jsonify

@app.route('/get_animais_por_cliente/<int:clientId>')
def get_animais_por_cliente(clientId):
    try:
        # Assuming you have a relationship set up between Cliente and Animal models
        # Replace 'Animal' and 'Cliente' with your actual model names
        animais = Animal.query.filter_by(Cliente_idCliente=clientId).all()

        # Transform the query result into a list of dictionaries
        animais_list = [{'id': animal.id_an, 'nome': animal.nome} for animal in animais]

        # Return the result as JSON
        return jsonify({'animais': animais_list})

    except Exception as e:
        # Handle exceptions (e.g., client not found, database errors)
        print(e)  # Log the error for debugging
        return jsonify({'error': 'Error fetching animals for the client'}), 500
    
@app.route('/buscar_servicos')
def buscar_servicos():
    query = request.args.get('query', '').strip()
    services = Servico.query.filter(Servico.tipo.ilike(f'%{query}%')).all()
    services_list = [{'id': service.id_ser, 'tipo': service.tipo, 'valor': service.valor} for service in services]
    return jsonify({'servicos': services_list})


# ------------------ fim das Rotas de Ordens -----------------------------------


#---------------- Rotas de serviço --------------------------------------
@app.route('/lista_servicos', methods=['GET'])
def lista_servicos():
    page = request.args.get('page', 1, type=int)
    search_term = request.args.get('searchTerm', '')

    if search_term:
        # Filtra serviços pelo nome e ordena alfabeticamente
        pagination = Servico.query.filter(Servico.tipo.ilike(f'%{search_term}%')).order_by(Servico.tipo).paginate(page=page, per_page=10, error_out=False)
    else:
        # Mostra todos os serviços ordenados alfabeticamente
        pagination = Servico.query.order_by(Servico.tipo).paginate(page=page, per_page=10, error_out=False)

    servicos = pagination.items
    total_pages = pagination.pages

    return render_template('lista_servicos.html', servicos=servicos, total_pages=total_pages, current_page=page, pagination=pagination)


@app.route('/servicos', methods=['GET', 'POST'])
def listar_servicos():
    if request.method == 'POST':
        # Process the form data when a new service is added
        tipo_servico = request.form['tipo_servico']
        valor_servico = request.form['valor_servico']
        tipo_servico = tipo_servico.capitalize()
        # Check if a service with the same type already exists
        existing_servico = Servico.query.filter_by(tipo=tipo_servico).first()
        if existing_servico:
            flash('Um serviço com este tipo já existe.', 'error')
        else:
            try:
                # Validate that the 'valor' is a non-negative float
                valor_servico = float(valor_servico)
                if valor_servico < 0:
                    flash('O valor do serviço não pode ser negativo.', 'error')
                else:
                    novo_servico = Servico(tipo=tipo_servico, valor=valor_servico)
                    db.session.add(novo_servico)
                    db.session.commit()
                    flash('Serviço adicionado com sucesso.', 'success')

                    # Redirect to the services list page
                    return redirect(url_for('lista_servicos'))
            except ValueError:
                flash('Informe um valor válido para o serviço.', 'error')

    # Fetch the list of services for rendering
    servicos = Servico.query.all()
    return render_template('servicos.html', servicos=servicos)

@app.route('/servicos', methods=['GET', 'POST'])
def adicionar_servico():
    if request.method == 'POST':
        tipo_servico = request.form['tipo_servico'].capitalize()  # Alterado para capitalizar a primeira letra
        valor_servico = request.form['valor_servico']

        # Verifica se já existe um serviço com o mesmo tipo
        existing_servico = Servico.query.filter_by(tipo=tipo_servico).first()
        if existing_servico:
            flash('Um serviço com este tipo já existe.', 'error')
        else:
            try:
                # Valida se o 'valor' é um float não negativo
                valor_servico = float(valor_servico)
                if valor_servico < 0:
                    flash('O valor do serviço não pode ser negativo.', 'error')
                else:
                    novo_servico = Servico(tipo=tipo_servico, valor=valor_servico)
                    db.session.add(novo_servico)
                    db.session.commit()
                    flash('Serviço adicionado com sucesso.', 'success')
            except ValueError:
                flash('Informe um valor válido para o serviço.', 'error')

    servicos = Servico.query.all()
    return render_template('servicos.html', servicos=servicos)

@app.route('/editar_servico/<int:servico_id>', methods=['GET', 'POST'])
def editar_servico(servico_id):
    servico = Servico.query.get_or_404(servico_id)
    
    if request.method == 'POST':
        tipo_servico = request.form['tipo_servico']
        valor_servico = float(request.form['valor_servico'])

        # Check if a service with the same type already exists
        existing_servico = Servico.query.filter(Servico.id_ser != servico_id, Servico.tipo == tipo_servico).first()
        if existing_servico:
            flash('Um serviço com este tipo já existe.', 'error')
        else:
            tipo_servico = tipo_servico.capitalize()
            servico.tipo = tipo_servico
            servico.valor = valor_servico

            db.session.commit()
            flash('Serviço atualizado com sucesso.', 'success')
            return redirect(url_for('lista_servicos'))

    return render_template('editar_servico.html', servico=servico)

@app.route('/excluir_servico/<int:servico_id>', methods=['GET', 'POST'])
def excluir_servico(servico_id):
    servico = Servico.query.get_or_404(servico_id)

    db.session.delete(servico)
    db.session.commit()

    flash('Serviço excluído com sucesso.', 'success')
    return redirect(url_for('lista_servicos'))
# ------------------ fim rotas de serviço -----------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Inicializa a mensagem de erro como None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verifique as credenciais (substitua isso com sua lógica de autenticação real)
        if username == 'admin' and password == 'admin123':
            # Autenticação bem-sucedida, salve o usuário na sessão
            session['username'] = username

            # Redirecione para a página principal ou para a página que estava tentando acessar
            next_page = request.args.get('next', 'home')
            return redirect(url_for(next_page))

        else:
            # Credenciais inválidas, define a mensagem de erro
            error = 'Credenciais inválidas. Tente novamente.'

    # Se o método for GET ou as credenciais estiverem incorretas, exiba o formulário de login com a mensagem de erro
    return render_template('login.html', error=error)

# --------------------- Criar Usuario -----------------------

@app.route('/criar_usuario', methods=['GET', 'POST'])
def criar_usuario():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']

        # Verifique se a senha e a confirmação de senha coincidem
        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return redirect(url_for('criar_usuario'))

        try:
            # Consulta se já existe um usuário com o mesmo nome
            existing_user = Usuario.query.filter_by(login=username).first()

            if existing_user:
                flash('Este nome de usuário já está em uso. Escolha outro.', 'error')
                return redirect(url_for('criar_usuario'))

            # Crie um novo usuário e salve no banco de dados
            novo_usuario = Usuario(login=username, senha=generate_password_hash(password), email=email)
            db.session.add(novo_usuario)
            db.session.commit()

            flash('Usuário criado com sucesso. Faça login agora.', 'success')
            return redirect(url_for('login'))
        except SQLAlchemyError as e:
         print(f'Error: {e}')
        flash('Erro ao criar usuário. Entre em contato com o suporte.', 'error')

 

# ------------------ fim rotas de Usuario -----------------------------------


if __name__ == '__main__':
   # with app.app_context():
   #     db.create_all()
   
    app.run(debug=True)

    # Apaga o banco e recomeça
# with app.app_context():
#        db.drop_all()
#        db.create_all()