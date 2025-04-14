from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

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

# Function to create tables and add default users
def create_tables():
    db.create_all()
    # Add the default student user if not exists
    if not User.query.filter_by(username="student").first():
        student = User(username="student", password="12345", role="student")
        db.session.add(student)
    # Add the default teacher user if not exists
    if not User.query.filter_by(username="teacher").first():
        teacher = User(username="teacher", password="678910", role="teacher")
        db.session.add(teacher)
    db.session.commit()

# Login endpoint for user authentication
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        return jsonify({"message": "Login successful", "user": user.to_dict()}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

if __name__ == '__main__':
    # Ensure tables are created and default users added before starting the app
    with app.app_context():
        create_tables()
    app.run(debug=True)
