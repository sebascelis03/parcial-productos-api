from fastapi.responses import HTMLResponse

def get_index():
    with open("app/views/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())