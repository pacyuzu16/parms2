# -*- coding: utf-8 -*-
"""
PARMS ML Engine
---------------
Trains a scikit-learn Random Forest on live ParkingTicket data and returns
actionable predictions for the admin dashboard ML Insights tab.

CI Research Results (Computer Intelligence project, 2024):
  Parking Occupancy: RF 99.3% | GB 96.0% | DNN 98.7% | ViT-MLP 98.7%
  License Plate:     RF 95.9% | GB 93.2% | MLP 90.5% | SVM 98.6% | KNN 94.6%
"""

from django.utils import timezone
from .models import ParkingTicket, ParkingSpace

# ---------------------------------------------------------------------------
# CI project results — hardcoded reference data
# ---------------------------------------------------------------------------

CI_MODELS = {
    "parking_occupancy": [
        {
            "name": "Random Forest",
            "accuracy": 99.3,
            "precision": 99.1,
            "recall": 99.3,
            "f1": 99.2,
            "training_time": "0.8s",
            "status": "Selected",
        },
        {
            "name": "Gradient Boosting",
            "accuracy": 96.0,
            "precision": 95.8,
            "recall": 96.0,
            "f1": 95.9,
            "training_time": "3.2s",
            "status": "Evaluated",
        },
        {
            "name": "Deep Neural Network (DNN)",
            "accuracy": 98.7,
            "precision": 98.5,
            "recall": 98.7,
            "f1": 98.6,
            "training_time": "12.4s",
            "status": "Evaluated",
        },
        {
            "name": "ViT-MLP Hybrid",
            "accuracy": 98.7,
            "precision": 98.6,
            "recall": 98.7,
            "f1": 98.6,
            "training_time": "28.1s",
            "status": "Evaluated",
        },
    ],
    "license_plate": [
        {
            "name": "Random Forest",
            "accuracy": 95.9,
            "precision": 95.7,
            "recall": 95.9,
            "f1": 95.8,
            "training_time": "0.6s",
            "status": "Evaluated",
        },
        {
            "name": "Gradient Boosting",
            "accuracy": 93.2,
            "precision": 93.0,
            "recall": 93.2,
            "f1": 93.1,
            "training_time": "2.9s",
            "status": "Evaluated",
        },
        {
            "name": "MLP",
            "accuracy": 90.5,
            "precision": 90.3,
            "recall": 90.5,
            "f1": 90.4,
            "training_time": "5.1s",
            "status": "Evaluated",
        },
        {
            "name": "SVM",
            "accuracy": 98.6,
            "precision": 98.5,
            "recall": 98.6,
            "f1": 98.5,
            "training_time": "14.7s",
            "status": "Best LP",
        },
        {
            "name": "KNN",
            "accuracy": 94.6,
            "precision": 94.4,
            "recall": 94.6,
            "f1": 94.5,
            "training_time": "0.1s",
            "status": "Evaluated",
        },
    ],
}

# ---------------------------------------------------------------------------
# Sensible defaults used when no ticket data is available
# ---------------------------------------------------------------------------

_DEFAULT_HOURLY = [
    5, 3, 2, 2, 3, 8, 20, 45, 65, 70, 72, 68,
    75, 70, 65, 60, 68, 75, 70, 55, 40, 30, 20, 10,
]

_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Typical pattern: weekdays busier, weekend lighter
_DEFAULT_WEEKLY = [72, 70, 74, 73, 78, 55, 40]


# ---------------------------------------------------------------------------
# Core ML function
# ---------------------------------------------------------------------------

def get_ml_insights():
    """
    Train a Random Forest on live ticket data and return ML insights dict.

    Returns a dict with:
        hourly_predictions  list[float]  — 24 predicted occupancy % values
        peak_hour           int
        off_peak_hour       int
        today_prediction    float
        next_hour_prediction float
        confidence          str  — "High" | "Low"
        ci_models           dict — hardcoded CI project results
        weekly_pattern      list[dict]  — Mon-Sun predictions
    """
    now = timezone.now()
    current_hour = now.hour
    current_weekday = now.weekday()  # 0=Mon ... 6=Sun

    try:
        return _compute_insights(now, current_hour, current_weekday)
    except Exception:
        return _fallback_insights(current_hour, current_weekday)


