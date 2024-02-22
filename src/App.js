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
        console.log("source to highlight", data.message.highlight);
        console.log("id", data)
        // const sourcesArray = Object.entries(data.message.sources).map(([sourceName, ids]) => ({ name: sourceName, ids }));
        //console.log(sourcesArray)
        setAnswer(data.message.answer);
        // setSources(sourcesArray);
        setChatHistory(prevHistory => [
          ...prevHistory,
          { query: query, answer: data.message.answer, sources: data.message.sources }
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
  
  useEffect(() => {
    const fetchChatHistory = async () => {
      try {
        const response = await fetch('History.json');
        const data = await response.json();
        setChatHistory(data);
      } catch (error) {
        console.error('Error fetching chat history:', error);
      }
    };

    fetchChatHistory();
  }, []);   
  console.log("chatHistory", chatHistory);

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
                  <div><strong>Sources:</strong> 
                  {Object.entries(item.sources).length > 0 ? (
                    <ul> 
                      {Object.entries(item.sources).map(([source, ids], sourceIndex) => (
                        <li key={sourceIndex}>
                          {/* <a href={require(`../public/RawDataset/${source}.pdf`)+`#page=${ids[0][0]}`} target = "_blank" rel="noreferrer"><strong>{source}:</strong></a> */}
                          <a href={`http://localhost:3001/api/generate-pdf/${index}/${source}`+`#page=${ids[0][0]}`} target="_blank" rel="noreferrer"><strong>{source}:</strong></a>
                          <ul>
                            {ids.map((id, subIndex) => (
                              <li key={subIndex}>
                                p: {Array.isArray(id) ? (
                                  <span>
                                  {id.map((subId, nestedIndex) => (
                                    // <a key={nestedIndex} href={require(`../public/RawDataset/${source}.pdf`)+`#page=${subId}`} target = "_blank" rel="noreferrer">
                                      <a key={nestedIndex} href={`http://localhost:3001/api/generate-pdf/${index}/${source}`+`#page=${subId}`} target="_blank" rel="noreferrer">
                                      {nestedIndex > 0 && ', '}
                                      {subId}
                                    </a>
                                  ))}
                                </span>
                                ) : (
                                  id
                                )}
                              </li>
                            ))}
                          </ul>

                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No sources available</p>
                  )}
                </div>
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
