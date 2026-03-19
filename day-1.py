from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def get_root():
    return {'hello':'world'}

@app.get('/items/{items_id}')
def add_items(items_id:int):
    return {"items_id": items_id}
