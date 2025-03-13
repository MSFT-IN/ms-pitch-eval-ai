import { useState } from "react";
import './App.css';
import axios from "axios";

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile && selectedFile.type === "audio/wav") {
      setFile(selectedFile);
    } else {
      alert("please upload .wav file");
    }
  };

  const handleUpload = async () => {
    if (!file) {
      alert("please upload .wav file");
      return;
    }
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const response = await fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData
      });

      const result = await response.json();
      setUrl(result.url);
      console.log("result: ", result);
    } catch (error) {
      console.error("upload failed", error);
      alert("Upload Failed");
    }
  };

  return (
    <div className="App">
      <div className="App-header">
        <p>Azure Sales Pitch Coaching System</p>
        <div>
          <input type="file" accept=".wav" onChange={handleFileChange} />
          <button onClick={handleUpload}>Upload to Blob</button>
        </div>
        <div>
        <p>{url ? 'blob url: ' + url : ''}</p>
        </div>
      </div>
    </div>
  );
}

export default App;
