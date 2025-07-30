
// frontend/src/Dashboard.js
import React, { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import './Dashboard.css';

const LOCAL_STORAGE_TOKEN_KEY = 'pragyashal_jwt_token';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState('');
  const [detectedCategory, setDetectedCategory] = useState('others');

  // Updated state for search functionality
  // searchResult will now be an object: { url: string, category: string } or null
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [searchMessage, setSearchMessage] = useState('');
  const [searching, setSearching] = useState(false);

  const FLASK_BACKEND_URL = process.env.REACT_APP_FLASK_BACKEND_URL;

  const getFileCategoryFromMime = (mimeType) => {
    if (!mimeType) return 'others';
    if (mimeType.startsWith('image/')) return 'images';
    if (mimeType.startsWith('video/')) return 'videos';
    if (mimeType.startsWith('audio/')) return 'audios';
    return 'others';
  };

  const handleLogout = () => {
    localStorage.removeItem(LOCAL_STORAGE_TOKEN_KEY);
    localStorage.removeItem('pragyashal_user');
    logout();
    navigate('/login');
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
    setUploadMessage('');

    if (file) {
      const category = getFileCategoryFromMime(file.type);
      setDetectedCategory(category);
    } else {
      setDetectedCategory('others');
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) {
      setUploadMessage('Please select a file first!');
      return;
    }

    setUploading(true);
    setUploadMessage('Uploading...');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('category', detectedCategory);
    
    


    try {
      const token = localStorage.getItem(LOCAL_STORAGE_TOKEN_KEY);
      if (!token) {
        setUploadMessage('No authentication token found. Please login again.');
        setUploading(false);
        return;
      }
      console.log('Using token:', token);
      for (let pair of formData.entries()) {
  console.log(pair[0] + ':', pair[1]);
}

// mokshasai910@

      const res = await fetch(`${FLASK_BACKEND_URL}/upload_file`, {
        method: 'POST',
        body: formData,
        headers: {
          Authorization: `Bearer ${token}`,
            // 'Content-Type': 'multipart/form-data',
        },
      });

      console.log(res);

      const data = await res.json();

      if (res.ok && data.success) {
        setUploadMessage('File uploaded successfully!');
        setSelectedFile(null);
        setDetectedCategory('others');
        document.getElementById('file-upload-input').value = '';
      } else {
        setUploadMessage(`Upload failed: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      setUploadMessage('Network error or server unavailable during upload.');
    } finally {
      setUploading(false);
    }
  };

  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
    setSearchResult(null); // Clear previous result on new query
    setSearchMessage('');
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchMessage('Please enter a filename to search.');
      setSearchResult(null);
      return;
    }

    setSearching(true);
    setSearchMessage('Searching...');
    setSearchResult(null); // Clear previous results

    try {
      const token = localStorage.getItem(LOCAL_STORAGE_TOKEN_KEY);
      if (!token) {
        setSearchMessage('No authentication token found. Please login again.');
        setSearching(false);
        return;
      }

      const res = await fetch(`${FLASK_BACKEND_URL}/search_file?filename=${encodeURIComponent(searchQuery.trim())}`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
            // 'Content-Type': 'multipart/form-data',
        },
      });

      const data = await res.json();

      if (res.ok && data.success) {
        // Store both the URL and the category returned from the backend
        setSearchResult({ url: data.file_url, category: data.file_category });
        setSearchMessage(`File found in '${data.file_category}' category!`);
      } else {
        setSearchResult(null);
        setSearchMessage(data.error || 'File not found or an error occurred.');
      }
    } catch (error) {
      console.error("Search API call error:", error);
      setSearchMessage('Network error or server unavailable during search.');
    } finally {
      setSearching(false);
    }
  };

  if (!user) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <h2 className="welcome-message">
          Welcome, <span>{user.name || user.email}!</span>
        </h2>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </header>

      <main>
        {/* Search Section - Moved to the top */}
        <div className="search-container">
          <h3>Search Your Files</h3>
          <div className="search-input-group">
            <input
              type="text"
              placeholder="Enter filename (e.g., my_image.png, my_song.mp3, my_document.pdf)"
              value={searchQuery}
              onChange={handleSearchChange}
              className="search-input"
            />
            <button
              onClick={handleSearch}
              disabled={searching}
              className="search-button"
            >
              {searching ? 'Searching...' : 'Search File'}
            </button>
          </div>

          {searchMessage && (
            <p
              className={`search-message ${
                searchMessage.toLowerCase().includes('not found') || searchMessage.toLowerCase().includes('error') ? 'error' : 'success'
              }`}
            >
              {searchMessage}
            </p>
          )}

          {searchResult && (
            <div className="search-result-display">
              <h4>Found File: ({searchResult.category})</h4>
              {/* Conditional rendering based on file category */}
              {searchResult.category === 'images' && (
                <img src={searchResult.url} alt="Searched File" className="searched-image" />
              )}
              {searchResult.category === 'videos' && (
                <video src={searchResult.url} controls className="searched-video">
                  Your browser does not support the video tag.
                </video>
              )}
              {searchResult.category === 'audios' && (
                <audio src={searchResult.url} controls className="searched-audio">
                  Your browser does not support the audio element.
                </audio>
              )}
              {searchResult.category === 'others' && (
                <div className="searched-other-file">
                  <p>Generic File Found:</p>
                  <a href={searchResult.url} target="_blank" rel="noopener noreferrer" className="download-link">
                    Download {searchQuery}
                  </a>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Content Upload Section - Moved below the search section */}
        <div className="upload-container">
          <h3>Content Upload</h3>
          <p>Your personal cloud storage is ready! Upload your multimedia files to begin.</p>

          <div className="file-dropzone">
            <span className="file-dropzone-text">
              {selectedFile ? selectedFile.name : 'Click here to select a file'}
            </span>
            <input
              id="file-upload-input"
              type="file"
              onChange={handleFileChange}
              className="file-input-hidden"
            />
          </div>

          {selectedFile && (
            <p className="detected-category">
              Detected Category: <span>{detectedCategory}</span>
            </p>
          )}

          <button
            onClick={handleFileUpload}
            disabled={uploading || !selectedFile}
            className="upload-button"
          >
            {uploading ? 'Uploading...' : 'Upload File'}
          </button>

          {uploadMessage && (
            <p
              className={`upload-message ${
                uploadMessage.toLowerCase().includes('failed') ? 'error' : 'success'
              }`}
            >
              {uploadMessage}
            </p>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
