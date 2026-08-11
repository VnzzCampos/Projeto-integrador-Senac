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

# Página inicial → Login
@app.route("/")
def homePage():
    return render_template("login.html")


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
                mensagem="E-mail ou senha incorretos."
            )

        # Verifica a senha usando o hash
        if check_password_hash(usuario["senha"], senha):

            print("Login realizado com sucesso!")
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

    return render_template("inicio.html", administrador=usuario_e_administrador())


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

    if request.method == "GET":
        return render_template("cadastrar_aluno.html")

    nome = request.form["nome"].strip()
    telefone = request.form["telefone"].strip()
    nascimento = request.form["nascimento"]

    banco = conectar_banco()
    cursor = banco.cursor()

    try:
        criar_tabela_alunos(cursor)
        cursor.execute("""
            INSERT INTO alunos (nome, telefone, nascimento)
            VALUES (%s, %s, %s)
        """, (nome, telefone, nascimento or None))
        banco.commit()
        return render_template(
            "cadastrar_aluno.html",
            sucesso="Aluno cadastrado com sucesso."
        )
    except mysql.connector.IntegrityError:
        return render_template(
            "cadastrar_aluno.html",
            mensagem="Não foi possível cadastrar o aluno. Verifique os dados informados."
        )
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

            if tipo == "usuario" and acao == "promover" and registro_id:
                cursor.execute("""
                    UPDATE usuarios
                    SET cargo = CASE cargo
                        WHEN 'aluno' THEN 'professor'
                        WHEN 'professor' THEN 'administrador'
                        ELSE cargo
                    END
                    WHERE id = %s
                """, (registro_id,))
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
            usuario_atual_id=session["usuario_id"]
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
