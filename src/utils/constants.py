"""
Physical and protocol constants for 5G NR fronthaul optimization.
"""

# 5G NR Physical Layer Constants
SYMBOL_DURATION_SEC = 35.7e-6  # 35.7 microseconds per symbol
SYMBOLS_PER_SLOT = 14  # 5G NR standard
SLOT_DURATION_SEC = SYMBOL_DURATION_SEC * SYMBOLS_PER_SLOT  # ~500 µs

# Buffer Configuration
BUFFER_SIZE_US = 143  # Microseconds (from problem statement)
MIN_BUFFER_US = 70
MAX_BUFFER_US = 200

# Traffic Analysis
CORRELATION_THRESHOLD = 0.70  # For topology discovery
PACKET_LOSS_LIMIT = 0.01  # 1% maximum allowed loss

# Link Rates (Gbps)
LINK_RATES = {
    '10G': 10.0,
    '25G': 25.0,
    '40G': 40.0,
    '100G': 100.0
}

# PAPR Thresholds for Adaptive Shaping
PAPR_LOW = 10.0
PAPR_MEDIUM = 100.0
PAPR_HIGH = 600.0

# Sustainability Constants (Rough Estimates)
OPTIC_COST = {
    '10G': 500,
    '25G': 1500,
    '40G': 5000,
    '100G': 15000
}

OPTIC_POWER_W = {
    '10G': 2.5,
    '25G': 3.5,
    '40G': 5.0,
    '100G': 8.0
}

# Energy to CO2 conversion (kg CO2e per kWh, global average)
KG_CO2_PER_KWH = 0.5
HOURS_PER_YEAR = 8760
