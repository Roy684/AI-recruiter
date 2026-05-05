
# ── Core programming languages ────────────────────────────────────────────────
LANGUAGES = {
    "python", "javascript", "typescript", "java", "c", "c++", "c#", "go",
    "rust", "ruby", "swift", "kotlin", "scala", "r", "matlab", "php",
    "bash", "shell", "sql", "html", "css",
}

# ── Web / UI frameworks ────────────────────────────────────────────────────────
WEB_FRAMEWORKS = {
    "react", "react.js", "reactjs", "next.js", "nextjs",
    "vue", "vue.js", "vuejs", "nuxt", "angular",
    "svelte", "gatsby", "remix",
    "tailwindcss", "tailwind", "bootstrap", "sass", "scss",
    "flask", "django", "fastapi", "express", "node.js", "nodejs",
    "graphql", "rest", "restful",
}

# ── Cloud / DevOps ─────────────────────────────────────────────────────────────
CLOUD_DEVOPS = {
    "aws", "gcp", "azure", "firebase", "firestore",
    "docker", "kubernetes", "k8s", "terraform", "ansible",
    "ci/cd", "github actions", "jenkins", "circleci", "helm",
    "nginx", "linux",
}

# ── Data / ML / AI ─────────────────────────────────────────────────────────────
DATA_AI = {
    "machine learning", "deep learning", "nlp", "natural language processing",
    "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
    "pandas", "numpy", "matplotlib", "seaborn", "huggingface",
    "langchain", "openai", "gemini", "llm", "rag",
    "spark", "hadoop", "airflow", "dbt",
}

# ── Databases ──────────────────────────────────────────────────────────────────
DATABASES = {
    "postgresql", "postgres", "mysql", "sqlite", "mongodb", "mongo",
    "redis", "elasticsearch", "cassandra", "dynamodb", "bigquery",
}

# ── General software tools ─────────────────────────────────────────────────────
TOOLS = {
    "git", "github", "gitlab", "bitbucket",
    "jira", "confluence", "notion", "figma", "postman",
    "vscode", "intellij", "vim",
}

# ── Soft skills (lower weight in scoring) ─────────────────────────────────────
SOFT_SKILLS = {
    "communication", "teamwork", "leadership", "problem solving",
    "critical thinking", "agile", "scrum", "kanban", "mentoring",
}

# ── LLM / GenAI ecosystem ──────────────────────────────────────────────────────
LLM_GENAI = {
    "llm", "llms", "large language model",
    "langchain", "llamaindex", "langgraph",
    "rag", "retrieval augmented generation",
    "faiss", "chromadb", "pinecone", "weaviate", "qdrant",
    "prompt engineering", "prompting",
    "agentic ai", "ai agents", "autonomous agents",
    "openai", "gemini", "claude", "mistral", "ollama",
    "huggingface", "transformers",
    "lcel", "vector search", "semantic search",
    "embedding", "embeddings",
    "fine tuning", "fine-tuning", "rlhf",
    "n8n", "langsmith",
}

SKILL_ALIASES: dict[str, str] = {
    "react.js": "react",   "reactjs": "react",
    "node.js": "nodejs",   "nodejs": "node.js",
    "postgres": "postgresql",
    "ml": "machine learning",
    "dl": "deep learning",
    "k8s": "kubernetes",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "cv": "computer vision",
}
# ── Flat set for quick membership tests ───────────────────────────────────────
ALL_SKILLS: set[str] = (
    LANGUAGES | WEB_FRAMEWORKS | CLOUD_DEVOPS | DATA_AI | DATABASES
    | TOOLS | SOFT_SKILLS | LLM_GENAI 
)

# ── Weights per category (used by scorer.py) ──────────────────────────────────
CATEGORY_WEIGHTS: dict[str, float] = {
    "language":   1.5,
    "web":        1.3,
    "cloud":      1.2,
    "data_ai":    1.4,
    "database":   1.1,
    "tool":       1.0,
    "soft_skill": 0.6,
    "llm_genai": 1.8,  # highest weight — GenAI is the focus
}

# Lookup: skill_name → category key (built once at import time)
SKILL_CATEGORY: dict[str, str] = {
    **{s: "language"   for s in LANGUAGES},
    **{s: "web"        for s in WEB_FRAMEWORKS},
    **{s: "cloud"      for s in CLOUD_DEVOPS},
    **{s: "data_ai"    for s in DATA_AI},
    **{s: "database"   for s in DATABASES},
    **{s: "tool"       for s in TOOLS},
    **{s: "soft_skill" for s in SOFT_SKILLS},
    **{s: "llm_genai" for s in LLM_GENAI},
}

