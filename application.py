import os

from flask import Flask, render_template, request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

engine = create_engine("postgresql://postgres:123@localhost/projeto1db")
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        bk = db.execute('SELECT * FROM books LIMIT 15')
        return render_template("home.html", bk=bk)
    else:
        tipo= request.form.get('tipo')
        input= request.form.get('input')
        if input == '':
            bk = db.execute('SELECT * FROM books LIMIT 15')
        elif tipo == 'autor':
            bk = db.execute('SELECT * FROM books WHERE author ILIKE :autor LIMIT 15', {"autor": '%'+input+'%'})
        elif tipo == 'livro':
            bk = db.execute('SELECT * FROM books WHERE title ILIKE :livro LIMIT 15', {"livro": '%'+input+'%'})
        elif tipo == 'ano':
            bk = db.execute('SELECT * FROM books WHERE year = :y LIMIT 15', {"y": input})
        else:
            bk = db.execute('SELECT * FROM books WHERE isbn ILIKE :isbn LIMIT 15', {"isbn": '%'+input+'%'})
        return render_template("home.html", bk=bk)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method=='GET':
        return render_template("login.html")
    else:
            user     = request.form.get("username")
            password = request.form.get("password")
            v = db.execute(
                "SELECT * FROM users WHERE username = :user AND password = :pass",
                 {"user":user, "pass":password}
                                                    ).fetchall()
            if v != []:
                return render_template("home.html")
            else:
                return render_template("login_erro.html", erro='usuário ou senha incorretos')


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

@app.route('/<livro>')
def livro(livro):
    return render_template('book.html')


    if __name__ == "__main__":
        app.run()
