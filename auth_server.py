from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
import redis
import time

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "super-secure-auth-key"
r = redis.Redis(host="ADRESSE_IP", port="PORT", db=1, decode_responses=True)

def create_token(user_id: str, expires_in: int = 3600):
    expiration = int(time.time()) + expires_in
    payload = {"sub": user_id, "exp": expiration}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

@app.post("/token")
async def generate_token(user_id: str):
    token = create_token(user_id)
    r.setex(f"token:{token}", 3600, user_id)
    return {"access_token": token, "token_type": "bearer"}

@app.get("/verify")
async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not r.exists(f"token:{token}"):
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id, "status": "Valid token"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
