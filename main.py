import time
from machine import Pin, SPI, RTC
import gc9a01
from bitmap import vga1_bold_16x32 as font
import network
import urequests
import gc
import cst816  # Import the touch module

# Initialize touch (assuming the library handles I2C internally)
touch = cst816.CST816()

# Wi-Fi credentials
WIFI_SSID = "Your SSID"
WIFI_PASSWORD = "WIFI Password"

# API URLs
GEOLOCATION_API_URL = "http://ip-api.com/json/"
WORLD_TIME_API_URL = "https://worldtimeapi.org/api/timezone/{timezone}"
WEATHER_API_URL = "http://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relativehumidity_2m"

# Global variable to track temperature unit
temperature_unit = "C"  # Default to Celsius

def truncate_to_hour(time_str):
    """Truncate time string to hourly format (YYYY-MM-DDTHH:00)"""
    try:
        # Split into date/time parts and remove timezone
        date_part, time_part = time_str.split('T', 1)
        time_part = time_part.split('+')[0].split('-')[0]  # Remove timezone
        hour = time_part.split(':')[0]
        return f"{date_part}T{hour}:00"
    except:
        return time_str  # Fallback if parsing fails

# Connect to Wi-Fi (unchanged)
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print("Connected to Wi-Fi")
    print("IP:", wlan.ifconfig()[0])

# Fetch geolocation data (unchanged)
def fetch_geolocation():
    try:
        response = urequests.get(GEOLOCATION_API_URL)
        if response.status_code == 200:
            print("Geolocation data fetched successfully")
            geolocation_data = response.json()
            print("Geolocation Data:", geolocation_data)
            return geolocation_data
        else:
            print("Failed to fetch geolocation data. Status code:", response.status_code)
            return None
    except Exception as e:
        print("Error fetching geolocation data:", e)
        return None
    finally:
        gc.collect()

# Fetch current time (unchanged)
def fetch_current_time(timezone):
    try:
        url = WORLD_TIME_API_URL.format(timezone=timezone)
        response = urequests.get(url)
        if response.status_code == 200:
            print("Current time fetched successfully")
            time_data = response.json()
            print("Time Data:", time_data)
            return time_data
        else:
            print("Failed to fetch current time. Status code:", response.status_code)
            return None
    except Exception as e:
        print("Error fetching current time:", e)
        return None
    finally:
        gc.collect()

# Synchronize time (unchanged)
def sync_time(timezone):
    try:
        time_data = fetch_current_time(timezone)
        if time_data:
            current_time = time_data['datetime']
            year = int(current_time[:4])
            month = int(current_time[5:7])
            day = int(current_time[8:10])
            hour = int(current_time[11:13])
            minute = int(current_time[14:16])
            second = int(current_time[17:19])
            
            rtc = RTC()
            rtc.datetime((year, month, day, 0, hour, minute, second, 0))
            print(f"Time synchronized with WorldTimeAPI: {rtc.datetime()}")
    except Exception as e:
        print("Error synchronizing time with WorldTimeAPI:", e)

# Fetch weather data (unchanged)
def fetch_weather_data(lat, lon):
    try:
        url = WEATHER_API_URL.format(lat=lat, lon=lon)
        response = urequests.get(url)
        if response.status_code == 200:
            print("Weather data fetched successfully")
            weather_data = response.json()
            print("Weather Data:", weather_data)
            return weather_data
        else:
            print("Failed to fetch weather data. Status code:", response.status_code)
            return None
    except Exception as e:
        print("Error fetching weather data:", e)
        return None
    finally:
        gc.collect()