def _compute_insights(now, current_hour, current_weekday):
    """Attempt to train RF on live data; fall back to defaults on any error."""
    try:
        from sklearn.ensemble import RandomForestRegressor
        import numpy as np
        sklearn_available = True
    except ImportError:
        sklearn_available = False

    # Fetch ticket data
    tickets = list(
        ParkingTicket.objects.values_list("entry_time", flat=True)
        .order_by("-entry_time")[:5000]
    )

    total_spaces = ParkingSpace.objects.count() or 1
    occupied = ParkingSpace.objects.filter(is_occupied=True).count()
    live_rate = round(occupied / total_spaces * 100)

    MIN_SAMPLES = 20
    has_data = len(tickets) >= MIN_SAMPLES

    if has_data and sklearn_available:
        # Build feature matrix
        X, y_raw = [], []
        for t in tickets:
            hour = t.hour
            dow = t.weekday()
            month = t.month
            X.append([hour, dow, month])
            y_raw.append(1)  # each ticket = 1 arrival

        import numpy as np
        X = np.array(X)

        # Aggregate: count arrivals per (hour, dow, month) bin
        from collections import defaultdict
        bin_counts = defaultdict(int)
        for feat in X:
            key = tuple(feat)
            bin_counts[key] += 1

        X_agg = np.array(list(bin_counts.keys()), dtype=float)
        y_agg = np.array(list(bin_counts.values()), dtype=float)
        # Normalise to [0, 100]
        y_max = y_agg.max() if y_agg.max() > 0 else 1
        y_agg = y_agg / y_max * 100

        rf = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
        )
        rf.fit(X_agg, y_agg)

        # Predict hourly for today
        month = now.month
        hourly = []
        for h in range(24):
            pred = rf.predict([[h, current_weekday, month]])[0]
            hourly.append(round(min(100.0, max(0.0, pred)), 1))

        # Weekly pattern: predict at 12:00 for each day
        weekly = []
        for d in range(7):
            pred = rf.predict([[12, d, month]])[0]
            weekly.append({
                "day": _DAYS[d],
                "predicted_pct": round(min(100.0, max(0.0, pred)), 1),
                "is_today": d == current_weekday,
            })

        confidence = "High"

    else:
        # Use statistical defaults
        hourly = [round(v, 1) for v in _DEFAULT_HOURLY]
        weekly = [
            {
                "day": _DAYS[d],
                "predicted_pct": float(_DEFAULT_WEEKLY[d]),
                "is_today": d == current_weekday,
            }
            for d in range(7)
        ]
        confidence = "Low"

    peak_hour = int(hourly.index(max(hourly)))
    off_peak_hour = int(hourly.index(min(hourly)))
    today_prediction = hourly[current_hour]
    next_hour = (current_hour + 1) % 24
    next_hour_prediction = hourly[next_hour]

    return {
        "hourly_predictions": hourly,
        "peak_hour": peak_hour,
        "peak_hour_label": f"{peak_hour:02d}:00",
        "off_peak_hour": off_peak_hour,
        "off_peak_hour_label": f"{off_peak_hour:02d}:00",
        "today_prediction": today_prediction,
        "next_hour_prediction": next_hour_prediction,
        "next_hour_label": f"{next_hour:02d}:00",
        "live_occupancy": live_rate,
        "confidence": confidence,
        "has_data": has_data,
        "ticket_count": len(tickets),
        "ci_models": CI_MODELS,
        "weekly_pattern": weekly,
        "current_hour": current_hour,
        "current_weekday": current_weekday,
        "current_day": _DAYS[current_weekday],
    }


def _fallback_insights(current_hour, current_weekday):
    """Return safe defaults when an unexpected exception occurs."""
    next_hour = (current_hour + 1) % 24
    return {
        "hourly_predictions": list(_DEFAULT_HOURLY),
        "peak_hour": 13,
        "peak_hour_label": "13:00",
        "off_peak_hour": 3,
        "off_peak_hour_label": "03:00",
        "today_prediction": float(_DEFAULT_HOURLY[current_hour]),
        "next_hour_prediction": float(_DEFAULT_HOURLY[next_hour]),
        "next_hour_label": f"{next_hour:02d}:00",
        "live_occupancy": 0,
        "confidence": "Low",
        "has_data": False,
        "ticket_count": 0,
        "ci_models": CI_MODELS,
        "weekly_pattern": [
            {
                "day": _DAYS[d],
                "predicted_pct": float(_DEFAULT_WEEKLY[d]),
                "is_today": d == current_weekday,
            }
            for d in range(7)
        ],
        "current_hour": current_hour,
        "current_weekday": current_weekday,
        "current_day": _DAYS[current_weekday],
    }
