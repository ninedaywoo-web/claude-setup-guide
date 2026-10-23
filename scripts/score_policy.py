"""Shared advisory bands, not a model of account suspension risk."""
import math


def assessment(name, value):
    if value is None:
        return 'unverified'
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 100:
        return 'invalid'
    ideal = value >= 80 if name == 'netcoffee' else value < (30 if name == 'ping0' else 10)
    close = value >= 75 if name == 'netcoffee' else value <= (35 if name == 'ping0' else 15)
    return 'reference_met' if ideal else 'near_reference' if close else 'recheck_recommended'
