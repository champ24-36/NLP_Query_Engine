import React, { useState } from 'react';
import { Upload, Loader, CheckCircle, AlertCircle } from 'lucide-react';

const DocumentUploader = ({ API_BASE_URL, onUploadComplete }) => {
  const [dragActive, setDragActive] = useState(false);
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
            failed_files: 0,
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
          if (onUploadComplete) {
            onUploadComplete(data);
          }
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

      {job.files && job.files.length > 0 && (
        <div className="mt-2 text-xs text-gray-500">
          <details>
            <summary className="cursor-pointer hover:text-gray-700">
              View files ({job.files.length})
            </summary>
            <ul className="mt-1 ml-4 list-disc">
              {job.files.map((filename, idx) => (
                <li key={idx}>{filename}</li>
              ))}
            </ul>
          </details>
        </div>
      )}
    </div>
  );
};

export default DocumentUploader;
