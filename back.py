from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
import redis
import re
import uuid
import time
import hashlib
from fastapi.exceptions import HTTPException
from jinja2 import Template
import ipaddress

app = FastAPI()
r = redis.Redis(host='192.168.1.104', port=6379, password='Superman5!', db=0, decode_responses=True)

SECRET_KEY = "SuperSecureSecretKey"
AUTHORIZED_IPS = ["192.168.1.0/24", "10.0.0.0/16"]

PLAYER_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Lecteur Vidéo</title>
    <script src="https://cdn.radiantmediatechs.com/rmp/9.6.0/js/rmp.min.js"></script>
    <style> 
        body { margin: 0; } 
        #rmp { width: 100%; height: 100vh; } 
        #waitingScreen {
            position: absolute; top: 0; left: 0; width: 100%; height: 100vh;
            background: url('{{ waiting_image }}') no-repeat center center; background-size: cover;
            display: flex; justify-content: center; align-items: center;
        }
    </style>
</head>
<body>
    <div id="waitingScreen"></div>
    <div id="rmp"></div>
    <script>
        var rmp = new RadiantMP("rmp");
        rmp.init({
            src: "{{ video_url }}",
            licenseKey: "{{ license_key }}",
            autoPlay: {{ "true" if autoplay else "false" }},
            muted: {{ "true" if muted else "false" }},
            controls: {{ "true" if controls else "false" }},
            waitForLive: {
                enabled: true,
                poster: "{{ poster_image }}",
                retryCount: 10,
                retryInterval: 5000
            }
        });
        rmp.on("live", function () {
            document.getElementById("waitingScreen").style.display = "none";
        });
    </script>
</body>
</html>
"""

def parse_ttl(ttl_str):
    if ttl_str == "unlimited":
        return None
    match = re.match(r"(\d+)([hd])", ttl_str)
    if match:
        value, unit = int(match.group(1)), match.group(2)
        return value * 3600 if unit == "h" else value * 86400
    raise HTTPException(status_code=400, detail="Invalid TTL format. Use 'Xh' for hours or 'Xd' for days.")

def is_authorized_ip(client_ip):
    ip = ipaddress.ip_address(client_ip)
    return any(ip in ipaddress.ip_network(net) for net in AUTHORIZED_IPS)

@app.middleware("http")
async def restrict_access(request: Request, call_next):
    client_ip = request.client.host
    protected_routes = ["/generate-player/", "/list-players/", "/delete-player/"]
    if any(request.url.path.startswith(route) for route in protected_routes) and not is_authorized_ip(client_ip):
        raise HTTPException(status_code=403, detail="Access denied from external network")
    return await call_next(request)

@app.post("/generate-player/")
async def generate_player(request: Request):
    data = await request.json()
    player_id = str(uuid.uuid4())
    ttl_seconds = parse_ttl(data.get("ttl", "1d"))
    player_data = {
        "video_url": data["video_url"],
        "allowed_domains": data.get("allowed_domains", []),
        "require_token": data.get("require_token", False)
    }
    if ttl_seconds:
        r.setex(f"player:{player_id}", ttl_seconds, str(player_data))
    else:
        r.set(f"player:{player_id}", str(player_data))
    signed_url = generate_signed_url(player_id, expiration=300)
    return {"iframe_url": signed_url, "player_id": player_id}

def generate_signed_url(player_id, expiration=300):
    timestamp = int(time.time()) + expiration
    signature = hashlib.sha256(f"{player_id}{timestamp}{SECRET_KEY}".encode()).hexdigest()
    return f"https://player.mondomaine.com/embed/{player_id}?expires={timestamp}&signature={signature}"

@app.get("/embed/{player_id}")
async def embed_player(player_id: str, request: Request):
    player_config = r.get(f"player:{player_id}")
    if not player_config:
        raise HTTPException(status_code=404, detail="Player expired or not found")
    player_config = eval(player_config)
    allowed_domains = player_config.get("allowed_domains", [])
    referer = request.headers.get("referer", "")
    if allowed_domains and not any(domain in referer for domain in allowed_domains):
        raise HTTPException(status_code=403, detail="This player cannot be embedded on this domain")
    return JSONResponse({"player_config": player_config})

@app.get("/list-players/")
async def list_players():
    keys = r.keys("player:*")
    players = [key.split(":")[1] for key in keys]
    return JSONResponse({"active_players": players})

@app.delete("/delete-player/{player_id}")
async def delete_player(player_id: str):
    deleted = r.delete(f"player:{player_id}")
    if deleted:
        return JSONResponse({"message": "Player deleted successfully"})
    raise HTTPException(status_code=404, detail="Player not found")
