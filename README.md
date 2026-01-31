# FastAPI Blog

A lightweight blog application built with FastAPI, demonstrating server-side rendering with Jinja2 templates.

## Technologies

- **FastAPI** - Modern Python web framework
- **Jinja2** - Template engine for HTML rendering
- **Python 3.12+** - Programming language
- **uv** - Fast Python package installer and resolver

## Features

- Blog post listing with metadata (author, date)
- Individual post detail pages
- Error handling with custom 404 pages
- Static file serving for CSS assets
- Responsive layout with clean styling

## Project Structure

```
fastapi_blog/
├── main.py              # Application entry point and routes
├── templates/           # Jinja2 HTML templates
│   ├── base.html       # Base template with shared layout
│   ├── home.html       # Posts listing page
│   ├── post_detail.html # Individual post page
│   └── error.html      # Error page template
├── static/             # Static assets
│   └── css/
│       └── styles.css  # Application styling
└── pyproject.toml      # Project dependencies
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/iamurtazo/FastAPI_Blog.git
cd FastAPI_Blog
```

2. Install dependencies:
```bash
uv sync
```

3. Activate virtual environment:
```bash
source .venv/bin/activate
```

## Running the Application

```bash
fastapi dev main.py
```

The application will be available at `http://127.0.0.1:8000`

## API Endpoints

- `GET /` - Home page with all blog posts
- `GET /posts` - Alternative route for posts listing
- `GET /posts/{post_id}` - Individual post detail page

## Development

The project uses FastAPI's development server with auto-reload enabled. Any changes to Python files will automatically restart the server.
