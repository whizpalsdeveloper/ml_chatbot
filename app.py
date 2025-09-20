from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from chatbot import chatbot_response

app = Flask(__name__)
app.config['SECRET_KEY'] = "aB3$9fG1kL8pQx2z!R7vYh6d"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///chatbot.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------- Database Models ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    sender = db.Column(db.String(10))  # "user" or "bot"
    message = db.Column(db.Text)

with app.app_context():
    db.create_all()

# ---------------- User Loader ----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- Routes ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = generate_password_hash(request.form['password'])  # default pbkdf2:sha256
        if User.query.filter_by(username=username).first():
            return "User already exists"
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        return "Invalid credentials"
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
@login_required
def get_bot_response():
    user_message = request.json.get("message")
    bot_message, _ = chatbot_response(user_message)

    # Store messages in DB
    db.session.add(ChatMessage(user_id=current_user.id, sender="user", message=user_message))
    db.session.add(ChatMessage(user_id=current_user.id, sender="bot", message=bot_message))
    db.session.commit()

    # Fetch full chat history for this user
    history = ChatMessage.query.filter_by(user_id=current_user.id).all()
    chat_history = [{"user": m.message} if m.sender=="user" else {"bot": m.message} for m in history]

    return jsonify({"response": bot_message, "history": chat_history})

@app.route("/get_history")
@login_required
def get_history():
    history = ChatMessage.query.filter_by(user_id=current_user.id).all()
    chat_history = [{"user": m.message} if m.sender=="user" else {"bot": m.message} for m in history]
    return jsonify({"history": chat_history})

# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True)


from flask_login import logout_user, login_required

@app.route("/logout")
@login_required
def logout():
    logout_user()  # Logs out the current user
    return redirect(url_for("login"))  # Redirect to login page
