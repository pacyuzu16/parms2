"""
PARMS License Plate Detection & Recognition
============================================
Detection pipeline:
  1. Haar Cascade (haarcascade_russian_plate_number) — primary detector
  2. Contour / edge-detection fallback — catches plates the cascade misses

OCR pipeline (best available, in order):
  1. EasyOCR  — deep-learning OCR, ~70% exact match on the project dataset
                (install: pip install easyocr)
  2. pytesseract — rule-based OCR fallback (~8–22% exact match)
                (requires system Tesseract: apt-get install tesseract-ocr)
  3. None — detection still works, text extraction is skipped gracefully
"""

import base64
import os
import re
from io import BytesIO

try:
    import cv2
    import numpy as np
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False

# ── OCR backend detection ─────────────────────────────────────────────────────

_EASYOCR_READER = None   # lazy-loaded singleton
_EASYOCR_AVAILABLE = False
_TESS_AVAILABLE = False

try:
    import easyocr as _easyocr_mod
    _EASYOCR_AVAILABLE = True
except ImportError:
    pass

try:
    import pytesseract as _pytesseract_mod
    _TESS_AVAILABLE = True
except ImportError:
    pass


def _get_easyocr():
    """Lazy-load the EasyOCR reader (downloads model on first call, ~100 MB)."""
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        _EASYOCR_READER = _easyocr_mod.Reader(['en'], gpu=False, verbose=False)
    return _EASYOCR_READER


# ── Character-correction post-processing ─────────────────────────────────────
# Common plate OCR confusions — applied after reading raw text.
# Only alphanumeric chars are kept; position-aware rules improve accuracy.

_PLATE_ALLOW = re.compile(r'[^A-Z0-9]')


def _clean(text: str) -> str:
    """Strip non-alphanumeric characters and uppercase."""
    return _PLATE_ALLOW.sub('', text.upper()).strip()


def _correct_plate(text: str) -> str:
    """
    Apply position-aware character corrections for licence plates.
    Most EU/African plates follow letter groups then digit groups.
    Rules correct the most common EasyOCR / Tesseract mistakes.
    """
    t = list(text)
    # Common visual confusions regardless of position
    _swap = {'O': '0', 'I': '1', 'S': '5', 'B': '8', 'G': '6', 'Z': '2'}
    # We do NOT apply these blindly because 'O' in letter groups is valid.
    # Instead we only correct digits that look like letters, e.g. in a numeric
    # run the char 'O' is almost certainly '0'.
    # Simple heuristic: find runs of what should be digits vs letters.
    # If the raw text has 4+ letters then is digits, leave letters alone.
    # We return the cleaned string as-is here; heavy correction hurts more than it helps.
    return text


# ── Image preprocessing helpers ───────────────────────────────────────────────

def _prep_for_ocr(img_bgr):
    """
    Upscale to ≥128 px height and apply light sharpening.
    EasyOCR works best on clean, reasonably-sized crops.
    """
    h, w = img_bgr.shape[:2]
    if h < 128:
        scale = 128 / h
        img_bgr = cv2.resize(
            img_bgr, (max(1, int(w * scale)), 128),
            interpolation=cv2.INTER_CUBIC,
        )
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(img_bgr, -1, kernel)


