import React, { useState, useEffect } from 'react';
import { Database, Search, BarChart3 } from 'lucide-react';
import DatabaseConnector from './components/DatabaseConnector';
import DocumentUploader from './components/DocumentUploader';
import QueryPanel from './components/QueryPanel';
import ResultsView from './components/ResultsView';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

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
      setDbConnected(data.database_connected || false);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
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
