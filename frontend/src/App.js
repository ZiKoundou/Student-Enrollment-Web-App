import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [username, setUsername]   = useState('');
  const [password, setPassword]   = useState('');
  const [user, setUser]           = useState(null);
  const [message, setMessage]     = useState('');

  const handleLogin = (e) => {
    e.preventDefault();
    fetch('http://localhost:5000/login', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setUser(data.user);  // user = {id, username, role, display_name}
          setMessage(data.message);
          // If the logged-in user is an admin, redirect to the admin panel.
          if (data.user.role === 'admin') {
            window.location.href = 'http://localhost:5000/admin';
          }
        } else {
          setMessage(data.message);
        }
      })
      .catch((err) => {
        console.error(err);
        setMessage("Error during login");
      });
  };

  const handleLogout = () => {
    fetch('http://localhost:5000/logout', {
      method: 'POST',
      credentials: 'include'
    })
      .then(() => {
        setUser(null);
        setUsername('');
        setPassword('');
        setMessage('Logged out successfully!');
      })
      .catch((err) => {
        console.error(err);
        setMessage('Error during logout');
      });
  };

  // Render dashboards for teachers and students.
  if (user && user.role === 'teacher') {
    return <TeacherDashboard user={user} onLogout={handleLogout} />;
  } else if (user && user.role === 'student') {
    return <StudentDashboard user={user} onLogout={handleLogout} />;
  }

  // If no dashboard applies, show the login form.
  return (
    <div className="App">
      <h2>Login</h2>
      <form onSubmit={handleLogin}>
        <div>
          <label>Username:</label>
          <input 
            type="text" 
            value={username}
            onChange={(e) => setUsername(e.target.value)} 
            required 
          />
        </div>
        <div>
          <label>Password:</label>
          <input 
            type="password" 
            value={password}
            onChange={(e) => setPassword(e.target.value)} 
            required 
          />
        </div>
        <button type="submit">Login</button>
      </form>
      {message && <p className="message">{message}</p>}
    </div>
  );
}

// ============= TEACHER DASHBOARD ============= //
function TeacherDashboard({ user, onLogout }) {
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [enrollments, setEnrollments] = useState([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch(`http://localhost:5000/teacher/courses?username=${user.username}`, { credentials: 'include' })
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setCourses(data);
        } else {
          setMessage(data.message);
        }
      })
      .catch(err => console.error(err));
  }, [user.username]);

  const handleSelectCourse = (course) => {
    setSelectedCourse(course);
    fetch(`http://localhost:5000/teacher/course/${course.id}/enrollments`, { credentials: 'include' })
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setEnrollments(data); 
        } else {
          setMessage(data.message);
        }
      })
      .catch(err => console.error(err));
  };

  const handleGradeChange = (studentUsername, newGrade) => {
    fetch('http://localhost:5000/teacher/update_grade', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        teacher_username: user.username,
        course_id: selectedCourse.id,
        student_username: studentUsername,
        new_grade: newGrade
      })
    })
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setMessage(data.message);
          handleSelectCourse(selectedCourse);
        } else {
          setMessage(data.message);
        }
      })
      .catch(err => console.error(err));
  };

  return (
    <div className="dashboard">
      <h2>Welcome, Teacher {user.display_name}!</h2>
      <button onClick={onLogout}>Logout</button>
      <div style={{ margin: '20px 0' }}>
        <h3>Your Courses</h3>
        {courses.map((course) => (
          <div 
            key={course.id} 
            className="course-card"
            style={{
              cursor: 'pointer',
              backgroundColor: selectedCourse && selectedCourse.id === course.id ? '#e0f0ff' : '#fff'
            }}
            onClick={() => handleSelectCourse(course)}
          >
            <p><strong>{course.name}</strong> – {course.time}</p>
            <p>Enrolled: {course.students_enrolled}/{course.capacity}</p>
          </div>
        ))}
      </div>

      {selectedCourse && (
        <div>
          <h3>Students in {selectedCourse.name}</h3>
          {enrollments.length === 0 && <p>No students enrolled yet.</p>}
          {enrollments.map((enroll) => (
            <div key={enroll.enrollment_id} className="course-card">
              <p><strong>Name:</strong> {enroll.student_name}</p>
              <p><strong>Username:</strong> {enroll.student_username}</p>
              <p>
                <strong>Grade:</strong>
                <input 
                  type="number"
                  defaultValue={enroll.grade}
                  style={{ width: '60px', marginLeft: '10px' }}
                  onBlur={(e) => {
                    const newGrade = e.target.value;
                    handleGradeChange(enroll.student_username, newGrade);
                  }}
                />
              </p>
            </div>
          ))}
        </div>
      )}

      {message && <p className="message">{message}</p>}
    </div>
  );
}

