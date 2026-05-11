"""
Benchmark EasyOCR (tuned) vs Tesseract on the license plate test set.
"""
import cv2
import os
import re
import numpy as np

TEST_DIR  = (r'C:\Users\Administrator\Desktop\y3\SEMESTER 1'
             r'\Computer Intelligence\PARMS-6\data\license-plates-dataset\test')
TRAIN_DIR = (r'C:\Users\Administrator\Desktop\y3\SEMESTER 1'
             r'\Computer Intelligence\PARMS-6\data\license-plates-dataset\train')


def clean_gt(fname):
    stem = os.path.splitext(fname)[0].upper()
    stem = re.sub(r'_\d+$', '', stem)   # strip _1, _2 etc.
    return stem.replace(' ', '')


def clean_pred(text):
    if not text:
        return ''
    return ''.join(c for c in text.upper() if c.isalnum()).strip()


def score(pred, gt):
    pred = clean_pred(pred)
    if pred == gt:
        return 'exact', pred
    if gt and pred:
        if gt in pred or pred in gt:
            return 'partial', pred
        matches = sum(a == b for a, b in zip(pred, gt))
        if len(gt) > 0 and matches / len(gt) >= 0.7:
            return 'partial', pred
    return 'fail', pred


# ── preprocessing helper ──────────────────────────────────────────────────────

def prep_for_ocr(img):
    """Upscale to ≥128px height, equalise contrast."""
    h, w = img.shape[:2]
    if h < 128:
        scale = 128 / h
        img = cv2.resize(img, (int(w * scale), 128), interpolation=cv2.INTER_CUBIC)
    # Sharpen slightly
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(img, -1, kernel)


# ── EasyOCR ───────────────────────────────────────────────────────────────────
print("Loading EasyOCR reader…")
import easyocr
reader = easyocr.Reader(['en'], gpu=False, verbose=False)
print("EasyOCR ready.\n")

PLATE_ALLOW = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def ocr_easy_tuned(img):
    """
    Run EasyOCR with detail=1 (confidence scores), then:
    - filter to plate-length strings (4-12 alphanumeric chars)
    - pick highest-confidence match
    - fall back to longest plausible string
    """
    img = prep_for_ocr(img)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = reader.readtext(rgb, detail=1,
                              allowlist=PLATE_ALLOW + '-',
                              paragraph=False,
                              width_ths=0.9,
                              add_margin=0.05)
    if not results:
        return ''

    candidates = []
    for (bbox, text, conf) in results:
        t = clean_pred(text)
        if 4 <= len(t) <= 12:
            candidates.append((conf, t))

    if candidates:
        candidates.sort(key=lambda x: -x[0])
        return candidates[0][1]

    # fallback: pick longest clean string
    all_texts = [clean_pred(r[1]) for r in results]
    all_texts = [t for t in all_texts if t]
    return max(all_texts, key=len) if all_texts else ''


# ── Tesseract (best-of) ───────────────────────────────────────────────────────
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def pre_clahe(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    eq = clahe.apply(gray)
    _, t = cv2.threshold(eq, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return t


def ocr_tess(img):
    proc = pre_clahe(img)
    cfg = '--psm 7 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    text = pytesseract.image_to_string(proc, config=cfg).strip()
    return clean_pred(text)


# ── Runner ────────────────────────────────────────────────────────────────────

def run(label, ocr_fn, directory):
    exact = partial = total = 0
    fails = []
    for fname in sorted(os.listdir(directory)):
        if os.path.splitext(fname)[1].lower() not in ('.jpg', '.jpeg', '.png', '.bmp'):
            continue
        gt  = clean_gt(fname)
        img = cv2.imread(os.path.join(directory, fname))
        if img is None:
            continue
        total += 1
        try:
            pred_raw = ocr_fn(img)
        except Exception:
            pred_raw = ''
        s, pred = score(pred_raw, gt)
        if s == 'exact':    exact += 1
        elif s == 'partial': partial += 1
        else:                fails.append((gt, pred))

    tag = directory.split(os.sep)[-1]
    print(f'\n{label}  [{tag}]')
    print(f'  Total  : {total}')
    print(f'  Exact  : {exact:3d}  ({exact/total*100:5.1f}%)')
    print(f'  Partial: {partial:3d}  ({partial/total*100:5.1f}%)')
    print(f'  Fail   : {total-exact-partial:3d}  ({(total-exact-partial)/total*100:5.1f}%)')
    if fails:
        print('  Sample failures:')
        for gt, pr in fails[:10]:
            print(f'    GT={gt:15s}  pred={pr}')
    return exact, partial, total


print('=' * 60)
print('BENCHMARK  —  test set (73 images)')
print('=' * 60)
run('Tesseract (2x+CLAHE, PSM7)',  ocr_tess,        TEST_DIR)
run('EasyOCR  (tuned, filtered)',  ocr_easy_tuned,  TEST_DIR)

print('\n' + '=' * 60)
print('TRAIN SET SAMPLE  (first 100 images)')
print('=' * 60)

def run_sample(label, ocr_fn, directory, n=100):
    exact = partial = total = 0
    files = sorted(os.listdir(directory))[:n]
    for fname in files:
        if os.path.splitext(fname)[1].lower() not in ('.jpg', '.jpeg', '.png', '.bmp'):
            continue
        gt  = clean_gt(fname)
        img = cv2.imread(os.path.join(directory, fname))
        if img is None:
            continue
        total += 1
        try:
            pred_raw = ocr_fn(img)
        except Exception:
            pred_raw = ''
        s, pred = score(pred_raw, gt)
        if s == 'exact':    exact += 1
        elif s == 'partial': partial += 1
    if total:
        print(f'{label}: exact={exact/total*100:.1f}%  partial={partial/total*100:.1f}%  (n={total})')

run_sample('Tesseract', ocr_tess,       TRAIN_DIR)
run_sample('EasyOCR  ', ocr_easy_tuned, TRAIN_DIR)
