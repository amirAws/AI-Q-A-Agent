'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

export default function Home() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [selectedPolicies, setSelectedPolicies] = useState<string[]>([]);
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Load policies on mount
  useEffect(() => {
    loadPolicies();
  }, []);

  const loadPolicies = async () => {
    try {
      const response = await axios.get(`${API_URL}/policies`);
      setPolicies(response.data.policies || []);
    } catch (error) {
      console.error('Error loading policies:', error);
    }
  };

  const togglePolicy = (policyId: string) => {
    setSelectedPolicies(prev =>
      prev.includes(policyId)
        ? prev.filter(id => id !== policyId)
        : [...prev, policyId]
    );
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        message: input,
        policy_ids: selectedPolicies,
        session_id: `session-${Date.now()}`
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error: Could not get response'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '20px' }}>
        Health Insurance Policy Advisor
      </h1>
      
      <div style={{ marginBottom: '15px', textAlign: 'right' }}>
        <a 
          href="/upload" 
          style={{ 
            color: '#007bff', 
            textDecoration: 'none',
            padding: '8px 16px',
            border: '1px solid #007bff',
            borderRadius: '6px',
            fontSize: '14px'
          }}
        >
          📤 Upload Policy
        </a>
      </div>

      {/* Policy Selector */}
      <div style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '8px' }}>
        <h2 style={{ fontSize: '18px', marginBottom: '10px' }}>Select Policies to Compare:</h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {policies.length === 0 ? (
            <p style={{ color: '#666' }}>No policies uploaded yet</p>
          ) : (
            policies.map(policy => (
              <button
                key={policy.policy_id}
                onClick={() => togglePolicy(policy.policy_id)}
                style={{
                  padding: '8px 16px',
                  borderRadius: '6px',
                  border: '1px solid #ddd',
                  background: selectedPolicies.includes(policy.policy_id) ? '#007bff' : '#fff',
                  color: selectedPolicies.includes(policy.policy_id) ? '#fff' : '#000',
                  cursor: 'pointer'
                }}
              >
                {policy.policy_name}
              </button>
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div style={{ border: '1px solid #ddd', borderRadius: '8px', height: '500px', display: 'flex', flexDirection: 'column' }}>
        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '15px' }}>
          {messages.length === 0 ? (
            <p style={{ color: '#666', textAlign: 'center', marginTop: '20px' }}>
              Ask a question about the selected policies
            </p>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  marginBottom: '15px',
                  padding: '10px 15px',
                  borderRadius: '8px',
                  background: msg.role === 'user' ? '#e3f2fd' : '#f5f5f5',
                  marginLeft: msg.role === 'user' ? '20%' : '0',
                  marginRight: msg.role === 'user' ? '0' : '20%'
                }}
              >
                <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong>
                <p style={{ margin: '5px 0 0 0', whiteSpace: 'pre-wrap' }}>{msg.content}</p>
              </div>
            ))
          )}
          {loading && (
            <div style={{ padding: '10px', color: '#666' }}>Thinking...</div>
          )}
        </div>

        {/* Input */}
        <div style={{ padding: '15px', borderTop: '1px solid #ddd', display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask about maternity coverage, premiums, exclusions..."
            style={{
              flex: 1,
              padding: '10px',
              border: '1px solid #ddd',
              borderRadius: '6px',
              fontSize: '14px'
            }}
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            style={{
              padding: '10px 20px',
              background: '#007bff',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              opacity: loading || !input.trim() ? 0.5 : 1
            }}
          >
            Send
          </button>
        </div>
      </div>

      {/* Info */}
      <div style={{ marginTop: '20px', padding: '15px', background: '#f8f9fa', borderRadius: '8px', fontSize: '14px' }}>
        <p><strong>Example questions:</strong></p>
        <ul style={{ marginTop: '10px', paddingLeft: '20px' }}>
          <li>What is the maternity coverage?</li>
          <li>Compare premium amounts between selected policies</li>
          <li>What are the exclusions in these policies?</li>
          <li>Which policy has better coverage for pre-existing conditions?</li>
        </ul>
      </div>
    </div>
  );
}
