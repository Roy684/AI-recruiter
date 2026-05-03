import { Link } from 'react-router-dom';
import { ArrowRight, BrainCircuit, Users, Zap } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center p-6 lg:p-12 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-secondary/20 blur-[120px] pointer-events-none" />

      <div className="max-w-4xl w-full text-center z-10 space-y-8">
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">
          Hire Smarter with AI
        </h1>
        <p className="text-xl md:text-2xl text-text-muted max-w-2xl mx-auto leading-relaxed">
          Automate your screening process, rank candidates instantly, and find the perfect match for your job descriptions in seconds.
        </p>
        
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-6">
          <Link
            to="/upload"
            className="flex items-center gap-2 px-8 py-4 bg-primary hover:bg-primary-hover text-white rounded-xl font-semibold transition-all shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:-translate-y-1"
          >
            Get Started
            <ArrowRight className="h-5 w-5" />
          </Link>
          <Link
            to="/job-description"
            className="flex items-center gap-2 px-8 py-4 bg-surface hover:bg-surface-hover text-text-main rounded-xl font-semibold transition-all border border-surface-hover hover:border-text-muted"
          >
            View Demo
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-16">
          <FeatureCard 
            icon={BrainCircuit} 
            title="AI-Powered" 
            desc="Advanced NLP models analyze resumes against your specific requirements." 
          />
          <FeatureCard 
            icon={Zap} 
            title="Lightning Fast" 
            desc="Screen hundreds of resumes in the time it takes to read just one." 
          />
          <FeatureCard 
            icon={Users} 
            title="Unbiased Ranking" 
            desc="Focus purely on skills and experience, eliminating human bias." 
          />
        </div>
      </div>
    </div>
  );
}

function FeatureCard({ icon: Icon, title, desc }) {
  return (
    <div className="bg-surface/50 border border-surface-hover p-6 rounded-2xl hover:bg-surface transition-colors">
      <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4 mx-auto text-primary">
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="text-lg font-bold text-text-main mb-2">{title}</h3>
      <p className="text-text-muted text-sm">{desc}</p>
    </div>
  );
}