// ============= STUDENT DASHBOARD ============= //
function StudentDashboard({ user, onLogout }) {
  const [myCourses, setMyCourses] = useState([]);
  const [allCourses, setAllCourses] = useState([]);
  const [tab, setTab] = useState('myCourses'); // 'myCourses' or 'addCourses'
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch(`http://localhost:5000/student/courses?username=${user.username}`, { credentials: 'include' })
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setMyCourses(data);
        } else {
          setMessage(data.message);
        }
      })
      .catch((err) => console.error(err));
  }, [user.username]);

  useEffect(() => {
    fetch('http://localhost:5000/courses', { credentials: 'include' })
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setAllCourses(data);
        } else {
          setMessage(data.message);
        }
      })
      .catch((err) => console.error(err));
  }, []);

  const enrollInCourse = (courseId) => {
    fetch('http://localhost:5000/student/enroll', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user.username, course_id: courseId })
    })
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setMessage(data.message);
          refreshCourses();
        } else {
          setMessage(data.message);
        }
      })
      .catch((err) => console.error(err));
  };

  const removeFromCourse = (courseId) => {
    fetch('http://localhost:5000/student/remove', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user.username, course_id: courseId })
    })
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setMessage(data.message);
          refreshCourses();
        } else {
          setMessage(data.message);
        }
      })
      .catch((err) => console.error(err));
  };

  const refreshCourses = () => {
    fetch(`http://localhost:5000/student/courses?username=${user.username}`, { credentials: 'include' })
      .then(res => res.json())
      .then(updatedCourses => setMyCourses(updatedCourses));

    fetch('http://localhost:5000/courses', { credentials: 'include' })
      .then(res => res.json())
      .then(updatedAllCourses => setAllCourses(updatedAllCourses));
  };

  return (
    <div className="dashboard">
      <h2>Welcome, Student {user.display_name}!</h2>
      <button onClick={onLogout}>Logout</button>

      <div style={{ marginTop: '20px' }}>
        <button onClick={() => setTab('myCourses')}>Your Courses</button>
        <button onClick={() => setTab('addCourses')}>Add/Remove Courses</button>
      </div>

      {tab === 'myCourses' && (
        <div>
          <h3>Your Courses</h3>
          {myCourses.map((course) => (
            <div key={course.id} className="course-card">
              <p><strong>Course Name:</strong> {course.name}</p>
              <p><strong>Teacher:</strong> {course.teacher}</p>
              <p><strong>Time:</strong> {course.time}</p>
              <p><strong>Enrolled:</strong> {course.students_enrolled}/{course.capacity}</p>
              <p><strong>Your Grade:</strong> {course.grade}</p>
              <hr />
            </div>
          ))}
        </div>
      )}

      {tab === 'addCourses' && (
        <div>
          <h3>Add/Remove Courses</h3>
          {allCourses.map((course) => {
            const isEnrolled = myCourses.some((mc) => mc.id === course.id);
            const isFull = course.students_enrolled >= course.capacity;
            return (
              <div key={course.id} className="course-card">
                <p><strong>Course Name:</strong> {course.name}</p>
                <p><strong>Teacher:</strong> {course.teacher}</p>
                <p><strong>Time:</strong> {course.time}</p>
                <p><strong>Enrolled:</strong> {course.students_enrolled}/{course.capacity}</p>
                {isEnrolled ? (
                  <button onClick={() => removeFromCourse(course.id)}>Remove</button>
                ) : (
                  !isFull ? (
                    <button onClick={() => enrollInCourse(course.id)}>Enroll</button>
                  ) : (
                    <p>This course is full.</p>
                  )
                )}
                <hr />
              </div>
            );
          })}
        </div>
      )}
      {message && <p className="message">{message}</p>}
    </div>
  );
}

export default App;
