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




# Hash the password with a shorter length
hashed_password = generate_password_hash('your_password', method='pbkdf2:sha256', salt_length=8)



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Guilherme1234@127.0.0.1/petsoft'
app.config['SECRET_KEY'] = 'chave_secreta'  
db = SQLAlchemy(app)


# Definindo modelos para as tabelas do banco de dados
class Cliente(db.Model):
    idCliente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(80), nullable=False)
    logradouro = db.Column(db.String(80), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)

class Animal(db.Model):
    id_an = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(80), nullable=False)
    data_nasc = db.Column(db.Date)
    pelagem = db.Column(db.String(20))
    porte = db.Column(db.String(5))
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
    tipo = db.Column(db.String(10), nullable=False)
    descricao = db.Column(db.String(45), nullable=False)
    valorTotal = db.Column(db.Float, nullable=False)
    data_in = db.Column(db.Date)
    Usuario_id_us = db.Column(db.Integer, db.ForeignKey('usuario.id_us'), nullable=False)
    Cliente_idCliente = db.Column(db.Integer, db.ForeignKey('cliente.idCliente'), nullable=False)
    Animal_id_an = db.Column(db.Integer, db.ForeignKey('animal.id_an'), nullable=False)
    Animal_Cliente_idCliente = db.Column(db.Integer, nullable=False)




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
    show_all = request.args.get('showAll', default=False, type=bool)
    search_term = request.args.get('searchTerm', default='', type=str).strip()

    # Lógica para obter a lista de clientes com base nos parâmetros de consulta
    if show_all:
        clientes = Cliente.query.all()
    else:
        clientes = Cliente.query.filter(func.lower(Cliente.nome).contains(func.lower(search_term))).all()

    return render_template('lista_clientes.html', clientes=clientes, show_all=show_all, search_term=search_term)

@app.route('/clientes', methods=['GET', 'POST'])
def listar_clientes():
    if request.method == 'GET':
        clientes = Cliente.query.all()
        return render_template('clientes.html', clientes=clientes)
    elif request.method == 'POST':
        nome_cliente = request.form['nome_cliente']
        telefone_cliente = request.form['telefone_cliente']
        endereco_cliente = request.form['endereco_cliente']

        # Server-side validation
        if not re.match(r"[A-Za-zÀ-ú ]+", nome_cliente):
            flash('O nome do cliente deve conter apenas letras e espaços.', 'error')
            return redirect(url_for('listar_clientes'))

        if not re.match(r"[0-9]{10,}", telefone_cliente):
            flash('Informe um número de telefone válido.', 'error')
            return redirect(url_for('listar_clientes'))

        # Verificar duplicação de nome de cliente
        cliente_existente = Cliente.query.filter_by(nome=nome_cliente).first()
        if cliente_existente:
            flash('Um cliente com o mesmo nome já existe. ID do cliente existente: {}'.format(cliente_existente.idCliente), 'error')
            return redirect(url_for('listar_clientes'))

        # Se todas as validações passarem, adicione o novo cliente ao banco de dados
        novo_cliente = Cliente(nome=nome_cliente, telefone=telefone_cliente, logradouro=endereco_cliente)
        db.session.add(novo_cliente)
        try:
            db.session.commit()
            flash('Cliente adicionado com sucesso.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Um cliente com o mesmo nome já existe.', 'error')
        
        return redirect(url_for('lista_clientes'))

    
