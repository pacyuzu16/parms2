"""
Benchmark current OCR accuracy on the license plate test set,
then compare against improved preprocessing strategies.
"""
import cv2
import numpy as np
import os
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

TEST_DIR = r'C:\Users\Administrator\Desktop\y3\SEMESTER 1\Computer Intelligence\PARMS-6\data\license-plates-dataset\test'

# ── preprocessing strategies ─────────────────────────────────────────────────

def pre_current(img):
    """Original pipeline: bilateral → adaptive threshold → dilate."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    filt = cv2.bilateralFilter(gray, 11, 17, 17)
    thresh = cv2.adaptiveThreshold(filt, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    k = np.ones((2, 2), np.uint8)
    return cv2.dilate(thresh, k, iterations=1)


def pre_upscale_clahe(img):
    """Upscale 2x + CLAHE + Otsu threshold."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    eq = clahe.apply(gray)
    _, thresh = cv2.threshold(eq, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def pre_sharpen_otsu(img):
    """Sharpen kernel + Otsu."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    kernel = np.array([[-1,-1,-1],[-1, 9,-1],[-1,-1,-1]])
    sharp = cv2.filter2D(gray, -1, kernel)
    _, thresh = cv2.threshold(sharp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


def pre_morph(img):
    """Morphological enhancement + adaptive thresh on upscaled image."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    filt = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(filt, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                   cv2.THRESH_BINARY, 15, 10)
    return thresh


# ── OCR runner ────────────────────────────────────────────────────────────────

def ocr(img_gray, psm=7):
    cfg = f'--psm {psm} --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'
    text = pytesseract.image_to_string(img_gray, config=cfg).strip()
    return ''.join(c for c in text if c.isalnum() or c == '-').upper()


def best_of(img):
    """Try multiple strategies + PSM modes; return text with highest confidence."""
    candidates = []
    for pre_fn in [pre_upscale_clahe, pre_sharpen_otsu, pre_morph, pre_current]:
        proc = pre_fn(img)
        for psm in [7, 8, 6]:
            text = ocr(proc, psm)
            if text:
                candidates.append(text)
    if not candidates:
        return ''
    # Pick most common result (simple voting)
    from collections import Counter
    return Counter(candidates).most_common(1)[0][0]


# ── benchmark ────────────────────────────────────────────────────────────────

def score(pred, gt):
    if pred == gt:
        return 'exact'
    if gt and pred and (gt in pred or pred in gt):
        return 'partial'
    if gt and pred:
        matches = sum(a == b for a, b in zip(pred, gt))
        if matches >= len(gt) * 0.7:
            return 'partial'
    return 'fail'


def run(label, pre_fn=None, psm=7):
    exact = partial = total = 0
    fails = []
    for fname in sorted(os.listdir(TEST_DIR)):
        ext = os.path.splitext(fname)[1].lower()
        if ext not in ('.jpg', '.jpeg', '.png', '.bmp'):
            continue
        gt = os.path.splitext(fname)[0].upper().replace(' ', '')
        img = cv2.imread(os.path.join(TEST_DIR, fname))
        if img is None:
            continue
        total += 1
        if pre_fn is None:
            pred = best_of(img)
        else:
            proc = pre_fn(img)
            pred = ocr(proc, psm)
        s = score(pred, gt)
        if s == 'exact':   exact += 1
        elif s == 'partial': partial += 1
        else: fails.append((gt, pred))

    print(f'\n{label}')
    print(f'  Total  : {total}')
    print(f'  Exact  : {exact:3d}  ({exact/total*100:5.1f}%)')
    print(f'  Partial: {partial:3d}  ({partial/total*100:5.1f}%)')
    print(f'  Fail   : {total-exact-partial:3d}  ({(total-exact-partial)/total*100:5.1f}%)')
    if fails:
        print('  Sample failures:')
        for gt, pr in fails[:8]:
            print(f'    GT={gt:15s}  pred={pr}')
    return exact, partial, total


if __name__ == '__main__':
    print('=' * 55)
    print('LICENSE PLATE OCR BENCHMARK — test set')
    print('=' * 55)
    run('Current pipeline (bilateral+adaptive, PSM 7)', pre_current, psm=7)
    run('Upscale 2x + CLAHE + Otsu (PSM 7)',            pre_upscale_clahe, psm=7)
    run('Sharpen + Otsu (PSM 7)',                        pre_sharpen_otsu, psm=7)
    run('Morph + adaptive (PSM 7)',                      pre_morph, psm=7)
    run('BEST-OF (4 strategies × 3 PSM modes — voting)', pre_fn=None)
