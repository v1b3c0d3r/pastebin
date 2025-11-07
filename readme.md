# Simple Pastebin Microservice

A minimal pastebin-like service with Python backend and simple web UI.

## Features

- Save text snippets (up to 5000 characters)
- Generate unique URLs for each paste
- Simple web interface
- SQLite database

## How to Run

1. Install Python dependencies:

```bash
    virtualenv venv
    source venv/bin/activate
    pip3 install -r requirements.txt
```
2. Run

```bash
    python3 app.py
```

3. Navigate to `http://localhost:5000` in your browser


The service will automatically create the SQLite database (`pastebin.db`) and necessary tables. Each paste gets a unique 8-character ID and can be accessed via `/pastes/<id>` URL.


