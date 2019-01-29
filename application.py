from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    variavel="LoucuraLoucuraLoucura"
    return render_template("index.html", variavel=variavel)
