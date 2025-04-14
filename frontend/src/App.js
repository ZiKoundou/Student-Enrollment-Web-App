import React, { useState } from 'react';
import './App.css';

function App() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [userRole, setUserRole] = useState(null);
  const [message, setMessage] = useState('');

  // Handle form submission and send credentials to Flask backend
  const handleSubmit = (e) => {
    e.preventDefault();
    fetch('http://localhost:5000/login', {
      method: 'POST',
      headers: {
         'Content-Type': 'application/json'
       },
      body: JSON.stringify({ username, password })
    })
      .then(async response => {
         const data = await response.json();
         if(response.status === 200) {
            setUserRole(data.user.role);
            setMessage(data.message);
         } else {
            setMessage(data.message);
         }
      })
      .catch(error => {
         console.error('Error:', error);
         setMessage("Error during login");
      });
  };

  // Conditionally render dashboard or login form based on authentication
  if(userRole === "teacher") {
    return <TeacherDashboard username={username} />;
  } else if(userRole === "student") {
    return <StudentDashboard username={username} />;
  } else {
    return (
      <div className="App">
         <h2>Login</h2>
         <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Username:</label>
              <input 
                type="text" 
                value={username} 
                onChange={(e)=>setUsername(e.target.value)} 
                required 
              />
            </div>
            <div className="form-group">
              <label>Password:</label>
              <input 
                type="password" 
                value={password} 
                onChange={(e)=>setPassword(e.target.value)} 
                required 
              />
            </div>
            <button type="submit">Login</button>
         </form>
         {message && <p className="message">{message}</p>}
      </div>
    );
  }
}

// Dashboard component for teachers
function TeacherDashboard({ username }) {
  return (
    <div className="dashboard">
      <h2>Welcome, Teacher {username}!</h2>
      <p>This is the teacher's dashboard page.</p>
      {/* Teacher-specific functionalities can be added here */}
    </div>
  );
}

// Dashboard component for students
function StudentDashboard({ username }) {
  return (
    <div className="dashboard">
      <h2>Welcome, Student {username}!</h2>
      <p>This is the student's dashboard page.</p>
      {/* Student-specific functionalities can be added here */}
    </div>
  );
}

export default App;
