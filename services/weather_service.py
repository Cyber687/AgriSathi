"""
AgriSathi - Weather Service

Retrieves current weather information from OpenWeather.

Responsibilities:
    - Fetch current weather by coordinates or location name.
    - Normalize weather data into a consistent structure.
    - Report unavailable data explicitly.
    - Handle API errors without fabricating weather information.

Environment variable:
    OPENWEATHER_API_KEY

Dependencies:
    requests
    python-dotenv
"""

import os
from typing import Optional

import requests
from dotenv import load_dotenv


# Load environment variables from the project root.
load_dotenv()


class WeatherService:
    """
    Provides current weather information for AgriSathi.

    Examples:
        service = WeatherService()

        service.get_weather(location="Bengaluru, India")

        service.get_weather(
            latitude=12.9716,
            longitude=77.5946
        )
    """

    BASE_URL = (
        "https://api.openweathermap.org/data/2.5/weather"
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 15
    ):
        self.api_key = (
            api_key or os.getenv("OPENWEATHER_API_KEY")
        )

        self.timeout = timeout

        self.session = requests.Session()

    # --------------------------------------------------
    # Validate input
    # --------------------------------------------------

    @staticmethod
    def _validate_coordinates(
        latitude: float,
        longitude: float
    ) -> None:
        """Validate latitude and longitude."""

        if not -90 <= latitude <= 90:
            raise ValueError(
                "Latitude must be between -90 and 90."
            )

        if not -180 <= longitude <= 180:
            raise ValueError(
                "Longitude must be between -180 and 180."
            )

    # --------------------------------------------------
    # Standard response format
    # --------------------------------------------------

    @staticmethod
    def _error_response(
        message: str,
        error_code: str
    ) -> dict:
        """Return a consistent error response."""

        return {
            "status": "error",
            "provider": "OpenWeather",
            "message": message,
            "error_code": error_code,
            "data": None
        }

    # --------------------------------------------------
    # Fetch current weather
    # --------------------------------------------------

    def get_weather(
        self,
        location: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> dict:
        """
        Retrieve current weather information.

        Supply either:
            1. location, such as "Ludhiana, India"
            OR
            2. latitude and longitude.

        Returns:
            A normalized dictionary containing weather data,
            or a structured error response.
        """

        if not self.api_key:
            return self._error_response(
                message=(
                    "OpenWeather API key is missing. "
                    "Configure OPENWEATHER_API_KEY in .env."
                ),
                error_code="MISSING_API_KEY"
            )

        has_latitude = latitude is not None
        has_longitude = longitude is not None

        # Coordinates must be provided together.
        if has_latitude != has_longitude:
            return self._error_response(
                message=(
                    "Both latitude and longitude "
                    "must be provided together."
                ),
                error_code="INVALID_COORDINATES"
            )

        # Select the location query method.
        if has_latitude and has_longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)

                self._validate_coordinates(
                    latitude,
                    longitude
                )

            except (ValueError, TypeError) as exc:
                return self._error_response(
                    message=str(exc),
                    error_code="INVALID_COORDINATES"
                )

            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": "metric"
            }

        elif location and location.strip():
            params = {
                "q": location.strip(),
                "appid": self.api_key,
                "units": "metric"
            }

        else:
            return self._error_response(
                message=(
                    "Provide a location name or both "
                    "latitude and longitude."
                ),
                error_code="MISSING_LOCATION"
            )

        # Request weather information.
        try:
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 401:
                return self._error_response(
                    message=(
                        "The API key is invalid or not yet "
                        "authorized. Check your OpenWeather "
                        "account and API key."
                    ),
                    error_code="INVALID_API_KEY"
                )

            if response.status_code == 404:
                return self._error_response(
                    message=(
                        "The requested location was not found. "
                        "Try a more specific location name."
                    ),
                    error_code="LOCATION_NOT_FOUND"
                )

            if response.status_code == 429:
                return self._error_response(
                    message=(
                        "The weather API request limit has "
                        "been reached."
                    ),
                    error_code="RATE_LIMIT_EXCEEDED"
                )

            response.raise_for_status()

            payload = response.json()

        except requests.Timeout:
            return self._error_response(
                message="The weather API request timed out.",
                error_code="API_TIMEOUT"
            )

        except requests.RequestException as exc:
            return self._error_response(
                message=(
                    "Unable to retrieve weather information: "
                    f"{exc}"
                ),
                error_code="API_REQUEST_FAILED"
            )

        except ValueError:
            return self._error_response(
                message=(
                    "The weather API returned invalid JSON."
                ),
                error_code="INVALID_API_RESPONSE"
            )

        # Normalize the response.
        try:
            main_data = payload["main"]
            wind_data = payload.get("wind", {})
            weather_list = payload.get("weather", [])

            weather_description = None

            if weather_list:
                weather_description = weather_list[0].get(
                    "description"
                )

            coordinates = payload.get("coord", {})

            weather_data = {
                "location": {
                    "name": payload.get("name"),
                    "country": payload.get(
                        "sys", {}
                    ).get("country"),
                    "latitude": coordinates.get("lat"),
                    "longitude": coordinates.get("lon")
                },
                "temperature_c": main_data.get("temp"),
                "feels_like_c": main_data.get("feels_like"),
                "temperature_min_c": main_data.get("temp_min"),
                "temperature_max_c": main_data.get("temp_max"),
                "humidity_percent": main_data.get("humidity"),
                "pressure_hpa": main_data.get("pressure"),
                "wind_speed_mps": wind_data.get("speed"),
                "wind_direction_degrees": wind_data.get("deg"),
                "weather_description": weather_description,
                "cloudiness_percent": payload.get(
                    "clouds", {}
                ).get("all"),
                "rainfall_last_1h_mm": payload.get(
                    "rain", {}
                ).get("1h"),
                "rainfall_last_3h_mm": payload.get(
                    "rain", {}
                ).get("3h"),
                "rain_probability": None,
                "observed_at_unix": payload.get("dt"),
                "timezone_offset_seconds": payload.get(
                    "timezone"
                ),
                "units": "metric",
                "provider": "OpenWeather"
            }

            return {
                "status": "success",
                "provider": "OpenWeather",
                "message": (
                    "Current weather retrieved successfully."
                ),
                "data": weather_data
            }

        except (KeyError, TypeError, AttributeError) as exc:
            return self._error_response(
                message=(
                    "The weather API response was missing "
                    "required fields or had an unexpected format."
                ),
                error_code="MALFORMED_API_RESPONSE"
            )

    # --------------------------------------------------
    # Close the HTTP session
    # --------------------------------------------------

    def close(self) -> None:
        """Close the HTTP session when no longer needed."""

        self.session.close()