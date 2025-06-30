import os
import base64
import requests
from dotenv import load_dotenv
from ai_usage_manager import AIUsageManager

# Load environment variables
load_dotenv()

# Initialize usage manager
usage_manager = AIUsageManager()

def analyze_fishing_spot_gemini(image_bytes):
    """
    Analyze a fishing spot image using Google AI Studio (Gemini Pro Vision)
    with smart usage management to stay within free tier limits
    """
    try:
        # Check if we can make a request
        can_request, reason = usage_manager.can_make_request()
        if not can_request:
            return f"⚠️ Usage limit reached: {reason}\n\nPlease try again later or use the OpenRouter fallback."
        
        # Get API key from environment
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            return "❌ Error: Google AI API key not found. Please set GOOGLE_AI_API_KEY in your .env file"
        
        # Convert image bytes to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create the optimized fishing-specific prompt (shorter to save tokens)
        fishing_prompt = """As an expert fishing guide, analyze this spot and provide:

🎯 **STRUCTURE**: Visible cover, vegetation, depth changes
🐟 **FISH TYPES**: Likely species based on habitat
🎣 **CASTING SPOTS**: Best target areas and why
🪝 **BAIT/LURES**: Top 3 recommendations
⚡ **TECHNIQUES**: Most effective methods
⏰ **TIMING**: Best times to fish here
📊 **SCORE**: Rate 1-10 for fishing potential

Keep response concise but actionable."""

        # Prepare the request with optimized settings
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": fishing_prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 800,  # Reduced to save quota
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
        
        # Make the API call
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                # Record successful request
                usage_manager.record_request()
                
                analysis = result['candidates'][0]['content']['parts'][0]['text']
                
                # Add usage stats to response
                stats = usage_manager.get_usage_stats()
                usage_info = f"\n\n📊 **API Usage Today**: {stats['daily']['used']}/{stats['daily']['limit']} ({stats['daily']['percentage']:.1f}%)"
                
                return analysis + usage_info
            else:
                return "❌ No analysis generated. The image might not be suitable for analysis. Please try with a clearer fishing spot photo."
        
        elif response.status_code == 429:
            return "⚠️ Rate limit exceeded. Please wait a moment and try again, or use the OpenRouter fallback."
        
        elif response.status_code == 400:
            error_detail = response.json() if response.content else "Bad request"
            return f"❌ Invalid request: {error_detail}. Please try with a different image."
        
        else:
            error_detail = response.json() if response.content else "Unknown error"
            return f"❌ API Error ({response.status_code}): {error_detail}"
        
    except requests.exceptions.Timeout:
        return "⏱️ Request timed out. Please try again with a smaller image."
    
    except requests.exceptions.ConnectionError:
        return "🌐 Connection error. Please check your internet connection and try again."
    
    except Exception as e:
        print(f"Error analyzing image with Gemini: {str(e)}")
        return f"❌ Sorry, I couldn't analyze this image right now. Error: {str(e)}"

def get_usage_stats():
    """Get current API usage statistics"""
    return usage_manager.get_usage_stats()

# Fallback function using Hugging Face (free alternative)
def analyze_fishing_spot_huggingface(image_bytes):
    """
    Fallback: Analyze a fishing spot image using Hugging Face Inference API
    """
    try:
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            return "❌ Error: Hugging Face API key not found. Please set HUGGINGFACE_API_KEY in your .env file"
        
        # Use BLIP model for image captioning
        API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.post(API_URL, headers=headers, data=image_bytes, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                caption = result[0].get('generated_text', '')
                
                # Enhance the basic caption with fishing-specific analysis
                enhanced_analysis = f"""🎣 **FISHING SPOT ANALYSIS** (Hugging Face Fallback)

📸 **Image Description**: {caption}

🎯 **Fishing Recommendations**:
Based on the visible features, here are some general suggestions:

• **Structure**: Look for areas with natural cover and depth changes
• **Casting**: Target visible structure, vegetation edges, or drop-offs  
• **Bait**: Match the hatch - use natural colors in clear water
• **Technique**: Start with versatile presentations like jigs or soft plastics
• **Timing**: Early morning and evening typically produce best results

📊 **Confidence Score**: 6/10 - Basic analysis (upgrade to Gemini for detailed insights)

💡 **Note**: This is a basic analysis. For detailed fishing recommendations, try again when Google AI quota resets."""
                
                return enhanced_analysis
            else:
                return "❌ Could not analyze the image. Please try again with a clearer photo."
        
        elif response.status_code == 503:
            return "⚠️ Hugging Face model is loading. Please wait 20 seconds and try again."
        
        else:
            return f"❌ Hugging Face API Error ({response.status_code}). Please try again later."
            
    except Exception as e:
        return f"❌ Fallback analysis error: {str(e)}"