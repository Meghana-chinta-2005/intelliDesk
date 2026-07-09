import React from "react";
import "./DocumentCard.css";

export default function DocumentCard({ doc, handleSummarizeDocument, isSummarizing }) {
  const getIconClass = (filename) => {
    if (!filename) return "pdf";
    const lower = filename.toLowerCase();
    if (lower.endsWith(".doc") || lower.endsWith(".docx") || lower.endsWith(".txt")) return "doc";
    if (lower.endsWith(".xls") || lower.endsWith(".xlsx") || lower.endsWith(".csv")) return "xls";
    return "pdf";
  };

  const iconClass = getIconClass(doc.filename);
  
  // Fake meta info based on size/chunks for visual matching
  const pages = Math.max(1, Math.floor(doc.file_size / 20000)); 
  const time = "Recently";

  return (
    <div className="doc-card">
      <div className={`doc-card-icon ${iconClass}`}>
        {iconClass === "pdf" && (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
        )}
        {iconClass === "doc" && (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
        )}
        {iconClass === "xls" && (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><rect x="8" y="13" width="8" height="4"></rect></svg>
        )}
      </div>
      
      <div className="doc-card-title" title={doc.filename}>{doc.filename}</div>
      
      <div className="doc-card-meta">
        <span>{pages} Pages</span>
        <span className="meta-dot"></span>
        <span>{time}</span>
      </div>

      <div className="doc-card-actions">
        <button className="action-btn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
          Open
        </button>
        <button 
          className="action-btn" 
          onClick={() => handleSummarizeDocument(doc.id)}
          disabled={isSummarizing}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg>
          Summary
        </button>
      </div>

      <button className="chat-btn">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        Chat with Doc
      </button>
    </div>
  );
}
