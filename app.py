from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
logging.basicConfig(level=logging.DEBUG)

# ====================
# Database Models
# ====================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), default="New Chat")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))
    sender = db.Column(db.String(10))  # user / bot
    text = db.Column(db.Text)


with app.app_context():
    db.create_all()

# ====================
# Routes
# ====================

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    chats = Chat.query.filter_by(user_id=session["user_id"]).all()
    return render_template("index.html", chats=chats)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            return "Username already exists!"
        password_hash = generate_password_hash(password, method="pbkdf2:sha256")
        new_user = User(username=username, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return redirect(url_for("home"))
        return "Invalid credentials!"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/new_chat", methods=["POST"])
def new_chat():
    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401
    new_chat = Chat(user_id=session["user_id"])
    db.session.add(new_chat)
    db.session.commit()
    return jsonify({"chat_id": new_chat.id, "title": new_chat.title})

@app.route("/get_history/<int:chat_id>")
def get_history(chat_id):
    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({"error": "Chat not found"}), 404
    messages = [
        {"sender": m.sender, "text": m.text}
        for m in Message.query.filter_by(chat_id=chat_id).all()
    ]
    return jsonify(messages)

@app.route("/get/<int:chat_id>", methods=["POST"])
def get_response(chat_id):
    try:
        data = request.get_json()
        user_msg = data.get("message", "")
        chat = Chat.query.get(chat_id)
        if not chat:
            return jsonify({"error": "Chat not found"}), 404

        user_message = Message(chat_id=chat_id, sender="user", text=user_msg)
        db.session.add(user_message)

        bot_response = f"You said: {user_msg}"
        bot_message = Message(chat_id=chat_id, sender="bot", text=bot_response)
        db.session.add(bot_message)

        db.session.commit()
        return jsonify({"response": bot_response})
    except Exception as e:
        app.logger.error(f"Error in /get: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
