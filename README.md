# AI Recruiter (Resume Screener)

An AI-powered web application designed to automate and streamline the resume screening process. By analyzing PDF resumes against targeted job descriptions using advanced Natural Language Processing (NLP), AI Recruiter provides HR professionals and recruiters with an intelligent, ranked list of candidates, saving time and improving hiring decisions.

## Web App Functionality

The application features a modern, responsive React frontend integrated with a robust Python/Flask backend and Firebase Firestore for data storage.

* **Job Description Management**: Recruiters can define active job roles, detailing specific requirements and essential skills.
* **Resume Upload & Parsing**: Users can upload PDF resumes. The system automatically extracts raw text, contact information (name, email, phone number), and intelligently categorizes the text into sections like experience, education, and skills.
* **AI-Powered Candidate Scoring**: Each resume undergoes a comprehensive evaluation against the active job description, generating an overall match score.
* **Candidate Dashboard**: A centralized dashboard allows recruiters to view all processed candidates. Candidates are ranked by their match scores, and recruiters can drill down into individual profiles to see a detailed breakdown of the score and the candidate's extracted information.

## Natural Language Processing (NLP) Methods

The core of the AI Recruiter is its scoring engine (`backend/nlp/scorer.py`), which evaluates candidate fitness using a multi-faceted NLP approach. It blends traditional keyword matching with deep semantic analysis to provide a balanced and accurate score.

### 1. Semantic Search with Sentence-BERT (SBERT) - *Weight: 60%*
* **Technology:** `sentence-transformers` (`all-MiniLM-L6-v2` model)
* **How it works:** Instead of just looking for exact words, SBERT understands the *meaning* and context of the text. It generates dense semantic embeddings for the job description and chunks of the resume. The system prioritizes key sections (projects, experience, skills, summary) and calculates the cosine similarity between the embeddings. This ensures that a candidate who describes relevant experience using different terminology than the job description still receives a high score.

### 2. Categorical Skill Matching - *Weight: 20%*
* **How it works:** The system extracts skills from the resume using a comprehensive, predefined master list of tech skills and their aliases (e.g., recognizing "React.js" and "React" as the same skill). It then computes a weighted score by matching these extracted skills against the required skills defined in the job description. Different skill categories (e.g., core languages vs. auxiliary tools) carry different weights to reflect their relative importance.

### 3. TF-IDF with Cosine Similarity - *Weight: 20%*
* **Technology:** `scikit-learn` (`TfidfVectorizer`)
* **How it works:** This method calculates the Term Frequency-Inverse Document Frequency (TF-IDF) to identify important keywords shared between the resume and the job description. It computes the cosine similarity between the two resulting vectors, rewarding exact keyword overlaps and structural alignment.

### Text Extraction & Named Entity Recognition (NER)
* **PDF Parsing:** `pdfplumber` is used to accurately extract raw text from PDF files.
* **NER:** `spaCy` (using the `en_core_web_sm` model) is utilized to identify the candidate's name (PERSON entity) from the unstructured text.
* **Heuristics & Regex:** Regular expressions are heavily used to identify section headers (Experience, Education, etc.) and to accurately extract email addresses and phone numbers.

## Tech Stack

* **Frontend:** React, Vite, Tailwind CSS, React Router, Lucide React (Icons)
* **Backend:** Python, Flask, Firebase Admin SDK
* **NLP & ML:** `spaCy`, `scikit-learn`, `sentence-transformers`, `pdfplumber`
* **Database:** Firebase Firestore
