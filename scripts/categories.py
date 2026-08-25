"""领域分类映射规则：根据仓库 topics 和 language 打领域标签。

优先匹配 topics（命中即返回），未命中再按 language 兜底，都未命中返回"其他"。
领域与颜色的对应关系由前端 app.js 里一份同名的 COLORS 表维护（保持同步即可）。
"""

# topics（小写、连字符）→ 领域
TOPIC_TO_CATEGORY = {
    # AI/ML
    "ai": "AI/ML", "artificial-intelligence": "AI/ML", "machine-learning": "AI/ML",
    "deep-learning": "AI/ML", "llm": "AI/ML", "llms": "AI/ML", "gpt": "AI/ML",
    "chatgpt": "AI/ML", "openai": "AI/ML", "neural-network": "AI/ML", "nlp": "AI/ML",
    "natural-language-processing": "AI/ML", "pytorch": "AI/ML", "tensorflow": "AI/ML",
    "transformer": "AI/ML", "agent": "AI/ML", "agents": "AI/ML", "rag": "AI/ML",
    "langchain": "AI/ML", "diffusion": "AI/ML", "stable-diffusion": "AI/ML",
    "computer-vision": "AI/ML", "vision": "AI/ML", "generative-ai": "AI/ML",
    "ai-agent": "AI/ML", "ai-agents": "AI/ML", "agentic": "AI/ML",
    "agentic-ai": "AI/ML", "claude": "AI/ML", "claude-code": "AI/ML",
    "anthropic": "AI/ML", "deepseek": "AI/ML", "gemini": "AI/ML", "mcp": "AI/ML",
    "model-context-protocol": "AI/ML", "coding-agent": "AI/ML",
    "coding-assistant": "AI/ML", "llm-agent": "AI/ML", "ai-coding": "AI/ML",
    "agent-skill": "AI/ML", "vibe-coding": "AI/ML",
    # 前端
    "frontend": "前端", "react": "前端", "vue": "前端", "vuejs": "前端", "css": "前端",
    "ui": "前端", "web": "前端", "webdev": "前端", "web-development": "前端",
    "javascript": "前端", "typescript": "前端", "svelte": "前端", "tailwindcss": "前端",
    "nextjs": "前端", "nuxt": "前端", "html": "前端", "design-system": "前端",
    # 后端
    "backend": "后端", "api": "后端", "server": "后端", "database": "后端",
    "microservices": "后端", "rest": "后端", "restful": "后端", "graphql": "后端",
    "postgresql": "后端", "mysql": "后端", "sql": "后端", "fastapi": "后端",
    "django": "后端", "flask": "后端", "spring": "后端", "spring-boot": "后端",
    "nodejs": "后端", "redis": "后端", "mongodb": "后端",
    # DevOps
    "devops": "DevOps", "docker": "DevOps", "kubernetes": "DevOps", "k8s": "DevOps",
    "ci": "DevOps", "cd": "DevOps", "cicd": "DevOps", "infrastructure": "DevOps",
    "terraform": "DevOps", "observability": "DevOps", "monitoring": "DevOps",
    "cloud": "DevOps", "cloud-native": "DevOps", "aws": "DevOps", "linux": "DevOps",
    # 安全
    "security": "安全", "pentest": "安全", "pentesting": "安全", "crypto": "安全",
    "privacy": "安全", "cybersecurity": "安全", "hacking": "安全", "infosec": "安全",
    "vulnerability": "安全", "cryptography": "安全", "password": "安全",
    # 数据
    "data": "数据", "analytics": "数据", "visualization": "数据", "big-data": "数据",
    "data-science": "数据", "etl": "数据", "pandas": "数据", "data-analysis": "数据",
    "dashboard": "数据", "business-intelligence": "数据",
    # 移动端
    "android": "移动端", "ios": "移动端", "mobile": "移动端", "flutter": "移动端",
    "swift": "移动端", "react-native": "移动端", "kotlin": "移动端", "app": "移动端",
    # 桌面
    "desktop": "桌面", "electron": "桌面", "gui": "桌面", "qt": "桌面", "tauri": "桌面",
    # 游戏
    "game": "游戏", "gamedev": "游戏", "game-development": "游戏", "unity": "游戏",
    "godot": "游戏", "game-engine": "游戏",
    # 工具
    "cli": "工具", "tool": "工具", "utility": "工具", "automation": "工具",
    "terminal": "工具", "productivity": "工具", "command-line": "工具", "shell": "工具",
    "editor": "工具", "vscode": "工具", "vim": "工具",
}

# language → 领域（topics 未命中时的兜底）
LANGUAGE_TO_CATEGORY = {
    "Python": "AI/ML", "Jupyter Notebook": "AI/ML",
    "JavaScript": "前端", "TypeScript": "前端", "Vue": "前端", "CSS": "前端",
    "HTML": "前端", "Svelte": "前端", "SCSS": "前端", "Astro": "前端",
    "Go": "后端", "Java": "后端", "C#": "后端", "PHP": "后端", "Ruby": "后端",
    "Rust": "工具", "C": "工具", "C++": "工具", "Zig": "工具", "Elixir": "后端",
    "Kotlin": "移动端", "Swift": "移动端", "Dart": "移动端", "Objective-C": "移动端",
    "Shell": "DevOps", "Dockerfile": "DevOps", "HCL": "DevOps", "Makefile": "DevOps",
    "Lua": "游戏", "GLSL": "游戏",
}


def classify(topics, language):
    """根据 topics 列表和 language 返回领域标签。"""
    for t in topics or []:
        key = (t or "").strip().lower()
        if key in TOPIC_TO_CATEGORY:
            return TOPIC_TO_CATEGORY[key]
    if language in LANGUAGE_TO_CATEGORY:
        return LANGUAGE_TO_CATEGORY[language]
    return "其他"
