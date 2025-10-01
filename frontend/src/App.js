import React, { useState, useEffect } from 'react';
import { Database, Search, BarChart3 } from 'lucide-react';
import DatabaseConnector from './components/DatabaseConnector';
import DocumentUploader from './components/DocumentUploader';
import QueryPanel from './components/QueryPanel';
import ResultsView from './components/ResultsView';

const API_BASE_URL = 'http://localhost:8000/api';

const NLPQueryEngine = () => {
  const [activeTab, setActiveTab] = useState('connect');
  const [dbConnected, setDbConnected] = useState(false);
  const [queryResults, setQueryResults] = useState(null);
  const [metrics, setMetrics] = useState({});

  // Fetch system metrics
  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/metrics`);
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const handleDatabaseConnection = (data) => {
    setDbConnected(true);
    fetchMetrics();
  };

  const handleUploadComplete = (data) => {
    fetchMetrics();
  };

  const handleQueryResult = (data) => {
    setQueryResults(data);
  };

  // Metrics dashboard
  const MetricsDashboard = () => {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Database</p>
              <p className="text-2xl font-bold text-blue-600">
                {metrics.database_connected ? 'Connected' : 'Disconnected'}
              </p>
            </div>
            <Database className={`${metrics.database_connected ? 'text-green-500' : 'text-red-500'}`} size={24} />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Documents</p>
              <p className="text-2xl font-bold text-green-600">{metrics.documents_indexed || 0}</p>
            </div>
            <BarChart3 className="text-green-500" size={24} />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Cache Hit Rate</p>
              <p className="text-2xl font-bold text-purple-600">
                {metrics.cache_hit_rate ? `${(metrics.cache_hit_rate * 100).toFixed(1)}%` : '0%'}
              </p>
            </div>
            <BarChart3 className="text-purple-500" size={24} />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Jobs</p>
              <p className="text-2xl font-bold text-orange-600">{metrics.active_jobs || 0}</p>
            </div>
            <Search className="text-orange-500" size={24} />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">NLP Query Engine</h1>
              <p className="text-sm text-gray-600">Dynamic employee data analysis with natural language</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className={`w-3 h-3 rounded-full ${dbConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">
                {dbConnected ? 'Connected' : 'Not Connected'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Metrics Dashboard */}
        <MetricsDashboard />
        
        {/* Navigation Tabs */}
        <div className="flex space-x-1 bg-gray-200 rounded-lg p-1 mb-8">
          {[
            { id: 'connect', label: 'Connect Data', icon: Database },
            { id: 'query', label: 'Query Data', icon: Search },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                <Icon className="mr-2" size={16} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        {activeTab === 'connect' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <DatabaseConnector 
              onConnectionSuccess={handleDatabaseConnection}
              API_BASE_URL={API_BASE_URL}
            />
            <DocumentUploader 
              API_BASE_URL={API_BASE_URL}
              onUploadComplete={handleUploadComplete}
            />
          </div>
        )}
        
        {activeTab === 'query' && (
          <div className="space-y-6">
            <QueryPanel 
              API_BASE_URL={API_BASE_URL}
              dbConnected={dbConnected}
              onQueryResult={handleQueryResult}
            />
            <ResultsView results={queryResults} />
          </div>
        )}
      </div>
    </div>
  );
};

export default NLPQueryEngine;

const NLPQueryEngine = () => {
  const [activeTab, setActiveTab] = useState('connect');
  const [dbConnected, setDbConnected] = useState(false);
  const [schema, setSchema] = useState(null);
  const [query, setQuery] = useState('');
  const [queryResults, setQueryResults] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [metrics, setMetrics] = useState({});
  const [connectionString, setConnectionString] = useState('');
  const [dragActive, setDragActive] = useState(false);

  // Fetch system metrics
  const fetchMetrics = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/metrics`);
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  }, []);

  // Fetch query history
  const fetchQueryHistory = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/query/history`);
      const data = await response.json();
      setQueryHistory(data);
    } catch (error) {
      console.error('Error fetching query history:', error);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    fetchQueryHistory();
  }, [fetchMetrics, fetchQueryHistory]);

  // Database connection component
  const DatabaseConnector = () => {
    const [connecting, setConnecting] = useState(false);
    const [connectionStatus, setConnectionStatus] = useState('');

    const handleConnect = async () => {
      if (!connectionString.trim()) {
        setConnectionStatus('Please enter a connection string');
        return;
      }

      setConnecting(true);
      setConnectionStatus('');

      try {
        const response = await fetch(`${API_BASE_URL}/connect-database`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ connection_string: connectionString }),
        });

        const data = await response.json();

        if (response.ok) {
          setDbConnected(true);
          setSchema(data.schema);
          setConnectionStatus(`✅ Connected! Found ${data.tables_count} tables, ${data.relationships_count} relationships`);
          fetchMetrics();
        } else {
          setConnectionStatus(`❌ Connection failed: ${data.detail}`);
        }
      } catch (error) {
        setConnectionStatus(`❌ Connection error: ${error.message}`);
      } finally {
        setConnecting(false);
      }
    };

    const testConnections = [
      'postgresql://user:password@localhost:5432/company_db',
      'sqlite:///./employee_data.db',
      'mysql://user:password@localhost:3306/hr_system'
    ];

    return (
      <div className="space-y-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Database className="mr-2" size={20} />
            Database Connection
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Connection String
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="postgresql://username:password@localhost:5432/database"
                value={connectionString}
                onChange={(e) => setConnectionString(e.target.value)}
                disabled={connecting}
              />
            </div>
            
            <div className="flex gap-2">
              <button
                onClick={handleConnect}
                disabled={connecting || !connectionString.trim()}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {connecting ? <Loader className="animate-spin mr-2" size={16} /> : <Database className="mr-2" size={16} />}
                {connecting ? 'Connecting...' : 'Connect & Analyze'}
              </button>
            </div>
            
            {connectionStatus && (
              <div className={`p-3 rounded-md ${connectionStatus.includes('✅') ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                {connectionStatus}
              </div>
            )}
            
            <div className="text-sm text-gray-600">
              <p className="font-medium mb-2">Example connections:</p>
              {testConnections.map((conn, idx) => (
                <button
                  key={idx}
                  onClick={() => setConnectionString(conn)}
                  className="block w-full text-left p-2 hover:bg-gray-50 rounded font-mono text-xs"
                >
                  {conn}
                </button>
              ))}
            </div>
          </div>
        </div>

        {schema && <SchemaVisualization schema={schema} />}
      </div>
    );
  };

  // Schema visualization component
  const SchemaVisualization = ({ schema }) => {
    const tables = schema?.tables || {};
    
    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-lg font-semibold mb-4">Discovered Schema</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(tables).map(([tableName, tableInfo]) => (
            <div key={tableName} className="border border-gray-200 rounded-md p-4">
              <h4 className="font-semibold text-blue-600 mb-2">{tableName}</h4>
              <p className="text-xs text-gray-500 mb-2">
                Purpose: {tableInfo.purpose} • Rows: {tableInfo.row_count}
              </p>
              
              <div className="space-y-1">
                <p className="text-xs font-medium text-gray-700">Columns:</p>
                {Object.entries(tableInfo.columns).slice(0, 5).map(([colName, colInfo]) => (
                  <div key={colName} className="text-xs text-gray-600 flex justify-between">
                    <span>{colName}</span>
                    <span className="text-gray-400">{colInfo.type}</span>
                  </div>
                ))}
                {Object.keys(tableInfo.columns).length > 5 && (
                  <p className="text-xs text-gray-400">...and {Object.keys(tableInfo.columns).length - 5} more</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Document uploader component
  const DocumentUploader = () => {
    const [uploadJobs, setUploadJobs] = useState({});

    const handleDrag = (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (e.type === 'dragenter' || e.type === 'dragover') {
        setDragActive(true);
      } else if (e.type === 'dragleave') {
        setDragActive(false);
      }
    };

    const handleDrop = (e) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      
      const files = Array.from(e.dataTransfer.files);
      handleFiles(files);
    };

    const handleFiles = async (files) => {
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));

      try {
        const response = await fetch(`${API_BASE_URL}/upload-documents`, {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        
        if (response.ok) {
          setUploadJobs(prev => ({
            ...prev,
            [data.job_id]: {
              status: data.status,
              total_files: data.total_files,
              processed_files: 0,
              files: files.map(f => f.name)
            }
          }));
          
          // Poll for status updates
          pollUploadStatus(data.job_id);
        }
      } catch (error) {
        console.error('Upload error:', error);
      }
    };

    const pollUploadStatus = async (jobId) => {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/ingestion-status/${jobId}`);
          const data = await response.json();
          
          setUploadJobs(prev => ({
            ...prev,
            [jobId]: { ...prev[jobId], ...data }
          }));
          
          if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(interval);
            fetchMetrics(); // Refresh metrics after upload
          }
        } catch (error) {
          console.error('Status polling error:', error);
          clearInterval(interval);
        }
      }, 2000);
    };

    return (
      <div className="space-y-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Upload className="mr-2" size={20} />
            Document Upload
          </h3>
          
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <Upload className="mx-auto mb-4 text-gray-400" size={48} />
            <p className="text-lg mb-2">Drop files here or click to browse</p>
            <p className="text-sm text-gray-500 mb-4">Supports PDF, DOCX, TXT, CSV files</p>
            
            <input
              type="file"
              multiple
              onChange={(e) => handleFiles(Array.from(e.target.files))}
              className="hidden"
              id="file-upload"
              accept=".pdf,.docx,.txt,.csv"
            />
            <label
              htmlFor="file-upload"
              className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md cursor-pointer hover:bg-blue-700"
            >
              Choose Files
            </label>
          </div>
          
          {Object.keys(uploadJobs).length > 0 && (
            <div className="mt-6 space-y-4">
              <h4 className="font-semibold">Upload Progress</h4>
              {Object.entries(uploadJobs).map(([jobId, job]) => (
                <UploadJobStatus key={jobId} jobId={jobId} job={job} />
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  const UploadJobStatus = ({ jobId, job }) => {
    const progress = job.total_files > 0 ? (job.processed_files / job.total_files) * 100 : 0;
    
    return (
      <div className="border border-gray-200 rounded-md p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Job {jobId.slice(0, 8)}...</span>
          <span className="text-sm text-gray-500">
            {job.processed_files}/{job.total_files} files
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              job.status === 'completed' ? 'bg-green-500' : 
              job.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
        
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span className="flex items-center">
            {job.status === 'processing' && <Loader className="animate-spin mr-1" size={12} />}
            {job.status === 'completed' && <CheckCircle className="text-green-500 mr-1" size={12} />}
            {job.status === 'failed' && <AlertCircle className="text-red-500 mr-1" size={12} />}
            {job.status}
          </span>
          {job.failed_files > 0 && (
            <span className="text-red-600">{job.failed_files} failed</span>
          )}
        </div>
      </div>
    );
  };

  // Query interface component
  const QueryInterface = () => {
    const [suggestions, setSuggestions] = useState([]);
    const [showHistory, setShowHistory] = useState(false);

    const sampleQueries = [
      "How many employees do we have?",
      "Average salary by department", 
      "List employees hired this year",
      "Show me Python developers",
      "Top 5 highest paid employees",
      "Employees with machine learning skills"
    ];

    const handleQuerySubmit = async (queryText = query) => {
      if (!queryText.trim()) return;
      
      setLoading(true);
      setQueryResults(null);

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
          setQueryResults(data);
          fetchQueryHistory(); // Refresh history
        } else {
          setQueryResults({
            error: data.detail || 'Query failed',
            query_type: 'error',
            results: [],
            sources: []
          });
        }
      } catch (error) {
        setQueryResults({
          error: `Network error: ${error.message}`,
          query_type: 'error',
          results: [],
          sources: []
        });
      } finally {
        setLoading(false);
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
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleQuerySubmit();
                  }
                }}
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
                        {item.processing_time?.toFixed(2)}s
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {queryResults && <QueryResults results={queryResults} />}
      </div>
    );
  };

  // Query results component
  const QueryResults = ({ results }) => {
    const downloadResults = () => {
      const data = JSON.stringify(results, null, 2);
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'query-results.json';
      a.click();
      URL.revokeObjectURL(url);
    };

    if (results.error) {
      return (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center text-red-600 mb-4">
            <AlertCircle className="mr-2" size={20} />
            <h3 className="text-lg font-semibold">Query Error</h3>
          </div>
          <p className="text-red-700">{results.error}</p>
        </div>
      );
    }

    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold flex items-center">
            <FileText className="mr-2" size={20} />
            Query Results
          </h3>
          
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span className="flex items-center">
              <Clock className="mr-1" size={14} />
              {results.performance_metrics?.response_time?.toFixed(2)}s
            </span>
            {results.performance_metrics?.cache_hit && (
              <span className="text-green-600">⚡ Cached</span>
            )}
            <button
              onClick={downloadResults}
              className="flex items-center text-blue-600 hover:text-blue-700"
            >
              <Download className="mr-1" size={14} />
              Export
            </button>
          </div>
        </div>
        
        <div className="mb-4 flex items-center gap-4 text-sm">
          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
            {results.query_type}
          </span>
          <span className="text-gray-600">
            Sources: {results.sources?.join(', ')}
          </span>
          {results.sql_query && (
            <button className="text-blue-600 hover:text-blue-700 flex items-center">
              <Eye className="mr-1" size={14} />
              View SQL
            </button>
          )}
        </div>
        
        {results.query_type === 'sql' && <SQLResults data={results.results} />}
        {results.query_type === 'document' && <DocumentResults data={results.results} />}
        {results.query_type === 'hybrid' && <HybridResults data={results.results} />}
      </div>
    );
  };

  const SQLResults = ({ data }) => {
    if (!Array.isArray(data) || data.length === 0) {
      return <p className="text-gray-500">No results found.</p>;
    }

    const columns = Object.keys(data[0]);
    
    return (
      <div className="overflow-x-auto">
        <table className="min-w-full border border-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map(col => (
                <th key={col} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.slice(0, 50).map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                {columns.map(col => (
                  <td key={col} className="px-4 py-2 text-sm text-gray-900 border-r">
                    {row[col] !== null && row[col] !== undefined ? String(row[col]) : '-'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        
        {data.length > 50 && (
          <p className="mt-2 text-sm text-gray-500">
            Showing first 50 of {data.length} results
          </p>
        )}
      </div>
    );
  };

  const DocumentResults = ({ data }) => {
    if (!Array.isArray(data) || data.length === 0) {
      return <p className="text-gray-500">No relevant documents found.</p>;
    }

    return (
      <div className="space-y-4">
        {data.map((doc, idx) => (
          <div key={idx} className="border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h4 className="font-semibold text-blue-600">{doc.filename}</h4>
                <p className="text-xs text-gray-500">
                  Type: {doc.doc_type} • Similarity: {(doc.similarity_score * 100).toFixed(1)}%
                </p>
              </div>
            </div>
            
            <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
              <p>{doc.chunk_text.substring(0, 300)}{doc.chunk_text.length > 300 ? '...' : ''}</p>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const HybridResults = ({ data }) => {
    return (
      <div className="space-y-6">
        {data.sql_results && data.sql_results.length > 0 && (
          <div>
            <h4 className="font-semibold mb-3 text-blue-600">Database Results</h4>
            <SQLResults data={data.sql_results} />
          </div>
        )}
        
        {data.document_results && data.document_results.length > 0 && (
          <div>
            <h4 className="font-semibold mb-3 text-green-600">Document Results</h4>
            <DocumentResults data={data.document_results} />
          </div>
        )}
      </div>
    );
  };

  // Metrics dashboard
  const MetricsDashboard = () => {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Database</p>
              <p className="text-2xl font-bold text-blue-600">
                {metrics.database_connected ? 'Connected' : 'Disconnected'}
              </p>
            </div>
            <Database className={`${metrics.database_connected ? 'text-green-500' : 'text-red-500'}`} size={24} />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Documents</p>
              <p className="text-2xl font-bold text-green-600">{metrics.documents_indexed || 0}</p>
            </div>
            <FileText className="text-green-500" size={24} />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Cache Hit Rate</p>
              <p className="text-2xl font-bold text-purple-600">
                {metrics.cache_hit_rate ? `${(metrics.cache_hit_rate * 100).toFixed(1)}%` : '0%'}
              </p>
            </div>
            <BarChart3 className="text-purple-500" size={24} />
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active Jobs</p>
              <p className="text-2xl font-bold text-orange-600">{metrics.active_jobs || 0}</p>
            </div>
            <Loader className="text-orange-500" size={24} />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">NLP Query Engine</h1>
              <p className="text-sm text-gray-600">Dynamic employee data analysis with natural language</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className={`w-3 h-3 rounded-full ${dbConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm text-gray-600">
                {dbConnected ? 'Connected' : 'Not Connected'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Metrics Dashboard */}
        <MetricsDashboard />
        
        {/* Navigation Tabs */}
        <div className="flex space-x-1 bg-gray-200 rounded-lg p-1 mb-8">
          {[
            { id: 'connect', label: 'Connect Data', icon: Database },
            { id: 'query', label: 'Query Data', icon: Search },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-white text-blue-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                <Icon className="mr-2" size={16} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        {activeTab === 'connect' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <DatabaseConnector />
            <DocumentUploader />
          </div>
        )}
        
        {activeTab === 'query' && <QueryInterface />}
      </div>
    </div>
  );
};

export default NLPQueryEngine;
