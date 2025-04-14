from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from React

# Configure the SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
db_file = os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the User model using SQLAlchemy
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {"username": self.username, "role": self.role}

# Create tables and default users before the first request
@app.before_first_request
def create_tables():
    db.create_all()
    # Add default student if not exists
    if not User.query.filter_by(username="student").first():
        student = User(username="student", password="12345", role="student")
        db.session.add(student)
    # Add default teacher if not exists
    if not User.query.filter_by(username="teacher").first():
        teacher = User(username="teacher", password="678910", role="teacher")
        db.session.add(teacher)
    db.session.commit()

# Login endpoint to authenticate users
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    # Check if there is a matching user in the database
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        return jsonify({"message": "Login successful", "user": user.to_dict()}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

if __name__ == '__main__':
    app.run(debug=True)
