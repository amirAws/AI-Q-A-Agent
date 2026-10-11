'use client';

import { useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [policyName, setPolicyName] = useState('');
  const [policyId, setPolicyId] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      
      // Auto-generate policy ID from filename
      if (!policyId) {
        const id = selectedFile.name
          .replace('.pdf', '')
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-');
        setPolicyId(id);
      }
    }
  };

  const handleUpload = async () => {
    if (!file || !policyName) {
      setError('Please select a file and enter policy name');
      return;
    }

    setUploading(true);
    setError('');
    setResult(null);

    try {
      // Convert file to base64
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64 = e.target?.result as string;
        const base64Data = base64.split(',')[1]; // Remove data:application/pdf;base64, prefix

        // Call Lambda via API Gateway
        const response = await fetch(`${API_URL}/upload`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            pdf_base64: base64Data,
            policy_name: policyName,
            policy_id: policyId,
          }),
        });

        const data = await response.json();
        
        if (response.ok) {
          setResult(data);
        } else {
          setError(data.error || 'Upload failed');
        }
        setUploading(false);
      };

      reader.onerror = () => {
        setError('Failed to read file');
        setUploading(false);
      };

      reader.readAsDataURL(file);
    } catch (err: any) {
      setError(err.message);
      setUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '20px' }}>
        Upload Insurance Policy
      </h1>

      <div style={{ 
        border: '2px dashed #ddd', 
        borderRadius: '8px', 
        padding: '30px',
        textAlign: 'center',
        marginBottom: '20px'
      }}>
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          style={{ marginBottom: '15px' }}
        />
        
        {file && (
          <p style={{ color: '#666', fontSize: '14px' }}>
            Selected: {file.name} ({(file.size / 1024).toFixed(0)} KB)
          </p>
        )}
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>
          Policy Name *
        </label>
        <input
          type="text"
          value={policyName}
          onChange={(e) => setPolicyName(e.target.value)}
          placeholder="e.g., HDFC Ergo Secure Plus"
          style={{
            width: '100%',
            padding: '10px',
            border: '1px solid #ddd',
            borderRadius: '6px',
            fontSize: '14px'
          }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500' }}>
          Policy ID
        </label>
        <input
          type="text"
          value={policyId}
          onChange={(e) => setPolicyId(e.target.value)}
          placeholder="e.g., hdfc-ergo-secure"
          style={{
            width: '100%',
            padding: '10px',
            border: '1px solid #ddd',
            borderRadius: '6px',
            fontSize: '14px'
          }}
        />
        <p style={{ color: '#666', fontSize: '12px', marginTop: '5px' }}>
          Auto-generated from filename. Used as unique identifier.
        </p>
      </div>

      <button
        onClick={handleUpload}
        disabled={uploading || !file || !policyName}
        style={{
          width: '100%',
          padding: '12px',
          background: uploading ? '#ccc' : '#007bff',
          color: '#fff',
          border: 'none',
          borderRadius: '6px',
          fontSize: '16px',
          fontWeight: '500',
          cursor: uploading ? 'not-allowed' : 'pointer'
        }}
      >
        {uploading ? 'Uploading...' : 'Upload Policy'}
      </button>

      {error && (
        <div style={{
          marginTop: '20px',
          padding: '15px',
          background: '#fee',
          border: '1px solid #fcc',
          borderRadius: '6px',
          color: '#c00'
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={{
          marginTop: '20px',
          padding: '15px',
          background: '#efe',
          border: '1px solid #cfc',
          borderRadius: '6px'
        }}>
          <h3 style={{ marginBottom: '10px' }}>✅ Upload Successful!</h3>
          <p><strong>Policy:</strong> {result.policy_name}</p>
          <p><strong>ID:</strong> {result.policy_id}</p>
          <p><strong>Pages:</strong> {result.pages}</p>
          <p><strong>Chunks:</strong> {result.chunks_created}</p>
        </div>
      )}

      <div style={{ marginTop: '30px', padding: '15px', background: '#f8f9fa', borderRadius: '6px' }}>
        <p style={{ fontSize: '14px', marginBottom: '10px' }}><strong>Note:</strong></p>
        <ul style={{ fontSize: '14px', paddingLeft: '20px' }}>
          <li>Only PDF files are supported</li>
          <li>Large files may take a few minutes to process</li>
          <li>The document will be chunked and embedded for search</li>
        </ul>
      </div>

      <div style={{ marginTop: '20px', textAlign: 'center' }}>
        <a href="/" style={{ color: '#007bff', textDecoration: 'none' }}>
          ← Back to Chat
        </a>
      </div>
    </div>
  );
}
