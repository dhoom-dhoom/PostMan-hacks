import React from 'react';
import ReactDOM from 'react-dom/client';  // Use the new root API
import App from './App';  // Import the App component

// Create a root to render the React app
const root = ReactDOM.createRoot(document.getElementById('root'));

// Render the App component inside the root element
root.render(
  <App />
);
