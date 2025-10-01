import React, { useState } from 'react';
import { FileText, Clock, Download, Eye, AlertCircle } from 'lucide-react';

const ResultsView = ({ results }) => {
  const [showSQL, setShowSQL] = useState(false);

  if (!results) return null;

  const downloadResults = () => {
    const data = JSON.stringify(results, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query-results-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadCSV = (data) => {
    if (!Array.isArray(data) || data.length === 0) return;
    
    const headers = Object.keys(data[0]);
    const csv = [
      headers.join(','),
      ...data.map(row => headers.map(h => JSON.stringify(row[h] || '')).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query-results-${Date.now()}.csv`;
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
            JSON
          </button>
          {results.query_type === 'sql' && Array.isArray(results.results) && (
            <button
              onClick={() => downloadCSV(results.results)}
              className="flex items-center text-blue-600 hover:text-blue-700"
            >
              <Download className="mr-1" size={14} />
              CSV
            </button>
          )}
        </div>
      </div>
      
      <div className="mb-4 flex items-center gap-4 text-sm flex-wrap">
        <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
          {results.query_type}
        </span>
        <span className="text-gray-600">
          Sources: {results.sources?.join(', ')}
        </span>
        {results.sql_query && (
          <button 
            onClick={() => setShowSQL(!showSQL)}
            className="text-blue-600 hover:text-blue-700 flex items-center"
          >
            <Eye className="mr-1" size={14} />
            {showSQL ? 'Hide SQL' : 'View SQL'}
          </button>
        )}
      </div>

      {showSQL && results.sql_query && (
        <div className="mb-4 bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
          <pre className="text-sm"><code>{results.sql_query}</code></pre>
        </div>
      )}
      
      {results.query_type === 'sql' && <SQLResults data={results.results} />}
      {results.query_type === 'document' && <DocumentResults data={results.results} />}
      {results.query_type === 'hybrid' && <HybridResults data={results.results} />}
    </div>
  );
};

const SQLResults = ({ data }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 50;

  if (!Array.isArray(data) || data.length === 0) {
    return <p className="text-gray-500">No results found.</p>;
  }

  const columns = Object.keys(data[0]);
  const totalPages = Math.ceil(data.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentData = data.slice(startIndex, endIndex);
  
  return (
    <div>
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
            {currentData.map((row, idx) => (
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
      </div>
      
      {data.length > itemsPerPage && (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Showing {startIndex + 1} to {Math.min(endIndex, data.length)} of {data.length} results
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              Previous
            </button>
            <span className="px-3 py-1">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
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
        <div key={idx} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
          <div className="flex justify-between items-start mb-2">
            <div>
              <h4 className="font-semibold text-blue-600">{doc.filename}</h4>
              <p className="text-xs text-gray-500">
                Type: {doc.doc_type} • Similarity: {(doc.similarity_score * 100).toFixed(1)}%
              </p>
            </div>
            <div className="text-right">
              <div 
                className="text-xs font-medium px-2 py-1 rounded"
                style={{
                  backgroundColor: doc.similarity_score > 0.7 ? '#dcfce7' : 
                                  doc.similarity_score > 0.5 ? '#fef3c7' : '#fee2e2',
                  color: doc.similarity_score > 0.7 ? '#166534' : 
                         doc.similarity_score > 0.5 ? '#92400e' : '#991b1b'
                }}
              >
                {doc.similarity_score > 0.7 ? 'High Match' : 
                 doc.similarity_score > 0.5 ? 'Medium Match' : 'Low Match'}
              </div>
            </div>
          </div>
          
          <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
            <p>{doc.chunk_text.substring(0, 400)}{doc.chunk_text.length > 400 ? '...' : ''}</p>
          </div>
          
          {doc.chunk_type && (
            <p className="text-xs text-gray-400 mt-2">Chunk type: {doc.chunk_type}</p>
          )}
        </div>
      ))}
    </div>
  );
};

const HybridResults = ({ data }) => {
  const [activeTab, setActiveTab] = useState('sql');

  return (
    <div className="space-y-6">
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('sql')}
          className={`px-4 py-2 border-b-2 transition-colors ${
            activeTab === 'sql' 
              ? 'border-blue-600 text-blue-600 font-medium' 
              : 'border-transparent text-gray-600 hover:text-gray-800'
          }`}
        >
          Database Results {data.sql_results && `(${data.sql_results.length})`}
        </button>
        <button
          onClick={() => setActiveTab('documents')}
          className={`px-4 py-2 border-b-2 transition-colors ${
            activeTab === 'documents' 
              ? 'border-green-600 text-green-600 font-medium' 
              : 'border-transparent text-gray-600 hover:text-gray-800'
          }`}
        >
          Document Results {data.document_results && `(${data.document_results.length})`}
        </button>
      </div>

      {activeTab === 'sql' && data.sql_results && data.sql_results.length > 0 && (
        <div>
          <h4 className="font-semibold mb-3 text-blue-600 flex items-center">
            <span className="w-2 h-2 bg-blue-600 rounded-full mr-2"></span>
            Database Results
          </h4>
          <SQLResults data={data.sql_results} />
        </div>
      )}
      
      {activeTab === 'documents' && data.document_results && data.document_results.length > 0 && (
        <div>
          <h4 className="font-semibold mb-3 text-green-600 flex items-center">
            <span className="w-2 h-2 bg-green-600 rounded-full mr-2"></span>
            Document Results
          </h4>
          <DocumentResults data={data.document_results} />
        </div>
      )}

      {activeTab === 'sql' && (!data.sql_results || data.sql_results.length === 0) && (
        <p className="text-gray-500 text-center py-8">No database results found.</p>
      )}

      {activeTab === 'documents' && (!data.document_results || data.document_results.length === 0) && (
        <p className="text-gray-500 text-center py-8">No document results found.</p>
      )}
    </div>
  );
};

export default ResultsView;
