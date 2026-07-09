import React from "react";
import "./Topbar.css";

export default function Topbar({ user }) {
  const username = user?.username || "Alex Rivera";
  const role = user?.is_admin ? "Administrator" : "Lead Researcher";
  const avatarLetter = username ? username.charAt(0).toUpperCase() : "A";

  return (
    <div className="topbar">
      <div className="search-container">
        <span className="search-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        </span>
        <input 
          type="text" 
          className="search-input" 
          placeholder="Search your knowledge base..." 
        />
      </div>

      <div className="topbar-right">
        <div className="notification-bell">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
        </div>
        
        <div className="profile-section">
          <div className="profile-info">
            <span className="profile-name">{username}</span>
            <span className="profile-role">{role}</span>
          </div>
          <div className="profile-avatar">
            {avatarLetter}
          </div>
        </div>
      </div>
    </div>
  );
}
