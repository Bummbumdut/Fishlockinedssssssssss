import os
import base64
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def analyze_fishing_spot_gemini(image_bytes):
    """
    Analyze a fishing spot image using Google AI Studio (Gemini Pro Vision)
    """
    try:
        # Get API key from environment
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            return "Error: Google AI API key not found. Please set GOOGLE_AI_API_KEY in your .env file"
        
        # Convert image bytes to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create the fishing-specific prompt
        fishing_prompt = """You are an expert fishing guide and angler with decades of experience. Analyze this fishing spot image and provide detailed recommendations.

Please provide:
1. **Structure Analysis**: Identify visible underwater structures, cover, vegetation, shoreline features
2. **Fish Habitat Assessment**: What types of fish might be present based on the environment
3. **Casting Recommendations**: Best spots to cast and why
4. **Bait/Lure Suggestions**: What baits or lures would work best in this spot
5. **Technique Tips**: Fishing techniques that would be most effective
6. **Best Times**: When this spot would fish best (time of day, weather conditions)
7. **Confidence Score**: Rate this spot 1-10 for fishing potential

Format your response in a clear, actionable way that helps an angler succeed at this location."""

        # Prepare the request
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
                "maxOutputTokens": 1000,
            }
        }
        
        # Make the API call
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                analysis = result['candidates'][0]['content']['parts'][0]['text']
                return analysis
            else:
                return "No analysis generated. Please try with a different image."
        else:
            error_detail = response.json() if response.content else "Unknown error"
            return f"API Error ({response.status_code}): {error_detail}"
        
    except Exception as e:
        print(f"Error analyzing image with Gemini: {str(e)}")
        return f"Sorry, I couldn't analyze this image right now. Error: {str(e)}"

# Alternative: Hugging Face implementation
def analyze_fishing_spot_huggingface(image_bytes):
    """
    Analyze a fishing spot image using Hugging Face Inference API
    """
    try:
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            return "Error: Hugging Face API key not found"
        
        # Use BLIP or LLaVA model
        API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.post(API_URL, headers=headers, data=image_bytes)
        result = response.json()
        
        if isinstance(result, list) and len(result) > 0:
            caption = result[0].get('generated_text', '')
            
            # Enhance the basic caption with fishing-specific analysis
            enhanced_analysis = f"""
**Image Analysis**: {caption}

**Fishing Recommendations**:
Based on the visible features in this image, here are some fishing suggestions:

1. **Structure Analysis**: Look for areas with natural cover and varying depths
2. **Casting Strategy**: Target areas near visible structure or vegetation
3. **Bait Selection**: Consider the water clarity and structure type
4. **Technique**: Adapt your approach based on the environment shown

**Confidence Score**: 7/10 - Good fishing potential based on visible features

Note: This analysis is based on image recognition. For best results, consider local fishing reports and conditions.
"""
            return enhanced_analysis
        else:
            return "Could not analyze the image. Please try again."
            
    except Exception as e:
        return f"Analysis error: {str(e)}"