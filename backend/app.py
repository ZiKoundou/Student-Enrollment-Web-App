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

# ============= MODELS ============= #

class User(db.Model):
    """
    User model:
      - username: unique username (e.g., 'ahepworth')
      - password: plain for simplicity
      - role: 'teacher' or 'student'
      - display_name: for teachers, e.g. 'Ammon Hepworth'; for students you can keep it same as username or something else
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    display_name = db.Column(db.String(128), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "display_name": self.display_name
        }

class Course(db.Model):
    """
    Course model:
      - name, teacher, time, capacity
      - teacher: store the teacher's display_name. Example: 'Ammon Hepworth'
    """
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    teacher = db.Column(db.String(128), nullable=False)
    time = db.Column(db.String(128), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)

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
            data["students_enrolled"] = len(self.enrollments)
        return data

class Enrollment(db.Model):
    """
    Enrollment model (a join table between User and Course) with an extra 'grade' column.
    """
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    grade = db.Column(db.Integer, nullable=False, default=0)

# ============= UTILITY FUNCTION ============= #

def create_and_seed_db():
    db.create_all()

    # --- Create Teacher Users ---
    teacher_users = [
        {"username": "ahepworth", "display_name": "Ammon Hepworth"},
        {"username": "swalker", "display_name": "Susan Walker"},
        {"username": "rjenkins", "display_name": "Ralph Jenkins"},
    ]
    for t in teacher_users:
        if not User.query.filter_by(username=t["username"]).first():
            db.session.add(User(
                username=t["username"],
                password="678910",
                role="teacher",
                display_name=t["display_name"]
            ))
    db.session.commit()

    # --- Create Student User ---
    if not User.query.filter_by(username="student").first():
        student = User(
            username="student",
            password="12345",
            role="student",
            display_name="Johnny Student"  # Or any name
        )
        db.session.add(student)
    db.session.commit()

    # --- Create Default Courses ---
    if not Course.query.first():
        course_data = [
            {
                "name": "Physics 121",
                "teacher": "Susan Walker",   # matches swalker
                "time": "TR 11:00-11:50 AM",
                "capacity": 10
            },
            {
                "name": "CS 106",
                "teacher": "Ammon Hepworth", # matches ahepworth
                "time": "MWF 2:00-2:50 PM",
                "capacity": 10
            },
            {
                "name": "Math 101",
                "teacher": "Ralph Jenkins",  # matches rjenkins
                "time": "MWF 10:00-10:50 AM",
                "capacity": 8
            },
            {
                "name": "CS 162",
                "teacher": "Ammon Hepworth", # matches ahepworth
                "time": "TR 3:00-3:50 PM",
                "capacity": 4
            }
        ]
        for c in course_data:
            new_course = Course(**c)
            db.session.add(new_course)
        db.session.commit()

    # --- Enroll Default Student in Some Courses with grade 80 ---
    student_user = User.query.filter_by(username="student").first()
    if student_user:
        physics_course = Course.query.filter_by(name="Physics 121").first()
        cs106_course = Course.query.filter_by(name="CS 106").first()

        if physics_course and not Enrollment.query.filter_by(
            user_id=student_user.id, course_id=physics_course.id).first():
            db.session.add(Enrollment(user_id=student_user.id, course_id=physics_course.id, grade=80))

        if cs106_course and not Enrollment.query.filter_by(
            user_id=student_user.id, course_id=cs106_course.id).first():
            db.session.add(Enrollment(user_id=student_user.id, course_id=cs106_course.id, grade=80))
        db.session.commit()

# ============= ROUTES ============= #

# --- LOGIN ---
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

# --- LOGOUT ---
@app.route('/logout', methods=['POST'])
def logout():
    # Typically handled by frontend (clear tokens, etc.)
    # We'll just return success.
    return jsonify({"message": "Logout successful"}), 200

# --- GET ALL COURSES (STUDENT "ADD COURSES") ---
@app.route('/courses', methods=['GET'])
def get_all_courses():
    courses = Course.query.all()
    data = [course.to_dict(include_enrolled=True) for course in courses]
    return jsonify(data), 200

# --- STUDENT: GET ENROLLED COURSES ---
@app.route('/student/courses', methods=['GET'])
def get_student_courses():
    username = request.args.get("username")
    user = User.query.filter_by(username=username, role="student").first()
    if not user:
        return jsonify({"message": "Student not found"}), 404

    enrollments = Enrollment.query.filter_by(user_id=user.id).all()
    enrolled_courses = []
    for e in enrollments:
        course = Course.query.get(e.course_id)
        cdata = course.to_dict(include_enrolled=True)
        cdata["grade"] = e.grade
        enrolled_courses.append(cdata)
    return jsonify(enrolled_courses), 200

# --- STUDENT: ENROLL IN A COURSE ---
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

    enrollment = Enrollment(user_id=user.id, course_id=course.id, grade=80)  # default grade
    db.session.add(enrollment)
    db.session.commit()
    return jsonify({"message": "Enrolled successfully"}), 200

# --- STUDENT: REMOVE A COURSE ---
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

# --- TEACHER: GET COURSES BY TEACHER (Matches display_name to course.teacher) ---
@app.route('/teacher/courses', methods=['GET'])
def teacher_courses():
    username = request.args.get("username")
    teacher_user = User.query.filter_by(username=username, role="teacher").first()
    if not teacher_user:
        return jsonify({"message": "Teacher not found"}), 404

    courses = Course.query.filter_by(teacher=teacher_user.display_name).all()
    data = [course.to_dict(include_enrolled=True) for course in courses]
    return jsonify(data), 200

# --- TEACHER: GET ENROLLMENTS FOR A COURSE ---
@app.route('/teacher/course/<int:course_id>/enrollments', methods=['GET'])
def teacher_course_enrollments(course_id):
    # Return the list of students (with their grade) for a given course
    enrollments = Enrollment.query.filter_by(course_id=course_id).all()
    results = []
    for e in enrollments:
        student_user = User.query.filter_by(id=e.user_id, role="student").first()
        if student_user:
            results.append({
                "enrollment_id": e.id,
                "student_username": student_user.username,
                "student_name": student_user.display_name,
                "grade": e.grade
            })
    return jsonify(results), 200

# --- TEACHER: UPDATE A STUDENT'S GRADE ---
@app.route('/teacher/update_grade', methods=['POST'])
def teacher_update_grade():
    """
    Expects JSON: {
      "teacher_username": "...",
      "course_id": ...,
      "student_username": "...",
      "new_grade": ...
    }
    Checks if teacher matches the course's teacher, then updates the grade in enrollment.
    """
    data = request.get_json()
    teacher_username = data.get("teacher_username")
    course_id = data.get("course_id")
    student_username = data.get("student_username")
    new_grade = data.get("new_grade")

    # Validate teacher
    teacher_user = User.query.filter_by(username=teacher_username, role="teacher").first()
    if not teacher_user:
        return jsonify({"message": "Teacher not found"}), 404
    course = Course.query.filter_by(id=course_id, teacher=teacher_user.display_name).first()
    if not course:
        return jsonify({"message": "Course not found or does not belong to you"}), 404

    # Validate student enrollment
    student_user = User.query.filter_by(username=student_username, role="student").first()
    if not student_user:
        return jsonify({"message": "Student not found"}), 404
    enrollment = Enrollment.query.filter_by(user_id=student_user.id, course_id=course_id).first()
    if not enrollment:
        return jsonify({"message": "Student not enrolled in this course"}), 404

    # Update grade
    try:
        new_grade_int = int(new_grade)
    except ValueError:
        return jsonify({"message": "Invalid grade format"}), 400

    enrollment.grade = new_grade_int
    db.session.commit()
    return jsonify({"message": "Grade updated successfully"}), 200

# ============= MAIN ENTRY POINT ============= #

if __name__ == '__main__':
    with app.app_context():
        create_and_seed_db()
    app.run(debug=True)
