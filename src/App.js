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
  const [loading, setLoading] = useState(false);
  

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
    setLoading(true);
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
        setLoading(false);
        
        console.log("message", data.message);
        console.log("answer_es", data.message.answer_es);
        console.log("answer_en", data.message.answer_en);
        console.log("sources array", data.message.sources);
        console.log("source to highlight", data.message.highlight);
        console.log("id", data)
        // const sourcesArray = Object.entries(data.message.sources).map(([sourceName, ids]) => ({ name: sourceName, ids }));
        //console.log(sourcesArray)
        setAnswer(data.message.answer_es);
        // setSources(sourcesArray);
        setChatHistory(prevHistory => [
          ...prevHistory,
          { query_es: query, answer_es: data.message.answer_es, query_en: data.message.query_en, answer_en: data.message.answer_en, sources: data.message.sources }
        ]);
      })
      .catch(error => {
        console.error('Error while sending the request to the backend: ', error);
        setLoading(false);
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
  console.log("chatHistory final", chatHistory);

  // Front
  return (
    <div className="main">
      <h1>Obstetric Search</h1>
      {chatHistory.length > 0 && (
      <div className="history-panel">
        <div className="history-scroll"  ref={chatHistoryRef}>
          <ul>
            {chatHistory.map((item, index) => (
              <li key={index}>
                <p><strong>Query:</strong> {item.query_es}</p>
                <p><strong>Answer:</strong> {item.answer_es}</p>
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
      <button className="search-button" onClick={handleSubmit} disabled={loading}>
            {loading ? <div className="loading-spinner"></div> : 'Submit'}
        </button>
      </div>
    </div>
  );
}

export default App;
