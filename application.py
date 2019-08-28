import os

from flask_sqlalchemy  import SQLAlchemy
from flask import Flask, render_template, request, session, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

app = Flask(__name__)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "secret"


def getlog():
    try:
        u = session["user"]
    except:
        u = None
    return u

@app.route("/", methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        bk = db.execute('SELECT * FROM books LIMIT 15')
        return render_template("home.html", bk=bk, u=getlog())
    else:
        tipo= request.form.get('tipo')
        input= request.form.get('input')
        if input == '':
            bk = db.execute('SELECT * FROM books LIMIT 15').fetchall()
        elif tipo == 'autor':
            bk = db.execute('SELECT * FROM books WHERE author ILIKE :autor LIMIT 15', {"autor": '%'+input+'%'}).fetchall()
        elif tipo == 'livro':
            bk = db.execute('SELECT * FROM books WHERE title ILIKE :livro LIMIT 15', {"livro": '%'+input+'%'}).fetchall()
        elif tipo == 'ano':
            bk = db.execute('SELECT * FROM books WHERE year = :y LIMIT 15', {"y": input}).fetchall()
        else:
            bk = db.execute('SELECT * FROM books WHERE isbn ILIKE :isbn LIMIT 15', {"isbn": '%'+input+'%'}).fetchall()

        if len(bk) == 0:
            return render_template("home.html", bk=bk, u=getlog(), erro = "Desculpe, sua pesquisa não retornou resultados...")
        return render_template("home.html", bk=bk, u=getlog())


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method=='GET':
        return render_template("login.html", u=getlog())
    else:
            user     = request.form.get("username")
            password = request.form.get("password")
            v = db.execute(
                "SELECT * FROM users WHERE username = :user AND password = :pass",
                 {"user":user, "pass":password}
                                                    ).fetchall()
            if v != []:
                session["user"] = user
                session["password"] = password
                bk = db.execute('SELECT * FROM books LIMIT 15')
                return render_template("home.html", bk=bk, u=getlog())
            else:
                return render_template("login_erro.html", erro='usuário ou senha incorretos', u=getlog())




@app.route("/registro", methods=['POST', 'GET'])
def registro():
    if request.method == 'GET':
        return render_template("registro.html", u=getlog())
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
            return render_template("sucesso.html", u=getlog())
        elif tamanho_senha<=5 or tamanho_username<=5:
            erro='erro: usuario e senha devem ter no minimo 6 caracteres'
        elif not vemail:
            erro='erro: os e-mails digitados são diferentes'
        elif not userv:
            erro='erro: O username ja existe, escolha outro'
        elif not emailv:
            erro='erro: O email ja existe, escolha outro'
        else:
            erro='erro: É necessário aceitar os termos'

        return render_template("registro_erro.html", erro=erro, u=getlog())

@app.route('/<livro>', methods=['GET','POST'])
def livro(livro):
    if request.method == 'POST':
        user = session["user"]
        #caso o usuário não esteja logado, retorne um erro
        if user == None:
            return render_template("login_erro.html", erro='Erro: faça login para deixar seus reviews', u=getlog())

        else:
            #confira se o usuario ja deixou um review
            p=db.execute("SELECT * FROM reviews WHERE usuario = :u AND livro = :livro", {'u' : session["user"], 'livro':livro}).fetchall()

            re = request.form.get('rev')
            avaliacao = request.form.get('nota')

            #se ele não deixou nenhum review, crie o review dele
            if p == []:
                db.execute('INSERT INTO reviews (pitaco, livro, usuario, avaliacao) VALUES (:review , :livro , :usuario, :avaliacao)', {'review' : re, 'livro' : livro, 'usuario':session['user'], 'avaliacao':avaliacao})
                db.commit()

            #se ele ja deixou, atualize.
            else:
                db.execute('UPDATE reviews SET pitaco = :review WHERE usuario = :u AND livro = :livro' , {'review': re, 'u': session['user'], 'livro':livro})
                db.execute('UPDATE reviews SET avaliacao = :avaliacao WHERE usuario = :u AND livro = :livro', {'avaliacao': avaliacao, 'u': session['user'], 'livro':livro})
                db.commit()


    if livro == "favicon.ico":
        return "favicon"
    bks=db.execute('SELECT * FROM books WHERE title = :book', {'book' : livro}).fetchall()
    isbn = bks[0]['isbn']
    reviews = db.execute('SELECT pitaco, usuario, avaliacao FROM reviews WHERE livro = :a', {'a':livro}).fetchall()
    util=[]
    avaliacao_i = 0
    for pitaco, usuario, avaliacao in reviews:
        util.append(avaliacao)
    for avaliacao in util:
        avaliacao_i += avaliacao




    navaliacao_i = len(util)


    # GoodreadsAPI

    res = requests.get('http://goodreads.com/book/review_counts.json',
            params={"key": "MroZjsvCAsem0zyWfFa3yQ", "isbns": isbn}).json()["books"][0]
    avaliacao_g = float(res["average_rating"])
    navaliacao_g = res["ratings_count"]


    navaliacao = navaliacao_g + navaliacao_i
    avaliacao = round((avaliacao_g * navaliacao_g + avaliacao_i) / navaliacao, 2)



    return render_template('book.html', livro = bks, review=reviews, u=getlog(), avaliacao = avaliacao, navaliacao= navaliacao)



@app.route('/logout')
def logout():
    session["user"]=None
    bk=db.execute("SELECT * FROM books LIMIT 15")
    return render_template("home.html", bk=bk, u=getlog())




@app.route('/api/<isbn>')
def api(isbn):
    livro = db.execute('SELECT * FROM books WHERE isbn = :isbn', {'isbn':isbn}).fetchone()
    if livro is None:
        return "Erro: O livro não foi encontrado em nosso banco de dados"

    res=requests.get('http://goodreads.com/book/review_counts.json',
                params={"key": "MroZjsvCAsem0zyWfFa3yQ", "isbns": isbn}).json()["books"][0]
    rew=db.execute('SELECT avaliacao FROM reviews').fetchall()
    a=0


    for i in range(len(rew)):
        a += rew[i][0]
        i += 1




    return jsonify(
    title= livro.title,
    author= livro.author,
    year= livro.year,
    isbn = livro.isbn,
    review_count= res["ratings_count"] + len(rew),
    average_rating = round((float(res["average_rating"]) * res["ratings_count"] +  a) / (res["ratings_count"] + len(rew)), 2)
    )



    if __name__ == "__main__":
        app.run()
