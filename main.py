from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import os
from ai_image import analyze_fishing_spot
from ai_image_gemini import analyze_fishing_spot_gemini, analyze_fishing_spot_huggingface, get_usage_stats
from catch_logger import CatchLogger
from forecast import get_fishing_forecast

app = FastAPI(title="Fishing Assistant API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize catch logger
catch_logger = CatchLogger()

class CatchEntry(BaseModel):
    species: str
    bait: str
    location: str
    date: str
    time: str
    notes: Optional[str] = ""

class ForecastRequest(BaseModel):
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

@app.get("/", response_class=HTMLResponse)
def read_root():
    # Get current usage stats
    try:
        stats = get_usage_stats()
        usage_display = f"Daily: {stats['daily']['used']}/{stats['daily']['limit']} ({stats['daily']['percentage']:.1f}%)"
    except:
        usage_display = "Usage tracking unavailable"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Fishing Assistant API</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #1a1a1a;
                color: #ffffff;
            }}
            .endpoint {{ 
                border: 1px solid #333; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 8px;
                background-color: #2a2a2a;
            }}
            .method {{ 
                background-color: #ff6b35; 
                color: white; 
                padding: 4px 8px; 
                border-radius: 4px; 
                font-size: 12px;
                font-weight: bold;
            }}
            .usage {{
                background-color: #2a4a2a;
                border: 1px solid #4a6a4a;
                padding: 10px;
                border-radius: 8px;
                margin: 15px 0;
            }}
            h1 {{ color: #ff6b35; }}
            h2 {{ color: #ffffff; }}
        </style>
    </head>
    <body>
        <h1>🎣 FishCast API</h1>
        <p>AI-powered fishing assistant backend with optimized Google AI Studio integration</p>
        
        <div class="usage">
            <strong>📊 Google AI Studio Usage:</strong> {usage_display}
        </div>
        
        <h2>Available Endpoints:</h2>
        
        <div class="endpoint">
            <span class="method">POST</span>
            <strong>/analyze-smart</strong>
            <p>🎯 Smart AI analysis - Uses Google Gemini (best quality) with automatic fallback</p>
            <small>Accepts: multipart/form-data with image file</small>
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span>
            <strong>/analyze-gemini</strong>
            <p>🧠 Google Gemini AI analysis (premium quality, limited quota)</p>
            <small>Accepts: multipart/form-data with image file</small>
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span>
            <strong>/analyze-hf</strong>
            <p>🔄 Hugging Face fallback analysis (unlimited, basic quality)</p>
            <small>Accepts: multipart/form-data with image file</small>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <strong>/usage-stats</strong>
            <p>📊 Get current API usage statistics</p>
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span>
            <strong>/catches</strong>
            <p>Log a new fishing catch</p>
            <small>Accepts: JSON with catch details</small>
        </div>
        
        <div class="endpoint">
            <span class="method">GET</span>
            <strong>/catches</strong>
            <p>Get all logged catches</p>
        </div>
        
        <div class="endpoint">
            <span class="method">POST</span>
            <strong>/forecast</strong>
            <p>Get fishing forecast for a location</p>
            <small>Accepts: JSON with location details</small>
        </div>
        
        <p><strong>Status:</strong> ✅ Smart AI routing with usage optimization</p>
    </body>
    </html>
    """

@app.post("/analyze-smart")
async def analyze_image_smart(file: UploadFile = File(...)):
    """
    Smart AI analysis - tries Google Gemini first, falls back to Hugging Face if quota exceeded
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image bytes
        image_bytes = await file.read()
        
        # Validate file size (max 10MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Try Google Gemini first
        analysis = analyze_fishing_spot_gemini(image_bytes)
        
        # If quota exceeded, automatically fall back to Hugging Face
        if "Usage limit reached" in analysis or "Rate limit" in analysis:
            analysis = analyze_fishing_spot_huggingface(image_bytes)
            provider = "Hugging Face (Fallback)"
        else:
            provider = "Google Gemini"
        
        return JSONResponse(content={
            "success": True,
            "recommendation": analysis,
            "filename": file.filename,
            "provider": provider
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in smart analyze endpoint: {str(e)}")
        return JSONResponse(
            status_code=500, 
            content={
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }
        )

@app.post("/analyze-gemini")
async def analyze_image_gemini_direct(file: UploadFile = File(...)):
    """
    Direct Google Gemini AI analysis (respects usage limits)
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image bytes
        image_bytes = await file.read()
        
        # Validate file size (max 10MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Analyze the image
        analysis = analyze_fishing_spot_gemini(image_bytes)
        
        return JSONResponse(content={
            "success": True,
            "recommendation": analysis,
            "filename": file.filename,
            "provider": "Google Gemini"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in analyze-gemini endpoint: {str(e)}")
        return JSONResponse(
            status_code=500, 
            content={
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }
        )

@app.post("/analyze-hf")
async def analyze_image_huggingface_direct(file: UploadFile = File(...)):
    """
    Direct Hugging Face AI analysis (unlimited fallback)
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image bytes
        image_bytes = await file.read()
        
        # Validate file size (max 10MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Analyze the image
        analysis = analyze_fishing_spot_huggingface(image_bytes)
        
        return JSONResponse(content={
            "success": True,
            "recommendation": analysis,
            "filename": file.filename,
            "provider": "Hugging Face"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in analyze-hf endpoint: {str(e)}")
        return JSONResponse(
            status_code=500, 
            content={
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }
        )

@app.get("/usage-stats")
async def get_ai_usage_stats():
    """Get current AI API usage statistics"""
    try:
        stats = get_usage_stats()
        return JSONResponse(content={
            "success": True,
            "usage": stats
        })
    except Exception as e:
        return JSONResponse(content={
            "success": False,
            "error": str(e)
        })

@app.post("/catches")
async def log_catch(catch_entry: CatchEntry):
    try:
        result = catch_logger.add_catch(catch_entry.dict())
        return {"message": f"Catch logged successfully! Total catches: {len(catch_logger.get_all_catches())}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/catches")
async def get_catches():
    try:
        catches = catch_logger.get_all_catches()
        return catches
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/forecast")
async def fishing_forecast(request: ForecastRequest):
    try:
        forecast = get_fishing_forecast(request.location, request.latitude, request.longitude)
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "FishCast API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)