from flask import Flask, render_template, request

app = Flask(__name__)


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

        print("E-mail:", email)
        print("Senha:", senha)

    return render_template("login.html")


# Registro
@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "POST":

        nome = request.form["nome"]
        email = request.form["email"]
        telefone = request.form["telefone"]
        dataNascimento = request.form["nascimento"]
        senha = request.form["senha"]
        confirmarSenha = request.form["confirmar"]

        print("Nome:", nome)
        print("E-mail:", email)
        print("Telefone:", telefone)
        print("Data de nascimento:", dataNascimento)
        print("Senha:", senha)
        print("Confirmação de senha:", confirmarSenha)

    return render_template("register.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
