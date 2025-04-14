from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests from React

# Configure the SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
db_file = os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============= MODELS ============= #

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role
        }

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    teacher = db.Column(db.String(128), nullable=False)
    time = db.Column(db.String(128), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    
    # Relationship to Enrollment (one course -> many enrollments)
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)

    def to_dict(self, include_enrolled=False):
        data = {
            "id": self.id,
            "name": self.name,
            "teacher": self.teacher,
            "time": self.time,
            "capacity": self.capacity
        }
        if include_enrolled:
            # Include the count of enrolled students
            data["students_enrolled"] = len(self.enrollments)
        return data

class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)

# ============= UTILITY FUNCTION ============= #

def create_and_seed_db():
    db.create_all()

    # --- Create Default Users (Student & Teacher) ---
    if not User.query.filter_by(username="student").first():
        student = User(username="student", password="12345", role="student")
        db.session.add(student)
    if not User.query.filter_by(username="teacher").first():
        teacher = User(username="teacher", password="678910", role="teacher")
        db.session.add(teacher)
    db.session.commit()

    # --- Create Default Courses ---
    if not Course.query.first():
        course_data = [
            {
                "name": "Physics 121",
                "teacher": "Susan Walker",
                "time": "TR 11:00-11:50 AM",
                "capacity": 10
            },
            {
                "name": "CS 106",
                "teacher": "Ammon Hepworth",
                "time": "MWF 2:00-2:50 PM",
                "capacity": 10
            },
            {
                "name": "Math 101",
                "teacher": "Ralph Jenkins",
                "time": "MWF 10:00-10:50 AM",
                "capacity": 8
            },
            {
                "name": "CS 162",
                "teacher": "Ammon Hepworth",
                "time": "TR 3:00-3:50 PM",
                "capacity": 4
            }
        ]
        for c in course_data:
            new_course = Course(**c)
            db.session.add(new_course)
        db.session.commit()

    # --- Enroll Default Student in Some Courses ---
    student_user = User.query.filter_by(username="student").first()
    if student_user:
        physics_course = Course.query.filter_by(name="Physics 121").first()
        cs106_course = Course.query.filter_by(name="CS 106").first()

        if physics_course and not Enrollment.query.filter_by(
            user_id=student_user.id, course_id=physics_course.id).first():
            db.session.add(Enrollment(user_id=student_user.id, course_id=physics_course.id))

        if cs106_course and not Enrollment.query.filter_by(
            user_id=student_user.id, course_id=cs106_course.id).first():
            db.session.add(Enrollment(user_id=student_user.id, course_id=cs106_course.id))
        db.session.commit()

# ============= ROUTES ============= #

# --- Login Endpoint ---
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

# Logout endpoint (optional backend call)
@app.route('/logout', methods=['POST'])
def logout():
    return jsonify({"message": "Logout successful"}), 200

# --- Get All Courses (for the "Add Courses" tab) ---
@app.route('/courses', methods=['GET'])
def get_all_courses():
    courses = Course.query.all()
    data = [course.to_dict(include_enrolled=True) for course in courses]
    return jsonify(data), 200

# --- Get Courses Enrolled by a Specific Student ---
@app.route('/student/courses', methods=['GET'])
def get_student_courses():
    username = request.args.get("username", None)
    user = User.query.filter_by(username=username, role="student").first()
    if not user:
        return jsonify({"message": "Student not found"}), 404

    enrollments = Enrollment.query.filter_by(user_id=user.id).all()
    enrolled_courses = []
    for e in enrollments:
        course = Course.query.get(e.course_id)
        enrolled_courses.append(course.to_dict(include_enrolled=True))
    return jsonify(enrolled_courses), 200

# --- Enroll in a Course if Not Full ---
@app.route('/student/enroll', methods=['POST'])
def enroll_student_in_course():
    data = request.get_json()
    username = data.get("username")
    course_id = data.get("course_id")

    user = User.query.filter_by(username=username, role="student").first()
    if not user:
        return jsonify({"message": "Student not found"}), 404

    course = Course.query.filter_by(id=course_id).first()
    if not course:
        return jsonify({"message": "Course not found"}), 404

    # Check capacity
    current_enrolled = len(course.enrollments)
    if current_enrolled >= course.capacity:
        return jsonify({"message": "Course is full"}), 400

    # Check if student already enrolled
    if Enrollment.query.filter_by(user_id=user.id, course_id=course.id).first():
        return jsonify({"message": "Already enrolled in this course"}), 400

    enrollment = Enrollment(user_id=user.id, course_id=course.id)
    db.session.add(enrollment)
    db.session.commit()
    return jsonify({"message": "Enrolled successfully"}), 200

# --- Remove a Course from a Student's Enrollment ---
@app.route('/student/remove', methods=['POST'])
def remove_student_from_course():
    data = request.get_json()
    username = data.get("username")
    course_id = data.get("course_id")

    user = User.query.filter_by(username=username, role="student").first()
    if not user:
        return jsonify({"message": "Student not found"}), 404

    enrollment = Enrollment.query.filter_by(user_id=user.id, course_id=course_id).first()
    if not enrollment:
        return jsonify({"message": "Not enrolled in this course"}), 404

    db.session.delete(enrollment)
    db.session.commit()
    return jsonify({"message": "Course removed successfully"}), 200

# ============= MAIN ENTRY POINT ============= #

if __name__ == '__main__':
    with app.app_context():
        create_and_seed_db()
    app.run(debug=True)
