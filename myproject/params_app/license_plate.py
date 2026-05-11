"""
PARMS License Plate Detection
==============================
Implements the Haar Cascade approach from the CI project.

Pipeline:
  1. Haar Cascade (haarcascade_russian_plate_number) — primary detector
  2. Contour / edge-detection fallback — catches plates the cascade misses
  3. Image preprocessing (bilateral filter, threshold, dilation) on the crop
  4. OCR via pytesseract (optional — degrades gracefully if not installed)
"""

import base64
from io import BytesIO

try:
    import cv2
    import numpy as np
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False


# ── Helpers ────────────────────────────────────────────────────────────────────

def _img_to_b64(img_bgr, quality=90):
    """Encode a BGR numpy array to a JPEG base64 string."""
    ok, buf = cv2.imencode('.jpg', img_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        return None
    return base64.b64encode(buf.tobytes()).decode('utf-8')


def _preprocess_plate(crop):
    """Sharpen a plate crop to improve OCR accuracy."""
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    # Bilateral filter preserves edges while removing noise
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)
    # Adaptive threshold for varying illumination
    thresh = cv2.adaptiveThreshold(
        filtered, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    # Dilate slightly to connect character strokes
    kernel = np.ones((2, 2), np.uint8)
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    return dilated


def _ocr(preprocessed_gray):
    """Run OCR on a preprocessed plate image. Returns (text, confidence)."""
    try:
        import pytesseract
        cfg = '--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789- '
        text = pytesseract.image_to_string(preprocessed_gray, config=cfg).strip()
        # Clean: keep only alphanumeric + space + dash
        text = ''.join(c for c in text if c.isalnum() or c in (' ', '-')).strip()
        conf_data = pytesseract.image_to_data(
            preprocessed_gray, config=cfg, output_type=pytesseract.Output.DICT
        )
        confs = [int(c) for c in conf_data['conf'] if str(c).lstrip('-').isdigit() and int(c) > 0]
        confidence = f"{sum(confs) // len(confs)}%" if confs else "—"
        return text or None, confidence
    except ImportError:
        return None, None
    except Exception:
        return None, None


# ── Main detection function ────────────────────────────────────────────────────

def detect_plate(image_bytes):
    """
    Detect license plate(s) from raw image bytes.

    Returns a dict:
        success        bool
        plates         list of plate dicts (crop_b64, text, confidence, method, bbox)
        annotated_b64  full image with drawn bounding boxes
        method         str  — which algorithm found plates
        error          str  — error message if success is False
    """
    if not _CV2_AVAILABLE:
        return {'success': False, 'error': 'OpenCV is not installed on this server. Contact your administrator.'}

    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {'success': False, 'error': 'Could not decode image. Try a JPG or PNG file.'}
    except Exception as e:
        return {'success': False, 'error': f'Image read error: {e}'}

    # Scale down very large images to speed up detection
    h, w = img.shape[:2]
    max_dim = 1280
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    annotated = img.copy()
    found_regions = []   # list of (x, y, w, h, method)

    # ── Step 1: Haar Cascade ───────────────────────────────────────────────────
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_russian_plate_number.xml'
        plate_cascade = cv2.CascadeClassifier(cascade_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        detected = plate_cascade.detectMultiScale(
            gray,
            scaleFactor=1.05,
            minNeighbors=3,
            minSize=(60, 20),
            maxSize=(500, 120),
        )
        for (x, y, rw, rh) in (detected if len(detected) > 0 else []):
            found_regions.append((int(x), int(y), int(rw), int(rh), 'Haar Cascade'))
    except Exception:
        pass

    # ── Step 2: Contour / edge fallback ───────────────────────────────────────
    if not found_regions:
        try:
            gray2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.bilateralFilter(gray2, 11, 17, 17)
            edged = cv2.Canny(blurred, 30, 200)
            contours, _ = cv2.findContours(
                edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15]

            for cnt in contours:
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.018 * peri, True)
                if len(approx) == 4:
                    x, y, rw, rh = cv2.boundingRect(approx)
                    ar = rw / max(rh, 1)
                    if 2.0 < ar < 7.0 and rw > 60 and rh > 15:
                        found_regions.append((x, y, rw, rh, 'Contour Detection'))
                        break   # take the best contour match
        except Exception:
            pass

    if not found_regions:
        return {
            'success': False,
            'error': 'No license plate detected. Make sure the plate is clearly visible and well-lit.',
        }

    # ── Step 3+4: Crop, preprocess, OCR ───────────────────────────────────────
    plates = []
    ih, iw = img.shape[:2]
    GREEN = (44, 95, 71)      # BGR for bounding box
    RED   = (60, 60, 220)

    for (x, y, rw, rh, method) in found_regions[:3]:   # max 3 plates
        # Pad crop slightly
        pad = 4
        x1 = max(0, x - pad); y1 = max(0, y - pad)
        x2 = min(iw, x + rw + pad); y2 = min(ih, y + rh + pad)
        crop = img[y1:y2, x1:x2]

        # Draw on annotated image
        cv2.rectangle(annotated, (x1, y1), (x2, y2), GREEN, 2)
        label = method.upper()
        cv2.rectangle(annotated, (x1, y1 - 22), (x1 + len(label) * 8 + 8, y1), GREEN, -1)
        cv2.putText(annotated, label, (x1 + 4, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        preprocessed = _preprocess_plate(crop)
        text, confidence = _ocr(preprocessed)

        if text:
            cv2.putText(annotated, text, (x1, y2 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, RED, 2)

        plates.append({
            'crop_b64':   _img_to_b64(crop),
            'text':       text,
            'confidence': confidence,
            'method':     method,
            'bbox':       [x1, y1, x2 - x1, y2 - y1],
        })

    method_used = found_regions[0][4] if found_regions else 'Unknown'

    return {
        'success':       True,
        'plates':        plates,
        'annotated_b64': _img_to_b64(annotated),
        'method':        method_used,
    }
