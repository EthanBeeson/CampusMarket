from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import os

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Welcome to the Campus Market API!!"}

@app.get("/listings")
def get_listings():
#Placeholder for actual DB call
    return [{"id": 1, "title": "Sample Listing", "price": 100}]


# Upload endpoint for images/files
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    upload_dir = "upload"
    os.makedirs(upload_dir, exist_ok=True)
    file_location = os.path.join(upload_dir, file.filename)
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"filename": file.filename, "url": f"/{upload_dir}/{file.filename}"}

@app.exception_handler(StarletteHTTPException)
async def custom_404_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
      return RedirectResponse(url="/")
    return JSONResponse(status_code=exc.status_code,
content={"detail": exc.detail})
