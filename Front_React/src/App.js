import { React, useState, useRef, useEffect } from "react";
import TextField from "@mui/material/TextField";
import authConf from "./authConf.json";
import "./App.css";

function App() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [connected, setConnected] = useState(false)

  const [query, setQuery] = useState([])
  const [chatHistory, setChatHistory] = useState([[]])
  const [currentChatHistory, setCurrentChatHistory] = useState({ conversation: [], conversationIndex: -1 });

  const chatHistoryRef = useRef(null);
  const [loading, setLoading] = useState(false);
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
  
  const handleLogin = (e) =>{
    e.preventDefault();
    if (username==authConf.username && password==authConf.password){
      setConnected(true)
    }
    else{
      console.log("Nombre de usuario o contraseña incorrectos, por favor inténtalo de nuevo.");
    }
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
      history: currentChatHistory.conversation,
    };
  
    fetch('api/query', {
      method: 'POST', 
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(jsonData),
    })
    .then(response => response.json())
    .then(data => {
      setLoading(false);
      if (data.message.answer_es === "Ha alcanzado el límite máximo de una conversación: por favor elimine mensajes anteriores o inicie una nueva conversación."){
        handleError("Ha ocurrido un error: "+data.message.answer_es);
        
      } else {
        setCurrentChatHistory(prevHistory => ({conversation:
          [
          ...(prevHistory.conversation || []),
          { id: data.message.id, query_es: query, answer_es: data.message.answer_es, query_en: data.message.query_en, answer_en: data.message.answer_en, sources: data.message.sources, highlight: data.message.highlight }
          ],
          conversationIndex: prevHistory.conversationIndex })
      );

        // Update  the global chat history to avoid incoherences
        if (currentChatHistory.conversation===undefined || currentChatHistory.conversation.length===0){
          setChatHistory([...chatHistory, [{ id: data.message.id, query_es: query, answer_es: data.message.answer_es, query_en: data.message.query_en, answer_en: data.message.answer_en, sources: data.message.sources, highlight: data.message.highlight  }]]);
        } else {
          const updatedHistory = chatHistory.map((conversation, index) => {
            if (index === currentChatHistory.conversationIndex) {
              return [...currentChatHistory.conversation, { id: data.message.id, query_es: query, answer_es: data.message.answer_es, query_en: data.message.query_en, answer_en: data.message.answer_en, sources: data.message.sources, highlight: data.message.highlight  }];
            }
            return conversation;
          });
          setChatHistory(updatedHistory);
        }
      }
    })
    .catch(error => {
      console.error('Error while sending the request to the backend: ', error);
      handleError("Ha ocurrido un error: por favor verifica que su pregunta no esté vacía.");
      setLoading(false);
    });
  };

  const handleChangeHistory = (index, item) =>{    
    setCurrentChatHistory({conversationIndex: index, conversation: item})
  };

  const handleNewChat = () => {
    const index = chatHistory.length
    setCurrentChatHistory({conversationIndex: index, conversation: []});
  };
  
  const handleDeleteMessage = (messageIndex) => {
    setChatHistory(prevChatHistory => {
      const updatedChatHistory = prevChatHistory.map((conversation, index) => {
        if (index === currentChatHistory.conversationIndex) {
          const updatedConversation = conversation.filter((_, index) => index !== messageIndex);
          const updatedConversationWithNewIDs = updatedConversation.map((message, index) => ({
            ...message,
            id: index, // Assign new ID based on index
          }));

          if (updatedConversationWithNewIDs.length === 0) {
            return null; // Filter out the empty conversation
          }

          return updatedConversationWithNewIDs;
        }
        return conversation;
      }).filter(conversation => conversation !== null);
      return updatedChatHistory;
    });

    setCurrentChatHistory(prevHistory => {
      const updatedConversation = prevHistory.conversation.filter((message) => {
        return message.id !== messageIndex;
      });
    
      // Assign new ID based on index for the updated messages
      const updatedConversationWithNewIDs = updatedConversation.map((message, index) => ({
        ...message,
        id: index,
      }));    
    
      // Return the updated conversation and preserve the conversation index
      return { conversation: updatedConversationWithNewIDs, conversationIndex: prevHistory.conversationIndex };
    });
  };

  const handleGeneratePdf = (index, source, id) =>{
    const jsonData = {
      history: currentChatHistory.conversation,
    };
    fetch(`api/generate-pdf/${index}/${source}`, {
      
    method: 'POST',
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
    //fetch('http://localhost:3001/api/save', {
      fetch('api/save', {
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
        if (data[0].length === 0) {
          setChatHistory([]);
          setCurrentChatHistory({conversationIndex: 0, conversation: []});
        } else {
          setChatHistory(data);
          setCurrentChatHistory({ conversationIndex: data.length - 1, conversation: data[data.length - 1] });
        }
      } catch (error) {
        console.error('Error fetching chat history:', error);
      }
    };

    fetchChatHistory();
  }, []);   

  if (!connected){
    return(<div className="container-form"> <form  id="msform"><fieldset><h2>Por favor, autentíquese </h2>
      <p><input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Usuario"/></p>
      <p><input type="password" value={password} onChange={(e)=>setPassword(e.target.value)} placeholder="Contraseña"/></p>
      <button className="saveHistory-button" onClick={handleLogin}>Entrar</button>
  </fieldset></form></div>);
  }

  // Front
  return (
    <div className="main">
      <h1>Obstetric Search</h1>
      <div class="border d-table w-100">
        <div class="d-table-cell tar">
          <button className="saveHistory-button" onClick={handleSaveHistory}>Guardar historial</button>
        </div>
      </div>
      <div className='container'>
        <div className="history-panel left">
          <div className="history-scroll"  ref={chatHistoryRef}>
            <div className="history-container">
              <h3>Historial</h3>
              <button className="newChat-button" onClick={handleNewChat}>Nueva conversación</button>
            </div>
            {chatHistory.length>0 && chatHistory.map((item, index) => (
              <button
                  className={`history-button ${index === currentChatHistory.conversationIndex ? 'selected-history-button' : ''}`}
                  key={index}
                  onClick={() => handleChangeHistory(index, item)}>
                  {item && item[0] && item[0].query_es}
              </button>
            ))}
          </div>
        </div>  
        <div className="history-panel right">
          <div className="history-scroll"  ref={chatHistoryRef}>
            <ul>
            
            {currentChatHistory && currentChatHistory.conversation.map((item, index) => (
              <li className = "messages" key={index}>
                <p className="whatsapp-bubble"><strong>Pregunta:</strong> {item.query_es}</p>
                <p className="whatsapp-bubble received">
                  <p><strong>Respuesta:</strong> {item.answer_es}</p>
                  <div><strong>Fuentes:</strong> 
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
                      <p>No hay fuentes disponibles</p>
                    )}
                  </div>
                </p>
                <button className="delete-button" onClick={() =>{handleDeleteMessage(index)}}>Suprimir</button>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
    <div className="search">
      <TextField
        id="outlined-basic"
        onChange={inputHandler}
        onKeyPress={handleKeyDown} 
        variant="outlined" 
        fullWidth
        label="Buscar"
      />
      <button className="search-button" onClick={handleSubmit} disabled={loading}>
            {loading ? <div className="loading-spinner"></div> : 'Enviar'}
      </button>
      {error && <ErrorModal error={error} onClose={handleClose} />}
    </div>
  </div>
  );
}

export default App;
