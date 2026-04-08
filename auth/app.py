from fastapi import FastAPI

app = FastAPI()

@app.get('/health')
async def health():
    return {'status': 'auth api is running...'}