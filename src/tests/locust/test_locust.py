from locust import HttpUser, task, between
import random

class WeatherAPIUser(HttpUser):
    # Temps d'attente entre les requêtes (1 à 3 secondes)
    wait_time = between(3, 10)
    
    def on_start(self):
        """Exécuté au démarrage de chaque utilisateur"""
        # Initialisation si nécessaire (login, setup, etc.)
        pass
    
    @task(3)  # Poids 3 : cette tâche sera exécutée 3x plus souvent
    def task_current_weather(self):
        """Test de l'endpoint météo actuelle"""
        cities = ["Paris", "London", "New York", "Berlin"]
        city = random.choice(cities)
        
        with self.client.get(f"/weather/current/{city}", 
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)  # Poids 2
    def task_forecast_weather(self):
        """Test de l'endpoint prévisions"""
        cities = ["Paris", "Madrid", "Rome"]
        city = random.choice(cities)
        self.client.get(f"/weather/forecast/{city}")

    @task(1)  # Poids 1 : moins fréquent
    def task_history_weather(self):
        """Test de l'endpoint historique"""
        self.client.get("/weather/history/Paris")
