import { React, useState } from "react";
import TextField from "@mui/material/TextField";
import "./App.css";
import "./app.py";


function App() {

  const [query, setQuery] = useState([])
  const [answer, setAnswer] = useState("")
  const [sources, setSources] = useState([])
  
  const inputHandler = (e) => {
    const userInput = e.target.value;
    setQuery(userInput);
  };

  // Enter key press launch a call to the API
  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleSubmit();
    }
  };

  // Submission of the query to the back API
  const handleSubmit = () => {
    const jsonData = {
      query: query,
    };
  
    fetch('http://localhost:3001/api/query', {
      method: 'POST', 
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(jsonData),
    })
      .then(response => response.json())
      .then(data => {
        
        console.log("message", data.message);
        console.log("answer", data.message.answer);
        console.log("sources array", data.message.sources);
        setAnswer(data.message.answer);
        setSources(JSON.parse(data.message.sources));
      })
      .catch(error => {
        console.error('Error while sending the request to the backend: ', error);
      });
      console.log(jsonData);

  };

  // Front
  return (
    <div className="main">
      <h1>Obstetric Search</h1>
      <div className="search">
        <TextField
          id="outlined-basic"
          onChange={inputHandler}
          onKeyPress={handleKeyDown} 
          variant="outlined" 
          fullWidth
          label="Search"
        />
      <button className="search-button" onClick={handleSubmit}>Submit</button>
      </div>
      {answer && (
      <div className="answer-container">
      <p className="answer-text">{answer}</p>
      </div>
      )}
      <div>Sources:</div>
      {sources && (
      <div><ul>
        {sources.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul></div>
      )}
    </div>
  );
}

export default App;
