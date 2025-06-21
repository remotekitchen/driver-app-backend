from apps.billing.models import DeliveryEarningConfig

# Safe config loader with defaults
def get_config():
    config = DeliveryEarningConfig.objects.first()

    if config:
        return {
            "base_distance_km": config.base_distance_km,
            "base_earning": config.base_earning,
            "extra_per_km": config.extra_per_km,
            "grace_period_minutes": config.grace_period_minutes,
            "penalty_6_10": config.penalty_6_10,
            "penalty_11_15": config.penalty_11_15,
            "penalty_above_15": config.penalty_above_15,
        }
    
    # Default values if config not found
    return {
        "base_distance_km": 10,
        "base_earning": 25,
        "extra_per_km": 3,
        "grace_period_minutes": 5,
        "penalty_6_10": 50, # Default 50% penalty for delays between 6-10 minutes
        "penalty_11_15": 50, # Default 50% penalty for delays between 11-15 minutes
        "penalty_above_15": 70, # Default 70% penalty for delays above 15 minutes
    }

# Calculate earning based on distance
def calculate_driver_earning(distance_km):
    config = get_config()

    distance_km = round(distance_km, 2)

    if distance_km <= config["base_distance_km"]:
        return config["base_earning"]
    
    extra_distance = distance_km - config["base_distance_km"]
    return config["base_earning"] + extra_distance * config["extra_per_km"]

# Calculate penalty
def calculate_penalty(delay_minutes):
    config = get_config()

    if delay_minutes <= config["grace_period_minutes"]:
        return 0
    elif 6 <= delay_minutes <= 10:
        return config["penalty_6_10"]
    elif 11 <= delay_minutes <= 15:
        return config["penalty_11_15"]
    else:
        return config["penalty_above_15"]

# Final earning calculation after delivery
def calculate_total_driver_earning(delivery):
    earning = calculate_driver_earning(delivery.distance)

    delay_minutes = 0
    if delivery.est_delivery_completed_time and delivery.actual_delivery_completed_time:
        delay_seconds = (delivery.actual_delivery_completed_time - delivery.est_delivery_completed_time).total_seconds()
        delay_minutes = delay_seconds / 60

    penalty = calculate_penalty(delay_minutes)
    final_earning = earning - penalty

    return max(final_earning, 0)
