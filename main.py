from fastapi import FastAPI
app = FastAPI()
@app.get("/")
def hello_world():
    return {" Hello" : "World"}
def hello_wo():
    return {"name" : "shanto"}