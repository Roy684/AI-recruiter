import { useState } from 'react';
import { UploadCloud, File, CheckCircle } from 'lucide-react';

export default function UploadResume() {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [candidateName, setCandidateName] = useState('');

  const handleProcess = async () => {
    if (files.length === 0) return;
    
    setLoading(true);
    const formData = new FormData();
    files.forEach(file => formData.append('resumes', file));
    if (candidateName) {
      formData.append('candidate_name', candidateName);
    }

    try {
      const res = await fetch('https://ai-recruiter-ne55.onrender.com/api/upload-resume', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        alert('Resumes uploaded successfully! You can view them in the dashboard.');
        setFiles([]);
      } else {
        alert('Upload failed: ' + data.message);
      }
    } catch (err) {
      console.error(err);
      alert('Failed to connect to the backend.');
    } finally {
      setLoading(false);
    }
  };

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
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFiles((prev) => [...prev, ...Array.from(e.dataTransfer.files)]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      setFiles((prev) => [...prev, ...Array.from(e.target.files)]);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 md:p-10">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-text-main mb-2">Upload Resumes</h1>
        <p className="text-text-muted">Drag and drop candidate resumes in PDF or Word format.</p>
      </div>

      <div 
        className={`relative w-full h-64 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center transition-all duration-200 ${
          dragActive ? 'border-primary bg-primary/5' : 'border-surface-hover bg-surface/30'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          type="file"
          multiple
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          onChange={handleChange}
          accept=".pdf,.doc,.docx"
        />
        <div className="flex flex-col items-center text-text-muted pointer-events-none">
          <UploadCloud className={`w-12 h-12 mb-4 transition-colors ${dragActive ? 'text-primary' : ''}`} />
          <p className="text-lg font-medium text-text-main">
            {dragActive ? 'Drop files here' : 'Click or drag files to upload'}
          </p>
          <p className="text-sm mt-1">Supports PDF, DOC, DOCX</p>
        </div>
      </div>

      <div className="mt-8 space-y-2 max-w-md mx-auto">
        <label htmlFor="candidateName" className="block text-sm font-medium text-text-main text-center">Candidate Name (Optional)</label>
        <input
          id="candidateName"
          type="text"
          placeholder="e.g. John Doe"
          value={candidateName}
          onChange={(e) => setCandidateName(e.target.value)}
          className="w-full bg-background border border-surface-hover rounded-xl px-4 py-3 text-text-main focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
        />
        <p className="text-xs text-text-muted text-center mt-1">If uploading a single resume, you can manually specify the name here to override AI extraction.</p>
      </div>

      {files.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-text-main mb-4">Uploaded Files</h2>
          <div className="space-y-3">
            {files.map((file, i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-surface rounded-xl border border-surface-hover">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/10 rounded-lg text-primary">
                    <File className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-text-main">{file.name}</p>
                    <p className="text-xs text-text-muted">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                <CheckCircle className="w-5 h-5 text-green-500" />
              </div>
            ))}
          </div>
          <div className="mt-6 flex justify-end">
            <button 
              onClick={handleProcess}
              disabled={loading}
              className="px-6 py-3 bg-primary hover:bg-primary-hover text-white rounded-xl font-semibold transition-colors shadow-lg shadow-primary/25 disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Process Resumes'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
