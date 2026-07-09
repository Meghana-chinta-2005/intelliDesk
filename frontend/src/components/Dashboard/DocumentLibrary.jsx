import React from "react";
import "./DocumentLibrary.css";
import DocumentCard from "./DocumentCard";

export default function DocumentLibrary({
  documents,
  isUploading,
  uploadError,
  handleFileUpload,
  handleSummarizeDocument,
  isSummarizing,
  uploadFilename
}) {
  return (
    <div className="doc-library">
      <div className="library-header">
        <div>
          <h1 className="library-title">Document Library</h1>
          <p className="library-subtitle">Manage and organize your research assets.</p>
        </div>
        <div className="library-filters">
          <button className="filter-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
            All Formats
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
          <button className="filter-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="20" x2="12" y2="10"></line><line x1="18" y1="20" x2="18" y2="4"></line><line x1="6" y1="20" x2="6" y2="16"></line></svg>
            Recent First
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
        </div>
      </div>

      <label className="dropzone-container" style={{ display: 'block' }}>
        <input
          type="file"
          accept=".pdf,.docx,.xlsx,.txt"
          onChange={handleFileUpload}
          style={{ display: "none" }}
          disabled={isUploading}
        />
        <div className="drop-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
        </div>
        <div className="drop-title">+ Drop Files Here</div>
        <div className="drop-subtitle">Support for PDF, DOCX, XLSX (Max 100MB per file)</div>
        {uploadError && (
          <div style={{ color: "red", fontSize: "0.85rem", marginTop: "10px" }}>{uploadError}</div>
        )}
      </label>

      {isUploading && (
        <div className="processing-card">
          <div className="processing-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          </div>
          <div className="processing-info">
            <div className="processing-filename">{uploadFilename || "Document.pdf"}</div>
            <div className="processing-size">Processing...</div>
          </div>
          <div className="processing-steps">
            Processing... <span className="step-arrow">→</span> Extracting Text... <span className="step-arrow">→</span> Creating Embeddings... <span className="step-arrow">→</span> Completed ✓
          </div>
          <div className="progress-bar-bg">
            <div className="progress-bar-fill"></div>
          </div>
        </div>
      )}

      <div className="documents-grid">
        {documents.map((doc) => (
          <DocumentCard 
            key={doc.id} 
            doc={doc} 
            handleSummarizeDocument={handleSummarizeDocument}
            isSummarizing={isSummarizing}
          />
        ))}
      </div>

      <div className="analytics-section">
        <h2>System Analytics</h2>
        {/* Placeholder for Analytics if activeTab changes or if it's integrated here */}
        <p style={{ color: 'var(--text-muted)' }}>Metrics are automatically aggregated from system logs.</p>
      </div>
    </div>
  );
}
