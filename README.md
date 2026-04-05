# blinkRoutines

REST API deployed on AWS Lambda to automate Blink security cameras: arm/disarm networks, push thumbnails and videos via Telegram, detect and identify persons with Amazon Rekognition, and build a podcast queue on Spotify.

---

## Features

- **OAuth 2.0 PKCE authentication** against the Blink API (2FA support)
- **Arm / disarm** camera networks
- **Thumbnail & video retrieval** sent directly to Telegram channels
- **Save images** to S3 with timestamped keys
- **Person detection** via Amazon Rekognition Face Collections
- **Face registration** from live thumbnails or uploaded images
- **Spotify podcast queue** – builds and plays unfinished episodes from configured shows
- **Fully serverless** – runs on AWS Lambda behind API Gateway

---

## Architecture

```
Phone/MacroDroid/Shortcuts
        │
        ▼
 API Gateway (REST)
        │
        ▼
 AWS Lambda (FastAPI + Mangum)
   ├── Blink API  ──────────────── cameras / networks
   ├── Telegram Bot API ─────────── push photos & videos
   ├── Amazon Rekognition ──────── face detection & collections
   ├── Amazon S3 ───────────────── thumbnail storage
   ├── Amazon DynamoDB ─────────── config persistence (optional)
   └── Spotify Web API ─────────── podcast queue
```

---

## Quickstart

### 1. Clone and configure

```bash
git clone https://github.com/<you>/blinkRoutines.git
cd blinkRoutines

cp config/config.example.ini config/config.ini
# Edit config/config.ini with your credentials (see Configuration section)
```

### 2. Build the Lambda layer

```bash
chmod +x build.sh
./build.sh
```

`build.sh` installs Linux-compatible wheels (manylinux2014 x86_64) and packages them into `layer.zip` together with the application code.

### 3. Deploy

Upload `layer.zip` to AWS Lambda manually or via your preferred IaC tool (SAM, Serverless Framework, Terraform, etc.).

**Required Lambda settings:**

| Setting | Value |
|---------|-------|
| Runtime | Python 3.14 |
| Architecture | x86\_64 |
| Handler | `app.main.handler` |
| Timeout | ≥ 30 s |
| Environment variable | `CONFIG_PATH=/tmp/blink_config.ini` |

The `config/config.ini` file must be uploaded to S3 (or baked into the layer) and copied to `/tmp/blink_config.ini` on cold start, **or** stored in AWS SSM Parameter Store and loaded automatically by `config_aws.py`.

---

## Configuration

All settings live in a single JSON file (`config/config.ini`). Copy `config/config.example.ini` and fill in your values.

### Blink

| Key | Description |
|-----|-------------|
| `blink_user` | Blink account e-mail |
| `blink_password` | Blink account password |
| `blink_hardware_id` | Device UUID sent to the Blink API |
| `blink_client_id` | Populated automatically after first login |
| `blink_tier` | API tier (`prod`) |
| `blink_account_id` | Populated automatically after first login |
| `blink_token_auth` | OAuth access token (auto-renewed) |
| `blink_refresh_token` | OAuth refresh token (persisted after 2FA) |

### Cameras

```json
"cameras": {
  "CameraName": {"id": "<numeric_camera_id>", "type": "cam"},
  "OwlName":    {"id": "<numeric_owl_id>",    "type": "owl"}
}
```

`cam_name` path parameters in the API refer to the keys of this object (e.g. `"Entrada"`).

### Telegram

