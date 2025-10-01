import React, { useState } from 'react';
import { Database, Loader, CheckCircle, AlertCircle } from 'lucide-react';

const DatabaseConnector = ({ onConnectionSuccess, API_BASE_URL }) => {
  const [connectionString, setConnectionString] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('');
  const [schema, setSchema] = useState(null);

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
        setSchema(data.schema);
        setConnectionStatus(`✅ Connected! Found ${data.tables_count} tables, ${data.relationships_count} relationships`);
        if (onConnectionSuccess) {
          onConnectionSuccess(data);
        }
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

export default DatabaseConnector;
