import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [user, setUser] = useState(null);
  const [message, setMessage] = useState('');

  const handleLogin = (e) => {
    e.preventDefault();
    fetch('http://localhost:5000/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
      .then(async (res) => {
        const data = await res.json();
        if (res.ok) {
          setUser(data.user);
          setMessage(data.message);
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
      method: 'POST'
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

  if (user && user.role === 'teacher') {
    return (
      <TeacherDashboard 
        user={user} 
        onLogout={handleLogout} 
      />
    );
  } else if (user && user.role === 'student') {
    return (
      <StudentDashboard 
        user={user} 
        onLogout={handleLogout} 
      />
    );
  }

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

// Teacher Dashboard remains similar (can be expanded as needed)
function TeacherDashboard({ user, onLogout }) {
  return (
    <div>
      <h2>Welcome, Teacher {user.username}!</h2>
      <button onClick={onLogout}>Logout</button>
      <p>This is the teacher's dashboard.</p>
    </div>
  );
}

// Student Dashboard with enrollment and removal functionality
function StudentDashboard({ user, onLogout }) {
  const [myCourses, setMyCourses] = useState([]);
  const [allCourses, setAllCourses] = useState([]);
  const [tab, setTab] = useState('myCourses'); // 'myCourses' or 'addCourses'
  const [message, setMessage] = useState('');

  // Fetch the student's enrolled courses
  useEffect(() => {
    fetch(`http://localhost:5000/student/courses?username=${user.username}`)
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

  // Fetch all available courses
  useEffect(() => {
    fetch('http://localhost:5000/courses')
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

  // Enroll in a course
  const enrollInCourse = (courseId) => {
    fetch('http://localhost:5000/student/enroll', {
      method: 'POST',
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

  // Remove a course enrollment
  const removeFromCourse = (courseId) => {
    fetch('http://localhost:5000/student/remove', {
      method: 'POST',
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

  // Helper function to refresh enrolled and all courses
  const refreshCourses = () => {
    fetch(`http://localhost:5000/student/courses?username=${user.username}`)
      .then(res => res.json())
      .then(updatedCourses => setMyCourses(updatedCourses));
    fetch('http://localhost:5000/courses')
      .then(res => res.json())
      .then(updatedAllCourses => setAllCourses(updatedAllCourses));
  };

  return (
    <div className="dashboard">
      <h2>Welcome, Student {user.username}!</h2>
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
              <hr />
            </div>
          ))}
        </div>
      )}

      {tab === 'addCourses' && (
        <div>
          <h3>Add/Remove Courses</h3>
          {allCourses.map((course) => {
            const isEnrolled = myCourses.some((myC) => myC.id === course.id);
            const isFull = course.students_enrolled >= course.capacity;
            return (
              <div key={course.id} className="course-card">
                <p><strong>Course Name:</strong> {course.name}</p>
                <p><strong>Teacher:</strong> {course.teacher}</p>
                <p><strong>Time:</strong> {course.time}</p>
                <p><strong>Enrolled:</strong> {course.students_enrolled}/{course.capacity}</p>
                {isEnrolled ? (
                  <button onClick={() => removeFromCourse(course.id)}>
                    Remove
                  </button>
                ) : (
                  !isFull ? (
                    <button onClick={() => enrollInCourse(course.id)}>
                      Enroll
                    </button>
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
      {message && <p style={{ color: 'red' }}>{message}</p>}
    </div>
  );
}

export default App;
