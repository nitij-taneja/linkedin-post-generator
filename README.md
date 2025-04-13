# LinkedIn Post Generator

An automated system that generates professional LinkedIn post drafts based on newsletter emails and trending AI/data science research.

## Features

- Fetches content from specified newsletter emails
- Retrieves trending AI/data science research from free APIs (arXiv, HuggingFace, PapersWithCode)
- Uses Groq API to generate professional LinkedIn posts
- Delivers drafts via Telegram for easy mobile access
- Runs on a daily schedule using GitHub Actions
- Focuses on AI, data science, generative AI, and RAG topics

## System Architecture

1. **Content Collection**
   - Email fetching module
   - Research API integration (arXiv, HuggingFace, PapersWithCode)

2. **Post Generation**
   - Groq API integration
   - Template-based generation

3. **Delivery**
   - Telegram bot integration

4. **Scheduling**
   - GitHub Actions workflow

## Setup and Usage

See the [Installation Guide](INSTALLATION.md) for detailed setup instructions.

## License

MIT
