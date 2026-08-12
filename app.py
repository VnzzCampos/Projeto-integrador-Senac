from datetime import date

from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "troque-esta-chave-por-uma-secreta-em-producao"

def conectar_banco():
    banco = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456789",
        database="ebd"
    )

    return banco


def criar_tabela_alunos(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alunos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(150) NOT NULL,
            telefone VARCHAR(20),
            nascimento DATE,
            curso VARCHAR(100) DEFAULT NULL,
            cadastrado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Compatibilidade com a versão anterior da tabela, que exigia e-mail e curso.
    cursor.execute("SHOW COLUMNS FROM alunos LIKE 'email'")
    if cursor.fetchone():
        cursor.execute("ALTER TABLE alunos MODIFY email VARCHAR(150) NULL")

    cursor.execute("SHOW COLUMNS FROM alunos LIKE 'curso'")
    if cursor.fetchone():
        cursor.execute("ALTER TABLE alunos MODIFY curso VARCHAR(100) NULL")

    cursor.execute("SHOW COLUMNS FROM alunos LIKE 'usuario_id'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE alunos ADD usuario_id INT NULL UNIQUE")


def criar_tabela_frequencias(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frequencias (
            id INT AUTO_INCREMENT PRIMARY KEY,
            aluno_id INT NOT NULL,
            turma_id INT NULL,
            data_aula DATE NOT NULL,
            status ENUM('presente', 'falta') NOT NULL,
            registrado_por INT NOT NULL,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY frequencia_por_aluno_turma_data (aluno_id, turma_id, data_aula),
            CONSTRAINT fk_frequencia_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE,
            CONSTRAINT fk_frequencia_responsavel FOREIGN KEY (registrado_por) REFERENCES usuarios(id) ON DELETE RESTRICT
        )
    """)

    cursor.execute("SHOW COLUMNS FROM frequencias LIKE 'turma_id'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE frequencias ADD turma_id INT NULL AFTER aluno_id")
        cursor.execute("ALTER TABLE frequencias DROP INDEX frequencia_por_aluno_e_data")
        cursor.execute("""
            ALTER TABLE frequencias
            ADD UNIQUE KEY frequencia_por_aluno_turma_data (aluno_id, turma_id, data_aula)
        """)


def criar_tabelas_turmas(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turmas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL UNIQUE,
            descricao VARCHAR(255) DEFAULT NULL,
            criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def criar_tabela_ofertas(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ofertas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            turma_id INT NOT NULL,
            usuario_id INT NULL,
            valor DECIMAL(10, 2) NOT NULL,
            data_oferta DATE NOT NULL,
            observacao VARCHAR(255) DEFAULT NULL,
            registrado_por INT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_oferta_turma FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE CASCADE,
            CONSTRAINT fk_oferta_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
            CONSTRAINT fk_oferta_registrado FOREIGN KEY (registrado_por) REFERENCES usuarios(id) ON DELETE RESTRICT
        )
    """)


def criar_tabelas_conteudo(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materiais (
            id INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(150) NOT NULL,
            descricao VARCHAR(255) DEFAULT NULL,
            link VARCHAR(500) NOT NULL,
            turma_id INT NULL,
            publicado_por INT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_material_turma FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE SET NULL,
            CONSTRAINT fk_material_publicador FOREIGN KEY (publicado_por) REFERENCES usuarios(id) ON DELETE RESTRICT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anuncios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(150) NOT NULL,
            conteudo TEXT NOT NULL,
            publicado_por INT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_anuncio_publicador FOREIGN KEY (publicado_por) REFERENCES usuarios(id) ON DELETE RESTRICT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS escalas_professores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            turma_id INT NOT NULL,
            professor_id INT NOT NULL,
            data_atividade DATE NOT NULL,
            atividade VARCHAR(150) NOT NULL,
            observacao VARCHAR(255) DEFAULT NULL,
            UNIQUE KEY escala_unica (turma_id, professor_id, data_atividade, atividade),
            CONSTRAINT fk_escala_turma FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE CASCADE,
            CONSTRAINT fk_escala_professor FOREIGN KEY (professor_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turma_professores (
            turma_id INT NOT NULL,
            professor_id INT NOT NULL,
            PRIMARY KEY (turma_id, professor_id),
            CONSTRAINT fk_turma_professor_turma FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE CASCADE,
            CONSTRAINT fk_turma_professor_usuario FOREIGN KEY (professor_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turma_alunos (
            turma_id INT NOT NULL,
            aluno_id INT NOT NULL,
            PRIMARY KEY (turma_id, aluno_id),
            CONSTRAINT fk_turma_aluno_turma FOREIGN KEY (turma_id) REFERENCES turmas(id) ON DELETE CASCADE,
            CONSTRAINT fk_turma_aluno_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE
        )
    """)


def garantir_cargo_usuarios(cursor):
    cursor.execute("SHOW COLUMNS FROM usuarios LIKE 'cargo'")
    if not cursor.fetchone():
        cursor.execute(
            "ALTER TABLE usuarios ADD cargo VARCHAR(20) NOT NULL DEFAULT 'aluno'"
        )


def usuario_e_administrador():
    if "usuario_id" not in session:
        return False

    banco = conectar_banco()
    cursor = banco.cursor(dictionary=True)
    try:
        garantir_cargo_usuarios(cursor)
        banco.commit()
        cursor.execute(
            "SELECT cargo FROM usuarios WHERE id = %s",
            (session["usuario_id"],)
        )
        usuario = cursor.fetchone()
        return usuario is not None and usuario["cargo"] == "administrador"
    finally:
        cursor.close()
        banco.close()


def usuario_pode_lancar_frequencia():
    if "usuario_id" not in session:
        return False

    banco = conectar_banco()
    cursor = banco.cursor(dictionary=True)
    try:
        garantir_cargo_usuarios(cursor)
        banco.commit()
        cursor.execute("SELECT cargo FROM usuarios WHERE id = %s", (session["usuario_id"],))
        usuario = cursor.fetchone()
        return usuario is not None and usuario["cargo"] in ("professor", "administrador")
    finally:
        cursor.close()
        banco.close()

# Página inicial → Login
@app.route("/")
def homePage():
    return render_template("login.html")


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))


# Login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        senha = request.form["senha"]

        banco = conectar_banco()
        cursor = banco.cursor(dictionary=True)

        sql = """
            SELECT id, nome, email, senha
            FROM usuarios
            WHERE email = %s
        """

        cursor.execute(sql, (email,))

        usuario = cursor.fetchone()

        cursor.close()
        banco.close()

        # Verifica se o usuário existe
        if usuario is None:
            return render_template(
                "login.html",
                mensagem="Usuário não encontrado. Verifique o e-mail informado ou cadastre-se."
            )

        # Verifica a senha usando somente o hash armazenado.
        if check_password_hash(usuario["senha"], senha):

            session["usuario_id"] = usuario["id"]

            return redirect(url_for("inicio"))

        else:

            return render_template(
                "login.html",
                mensagem="E-mail ou senha incorretos."
            )

    return render_template("login.html")


# Registro
@app.route("/registro", methods=["GET", "POST"])
def registro():

    # Quando apenas abre a página de cadastro
    if request.method == "GET":
        return render_template("register.html")

    # Pegando os dados do formulário
    nome = request.form["nome"]
    email = request.form["email"]
    telefone = request.form["telefone"]
    dataNascimento = request.form["nascimento"]
    senha = request.form["senha"]
    confirmarSenha = request.form["confirmar"]

    # Verifica se as senhas são iguais
    if senha != confirmarSenha:
        return render_template(
            "register.html",
            mensagem="As senhas não são iguais."
        )
    
    senhaHash = generate_password_hash(senha)

    banco = conectar_banco()
    cursor = banco.cursor()

    sql = """
        INSERT INTO usuarios
        (nome, email, telefone, nascimento, senha)
        VALUES (%s, %s, %s, %s, %s)
    """

    valores = (
        nome,
        email,
        telefone,
        dataNascimento,
        senhaHash
    )

    try:

        # Tenta cadastrar o usuário
        cursor.execute(sql, valores)

        # Salva no banco
        banco.commit()

        print("Usuário cadastrado com sucesso!")

        # Vai para a página de login
        return redirect(url_for("login"))

    except mysql.connector.IntegrityError as erro:

        if "usuarios.email" in str(erro):
            mensagem = "Este e-mail já está cadastrado."

        elif "usuarios.telefone" in str(erro):
            mensagem = "Este telefone já está cadastrado."

        elif "usuarios.nome" in str(erro):
            mensagem = "Este nome já está cadastrado."

        else:
            mensagem = "Não foi possível realizar o cadastro."

        return render_template(
            "register.html",
            mensagem=mensagem
        )

    finally:

        cursor.close()
        banco.close()


@app.route("/inicio", methods=["GET", "POST"])
def inicio():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "inicio.html",
        administrador=usuario_e_administrador(),
        pode_lancar_frequencia=usuario_pode_lancar_frequencia()
    )


@app.route("/perfil")
def perfil():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    banco = conectar_banco()
    cursor = banco.cursor(dictionary=True)
    cursor.execute(
        "SELECT nome, email, telefone, nascimento FROM usuarios WHERE id = %s",
        (session["usuario_id"],)
    )
    usuario = cursor.fetchone()
    cursor.close()
    banco.close()

    if usuario is None:
        session.clear()
        return redirect(url_for("login"))

    return render_template(
        "perfil.html",
        usuario=usuario,
        administrador=usuario_e_administrador()
    )


@app.route("/alunos/cadastrar", methods=["GET", "POST"])
def cadastrar_aluno():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if not usuario_e_administrador():
        return redirect(url_for("inicio"))

    banco = conectar_banco()
    cursor = banco.cursor(dictionary=True)

    try:
        criar_tabela_alunos(cursor)
        garantir_cargo_usuarios(cursor)
        banco.commit()

        if request.method == "POST":
            usuarios_ids = request.form.getlist("usuarios_ids")
            if not usuarios_ids:
                raise ValueError
            try:
                usuarios_ids = [int(usuario_id) for usuario_id in usuarios_ids]
            except ValueError:
                raise ValueError
            marcadores = ", ".join(["%s"] * len(usuarios_ids))
            cursor.execute("""
                SELECT usuarios.id, usuarios.nome, usuarios.telefone, usuarios.nascimento
                FROM usuarios LEFT JOIN alunos ON alunos.usuario_id = usuarios.id
                WHERE usuarios.id IN ({}) AND usuarios.cargo = 'aluno' AND alunos.usuario_id IS NULL
            """.format(marcadores), tuple(usuarios_ids))
            usuarios = cursor.fetchall()
            if len(usuarios) != len(set(usuarios_ids)):
                raise ValueError
            cursor.executemany("""
                INSERT INTO alunos (usuario_id, nome, telefone, nascimento)
                VALUES (%s, %s, %s, %s)
            """, [(usuario["id"], usuario["nome"], usuario["telefone"], usuario["nascimento"]) for usuario in usuarios])
            banco.commit()
            return redirect(url_for("cadastrar_aluno", sucesso=str(len(usuarios))))

        cursor.execute("""
            SELECT usuarios.id, usuarios.nome, usuarios.email, usuarios.telefone
            FROM usuarios LEFT JOIN alunos ON alunos.usuario_id = usuarios.id
            WHERE usuarios.cargo = 'aluno' AND alunos.usuario_id IS NULL
            ORDER BY usuarios.nome
        """)
        mensagem = "Não foi possível cadastrar o aluno. Escolha uma conta disponível." if request.method == "POST" else None
        return render_template("cadastrar_aluno.html", usuarios=cursor.fetchall(), mensagem=mensagem,
                               sucesso="{} aluno(s) vinculado(s) com sucesso.".format(request.args.get("sucesso")) if request.args.get("sucesso") else None)
    except (mysql.connector.IntegrityError, ValueError):
        banco.rollback()
        cursor.execute("""
            SELECT usuarios.id, usuarios.nome, usuarios.email, usuarios.telefone
            FROM usuarios LEFT JOIN alunos ON alunos.usuario_id = usuarios.id
            WHERE usuarios.cargo = 'aluno' AND alunos.usuario_id IS NULL
            ORDER BY usuarios.nome
        """)
        return render_template("cadastrar_aluno.html", usuarios=cursor.fetchall(),
                               mensagem="Não foi possível cadastrar o aluno. Escolha uma conta disponível.")
    finally:
        cursor.close()
        banco.close()


@app.route("/turmas/nova", methods=["GET", "POST"])
def cadastrar_turma():
    if "usuario_id" not in session or not usuario_e_administrador():
        return redirect(url_for("inicio"))

    banco = conectar_banco()
    cursor = banco.cursor(dictionary=True)
    mensagem = None
    sucesso = None
    try:
        criar_tabela_alunos(cursor)
        garantir_cargo_usuarios(cursor)
        criar_tabelas_turmas(cursor)
        banco.commit()

        if request.method == "POST":
            nome = request.form.get("nome", "").strip()
            descricao = request.form.get("descricao", "").strip()
            professores_ids = request.form.getlist("professores")
            alunos_ids = request.form.getlist("alunos")

            if not nome:
                mensagem = "Informe o nome da turma."
            elif not professores_ids:
                mensagem = "Selecione pelo menos um professor para a turma."
            else:
                try:
                    cursor.execute(
                        "INSERT INTO turmas (nome, descricao) VALUES (%s, %s)",
                        (nome, descricao or None)
                    )
                    turma_id = cursor.lastrowid
                    cursor.executemany(
                        "INSERT INTO turma_professores (turma_id, professor_id) VALUES (%s, %s)",
                        [(turma_id, professor_id) for professor_id in professores_ids]
                    )
                    if alunos_ids:
                        cursor.executemany(
                            "INSERT INTO turma_alunos (turma_id, aluno_id) VALUES (%s, %s)",
                            [(turma_id, aluno_id) for aluno_id in alunos_ids]
                        )
                    banco.commit()
                    sucesso = "Turma criada e participantes vinculados com sucesso."
                except mysql.connector.IntegrityError:
                    banco.rollback()
                    mensagem = "Não foi possível criar a turma. Verifique se o nome já está em uso."

        cursor.execute("SELECT id, nome FROM usuarios WHERE cargo = 'professor' ORDER BY nome")
        professores = cursor.fetchall()
        cursor.execute("SELECT id, nome, telefone FROM alunos ORDER BY nome")
        alunos = cursor.fetchall()
        return render_template("cadastrar_turma.html", professores=professores, alunos=alunos,
                               mensagem=mensagem, sucesso=sucesso)
    finally:
        cursor.close()
        banco.close()


@app.route("/relatorios/turmas")
def relatorio_turmas():
    if "usuario_id" not in session or not usuario_e_administrador():
        return redirect(url_for("inicio"))

    banco = conectar_banco()
    cursor = banco.cursor(dictionary=True)
    try:
        criar_tabela_alunos(cursor)
        criar_tabela_frequencias(cursor)
        criar_tabelas_turmas(cursor)
        banco.commit()

        cursor.execute("SELECT id, nome, descricao FROM turmas ORDER BY nome")
        turmas = cursor.fetchall()
        turma_id = request.args.get("turma", type=int)
        turma = next((item for item in turmas if item["id"] == turma_id), None)
        relatorio = []
        professores = []

        if turma:
            cursor.execute("""
                SELECT usuarios.nome FROM turma_professores
                JOIN usuarios ON usuarios.id = turma_professores.professor_id
                WHERE turma_professores.turma_id = %s ORDER BY usuarios.nome
            """, (turma_id,))
            professores = cursor.fetchall()
            cursor.execute("""
                SELECT alunos.nome, alunos.telefone,
                    SUM(frequencias.status = 'presente') AS presencas,
                    SUM(frequencias.status = 'falta') AS faltas,
                    COUNT(frequencias.id) AS lancamentos
                FROM turma_alunos
                JOIN alunos ON alunos.id = turma_alunos.aluno_id
                LEFT JOIN frequencias ON frequencias.aluno_id = alunos.id AND frequencias.turma_id = %s
                WHERE turma_alunos.turma_id = %s
                GROUP BY alunos.id, alunos.nome, alunos.telefone
                ORDER BY alunos.nome
            """, (turma_id, turma_id))
            relatorio = cursor.fetchall()
            for aluno in relatorio:
                aluno["presencas"] = aluno["presencas"] or 0
                aluno["faltas"] = aluno["faltas"] or 0
                aluno["percentual"] = round((aluno["presencas"] / aluno["lancamentos"] * 100), 1) if aluno["lancamentos"] else None

        return render_template("relatorio_turmas.html", turmas=turmas, turma=turma,
                               professores=professores, relatorio=relatorio)
    finally:
        cursor.close()
        banco.close()


@app.route("/ofertas", methods=["GET", "POST"])
def ofertas():
    if "usuario_id" not in session or not usuario_e_administrador():
        return redirect(url_for("inicio"))

    banco = conectar_banco()
    cursor = banco.cursor(dictionary=True)
    mensagem = None
    sucesso = None
    try:
        criar_tabela_alunos(cursor)
        criar_tabelas_turmas(cursor)
        criar_tabela_ofertas(cursor)
        banco.commit()

        if request.method == "POST":
            try:
                turma_id = int(request.form.get("turma_id", ""))
                usuario_id = int(request.form.get("usuario_id", "")) if request.form.get("usuario_id") else None
                valor = float(request.form.get("valor", "").replace(",", "."))
            except ValueError:
                turma_id, usuario_id, valor = 0, None, 0
            data_oferta = request.form.get("data_oferta", date.today().isoformat())
            observacao = request.form.get("observacao", "").strip()
            if turma_id and valor > 0:
                cursor.execute("""
                    INSERT INTO ofertas (turma_id, usuario_id, valor, data_oferta, observacao, registrado_por)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (turma_id, usuario_id, valor, data_oferta, observacao or None, session["usuario_id"]))
                banco.commit()
                sucesso = "Oferta ilustrativa registrada com sucesso."
            else:
                mensagem = "Informe uma turma e um valor maior que zero."

        cursor.execute("SELECT id, nome FROM turmas ORDER BY nome")
        turmas = cursor.fetchall()
        cursor.execute("SELECT id, nome, email FROM usuarios ORDER BY nome")
        usuarios = cursor.fetchall()
        cursor.execute("""
            SELECT ofertas.id, turmas.nome AS turma, usuarios.nome AS pessoa, ofertas.valor,
                   ofertas.data_oferta, ofertas.observacao
            FROM ofertas JOIN turmas ON turmas.id = ofertas.turma_id
            LEFT JOIN usuarios ON usuarios.id = ofertas.usuario_id
            ORDER BY ofertas.data_oferta DESC, ofertas.id DESC LIMIT 30
        """)
        registros = cursor.fetchall()
        cursor.execute("SELECT COALESCE(SUM(valor), 0) AS total FROM ofertas")
        total = cursor.fetchone()["total"]
        return render_template("ofertas.html", turmas=turmas, usuarios=usuarios, registros=registros,
                               total=total, mensagem=mensagem, sucesso=sucesso, hoje=date.today().isoformat())
    finally:
        cursor.close()
        banco.close()


@app.route("/pagamento")
def pagamento():
    return render_template("pagamento.html")


@app.route("/comunicacao", methods=["GET", "POST"])
def comunicacao():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    banco = conectar_banco()
    cursor = banco.cursor(dictionary=True)
    try:
        criar_tabelas_turmas(cursor)
        criar_tabelas_conteudo(cursor)
        banco.commit()
        administrador = usuario_e_administrador()
        mensagem = None
        if request.method == "POST" and administrador:
            tipo = request.form.get("tipo")
            if tipo == "anuncio":
                titulo, conteudo = request.form.get("titulo", "").strip(), request.form.get("conteudo", "").strip()
                if titulo and conteudo:
                    cursor.execute("INSERT INTO anuncios (titulo, conteudo, publicado_por) VALUES (%s, %s, %s)", (titulo, conteudo, session["usuario_id"]))
                    banco.commit()
                else: mensagem = "Preencha título e conteúdo do anúncio."
            elif tipo == "material":
                titulo, link = request.form.get("titulo", "").strip(), request.form.get("link", "").strip()
                if titulo and link.startswith(("http://", "https://")):
                    turma_id = request.form.get("turma_id") or None
                    cursor.execute("INSERT INTO materiais (titulo, descricao, link, turma_id, publicado_por) VALUES (%s, %s, %s, %s, %s)", (titulo, request.form.get("descricao", "").strip() or None, link, turma_id, session["usuario_id"]))
                    banco.commit()
                else: mensagem = "Informe título e um link válido (http:// ou https://)."
        cursor.execute("SELECT id, nome FROM turmas ORDER BY nome")
        turmas = cursor.fetchall()
        cursor.execute("""SELECT anuncios.titulo, anuncios.conteudo, anuncios.criado_em, usuarios.nome AS autor FROM anuncios JOIN usuarios ON usuarios.id=anuncios.publicado_por ORDER BY anuncios.criado_em DESC""")
        anuncios = cursor.fetchall()
        cursor.execute("""SELECT materiais.titulo, materiais.descricao, materiais.link, turmas.nome AS turma FROM materiais LEFT JOIN turmas ON turmas.id=materiais.turma_id ORDER BY materiais.criado_em DESC""")
        materiais = cursor.fetchall()
        return render_template("comunicacao.html", administrador=administrador, turmas=turmas, anuncios=anuncios, materiais=materiais, mensagem=mensagem)
    finally:
        cursor.close(); banco.close()


@app.route("/escala", methods=["GET", "POST"])
def escala():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    banco = conectar_banco(); cursor = banco.cursor(dictionary=True)
    try:
        criar_tabelas_turmas(cursor); criar_tabelas_conteudo(cursor); garantir_cargo_usuarios(cursor); banco.commit()
        administrador = usuario_e_administrador(); mensagem = None
        if request.method == "POST" and administrador:
            try:
                cursor.execute("INSERT INTO escalas_professores (turma_id, professor_id, data_atividade, atividade, observacao) VALUES (%s,%s,%s,%s,%s)", (int(request.form["turma_id"]), int(request.form["professor_id"]), request.form["data_atividade"], request.form["atividade"].strip(), request.form.get("observacao", "").strip() or None)); banco.commit()
            except (ValueError, mysql.connector.Error): mensagem = "Não foi possível salvar a escala. Verifique os dados."
        cursor.execute("SELECT id,nome FROM turmas ORDER BY nome"); turmas = cursor.fetchall()
        cursor.execute("SELECT id,nome FROM usuarios WHERE cargo='professor' ORDER BY nome"); professores = cursor.fetchall()
        if administrador:
            cursor.execute("""SELECT escalas_professores.data_atividade, escalas_professores.atividade, escalas_professores.observacao, turmas.nome AS turma, usuarios.nome AS professor FROM escalas_professores JOIN turmas ON turmas.id=escalas_professores.turma_id JOIN usuarios ON usuarios.id=escalas_professores.professor_id ORDER BY data_atividade""")
        else:
            cursor.execute("""SELECT escalas_professores.data_atividade, escalas_professores.atividade, escalas_professores.observacao, turmas.nome AS turma, usuarios.nome AS professor FROM escalas_professores JOIN turmas ON turmas.id=escalas_professores.turma_id JOIN usuarios ON usuarios.id=escalas_professores.professor_id WHERE professor_id=%s ORDER BY data_atividade""", (session["usuario_id"],))
        return render_template("escala.html", administrador=administrador, turmas=turmas, professores=professores, escalas=cursor.fetchall(), mensagem=mensagem)
    finally:
        cursor.close(); banco.close()


@app.route("/desempenho")
def desempenho():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    banco = conectar_banco(); cursor = banco.cursor(dictionary=True)
    try:
        criar_tabelas_turmas(cursor); criar_tabela_frequencias(cursor); banco.commit()
        cursor.execute("""SELECT turmas.nome, COUNT(DISTINCT turma_alunos.aluno_id) AS alunos, COALESCE(ROUND(100 * SUM(frequencias.status='presente') / NULLIF(COUNT(frequencias.id),0),1),0) AS frequencia FROM turmas LEFT JOIN turma_alunos ON turma_alunos.turma_id=turmas.id LEFT JOIN frequencias ON frequencias.turma_id=turmas.id AND frequencias.aluno_id=turma_alunos.aluno_id GROUP BY turmas.id,turmas.nome ORDER BY turmas.nome""")
        turmas = cursor.fetchall()
        maior = max([float(turma["frequencia"]) for turma in turmas], default=0) or 1
        for turma in turmas: turma["largura"] = round(float(turma["frequencia"]) / maior * 100)
        return render_template("desempenho.html", turmas=turmas)
    finally:
        cursor.close(); banco.close()


@app.route("/frequencia", methods=["GET", "POST"])
def frequencia():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    if not usuario_pode_lancar_frequencia():
        return redirect(url_for("inicio"))

    data_aula = request.values.get("data", date.today().isoformat())
    try:
        data_aula = date.fromisoformat(data_aula).isoformat()
    except ValueError:
        data_aula = date.today().isoformat()

    banco = conectar_banco()
    cursor = banco.cursor(dictionary=True)
    sucesso = None
    try:
        criar_tabela_alunos(cursor)
        criar_tabelas_turmas(cursor)
        criar_tabela_frequencias(cursor)
        banco.commit()

        administrador = usuario_e_administrador()
        if administrador:
            cursor.execute("SELECT id, nome FROM turmas ORDER BY nome")
        else:
            cursor.execute("""
                SELECT turmas.id, turmas.nome FROM turma_professores
                JOIN turmas ON turmas.id = turma_professores.turma_id
                WHERE turma_professores.professor_id = %s ORDER BY turmas.nome
            """, (session["usuario_id"],))
        turmas = cursor.fetchall()

        try:
            turma_id = int(request.values.get("turma", ""))
        except ValueError:
            turma_id = 0
        turma = next((item for item in turmas if item["id"] == turma_id), None)
        if turma is None and turmas:
            turma = turmas[0]
            turma_id = turma["id"]

        if request.method == "POST" and turma:
            cursor.execute("SELECT aluno_id AS id FROM turma_alunos WHERE turma_id = %s", (turma_id,))
            lancamentos = []
            for aluno in cursor.fetchall():
                status = request.form.get("status_{}".format(aluno["id"]))
                if status in ("presente", "falta"):
                    lancamentos.append((aluno["id"], turma_id, data_aula, status, session["usuario_id"]))
            if lancamentos:
                cursor.executemany("""
                    INSERT INTO frequencias (aluno_id, turma_id, data_aula, status, registrado_por)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE status = VALUES(status), registrado_por = VALUES(registrado_por)
                """, lancamentos)
                banco.commit()
                sucesso = "Frequência da turma salva com sucesso."

        alunos = []
        if turma:
            cursor.execute("""
                SELECT alunos.id, alunos.nome, alunos.telefone, frequencias.status
                FROM turma_alunos JOIN alunos ON alunos.id = turma_alunos.aluno_id
                LEFT JOIN frequencias ON frequencias.aluno_id = alunos.id
                    AND frequencias.turma_id = %s AND frequencias.data_aula = %s
                WHERE turma_alunos.turma_id = %s ORDER BY alunos.nome
            """, (turma_id, data_aula, turma_id))
            alunos = cursor.fetchall()
        return render_template("frequencia.html", alunos=alunos, data_aula=data_aula,
                               sucesso=sucesso, administrador=administrador, turmas=turmas,
                               turma=turma, turma_id=turma_id)
    finally:
        cursor.close()
        banco.close()


@app.route("/gestao", methods=["GET", "POST"])
def gestao():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if not usuario_e_administrador():
        return redirect(url_for("inicio"))

    mensagem = None
    sucesso = None
    banco = conectar_banco()
    cursor = banco.cursor(dictionary=True)

    try:
        garantir_cargo_usuarios(cursor)
        banco.commit()

        if request.method == "POST":
            tipo = request.form.get("tipo")
            acao = request.form.get("acao")

            try:
                registro_id = int(request.form.get("id", ""))
            except ValueError:
                registro_id = 0

            if tipo == "usuario" and acao == "definir_cargo" and registro_id:
                cargo = request.form.get("cargo")
                if cargo not in ("aluno", "professor"):
                    mensagem = "Selecione um cargo válido."
                else:
                    cursor.execute(
                        "UPDATE usuarios SET cargo = %s WHERE id = %s",
                        (cargo, registro_id)
                    )
                    banco.commit()
                sucesso = "Cargo do usuário atualizado."

            elif tipo == "usuario" and acao == "excluir" and registro_id:
                if registro_id == session["usuario_id"]:
                    mensagem = "Você não pode excluir a própria conta."
                else:
                    cursor.execute("DELETE FROM usuarios WHERE id = %s", (registro_id,))
                    banco.commit()
                    sucesso = "Usuário excluído com sucesso."
            else:
                mensagem = "Ação inválida."

        cursor.execute("SELECT id, nome, email, telefone, cargo FROM usuarios ORDER BY nome")
        usuarios = cursor.fetchall()
        cursor.execute("""
            SELECT nome, email, cargo FROM usuarios WHERE id = %s
        """, (session["usuario_id"],))
        usuario_atual = cursor.fetchone()
        cursor.execute("""
            SELECT id, nome, email, telefone, nascimento, cargo
            FROM usuarios
            WHERE cargo = 'professor'
            ORDER BY nome
        """)
        professores = cursor.fetchall()

        return render_template(
            "gestao.html",
            usuarios=usuarios,
            professores=professores,
            mensagem=mensagem,
            sucesso=sucesso,
            usuario_atual_id=session["usuario_id"],
            usuario_atual=usuario_atual
        )
    finally:
        cursor.close()
        banco.close()

banco = conectar_banco()

if banco.is_connected():
        print("Conectado ao MySQL com sucesso!")
banco.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
