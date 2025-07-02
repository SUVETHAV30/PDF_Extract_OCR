from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
import os
from pathlib import Path
import mimetypes

app = FastAPI()

# Get the current directory where your files are located
CURRENT_DIR = Path(".")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML file"""
    html_files = list(CURRENT_DIR.glob("*.html"))
    
    if not html_files:
        raise HTTPException(status_code=404, detail="No HTML file found")
    
    # If there are multiple HTML files, serve the first one
    # You can modify this logic to serve a specific HTML file
    html_file = html_files[0]
    
    try:
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading HTML file: {str(e)}")

@app.get("/{filename}")
async def serve_static_files(filename: str):
    """Serve static files (JS, CSS, images, etc.) from the current directory"""
    file_path = CURRENT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Not a file")
    
    # Get the file extension to determine content type
    file_extension = file_path.suffix.lower()
    
    # Read file content based on type
    try:
        if file_extension in ['.js', '.css', '.html', '.txt', '.json', '.xml', '.svg']:
            # Text-based files
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Set appropriate content type
            content_type_map = {
                '.js': 'application/javascript',
                '.css': 'text/css',
                '.html': 'text/html',
                '.txt': 'text/plain',
                '.json': 'application/json',
                '.xml': 'application/xml',
                '.svg': 'image/svg+xml'
            }
            content_type = content_type_map.get(file_extension, 'text/plain')
            
            return Response(content=content, media_type=content_type)
            
        else:
            # Binary files (images, etc.)
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Get MIME type for binary files
            content_type, _ = mimetypes.guess_type(str(file_path))
            if not content_type:
                content_type = 'application/octet-stream'
            
            return Response(content=content, media_type=content_type)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    # List available files for debugging
    print("Available files in current directory:")
    for file in CURRENT_DIR.iterdir():
        if file.is_file():
            print(f"  - {file.name}")
    
    uvicorn.run(app, host="0.0.0.0", port=5000)