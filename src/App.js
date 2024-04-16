import { React, useState, useRef, useEffect } from "react";
import TextField from "@mui/material/TextField";
import "./App.css";
import "./app.py";

function App() {

  const [query, setQuery] = useState([])
  const [answer, setAnswer] = useState("")
  const [sources, setSources] = useState([])
  // const [chatHistory, setChatHistory] = useState([])
  const [chatHistory, setChatHistory] = useState([[]])
  const [currentChatHistory, setCurrentChatHistory] = useState([])
  const chatHistoryRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState(null);


  const handleError = (errorMessage) => {
    setError(errorMessage);
  };

  const handleClose = () => {
    setError(null);
  };

  function ErrorModal({ error, onClose }) {
    return (
      <div className="modal">
        <div className="modal-content">
          <span className="close" onClick={onClose}>&times;</span>
          <p>{error}</p>
        </div>
      </div>
    );
  }
  

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
      history: currentChatHistory,
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
        console.log('data', data)
        setLoading(false);
        
        console.log("message", data.message);
        console.log("answer_es", data.message.answer_es);
        console.log("answer_en", data.message.answer_en);
        console.log("sources array", data.message.sources);
        console.log("source to highlight", data.message.highlight);
        console.log("id", data)
        setAnswer(data.message.answer_es);
        setCurrentChatHistory(prevHistory => [
          ...prevHistory,
          { id: data.message.id, query_es: query, answer_es: data.message.answer_es, query_en: data.message.query_en, answer_en: data.message.answer_en, sources: data.message.sources, highlight: data.message.highlight }
        ]);
        console.log("lengthes", currentChatHistory.length, chatHistory.length)
        // Update  the global chat history to avoid incoherences
        if (currentChatHistory.length==0){
          console.log('current chat', currentChatHistory);
          setChatHistory([...chatHistory, [{ id: data.message.id, query_es: query, answer_es: data.message.answer_es, query_en: data.message.query_en, answer_en: data.message.answer_en, sources: data.message.sources, highlight: data.message.highlight  }]]);
        } else {
          const updatedHistory = chatHistory.map((row, rowIndex) =>{
            if (chatHistory[rowIndex].every(item => currentChatHistory.includes(item))){
              return [...currentChatHistory, { id: data.message.id, query_es: query, answer_es: data.message.answer_es, query_en: data.message.query_en, answer_en: data.message.answer_en, sources: data.message.sources, highlight: data.message.highlight  }];
            }
            return row;
          });
          setChatHistory(updatedHistory);
        }
      })
      .catch(error => {
        console.error('Error while sending the request to the backend: ', error);
        handleError("Ha ocurrido un error: por favor verifica que su pregunta no esté vacía.");
        setLoading(false);
      });
      console.log("jsonData", jsonData);
      console.log("chat history", chatHistory);

  };

  const handleChangeHistory = (item) =>{
    console.log("the new current history", item)
    setCurrentChatHistory(item)
  };

  const handleNewChat = () => {
    setCurrentChatHistory([]);
    console.log("New chat chat history", chatHistory);
  };

  const handleGeneratePdf = (index, source, id) =>{
    console.log(index, source, id)
    const jsonData = {
      history: currentChatHistory,
    };
    fetch(`http://localhost:3001/api/generate-pdf/${index}/${source}`, {
      
    method: 'POST',
    mode:'cors',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(jsonData)
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    // Consume the response body and convert it into a Blob object
    return response.blob();
  })
  .then(blob => {
    // Create a URL for the blob object
    const url = URL.createObjectURL(blob);
    // Open the PDF in a new tab
    window.open(url+`#page=${id}`);
  })
  // .then(response => {
  //   if (!response.ok) {
  //     throw new Error('Network response was not ok');
  //   }
    
    // Success response, open the PDF in a new tab
    //window.open(`http://localhost:3001/api/generate-pdf/${index}/${source}`);
  .catch(error => {
    console.error('Error:', error);
    // Handle error
  });
  };

  const handleSaveHistory = () =>{
    const jsonData = {
      history: chatHistory,
    };
    fetch('http://localhost:3001/api/save', {
      method: 'POST', 
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(jsonData),
    })
    .then(response => response.json())
    .then(data => {
      console.log('handleSaveChatHistory', data.message)
    })
    .catch(error => {
      console.error('Error while sending the request to the backend: ', error);
    });

  };
  
  // console.log("sources", sources);
  // console.log("chatHistory", chatHistory);

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
        setCurrentChatHistory(data[data.length - 1])
      } catch (error) {
        console.error('Error fetching chat history:', error);
      }
      finally{
        setHistoryLoading(false);
      }
    };

    fetchChatHistory();
  }, []);   
  console.log("chatHistory final", chatHistory);

  if (historyLoading){
    return <div>Loading...</div>
  }

  // Front
  return (
    <div className="main">
      <h1>Obstetric Search</h1>
      <button className="saveHistory-button" onClick={handleSaveHistory}>Save history</button>
      {chatHistory.length && (
      <div className='container'>
        <div className="history-panel left">
          <div className="history-scroll"  ref={chatHistoryRef}>
            <div className="container">
              <h3>History</h3>
              <button className="search-button" onClick={handleNewChat}>New chat</button>
            </div>
            {chatHistory.map((item, index) => (
                <button className="history-button" key={index}  onClick={ () => handleChangeHistory(item)}>
                  {item[0].query_es}
                </button>
              ))}
          </div>
        </div>  
        <div className="history-panel right">
          <div className="history-scroll"  ref={chatHistoryRef}>
            <ul>
            
            {currentChatHistory.map((item, index) => (
              <li key={index}>
                <p><strong>Query:</strong> {item.query_es}</p>
                <p><strong>Answer:</strong> {item.answer_es}</p>
                <div><strong>Sources:</strong> 
                  {Object.entries(item.sources).length > 0 ? (
                  <ul> 
                    {Object.entries(item.sources).map(([source, ids], sourceIndex) => (
                    <li key={sourceIndex}>
                      {/* <a href={`http://localhost:3001/api/generate-pdf/${index}/${source}`+`#page=${ids[0][0]}`} target="_blank" rel="noreferrer"><strong>{source}:</strong></a> */}
                      <a href="#" onClick={() => handleGeneratePdf(index, source, ids[0][0])}><strong>{source}:</strong></a>
                      <ul>
                        {ids.map((id, subIndex) => (
                        <li key={subIndex}>
                          p: {Array.isArray(id) ? (
                          <span>
                            {id.map((subId, nestedIndex) => (
                            // <a key={nestedIndex} href={`http://localhost:3001/api/generate-pdf/${index}/${source}`+`#page=${subId}`} target="_blank" rel="noreferrer">
                            //   {nestedIndex > 0 && ', '}
                            //   {subId}
                            // </a>
                            <a href="#" onClick={() => handleGeneratePdf(index, source, subId)}>
                              {nestedIndex > 0 && ', '}
                              {subId}</a>
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
      {error && <ErrorModal error={error} onClose={handleClose} />}
    </div>
  </div>
  );
}

export default App;