@app.route('/clientes/editar/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    # Lógica para obter os dados do cliente com o ID fornecido
    cliente = Cliente.query.get_or_404(cliente_id)

    if request.method == 'POST':
        # Lógica para processar os dados do formulário de edição
        cliente.nome = request.form['nome_cliente']
        cliente.telefone = request.form['telefone_cliente']
        cliente.logradouro = request.form['endereco_cliente']

        # Atualiza os dados no banco de dados
        db.session.commit()

        flash('Alterações salvas com sucesso!', 'success')
        return redirect(url_for('lista_clientes'))  # Redirect to the list of clients

    # Renderize a página de edição com os dados do cliente
    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/excluir_cliente/<int:cliente_id>', methods=['GET', 'POST'])
def excluir_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    
    db.session.delete(cliente)
    db.session.commit()
    
    flash(' Cliente excluido com sucesso.', 'sucess')
    return redirect(url_for('lista_clientes'))

#------------------ fim da rota de cliente -------------------------------

#---------- Rotas Animais ---------------------------------------------------------------------
    

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
        else:
        # Validar o nome do animal usando expressão regular
            if not re.match(r"^[A-Za-zÀ-ú ]+$", nome_animal):
                flash('O nome do animal deve conter apenas letras e espaços.', 'error')
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
    
    show_all = request.args.get('showAll', default=False, type=bool)
    search_term = request.args.get('searchTerm', default='', type=str).strip()

    # Lógica para obter a lista de animais com base nos parâmetros de consulta
    if show_all:
        animais = Animal.query.all()
    else:
        animais = Animal.query.filter(func.lower(Animal.nome).contains(func.lower(search_term))).all()
    
    return render_template('lista_animais.html', animais=animais, show_all=show_all, search_term=search_term)


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

#--------------------- Fim de Animais --------------------------------------

@app.route('/agendamento')
def listar_agendamento():
    agendamento = OrdemDeServico.query.all()
    return render_template('agendamento.html', agendamento=agendamento)


#------------------- Rota de Ordens --------------------------------------------

# Rota para a página "Nova Ordem"
@app.route('/nova-ordem', methods=['GET', 'POST'])
def nova_ordem():
    # Assuming you have a Servico model
    servicos = Servico.query.all()

    if request.method == 'POST':
        # Process the form data when the form is submitted
        animal_id = request.form['animal']
        cliente_id = request.form['cliente']
        servicos_ids = request.form.getlist('servicos[]')  # Use getlist to get multiple selected values
        valor_total = sum(float(Servico.query.get(servico_id).valor) for servico_id in servicos_ids)
        data_ordem = datetime.strptime(request.form['data_ordem'], '%Y-%m-%d')
        descricao = request.form['descricao']

        # Create a new order and add it to the database
        nova_ordem = OrdemDeServico(
            tipo='Tipo Exemplo',
            descricao=descricao,
            valorTotal=valor_total,
            data_in=data_ordem,
            Usuario_id_us=1,  # Replace with the actual user ID
            Cliente_idCliente=cliente_id,
            Animal_id_an=animal_id,
            Animal_Cliente_idCliente=cliente_id
        )

        # Associate services with the order
        nova_ordem.servicos.extend(Servico.query.filter(Servico.id_ser.in_(servicos_ids)).all())

        db.session.add(nova_ordem)

        try:
            db.session.commit()
            flash('Ordem de serviço adicionada com sucesso.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Erro ao adicionar a ordem de serviço.', 'error')

        return redirect(url_for('index'))  # Replace with the appropriate route

    # Render the form with the list of services
    return render_template('nova-ordem.html', servicos=servicos)


# Rota para salvar a ordem de serviço
@app.route('/salvar_ordem', methods=['POST'])
def salvar_ordem():
    if request.method == 'POST':
        animal_id = request.form['animal']
        cliente_id = request.form['cliente']
        servicos_ids = request.form.getlist('servicos[]')
        valor_total = float(request.form['valor_total'])
        data_ordem = datetime.strptime(request.form['data_ordem'], '%Y-%m-%d')
        descricao = request.form['descricao']

        # Example: You may want to check if the animal, client, and services exist in the database
        # animal = Animal.query.get(animal_id)
        # cliente = Cliente.query.get(cliente_id)
        # servicos = Servico.query.filter(Servico.id_ser.in_(servicos_ids)).all()

        # Create a new order and add it to the database
        nova_ordem = OrdemDeServico(
            tipo='Tipo Exemplo',
            descricao=descricao,
            valorTotal=valor_total,
            data_in=data_ordem,
            Usuario_id_us=1,  # Replace with the actual user ID
            Cliente_idCliente=cliente_id,
            Animal_id_an=animal_id,
            Animal_Cliente_idCliente=cliente_id
        )

        # Associate services with the order
        # nova_ordem.servicos.extend(servicos)

        db.session.add(nova_ordem)

        try:
            db.session.commit()
            flash('Ordem de serviço adicionada com sucesso.', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Erro ao adicionar a ordem de serviço.', 'error')

        return redirect(url_for('index'))  
    

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



# ------------------ fim das Rotas de Ordens -----------------------------------

#---------------- Rotas de serviço --------------------------------------
@app.route('/lista_servicos', methods=['GET'])
def lista_servicos():
    show_all = request.args.get('showAll', default=False, type=bool)
    search_term = request.args.get('searchTerm', default='', type=str).strip()

    # Lógica para obter a lista de servicos com base nos parâmetros de consulta
    if show_all:
        servicos = Servico.query.all()
    else:
       servicos = Servico.query.filter(func.lower(Servico.tipo).contains(func.lower(search_term))).all()

    return render_template('lista_servicos.html', servicos=servicos, show_all=show_all, search_term=search_term)


@app.route('/servicos', methods=['GET', 'POST'])
def listar_servicos():
    if request.method == 'POST':
        # Process the form data when a new service is added
        tipo_servico = request.form['tipo_servico']
        valor_servico = request.form['valor_servico']

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
        tipo_servico = request.form['tipo_servico']
        valor_servico = request.form['valor_servico']

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
            servico.tipo = tipo_servico
            servico.valor = valor_servico

            db.session.commit()
            flash('Serviço atualizado com sucesso.', 'success')
            return redirect(url_for('listar_servicos'))

    return render_template('editar_servico.html', servico=servico)

@app.route('/excluir_servico/<int:servico_id>', methods=['GET', 'POST'])
def excluir_servico(servico_id):
    servico = Servico.query.get_or_404(servico_id)

    db.session.delete(servico)
    db.session.commit()

    flash('Serviço excluído com sucesso.', 'success')
    return redirect(url_for('listar_servicos'))
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

 

    return render_template('criar_usuario.html')

# Proteção de rotas
@app.before_request
def before_request():
    # Lista de rotas públicas
    rotas_publicas = ['login', 'redirecionar_para_login']

    # Verifica se a rota está nas rotas públicas
    if request.endpoint and request.endpoint not in rotas_publicas:
        if 'username' not in session:
            return redirect(url_for('login', next=request.endpoint))

# ------------------ fim rotas de Usuario -----------------------------------


if __name__ == '__main__':
   # with app.app_context():
   #     db.create_all()
   
    app.run(debug=True)

#     # Apaga o banco e recomeça
#with app.app_context():
   #     db.drop_all()
   # db.create_all()
