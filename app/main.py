from fastapi import FastAPI

app = FastAPI(title="Inventory System")


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Inventory System is running."}
