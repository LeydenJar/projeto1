import os

from flask import Flask, render_template, request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

engine = create_engine("postgresql://postgres:123@localhost/projeto1db")
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/registro", methods=['POST', 'GET'])
def registro():
    if request.method == 'GET':
        return render_template("registro.html")
    else:
        #Comparando e-mails #verificando se o email ja consta no db
        email = request.form.get('e-mail')
        cemail = request.form.get('confirmar e-mail')
        vemail = email == cemail

        emailv = db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).fetchall()
        if emailv == []:
            emailv=True
        else:
            emailv = False


        #verificando tamanho do usuario#     #verificando se o username ja existe no db
        usuario = request.form.get("username")
        tamanho_username = len(usuario)

        userv=db.execute("SELECT * FROM users WHERE username = :user", {"user": usuario}).fetchall()
        if userv == []:
            userv=True
        else:
            userv=False


        #verificando tamanho da senha#
        senha = request.form.get("password")
        tamanho_senha = len(senha)

        #verificando se o usuario topou os termos#
        topou = request.form.get('termos')

        if vemail and tamanho_senha > 5 and tamanho_username > 5 and topou and userv and emailv:
            db.execute("INSERT INTO users(username, password, email) VALUES (:user, :pass, :email)",
            {"user":usuario, "pass":senha, "email":email})
            db.commit()
            return render_template("sucesso.html")
        elif tamanho_senha<=5 or tamanho_username<=5:
            return render_template("registro_erro.html", erro='erro: usuario e senha devem ter no minimo 6 caracteres')
        elif not vemail:
            return render_template("registro_erro.html", erro='erro: os e-mails digitados são diferentes')
        elif not userv:
            return render_template("registro_erro.html", erro='erro: O username ja existe, escolha outro')
        elif not emailv:
            return render_template("registro_erro.html", erro='erro: O email ja existe, escolha outro')
        else:
            return render_template("registro_erro.html", erro='erro: É necessário aceitar os termos')


@app.route("/validarl", methods=["POST"])
def validarl():
    user     = request.form.get("username")
    password = request.form.get("password")
    v = db.execute(
        "SELECT * FROM users WHERE username = :user AND password = :pass",
         {"user":user, "pass":password}
                                            ).fetchall()
    if v != []:
        return render_template("layout2.html", retorno=v)
    else:
        return render_template("login.html")



    if __name__ == "__main__":
        app.run()
