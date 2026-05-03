import { useState } from 'react';
import { Target, Save } from 'lucide-react';

export default function JobDescription() {
  const [jobTitle, setJobTitle] = useState('');
  const [description, setDescription] = useState('');
  const [skills, setSkills] = useState('');

  const [loading, setLoading] = useState(false);

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('https://ai-recruiter-ne55.onrender.com/api/job-description', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jobTitle, description, skills }),
      });
      const data = await res.json();
      if (data.success) {
        alert('Job description saved successfully!');
      } else {
        alert('Error: ' + data.message);
      }
    } catch (err) {
      console.error(err);
      alert('Failed to connect to the backend.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 md:p-10">
      <div className="mb-8 flex items-center gap-4">
        <div className="p-3 bg-secondary/10 rounded-xl text-secondary">
          <Target className="w-8 h-8" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-text-main">Job Description</h1>
          <p className="text-text-muted">Define the requirements to match against candidates.</p>
        </div>
      </div>

      <form onSubmit={handleSave} className="bg-surface border border-surface-hover rounded-2xl p-6 md:p-8 space-y-6 shadow-xl">
        <div className="space-y-2">
          <label htmlFor="title" className="block text-sm font-medium text-text-main">Job Title</label>
          <input
            id="title"
            type="text"
            placeholder="e.g. Senior Frontend Engineer"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            className="w-full bg-background border border-surface-hover rounded-xl px-4 py-3 text-text-main focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
            required
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="skills" className="block text-sm font-medium text-text-main">Required Skills (Comma separated)</label>
          <input
            id="skills"
            type="text"
            placeholder="e.g. React, Node.js, TypeScript"
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
            className="w-full bg-background border border-surface-hover rounded-xl px-4 py-3 text-text-main focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
            required
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="description" className="block text-sm font-medium text-text-main">Full Description</label>
          <textarea
            id="description"
            rows={6}
            placeholder="Paste the full job description here..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full bg-background border border-surface-hover rounded-xl px-4 py-3 text-text-main focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all resize-y"
            required
          />
        </div>

        <div className="pt-4 flex justify-end">
          <button 
            type="submit" 
            disabled={loading}
            className="flex items-center gap-2 px-6 py-3 bg-primary hover:bg-primary-hover text-white rounded-xl font-semibold transition-colors shadow-lg shadow-primary/25 disabled:opacity-50"
          >
            <Save className="w-5 h-5" />
            {loading ? 'Saving...' : 'Save Requirements'}
          </button>
        </div>
      </form>
    </div>
  );
}
