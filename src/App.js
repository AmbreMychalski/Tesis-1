import { React, useState, useRef, useEffect } from "react";
import TextField from "@mui/material/TextField";
import "./App.css";
import "./app.py";


function App() {

  const [query, setQuery] = useState([])
  const [answer, setAnswer] = useState("")
  const [sources, setSources] = useState([])
  const [chatHistory, setChatHistory] = useState([])
  const chatHistoryRef = useRef(null);
  
  // const saveChatHistory = () => {
  //   const jsonChatHistory = JSON.stringify(chatHistory);
  //   const blob = new Blob([jsonChatHistory], { type: 'application/json' });
  //   const href = URL.createObjectURL(blob);
  //   const link = document.createElement('a');
  //   link.href = href;
  //   link.download = 'chat_history.json';
  //   document.body.appendChild(link);
  //   link.click();
  //   document.body.removeChild(link);
  // };

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
        const sourcesArray = Object.entries(data.message.sources).map(([sourceName, ids]) => ({ name: sourceName, ids }));
        console.log(sourcesArray)
        setAnswer(data.message.answer);
        setSources(sourcesArray);
        setChatHistory(prevHistory => [
          ...prevHistory,
          { query: query, answer: data.message.answer, sources: sourcesArray }
        ]);
      })
      .catch(error => {
        console.error('Error while sending the request to the backend: ', error);
      });
      console.log("jsonData", jsonData);

  };
  
  console.log("sources", sources);
  console.log("chatHistory", chatHistory);

  useEffect(() => {
    if (chatHistoryRef.current) {
      chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
    }
  }, [chatHistory]);
  
  console.log("chatHistory", chatHistory);
  useEffect(() => {
    fetch('./History.json') // Assurez-vous de spécifier le bon chemin d'accès au fichier History.json
      .then((response) => response.json())
      .then((data) => {
        setChatHistory(data); 
        console.log("chatHistory", chatHistory);
      })
      .catch((error) => {
        console.error("Error fetching data:", error);
      });
  }, []); 

  // Front
  return (
    <div className="main">
      <h1>Obstetric Search</h1>
      {chatHistory && (
      <div className="history-panel">
        <div className="history-scroll"  ref={chatHistoryRef}>
          <ul>
            {chatHistory.map((item, index) => (
              <li key={index}>
                <p><strong>Query:</strong> {item.query}</p>
                <p><strong>Answer:</strong> {item.answer}</p>
                  <p><strong>Sources:</strong> 
                    {item.sources.length > 0 ? (
                      <ul>
                        {item.sources.map((source, index) => (
                          <li key={index}>
                            <strong>{source.name}:</strong> 
                            <ul>
                              {source.ids.map((id, subIndex) => (
                                <li key={subIndex}>p: {id}</li>
                              ))}
                            </ul>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p>No sources available</p>
                  )}
                  </p>

              </li>
            ))}
          </ul>
        </div>
      </div>)}
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
    </div>
  );
}

export default App;
