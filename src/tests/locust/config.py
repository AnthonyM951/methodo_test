class ConfigChargeTest:
    # Point de base pour les appels API
    API_ENDPOINT = "http://localhost:8000"
    
    # Scénarios de charge
    CHARGE_LEGERE = {
        "users": 10,
        "spawn_rate": 2,
        "duration": "2m"
    }
    
    CHARGE_MODEREE = {
        "users": 50,
        "spawn_rate": 10,
        "duration": "5m"
    }

    # Liste de villes pour les scénarios de test
    VILLES_TEST = [
        "Paris", "London", "Berlin", "Madrid", "Rome",
        "Tokyo", "Sydney", "New York", "Los Angeles"
    ]