# Weather condition mapping (unchanged)
def get_weather_condition(weather_code):
    weather_conditions = {0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle", 56: "Light freezing drizzle", 57: "Dense freezing drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 66: "Light freezing rain", 67: "Heavy freezing rain", 71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall", 77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers", 95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"}
    return weather_conditions.get(weather_code, "Unknown")

# Weather image mapping (unchanged)
def get_weather_image(weather_code):
    weather_images = {0: "jpg/clear_sky.jpg", 1: "jpg/mainly_clear.jpg", 2: "jpg/partly_cloudy.jpg", 3: "jpg/overcast.jpg", 45: "jpg/fog.jpg", 48: "jpg/fog.jpg", 51: "jpg/light_drizzle.jpg", 53: "jpg/moderate_drizzle.jpg", 55: "jpg/dense_drizzle.jpg", 56: "jpg/freezing_drizzle.jpg", 57: "jpg/freezing_drizzle.jpg", 61: "jpg/light_rain.jpg", 63: "jpg/moderate_drizzle.jpg", 65: "jpg/dense_drizzle.jpg", 66: "jpg/freezing_rain.jpg", 67: "jpg/freezing_rain.jpg", 71: "jpg/light_snow.jpg", 73: "jpg/moderate_snow.jpg", 75: "jpg/heavy_snow.jpg", 77: "jpg/snow_grains.jpg", 80: "jpg/light_drizzle.jpg", 81: "jpg/moderate_drizzle.jpg", 82: "jpg/dense_drizzle.jpg", 85: "jpg/light_snow.jpg", 86: "jpg/heavy_snow.jpg", 95: "jpg/thunderstorm.jpg", 96: "jpg/thunderstorm_hail.jpg", 99: "jpg/thunderstorm_heavyhail.jpg"}
    return weather_images.get(weather_code, "jpg/unknown.jpg")

def convert_temperature(temp, unit):
    if unit == "F":
        return (temp * 9/5) + 32  # Convert to Fahrenheit
    return temp  # Default to Celsius

def display_weather_data(tft, weather_data, geolocation_data):
    global temperature_unit
    try:
        tft.fill(gc9a01.BLACK)

        if weather_data and 'current_weather' in weather_data:
            current_weather = weather_data['current_weather']
            temperature = current_weather['temperature']
            weather_code = current_weather['weathercode']
            current_time = current_weather['time']

            # Process hourly data with truncation
            hourly_data = weather_data.get('hourly', {})
            time_list = hourly_data.get('time', [])
            humidity_list = hourly_data.get('relativehumidity_2m', [])

            # Truncate times to hourly format
            current_time_truncated = truncate_to_hour(current_time)
            time_list_truncated = [truncate_to_hour(t) for t in time_list]

            try:
                time_index = time_list_truncated.index(current_time_truncated)
                humidity = humidity_list[time_index]
            except (ValueError, IndexError):
                print("Using fallback: First humidity entry")
                humidity = humidity_list[0] if humidity_list else "N/A"

            # Temperature display
            display_temp = convert_temperature(temperature, temperature_unit)
            
            # Display layout calculations
            def center_x(text):
                return (tft.width() - len(text) * font.WIDTH) // 2

            # Humidity and temperature display
            humidity_text = f"{humidity}%/"
            temp_text = f"{display_temp:.1f}"
            combined_text = f"{humidity_text}{temp_text}"
            combined_x = center_x(combined_text)
            tft.text(font, humidity_text, combined_x, 45, gc9a01.WHITE, gc9a01.BLACK)
            temp_x = combined_x + len(humidity_text) * font.WIDTH
            tft.text(font, temp_text, temp_x, 45, gc9a01.WHITE, gc9a01.BLACK)

            # Unit display
            unit_image = "jpg/celsius.jpg" if temperature_unit == "C" else "jpg/fahrenheit.jpg"
            unit_x = temp_x + len(temp_text) * font.WIDTH
            tft.jpg(unit_image, unit_x, 45, 30)

            # City name
            city_name = geolocation_data.get('city', 'Unknown City')
            city_text = city_name
            city_x = center_x(city_text)
            tft.text(font, city_text, city_x, 85, gc9a01.WHITE, gc9a01.BLACK)

            # Weather condition
            weather_condition = get_weather_condition(weather_code)
            condition_x = center_x(weather_condition)
            tft.text(font, weather_condition, condition_x, 125, gc9a01.WHITE, gc9a01.BLACK)

            # Weather image
            image_file = get_weather_image(weather_code)
            tft.jpg(image_file, 80, 160, 75)

    except Exception as e:
        print("Error displaying weather data:", e)
    finally:
        gc.collect()

# Touch handling (unchanged)
def handle_touch(tft):
    global temperature_unit
    if touch.get_touch():
        print("Touch detected!")
        new_unit = "F" if temperature_unit == "C" else "C"
        message = f"Changing to {new_unit}"
        message2 = "in 60 sec"
        tft.fill(gc9a01.BLACK)
        tft.text(font, message, 10, 100, gc9a01.WHITE, gc9a01.BLACK)
        tft.text(font, message2, 50, 135, gc9a01.WHITE, gc9a01.BLACK)
        time.sleep(60)
        temperature_unit = new_unit
        tft.fill(gc9a01.BLACK)

# Main function (unchanged)
def main():
    global temperature_unit

    spi = SPI(2, baudrate=80000000, polarity=0, sck=Pin(10), mosi=Pin(11))
    tft = gc9a01.GC9A01(
        spi,
        240,
        240,
        reset=Pin(14, Pin.OUT),
        cs=Pin(9, Pin.OUT),
        dc=Pin(8, Pin.OUT),
        backlight=Pin(2, Pin.OUT),
        rotation=0,
        buffer_size=32*32*2
    )

    tft.init()
    tft.fill(gc9a01.BLACK)
    time.sleep(1)

    connect_wifi()

    geolocation_data = fetch_geolocation()
    if not geolocation_data:
        print("Failed to fetch geolocation data. Exiting...")
        return

    lat = geolocation_data.get('lat', geolocation_data.get('latitude'))
    lon = geolocation_data.get('lon', geolocation_data.get('longitude'))
    timezone = geolocation_data.get('timezone')

    if None in (lat, lon, timezone):
        print("Invalid coordinates/timezone. Exiting...")
        return

    sync_time(timezone)

    last_weather_fetch = time.time() - 60
    while True:
        current_time = time.time()

        handle_touch(tft)

        if current_time - last_weather_fetch >= 60:
            weather_data = fetch_weather_data(lat, lon)
            if weather_data:
                display_weather_data(tft, weather_data, geolocation_data)
                last_weather_fetch = current_time
            else:
                print("Retrying weather fetch...")
                time.sleep(10)

        time.sleep(0.1)
        gc.collect()

if __name__ == "__main__":
    main()
