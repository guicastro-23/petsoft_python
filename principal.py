from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask import request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import func
import re
from flask import jsonify
from flask_migrate import Migrate
from functools import wraps


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:senha123@127.0.0.1/petsoft'
app.config['SECRET_KEY'] = 'chave_secreta'  
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# Definindo modelos para as tabelas do banco de dados
class Cliente(db.Model):
    idCliente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(80), nullable=False)
    logradouro = db.Column(db.String(80), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)

class Animal(db.Model):
    id_an = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(80), nullable=False)
    data_nasc = db.Column(db.Date, nullable=False)
    pelagem = db.Column(db.String(50))
    porte = db.Column(db.String(20))
    agressivo = db.Column(db.Enum('Sim', 'Não'))
    obs = db.Column(db.String(100))

    # Chave estrangeira referenciando a tabela Cliente
    Cliente_idCliente = db.Column(db.Integer, db.ForeignKey('cliente.idCliente'), nullable=False)

    # Relacionamento com o Cliente
    cliente = db.relationship('Cliente', backref=db.backref('animais', lazy=True))


class Usuario(db.Model):
    id_us = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login = db.Column(db.String(100), nullable=False)
    senha = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(100), nullable=False)

class Servico(db.Model):
    id_ser = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo = db.Column(db.String(10))
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

        # If validation passes, add the new client to the database
        novo_cliente = Cliente(nome=nome_cliente, telefone=telefone_cliente, logradouro=endereco_cliente)
        db.session.add(novo_cliente)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Um cliente com o mesmo nome já existe.', 'error')
        
        return redirect(url_for('listar_clientes'))


@app.route('/animais', methods=['GET', 'POST'])
def listar_animais():
    if request.method == 'GET':
        animais = Animal.query.all()
        clientes = Cliente.query.all()
        return render_template('animais.html', animais=animais, clientes=clientes)

    elif request.method == 'POST':
        # Obter os dados do formulário
        nome_animal = request.form.get('nome_animal')
        cliente_id = request.form.get('cliente_animal')
        data_nasc = request.form.get('data_nasc_animal')
        pelagem = request.form.get('pelagem_animal')
        porte = request.form.get('porte_animal')
        agressivo = request.form.get('agressivo_animal')  # Verificar se a caixa de seleção agressivo está marcada
        obs = request.form.get('observacoes_animal')


        # Validar o nome do animal usando expressão regular

        if not re.match(r"^[A-Za-zÀ-ú ]+$", nome_animal):
            flash('O nome do animal deve conter apenas letras e espaços.', 'error')
            return redirect(url_for('listar_animais'))
        
        # Verificar se o cliente existe
        cliente = Cliente.query.get(cliente_id)
        if cliente is None:
            flash('Cliente não encontrado.', 'error')
            return redirect(url_for('listar_animais'))

        # Verificar se o animal já tem um dono
        if Animal.query.filter_by(nome=nome_animal).first():
            flash('Já existe um animal com esse nome.', 'error')
            return redirect(url_for('listar_animais'))
        
        #  # Verificar se a pelagem é válida
        # pelagens_validas = ['Curta', 'Dupla', 'Longa', 'Longa e Curta','Encaracolada']
        # if pelagem not in pelagens_validas:
        #     flash('Pelagem do animal inválida.', 'error')
        #     return redirect(url_for('listar_animais'))

        # # Verificar se o porte é válido
        # portes_validos = ['Pequeno', 'Médio', 'Grande']
        # if porte not in portes_validos:
        #     flash('Porte do animal inválido.', 'error')
        #     return redirect(url_for('listar_animais'))

        # Se todas as verificações passarem, criar o novo animal
        novo_animal = Animal(
            nome=nome_animal,
            data_nasc=data_nasc,
            Cliente_idCliente=cliente_id,
            pelagem=pelagem,
            porte=porte,
            agressivo=agressivo,
            obs=obs
        )

        db.session.add(novo_animal)
        
        try:
            db.session.commit()
            flash('Animal adicionado com sucesso.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar o animal: {str(e)}', 'error')

        return redirect(url_for('listar_animais'))

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
    
    

# ------------------ fim das Rotas de Ordens -----------------------------------



#--------------------- rotas de serviço ------------------------------------------#
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
# ------------------ fim rotas de serviço --------------------------------------



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

# Proteção de rotas
@app.before_request
def before_request():
    rotas_publicas = ['login', 'logout']
    if request.endpoint and request.endpoint not in rotas_publicas:
        if 'username' not in session:
            flash('Você precisa fazer login para acessar esta página.', 'error')
            return redirect(url_for('login', next=request.endpoint))

        
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    #with app.app_context():
       # db.create_all()
    app.run(debug=True)


#     # Apaga o banco e recomeça
# with app.app_context():
#     db.drop_all()
#     db.create_all()