from fastapi import FastAPI
app = FastAPI()

@app.get("/welcome")
def welcom():
    return{
        "message":"Hello World"
    }