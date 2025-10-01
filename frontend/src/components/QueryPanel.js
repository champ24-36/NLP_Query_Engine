import React, { useState, useEffect } from 'react';
import { Search, Clock, Loader } from 'lucide-react';

const QueryPanel = ({ API_BASE_URL, dbConnected, onQueryResult }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [queryHistory, setQueryHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  const sampleQueries = [
    "How many employees do we have?",
    "Average salary by department", 
    "List employees hired this year",
    "Show me Python developers",
    "Top 5 highest paid employees",
    "Employees with machine learning skills"
  ];

  useEffect(() => {
    fetchQueryHistory();
  }, []);

  const fetchQueryHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/query/history`);
      const data = await response.json();
      setQueryHistory(data);
    } catch (error) {
      console.error('Error fetching query history:', error);
    }
  };

  const handleQuerySubmit = async (queryText = query) => {
    if (!queryText.trim()) return;
    
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: queryText }),
      });

      const data = await response.json();
      
      if (response.ok) {
        if (onQueryResult) {
          onQueryResult(data);
        }
        fetchQueryHistory(); // Refresh history
      } else {
        if (onQueryResult) {
          onQueryResult({
            error: data.detail || 'Query failed',
            query_type: 'error',
            results: [],
            sources: []
          });
        }
      }
    } catch (error) {
      if (onQueryResult) {
        onQueryResult({
          error: `Network error: ${error.message}`,
          query_type: 'error',
          results: [],
          sources: []
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleQuerySubmit();
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <Search className="mr-2" size={20} />
          Natural Language Query
        </h3>
        
        <div className="space-y-4">
          <div className="relative">
            <textarea
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              placeholder="Ask anything about your employee data..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={3}
              disabled={!dbConnected}
            />
            
            {!dbConnected && (
              <div className="absolute inset-0 bg-gray-50 bg-opacity-75 flex items-center justify-center rounded-lg">
                <p className="text-gray-500">Connect to database first</p>
              </div>
            )}
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => handleQuerySubmit()}
              disabled={!dbConnected || !query.trim() || loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {loading ? <Loader className="animate-spin mr-2" size={16} /> : <Search className="mr-2" size={16} />}
              {loading ? 'Processing...' : 'Query'}
            </button>
            
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 flex items-center"
            >
              <Clock className="mr-2" size={16} />
              History
            </button>
          </div>
        </div>
        
        {/* Sample queries */}
        <div className="mt-6">
          <p className="text-sm font-medium text-gray-700 mb-3">Try these sample queries:</p>
          <div className="flex flex-wrap gap-2">
            {sampleQueries.map((sample, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuery(sample);
                  handleQuerySubmit(sample);
                }}
                className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                disabled={!dbConnected}
              >
                {sample}
              </button>
            ))}
          </div>
        </div>
        
        {/* Query history */}
        {showHistory && queryHistory.length > 0 && (
          <div className="mt-6 border-t pt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Recent Queries</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {queryHistory.slice(0, 10).map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setQuery(item.query);
                    handleQuerySubmit(item.query);
                  }}
                  className="block w-full text-left p-2 text-sm bg-gray-50 hover:bg-gray-100 rounded transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <span className="flex-1 truncate">{item.query}</span>
                    <span className="text-xs text-gray-500 ml-2">
                      {item.cached ? '⚡' : ''}
                      {item.processing_time ? `${item.processing_time.toFixed(2)}s` : ''}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default QueryPanel;
