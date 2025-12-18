# Holograph OCR Service Options

This document outlines affordable and free options for holograph detection and document verification.

## 🆓 Free/Open Source Options

### 1. **Tesseract OCR + Custom Hologram Detection**
- **Cost**: FREE (Open Source)
- **Best for**: Development/testing, basic OCR
- **Limitations**: No built-in hologram detection (requires custom implementation)
- **Installation**:
  ```bash
  pip install pytesseract pillow opencv-python
  ```
- **Pros**: 
  - Completely free
  - No API limits
  - Full control over processing
- **Cons**: 
  - Requires custom hologram detection logic
  - Less accurate than specialized services
  - More development time

### 2. **OCR.space API**
- **Cost**: FREE (25,000 requests/month, 500/day per IP)
- **Best for**: High-volume OCR needs
- **Features**: 
  - Multi-language support
  - Automatic language detection
  - Vertical text recognition
- **API**: REST API with simple integration
- **Website**: https://ocr.space/ocrapi
- **Pros**: 
  - Very generous free tier
  - Easy to integrate
  - Good accuracy
- **Cons**: 
  - No built-in hologram detection
  - Rate limited per IP

### 3. **Atlas OCR**
- **Cost**: FREE (100 pages/month)
- **Best for**: Low-volume production use
- **Features**: 
  - JSON-ready output
  - Document Q&A capabilities
  - Multi-language support
- **Pricing**: $0.01 per page beyond free tier
- **Website**: https://atlasocr.com
- **Pros**: 
  - No credit card required
  - Very cheap paid tier
  - Good API documentation
- **Cons**: 
  - Limited free tier
  - No hologram detection

## 💰 Affordable Paid Options

### 4. **Arya.ai Hologram Detection API**
- **Cost**: Contact for pricing (likely has free trial)
- **Best for**: Production hologram detection
- **Features**: 
  - AI-driven hologram detection
  - Supports PNG, JPEG, TIFF, PDF
  - Rapid analysis with visual outputs
- **Website**: https://arya.ai/apex-apis/hologram-detection-api
- **Pros**: 
  - Specialized for hologram detection
  - High accuracy
  - Professional service
- **Cons**: 
  - Pricing not publicly available
  - May be expensive for small projects

### 5. **Veryfi OCR API**
- **Cost**: FREE (100 transactions/month)
- **Best for**: Receipt/invoice processing with fraud detection
- **Features**: 
  - Fraud detection capabilities
  - AI-generated document detection
  - Document forensics
- **Pricing**: $0.08 per receipt, $0.16 per invoice (min $500/month)
- **Website**: https://veryfi.com
- **Pros**: 
  - Includes fraud detection
  - Good for financial documents
- **Cons**: 
  - Expensive for high volume
  - Not specialized for diplomas

### 6. **OCR Studio Document Verification**
- **Cost**: Contact for pricing
- **Best for**: ID/document verification
- **Features**: 
  - Multispectral ID authentication
  - UV luminescence control
  - Security element verification
  - Anti-Photoshop algorithms
- **Website**: https://ocrstudio.ai/document-verification
- **Pros**: 
  - Advanced security features
  - Good for official documents
- **Cons**: 
  - Pricing not public
  - May be overkill for diplomas

## 🎯 Recommended Approach for BlockProof

### **Option 1: Hybrid Approach (Recommended for MVP)**
1. **Use OCR.space** for text extraction (free tier: 25K/month)
2. **Implement basic hologram detection** using OpenCV:
   - Detect reflective surfaces
   - Analyze light patterns
   - Check for security features
3. **Add file hash verification** (already implemented)
4. **Store metadata** for manual review if needed

### **Option 2: Production-Ready**
1. **Start with OCR.space** for OCR
2. **Integrate Arya.ai** for hologram detection (if budget allows)
3. **Fallback to hash verification** if hologram detection fails

### **Option 3: Fully Free**
1. **Use Tesseract OCR** (pytesseract) for text extraction
2. **Custom OpenCV hologram detection**:
   ```python
   import cv2
   import numpy as np
   
   def detect_hologram_features(image):
       # Convert to grayscale
       gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
       
       # Detect reflective surfaces (holograms reflect light differently)
       # This is a simplified approach
       edges = cv2.Canny(gray, 50, 150)
       contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
       
       # Analyze patterns that might indicate holograms
       # (This requires domain knowledge and training data)
       return {
           'has_reflective_surfaces': len(contours) > threshold,
           'confidence': 0.5  # Placeholder
       }
   ```

## 📝 Implementation Notes

### For Development (Current State)
- The placeholder in `document_service.py` is sufficient
- Focus on hash-based verification (already implemented)
- Add basic OCR for text extraction if needed

### For Production
- Consider integrating OCR.space for OCR (free tier is generous)
- Add custom hologram detection using OpenCV
- Consider paid services only if volume/accuracy requirements demand it

## 🔗 Quick Integration Examples

### OCR.space Integration
```python
import requests

def ocr_space_file(file_path, api_key='helloworld'):
    url = 'https://api.ocr.space/parse/image'
    with open(file_path, 'rb') as f:
        response = requests.post(
            url,
            files={'file': f},
            data={'apikey': api_key}
        )
    return response.json()
```

### Tesseract Integration
```python
import pytesseract
from PIL import Image

def extract_text(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    return text
```

## 💡 Recommendation

**For your current use case (localhost, development):**
- ✅ Use **OCR.space** for OCR (free, 25K/month)
- ✅ Implement **basic hash verification** (already done)
- ✅ Add **simple OpenCV-based hologram detection** (optional)
- ✅ Store **metadata for manual review** if needed

**For production deployment:**
- Consider **Arya.ai** if hologram detection is critical
- Or stick with **hash verification** + **OCR.space** for cost-effectiveness