| Key | Description |
|-----|-------------|
| `telegram_api_token` | Bot token from [@BotFather](https://t.me/BotFather) |

Pass the Telegram channel/group ID as a path parameter (`channel_id`) in each request.

### AWS

| Key | Description |
|-----|-------------|
| `aws_access_key_id` | IAM access key |
| `aws_secret_access_key` | IAM secret key |
| `aws_region` | AWS region (e.g. `us-east-1`) |
| `aws_bucket` | S3 bucket for thumbnail storage |
| `aws_folder` | S3 key prefix (e.g. `cameras/`) |
| `aws_table` | DynamoDB table name (optional) |

Required IAM permissions: `s3:PutObject`, `rekognition:*` on the face collection, `dynamodb:PutItem` / `GetItem` (if using DynamoDB).

### Amazon Rekognition

The face collection name is hardcoded as `"familia"` in `person_detector_rekognition.py`. Change it there if needed. No extra config keys are required beyond the AWS credentials above.

### Spotify

| Key | Description |
|-----|-------------|
| `spotify_client_id` | Client ID from the Spotify Developer Dashboard |
| `spotify_client_secret` | Client Secret from the Spotify Developer Dashboard |
| `spotify_refresh_token` | Long-lived refresh token (see Spotify Setup) |
| `spotify_device_id` | Target playback device ID |
| `spotify_queue_playlist_id` | Playlist used as a staging queue |
| `spotify_podcasts` | Array of `{id, window_hours}` objects (see below) |

`spotify_podcasts` example:

```json
"spotify_podcasts": [
  {"id": "3lKgGQAMcXMCbJMDHkIhla", "window_hours": 24},
  {"id": "6ShyjQIAZm9mwrQl7znVhO", "window_hours": 168},
  {"id": "5CnDmMUG0S5bSSw612fs8C", "window_hours": null}
]
```

- `window_hours`: only episodes released within this many hours are included. `null` means no time filter.
- Episodes already fully played are skipped automatically.

---

## Authentication Flow

Blink uses OAuth 2.0 Authorization Code + PKCE with optional SMS 2FA.

### Step 1 – Initiate login

```bash
curl -X POST "https://<api-id>.execute-api.<region>.amazonaws.com/prod/api/v1/basic_config/?username=you@example.com&password=yourpassword"
```

- If 2FA is **not** required: returns `TOKEN_AUTH`, `TIER`, and `ACCOUNT_ID` directly.
- If 2FA is **required**: returns `{"2fa_required": true}`. A PIN is sent via SMS.

### Step 2 – Verify 2FA (if required)

```bash
curl -X POST "https://<api-id>.execute-api.<region>.amazonaws.com/prod/api/v1/mfa/?mfa_code=123456"
```

Returns the access token and persists it to config for future automatic renewal.

---

## API Endpoints

### Auth

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/basic_config/` | Login (step 1 PKCE) |
| `POST` | `/api/v1/mfa/` | Complete 2FA (step 2 PKCE) |

### Network

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/arm/{network_id}` | Arm a network |
| `GET` | `/api/v1/disarm/{network_id}` | Disarm a network |
| `GET` | `/api/v1/telegram/{channel_id}?message=…` | Send a Telegram message |

### Camera

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/get_image/{channel_id}/{cam_name}` | Send current thumbnail via Telegram |
| `GET` | `/api/v1/save_images/{cam_name}` | Save thumbnail to S3 |
| `GET` | `/api/v1/update_thumb/{camera_id}` | Force a new thumbnail on a camera |
| `GET` | `/api/v1/update_owl/{owl_id}` | Force a new thumbnail on an Owl device |
| `GET` | `/api/v1/get_local_video/{channel_id}/{cam_name}` | Send latest local video via Telegram |
| `GET` | `/api/v1/get_remote_video/{channel_id}/{cam_name}` | Send latest cloud video via Telegram |

### Detection

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/detect_person/{channel_id}/{cam_name}` | Detect & identify persons, notify Telegram |
| `POST` | `/api/v1/register_face/{person_name}/{cam_name}` | Register face from a freshly captured thumbnail |
| `POST` | `/api/v1/train_face/{person_name}/{cam_name}` | Register face from the existing thumbnail |
| `POST` | `/api/v1/upload_face/{person_name}` | Register face from uploaded image (`multipart/form-data`, field `image`) |
| `GET` | `/api/v1/list_faces` | List all registered faces |
| `DELETE` | `/api/v1/delete_face/{person_name}` | Delete all faces for a person |

### Music

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/play_music?play=true` | Build podcast queue and start playback |
| `POST` | `/api/v1/play_music?play=false` | Build podcast queue without starting playback |

---

## Spotify Setup

### 1. Create a Spotify app

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and create an app.
2. Add `http://localhost:8888/callback` as a Redirect URI.
3. Copy **Client ID** and **Client Secret** to `config.ini`.

### 2. Obtain a refresh token

```bash
CLIENT_ID="your-client-id"
REDIRECT_URI="http://localhost:8888/callback"
SCOPES="user-modify-playback-state user-read-playback-state user-read-playback-position playlist-modify-public playlist-modify-private"

# Open this URL in a browser and authorise the app
echo "https://accounts.spotify.com/authorize?client_id=${CLIENT_ID}&response_type=code&redirect_uri=${REDIRECT_URI}&scope=${SCOPES// /%20}"
```

Copy the `code` from the redirect URL and exchange it:

```bash
CODE="the-code-from-redirect"
CLIENT_SECRET="your-client-secret"

curl -s -X POST https://accounts.spotify.com/api/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code&code=${CODE}&redirect_uri=${REDIRECT_URI}&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}" \
  | python3 -m json.tool
```

Copy the `refresh_token` from the response into `config.ini`.

### 3. Get the device ID

```bash
ACCESS_TOKEN="the-access-token-from-above"

curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  https://api.spotify.com/v1/me/player/devices | python3 -m json.tool
```

Copy the `id` of the target device into `spotify_device_id` in `config.ini`.

### 4. Configure show IDs

Find the show ID in a Spotify show URL:
`https://open.spotify.com/show/**3lKgGQAMcXMCbJMDHkIhla**`

Add each show to the `spotify_podcasts` array with the desired `window_hours`.

---

## GPS Automation

Trigger API calls automatically when arriving at or leaving a location.

### Android – MacroDroid

1. **Trigger**: GPS / Enter location (home coordinates, radius ~100 m)
2. **Action**: HTTP Request → `GET https://<api-id>.execute-api.../prod/api/v1/disarm/<network_id>`
3. Mirror setup for leaving (Arm on exit).

### iOS – Shortcuts

1. Create a new Shortcut with trigger **Arrive** at Home.
2. Add action **Get Contents of URL**: method `GET`, URL `.../disarm/<network_id>`.
3. Duplicate for **Leave** using `.../arm/<network_id>`.

---

## Local Development

```bash
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Run tests

```bash
pytest tests/
```
