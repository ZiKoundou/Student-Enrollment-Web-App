from flask import Flask, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms.fields import SelectField
import os

app = Flask(__name__)
app.secret_key = 'mysecretkey'
CORS(app, supports_credentials=True)

# Configure the SQLite database
basedir = os.path.abspath(os.path.dirname(__file__))
db_file = os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_file
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============= MODELS ============= #

class User(db.Model):
    """
    User model with display_name.
    Role can be 'teacher', 'student', or 'admin'.
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
    Course model.
    """
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    teacher = db.Column(db.String(128), nullable=False)
    time = db.Column(db.String(128), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    
    # Relationship to Enrollment
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
    Enrollment model (join table) with a grade column.
    """
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    grade = db.Column(db.Integer, nullable=False, default=0)

# ============= SEEDING FUNCTION ============= #

def create_and_seed_db():
    db.create_all()

    # --- Create Admin User ---
    if not User.query.filter_by(username="admin").first():
        db.session.add(User(
            username="admin",
            password="bruh",
            role="admin",
            display_name="Administrator"
        ))
    db.session.commit()

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

    # --- Create the Default Student User ---
    if not User.query.filter_by(username="student").first():
        db.session.add(User(
            username="student",
            password="12345",
            role="student",
            display_name="Johnny Student"
        ))
    db.session.commit()

    additional_students = ["student1", "student2", "student3", "student4"]
    for s in additional_students:
        if not User.query.filter_by(username=s).first():
            db.session.add(User(
                username=s,
                password="12345",
                role="student",
                display_name=s
            ))
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
            db.session.add(Course(**c))
        db.session.commit()

    # --- Enroll the Default Student ("student") in Some Courses with Grade 80 ---
    student_user = User.query.filter_by(username="student").first()
    if student_user:
        physics_course = Course.query.filter_by(name="Physics 121").first()
        cs106_course = Course.query.filter_by(name="CS 106").first()
        if physics_course and not Enrollment.query.filter_by(user_id=student_user.id, course_id=physics_course.id).first():
            db.session.add(Enrollment(user_id=student_user.id, course_id=physics_course.id, grade=80))
        if cs106_course and not Enrollment.query.filter_by(user_id=student_user.id, course_id=cs106_course.id).first():
            db.session.add(Enrollment(user_id=student_user.id, course_id=cs106_course.id, grade=80))
        db.session.commit()

    # --- Enroll Each Additional Student in ALL Courses with Grade 50 ---
    additional_student_objs = User.query.filter(User.username.in_(additional_students)).all()
    all_courses = Course.query.all()
    for student in additional_student_objs:
        for course in all_courses:
            if not Enrollment.query.filter_by(user_id=student.id, course_id=course.id).first():
                db.session.add(Enrollment(user_id=student.id, course_id=course.id, grade=50))
    db.session.commit()

# ============= ADMIN PANEL SETUP ============= #

# Create a Secure ModelView that only allows admin access.
class SecureModelView(ModelView):
    def is_accessible(self):
        user = session.get("user")
        return user is not None and user.get("role") == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))

# Allow editing password in Admin
class UserAdmin(SecureModelView):
    form_columns = ('username', 'password', 'role', 'display_name')
    
    form_extra_fields = {
        'role': SelectField(
            'Role',
            choices=[('admin', 'admin'), ('teacher', 'teacher'), ('student', 'student')],
            coerce=str
        )
    }

# Custom CourseAdmin: delete enrollments before deleting a course
class CourseAdmin(SecureModelView):
    """
    We override delete_model so that when you delete a course,
    we first remove the associated enrollments that reference it.
    This prevents the NOT NULL / foreign key constraint errors.
    """
    def delete_model(self, model):
        try:
            # Remove all enrollments that reference this course
            Enrollment.query.filter_by(course_id=model.id).delete()
            # Now remove the course
            db.session.delete(model)
            db.session.commit()
        except:
            db.session.rollback()
            return False
        return True

# Add the views to the admin panel
admin_panel = Admin(app, name="Admin Panel", template_mode="bootstrap3")
admin_panel.add_view(UserAdmin(User, db.session))
admin_panel.add_view(CourseAdmin(Course, db.session))
admin_panel.add_view(SecureModelView(Enrollment, db.session))

# ============= ROUTES ============= #

@app.route('/me', methods=['GET'])
def me():
    return jsonify(session.get("user", {}))

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        session["user"] = user.to_dict()
        return jsonify({"message": "Login successful", "user": user.to_dict()}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop("user", None)
    return jsonify({"message": "Logout successful"}), 200

@app.route('/courses', methods=['GET'])
def get_all_courses():
    courses = Course.query.all()
    data = [course.to_dict(include_enrolled=True) for course in courses]
    return jsonify(data), 200

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
    if len(course.enrollments) >= course.capacity:
        return jsonify({"message": "Course is full"}), 400
    if Enrollment.query.filter_by(user_id=user.id, course_id=course.id).first():
        return jsonify({"message": "Already enrolled in this course"}), 400
    enrollment = Enrollment(user_id=user.id, course_id=course.id, grade=80)
    db.session.add(enrollment)
    db.session.commit()
    return jsonify({"message": "Enrolled successfully"}), 200

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

@app.route('/teacher/courses', methods=['GET'])
def teacher_courses():
    username = request.args.get("username")
    teacher_user = User.query.filter_by(username=username, role="teacher").first()
    if not teacher_user:
        return jsonify({"message": "Teacher not found"}), 404
    courses = Course.query.filter_by(teacher=teacher_user.display_name).all()
    data = [course.to_dict(include_enrolled=True) for course in courses]
    return jsonify(data), 200

@app.route('/teacher/course/<int:course_id>/enrollments', methods=['GET'])
def teacher_course_enrollments(course_id):
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

@app.route('/teacher/update_grade', methods=['POST'])
def teacher_update_grade():
    data = request.get_json()
    teacher_username = data.get("teacher_username")
    course_id = data.get("course_id")
    student_username = data.get("student_username")
    new_grade = data.get("new_grade")
    teacher_user = User.query.filter_by(username=teacher_username, role="teacher").first()
    if not teacher_user:
        return jsonify({"message": "Teacher not found"}), 404
    course = Course.query.filter_by(id=course_id, teacher=teacher_user.display_name).first()
    if not course:
        return jsonify({"message": "Course not found or does not belong to you"}), 404
    student_user = User.query.filter_by(username=student_username, role="student").first()
    if not student_user:
        return jsonify({"message": "Student not found"}), 404
    enrollment = Enrollment.query.filter_by(user_id=student_user.id, course_id=course_id).first()
    if not enrollment:
        return jsonify({"message": "Student not enrolled in this course"}), 404
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