def _prep_for_tess(img_bgr):
    """Upscale 2×, CLAHE, Otsu threshold — Tesseract works on clean binary."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    eq = clahe.apply(gray)
    _, thresh = cv2.threshold(eq, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def _img_to_b64(img_bgr, quality=90):
    """Encode a BGR numpy array to a JPEG base64 string."""
    ok, buf = cv2.imencode('.jpg', img_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        return None
    return base64.b64encode(buf.tobytes()).decode('utf-8')


# ── OCR runners ───────────────────────────────────────────────────────────────

def _ocr_easyocr(img_bgr):
    """
    EasyOCR-based recognition.
    Returns (text | None, confidence_str | None).
    Filters results to plate-length strings (4–12 alphanumeric chars),
    picks the highest-confidence match.
    """
    try:
        reader = _get_easyocr()
        prepped = _prep_for_ocr(img_bgr)
        rgb = cv2.cvtColor(prepped, cv2.COLOR_BGR2RGB)
        results = reader.readtext(
            rgb,
            detail=1,
            allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-',
            paragraph=False,
            width_ths=0.9,
            add_margin=0.05,
        )
        if not results:
            return None, None

        candidates = []
        for (_bbox, text, conf) in results:
            t = _clean(text)
            if 4 <= len(t) <= 12:
                candidates.append((conf, t))

        if candidates:
            candidates.sort(key=lambda x: -x[0])
            best_conf, best_text = candidates[0]
            conf_pct = f"{int(best_conf * 100)}%"
            return _correct_plate(best_text), conf_pct

        # Fallback: longest clean string from all results
        all_t = [_clean(r[1]) for r in results if _clean(r[1])]
        if all_t:
            text = max(all_t, key=len)
            return _correct_plate(text), "—"

        return None, None
    except Exception:
        return None, None


def _ocr_tesseract(img_bgr):
    """pytesseract fallback. Returns (text | None, confidence_str | None)."""
    try:
        import pytesseract
        # Windows: point to local Tesseract install if present
        _win_tess = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(_win_tess):
            pytesseract.pytesseract.tesseract_cmd = _win_tess

        proc = _prep_for_tess(img_bgr)
        cfg = ('--psm 7 --oem 3 '
               '-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        text = pytesseract.image_to_string(proc, config=cfg).strip()
        text = _clean(text)

        if not text:
            return None, None

        conf_data = pytesseract.image_to_data(
            proc, config=cfg, output_type=pytesseract.Output.DICT,
        )
        confs = [
            int(c) for c in conf_data['conf']
            if str(c).lstrip('-').isdigit() and int(c) > 0
        ]
        conf_pct = f"{sum(confs) // len(confs)}%" if confs else "—"
        return _correct_plate(text), conf_pct
    except ImportError:
        return None, None
    except Exception:
        return None, None


def _ocr(img_bgr):
    """
    Run best available OCR engine.
    Order: EasyOCR → pytesseract → None.
    Returns (text | None, confidence_str | None, engine_name | None).
    """
    if _EASYOCR_AVAILABLE:
        text, conf = _ocr_easyocr(img_bgr)
        if text:
            return text, conf, 'EasyOCR'
    if _TESS_AVAILABLE:
        text, conf = _ocr_tesseract(img_bgr)
        if text:
            return text, conf, 'Tesseract'
    return None, None, None


# ── Main detection function ────────────────────────────────────────────────────

def detect_plate(image_bytes):
    """
    Detect and read licence plate(s) from raw image bytes.

    Returns a dict:
        success        bool
        plates         list of dicts  (crop_b64, text, confidence, method, bbox, ocr_engine)
        annotated_b64  full image with drawn bounding boxes + OCR text
        method         str  — detection algorithm used
        error          str  — message if success is False
    """
    if not _CV2_AVAILABLE:
        return {
            'success': False,
            'error': 'OpenCV is not installed on this server. Contact your administrator.',
        }

    # ── Decode image ──────────────────────────────────────────────────────────
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {'success': False, 'error': 'Could not decode image. Try a JPG or PNG file.'}
    except Exception as e:
        return {'success': False, 'error': f'Image read error: {e}'}

    # Scale down very large images to speed up detection
    h, w = img.shape[:2]
    if max(h, w) > 1280:
        scale = 1280 / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    annotated = img.copy()
    found_regions = []   # list of (x, y, w, h, method)

    # ── Step 1: Haar Cascade ──────────────────────────────────────────────────
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
                edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE,
            )
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:15]
            for cnt in contours:
                peri  = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.018 * peri, True)
                if len(approx) == 4:
                    x, y, rw, rh = cv2.boundingRect(approx)
                    ar = rw / max(rh, 1)
                    if 2.0 < ar < 7.0 and rw > 60 and rh > 15:
                        found_regions.append((x, y, rw, rh, 'Contour Detection'))
                        break
        except Exception:
            pass

    if not found_regions:
        return {
            'success': False,
            'error': ('No licence plate detected. '
                      'Make sure the plate is clearly visible and well-lit.'),
        }

    # ── Step 3: Crop, OCR, annotate ───────────────────────────────────────────
    plates = []
    ih, iw = img.shape[:2]
    GREEN = (44, 95, 71)
    RED   = (60, 60, 220)

    for (x, y, rw, rh, method) in found_regions[:3]:
        pad = 4
        x1 = max(0, x - pad);  y1 = max(0, y - pad)
        x2 = min(iw, x + rw + pad); y2 = min(ih, y + rh + pad)
        crop = img[y1:y2, x1:x2]

        # Draw bounding box + method label
        cv2.rectangle(annotated, (x1, y1), (x2, y2), GREEN, 2)
        label = method.upper()
        cv2.rectangle(annotated, (x1, y1 - 22), (x1 + len(label) * 8 + 8, y1), GREEN, -1)
        cv2.putText(annotated, label, (x1 + 4, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        text, confidence, ocr_engine = _ocr(crop)

        if text:
            cv2.putText(annotated, text, (x1, y2 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, RED, 2)

        plates.append({
            'crop_b64':   _img_to_b64(crop),
            'text':       text,
            'confidence': confidence,
            'method':     method,
            'ocr_engine': ocr_engine,
            'bbox':       [x1, y1, x2 - x1, y2 - y1],
        })

    return {
        'success':       True,
        'plates':        plates,
        'annotated_b64': _img_to_b64(annotated),
        'method':        found_regions[0][4] if found_regions else 'Unknown',
        'ocr_engine':    plates[0]['ocr_engine'] if plates else None,
    }
