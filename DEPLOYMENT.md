# AquaFlow Backend Deployment Guide (Render)

## Step-by-Step Render Deployment

### 1. Configure Render Settings

Use these exact settings in the Render form:

**Basic Settings:**
- **Name**: `aquaflow-backend`
- **Source Code**: `IRASUBIZA-SALY-NELSON/Aquaflow`
- **Branch**: `main`
- **Language**: Python 3
- **Region**: Oregon (US West)
- **Root Directory**: Leave empty
- **Build Command**: `pip install -r requirements-backend.txt`
- **Start Command**: `python -m backend.app`

**Instance Type:**
- Select: **Free** ($0/month, 512 MB RAM, 0.1 CPU)

### 2. Environment Variables

Click "Add Environment Variable" and add these **4 variables**:

| Key | Value |
|-----|-------|
| `AQUAFLOW_MODE` | `wifi` |
| `AQUAFLOW_PORT` | `10000` |
| `AQUAFLOW_HOST` | `0.0.0.0` |
| `AQUAFLOW_SIMULATE` | `1` |

### 3. Deploy

1. Click **"Deploy Web Service"** button
2. Wait 3-5 minutes for build and deployment
3. Once deployed, you'll get a URL like: `https://aquaflow-backend.onrender.com`

### 4. Test Your Deployment

Open your browser and visit:
```
https://aquaflow-backend.onrender.com
```

You should see the AquaFlow dashboard with live simulation data!

### 5. API Endpoints

Your backend will have these endpoints:

- `GET /` - Dashboard UI
- `GET /api/data` - Current sensor data (JSON)
- `GET /api/history` - Historical data (JSON)
- `POST /api/ingest` - ESP32 data upload endpoint
- `POST /api/command` - Manual control commands

### Test API:
```bash
curl https://aquaflow-backend.onrender.com/api/data
```

## Important Notes

### Free Tier Limitations:
- ⚠️ **Spins down after 15 minutes of inactivity**
- First request after spin-down takes ~30 seconds
- No persistent disk storage
- Automatic sleep/wake cycle

### For Production Use:
Upgrade to **Starter** ($7/month) for:
- ✓ Always-on (no spin-down)
- ✓ Faster performance
- ✓ Better reliability
- ✓ SSL certificate included

## Troubleshooting

### Build Failed?
- Check that `requirements-backend.txt` exists in repo
- Verify Python version compatibility

### App Crashed?
- Check logs in Render dashboard
- Verify environment variables are set correctly
- Ensure PORT matches AQUAFLOW_PORT (10000)

### Dashboard Not Loading?
- Wait 30 seconds if app was sleeping
- Check browser console for JavaScript errors
- Verify `/api/data` endpoint returns JSON

## Connecting Real ESP32

Once deployed, update your ESP32 firmware:

```cpp
const char* SERVER_HOST = "aquaflow-backend.onrender.com";
const uint16_t SERVER_PORT = 443;  // Use HTTPS
```

Modify the POST request to use HTTPS instead of HTTP.

## Alternative: Deploy with AI Model

If you want to deploy WITH the AI/LSTM model:

1. Change build command to: `pip install -r requirements.txt`
2. Add environment variable: `TF_CPP_MIN_LOG_LEVEL=2`
3. Use **Starter** instance minimum (free tier too slow for TensorFlow)
4. Build will take ~10 minutes

---

**Your deployment URL will be**: `https://aquaflow-backend.onrender.com`

Replace this with your actual URL once deployed!
