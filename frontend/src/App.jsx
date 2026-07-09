import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import Login from "./components/Login/Login";
import Sidebar from "./components/Layout/Sidebar";
import Topbar from "./components/Layout/Topbar";
import DocumentLibrary from "./components/Dashboard/DocumentLibrary";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  // Auth State
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [user, setUser] = useState(null);
  const [isRegister, setIsRegister] = useState(false);
  const [authError, setAuthError] = useState("");
  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [isLoadingUser, setIsLoadingUser] = useState(!!token);

  // App Navigation State
  const [activeTab, setActiveTab] = useState("chat"); // 'chat' | 'admin'

  // Chat/RAG State
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [activeMessages, setActiveMessages] = useState([]);
  const [questionInput, setQuestionInput] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const [chatError, setChatError] = useState("");

  // Documents State
  const [documents, setDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [summarizedDoc, setSummarizedDoc] = useState(null);
  const [isSummarizing, setIsSummarizing] = useState(false);

  // Admin Dashboard State
  const [adminStats, setAdminStats] = useState(null);
  const [adminError, setAdminError] = useState("");
  const [isAdminLoading, setIsAdminLoading] = useState(false);

  // Citation Preview Modal State
  const [selectedCitation, setSelectedCitation] = useState(null);

  // Scroll ref
  const messageEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // -------------------------------------------------------------
  // 1. Authentication Hooks
  // -------------------------------------------------------------
  useEffect(() => {
    if (token) {
      fetchUserProfile();
    }
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        // Token stale or invalid
        handleLogout();
      }
    } catch (e) {
      console.error("Error fetching profile", e);
      handleLogout();
    } finally {
      setIsLoadingUser(false);
    }
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthError("");
    const path = isRegister ? "/api/auth/register" : "/api/auth/login";
    const body = { username: usernameInput, password: passwordInput };

    try {
      const res = await fetch(`${API_BASE_URL}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Authentication request failed.");
      }

      if (isRegister) {
        // Toggle back to login automatically after registration
        setIsRegister(false);
        setAuthError("");
        setUsernameInput("");
        setPasswordInput("");
        alert("Registration successful! Please login.");
      } else {
        // Login successful
        localStorage.setItem("token", data.access_token);
        setToken(data.access_token);
      }
    } catch (err) {
      setAuthError(err.message);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken("");
    setUser(null);
    setConversations([]);
    setActiveConvId(null);
    setActiveMessages([]);
    setDocuments([]);
    setAdminStats(null);
  };

  // -------------------------------------------------------------
  // 2. Chat/RAG Operations
  // -------------------------------------------------------------
  useEffect(() => {
    if (user) {
      fetchConversations();
      fetchDocuments();
    }
  }, [user]);

  useEffect(() => {
    if (activeConvId) {
      fetchConversationDetail(activeConvId);
    }
  }, [activeConvId]);

  useEffect(() => {
    // Scroll to bottom on new messages
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeMessages]);

  const fetchConversations = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/chat/conversations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
      }
    } catch (e) {
      console.error("Error fetching conversations", e);
    }
  };

  const fetchConversationDetail = async (id) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/chat/conversations/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setActiveMessages(data.messages);
      }
    } catch (e) {
      console.error("Error fetching conversation details", e);
    }
  };

  const handleNewChat = () => {
    setActiveConvId(null);
    setActiveMessages([]);
    setQuestionInput("");
    setChatError("");
  };

  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!questionInput.trim() || isAsking) return;

    setChatError("");
    const userMsg = {
      id: Date.now(),
      sender: "user",
      text: questionInput,
      created_at: new Date().toISOString(),
    };
    setActiveMessages((prev) => [...prev, userMsg]);
    const payload = { question: questionInput, conversation_id: activeConvId };
    setQuestionInput("");
    setIsAsking(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Error obtaining grounded answer.");
      }

      // If a new conversation was created on the fly
      if (!activeConvId) {
        setActiveConvId(data.conversation_id);
        fetchConversations();
      }

      const botMsg = {
        id: Date.now() + 1,
        sender: "assistant",
        text: data.answer,
        sources: data.sources,
        created_at: new Date().toISOString(),
      };
      setActiveMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setChatError(err.message);
      setActiveMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 2,
          sender: "assistant",
          text: `⚠️ Error: ${err.message}`,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsAsking(false);
    }
  };

  const handleDeleteConversation = async (e, id) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat session?")) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat/conversations/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setConversations((prev) => prev.filter((c) => c.id !== id));
        if (activeConvId === id) {
          handleNewChat();
        }
      }
    } catch (e) {
      console.error("Delete conversation failed", e);
    }
  };

  // -------------------------------------------------------------
  // 3. Document Controls
  // -------------------------------------------------------------
  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/documents`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (e) {
      console.error("Error listing documents", e);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Client-side quick size validation
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      setUploadError("File size exceeds 10MB limit.");
      return;
    }

    setUploadError("");
    setIsUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE_URL}/api/documents/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "File ingestion error.");
      }

      setDocuments((prev) => [data, ...prev]);
      alert(`Document '${file.name}' successfully parsed and indexed!`);
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setIsUploading(false);
      // Reset input value
      e.target.value = "";
    }
  };

  const handleDeleteDocument = async (id) => {
    if (!confirm("Confirm complete eviction of document and vectors from system?")) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/documents/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setDocuments((prev) => prev.filter((d) => d.id !== id));
        alert("Document deleted and vector space cleaned.");
      } else {
        const data = await res.json();
        alert(`Deletion failed: ${data.detail}`);
      }
    } catch (e) {
      alert("Error deleting document.");
    }
  };

  const handleSummarizeDocument = async (id) => {
    setIsSummarizing(true);
    setSummarizedDoc(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/documents/${id}/summarize`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.ok) {
        const doc = documents.find((d) => d.id === id);
        setSummarizedDoc({
          filename: doc ? doc.filename : "Document Summary",
          text: data.summary,
        });
      } else {
        alert(`Summarization failed: ${data.detail}`);
      }
    } catch (e) {
      alert("Error summarizing document.");
    } finally {
      setIsSummarizing(false);
    }
  };

  // -------------------------------------------------------------
  // 4. Admin Dashboard Metrics
  // -------------------------------------------------------------
  const fetchAdminStats = async () => {
    setIsAdminLoading(true);
    setAdminError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/admin/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.ok) {
        setAdminStats(data);
      } else {
        setAdminError(data.detail || "Unauthorized access to administrator dashboard.");
      }
    } catch (e) {
      setAdminError("Failed to load administration metrics.");
    } finally {
      setIsAdminLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "admin") {
      fetchAdminStats();
    }
  }, [activeTab]);

  // -------------------------------------------------------------
  // RENDERS
  // -------------------------------------------------------------
  if (isLoadingUser) {
    return (
      <div className="full-page-loader">
        <div className="spinner"></div>
        <p>Loading user profile context...</p>
      </div>
    );
  }

  // Not logged in view
  if (!token || !user) {
    return (
      <Login 
        isRegister={isRegister}
        setIsRegister={setIsRegister}
        authError={authError}
        setAuthError={setAuthError}
        usernameInput={usernameInput}
        setUsernameInput={setUsernameInput}
        passwordInput={passwordInput}
        setPasswordInput={setPasswordInput}
        handleAuthSubmit={handleAuthSubmit}
      />
    );
  }

  // Logged in main workspace
  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="main-view">
        <Topbar user={user} />
        
        {activeTab === "documents" && (
          <DocumentLibrary 
            documents={documents}
            isUploading={isUploading}
            uploadError={uploadError}
            handleFileUpload={handleFileUpload}
            handleSummarizeDocument={handleSummarizeDocument}
            isSummarizing={isSummarizing}
            uploadFilename={null}
          />
        )}
        
        {activeTab === "chat" && (
          <div className="chat-container">
            <div className="chat-messages-area">
              <div className="messages-list">
                {activeMessages.length === 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", height: "100%", alignItems: "center", justifyContent: "center", color: "var(--text-muted)", textAlign: "center" }}>
                    <h2 style={{ fontFamily: "var(--font-heading)", color: "var(--text-main)", marginBottom: "8px" }}>Welcome to IntelliDesk</h2>
                    <p style={{ maxWidth: "450px", fontSize: "0.9rem" }}>
                      Upload corporate documentation in the panel to your right, then type questions below. The assistant will answer using only verified document context.
                    </p>
                  </div>
                ) : (
                  activeMessages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`message-bubble-container ${msg.sender === "user" ? "user" : "assistant"}`}
                    >
                      {msg.sender === "user" ? null : (
                        <span className="message-sender">IntelliDesk AI</span>
                      )}
                      <div className="message-bubble">{msg.text}</div>
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="message-sources">
                          {msg.sources.map((src, i) => (
                            <span
                              key={i}
                              className="source-badge"
                              onClick={() => setSelectedCitation(src)}
                            >
                              📄 {src.filename} (Page {src.page})
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                )}
                {isAsking && (
                  <div className="message-bubble-container assistant">
                    <span className="message-sender">IntelliDesk AI</span>
                    <div className="message-bubble" style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div className="spinner"></div>
                      Retrieving context & generating answer...
                    </div>
                  </div>
                )}
                <div ref={messageEndRef} />
              </div>

              {chatError && <div className="error-banner" style={{ margin: "0 28px" }}>⚠️ {chatError}</div>}

              <form className="chat-input-area" onSubmit={handleAskQuestion}>
                <div className="chat-input-wrapper">
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    style={{ display: 'none' }} 
                    onChange={handleFileUpload} 
                  />
                  <button 
                    type="button" 
                    className="chat-icon-btn plus-btn" 
                    title="Add File"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
                  </button>
                  <input
                    className="chat-textbox"
                    value={questionInput}
                    onChange={(e) => setQuestionInput(e.target.value)}
                    placeholder="Ask anything"
                    disabled={isAsking}
                  />
                  <div className="chat-input-actions">
                    <button type="button" className="chat-icon-btn voice-btn" title="Voice Input">
                       <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="22"></line></svg>
                    </button>
                    {questionInput.trim() ? (
                       <button className="chat-icon-btn generate-btn" type="submit" disabled={isAsking} title="Send Message">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                      </button>
                    ) : (
                      <button type="button" className="chat-icon-btn generate-btn" title="Generate">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/></svg>
                      </button>
                    )}
                  </div>
                </div>
              </form>
            </div>
          </div>
        )}

        {activeTab === "dashboard" && (
          <div style={{ padding: "32px", maxWidth: "1200px", margin: "0 auto" }}>
            <h2 style={{fontSize: "1.8rem", marginBottom: "8px"}}>Dashboard</h2>
            <p style={{color: "var(--text-muted)"}}>Welcome to your FluidMind AI Dashboard.</p>
          </div>
        )}

        {activeTab === "admin" && (
           <div className="admin-view">
            {adminError && <div className="error-banner">⚠️ {adminError}</div>}
            {isAdminLoading ? (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "200px" }}>
                <div className="spinner"></div>
              </div>
            ) : adminStats ? (
              <>
                <div className="stats-grid">
                  <div className="stat-card glass-panel">
                    <span className="stat-label">Total Users</span>
                    <span className="stat-value">{adminStats.total_users}</span>
                  </div>
                  <div className="stat-card glass-panel">
                    <span className="stat-label">Indexed Documents</span>
                    <span className="stat-value">{adminStats.total_documents}</span>
                  </div>
                  <div className="stat-card glass-panel">
                    <span className="stat-label">Total API Queries</span>
                    <span className="stat-value">{adminStats.total_queries}</span>
                  </div>
                  <div className="stat-card glass-panel">
                    <span className="stat-label">Avg Response Time</span>
                    <span className="stat-value">{adminStats.avg_response_time.toFixed(2)}s</span>
                  </div>
                </div>
                <div className="logs-container glass-panel">
                  <div className="logs-header">📋 Recent Activity Logs</div>
                  <div className="logs-list">
                    {adminStats.recent_logs.map((log) => (
                      <div key={log.id} className="log-entry">
                        <span className="log-timestamp">[{new Date(log.created_at).toLocaleTimeString()}]</span>
                        <span className={`log-badge ${log.event_type}`}>{log.event_type.toUpperCase()}</span>
                        {log.username && (
                          <span className="log-user">&lt;{log.username}&gt;</span>
                        )}
                        <span className="log-message">{log.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : null}
          </div>
        )}
      </main>

      {/* 3. Summarization modal view */}
      {summarizedDoc && (
        <div className="modal-overlay" onClick={() => setSummarizedDoc(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setSummarizedDoc(null)}>✖</button>
            <h2 className="summary-title">📝 {summarizedDoc.filename} Summary</h2>
            <div className="summary-text" style={{ whiteSpace: "pre-wrap" }}>{summarizedDoc.text}</div>
          </div>
        </div>
      )}

      {/* 4. Citation detail modal view */}
      {selectedCitation && (
        <div className="modal-overlay" onClick={() => setSelectedCitation(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close-btn" onClick={() => setSelectedCitation(null)}>✖</button>
            <h2 className="summary-title">📄 Source Document Citation</h2>
            <div className="summary-block">
              <span className="summary-section-label">Source File</span>
              <p className="summary-text">{selectedCitation.filename}</p>
            </div>
            <div className="summary-block">
              <span className="summary-section-label">Source Coordinates</span>
              <p className="summary-text">Page / Sheet Reference: <b>{selectedCitation.page}</b></p>
            </div>
            <div style={{ marginTop: "20px", display: "flex", gap: "10px" }}>
              <button onClick={() => setSelectedCitation(null)} style={{ flex: 1, padding: '10px', background: 'var(--primary-color)', color: 'white', borderRadius: '8px' }}>
                Dismiss Reference
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
