import time
from machine import Pin, SPI, RTC
import gc9a01
from bitmap import vga1_bold_16x32 as font
import network
import urequests
import gc
import cst816  # Import the touch module
import ntptime  # Import the NTP time module

# Initialize touch (assuming the library handles I2C internally)
touch = cst816.CST816()

# Wi-Fi credentials
WIFI_SSID = "Your SSID"
WIFI_PASSWORD = "Your Password"

# API URLs
GEOLOCATION_API_URL = "http://ip-api.com/json/"
WEATHER_API_URL = "http://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relativehumidity_2m"

# Global variable to track temperature unit
temperature_unit = "C"  # Default to Celsius

# Connect to Wi-Fi
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

# Synchronize time with NTP server
def sync_time():
    try:
        ntptime.settime()
        print("Time synchronized with NTP server")
        
        # Define the time zone offset (in seconds)
        # For example, UTC+2 (e.g., Central European Summer Time)
        timezone_offset = -6 * 3600  # 2 hours * 3600 seconds per hour
        
        # Get the current time in seconds since the epoch
        current_time = time.time()
        
        # Adjust the time for the time zone
        adjusted_time = current_time + timezone_offset
        
        # Set the adjusted time
        time.localtime(adjusted_time)
        
        print(f"Adjusted time for time zone: {time.localtime(adjusted_time)}")
    except Exception as e:
        print("Error synchronizing time with NTP server:", e)

# Fetch geolocation data
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

# Fetch weather data
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

# Get weather condition based on weather code
def get_weather_condition(weather_code):
    weather_conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return weather_conditions.get(weather_code, "Unknown")

# Get image file name based on weather code
def get_weather_image(weather_code):
    weather_images = {
        0: "jpg/clear_sky.jpg",
        1: "jpg/mainly_clear.jpg",
        2: "jpg/partly_cloudy.jpg",
        3: "jpg/overcast.jpg",
        45: "jpg/fog.jpg",
        48: "jpg/fog.jpg",
        51: "jpg/light_drizzle.jpg",
        53: "jpg/moderate_drizzle.jpg",
        55: "jpg/dense_drizzle.jpg",
        56: "jpg/freezing_drizzle.jpg",
        57: "jpg/freezing_drizzle.jpg",
        61: "jpg/light_rain.jpg",
        63: "jpg/moderate_drizzle.jpg",
        65: "jpg/dense_drizzle.jpg",
        66: "jpg/freezing_rain.jpg",
        67: "jpg/freezing_rain.jpg",
        71: "jpg/light_snow.jpg",
        73: "jpg/moderate_snow.jpg",
        75: "jpg/heavy_snow.jpg",
        77: "jpg/snow_grains.jpg",
        80: "jpg/light_drizzle.jpg",
        81: "jpg/moderate_drizzle.jpg",
        82: "jpg/dense_drizzle.jpg",
        85: "jpg/light_snow.jpg",
        86: "jpg/heavy_snow.jpg",
        95: "jpg/thunderstorm.jpg",
        96: "jpg/thunderstorm_hail.jpg",
        99: "jpg/thunderstorm_heavyhail.jpg"
    }
    return weather_images.get(weather_code, "jpg/unknown.jpg")

# Convert temperature between Celsius and Fahrenheit
def convert_temperature(temp, unit):
    if unit == "F":
        return (temp * 9/5) + 32  # Convert to Fahrenheit
    return temp  # Default to Celsius

def display_weather_data(tft, weather_data, geolocation_data):
    global temperature_unit
    try:
        tft.fill(gc9a01.BLACK)  # Clear the screen

        if weather_data and 'current_weather' in weather_data:
            current_weather = weather_data['current_weather']
            temperature = current_weather['temperature']
            weather_code = current_weather['weathercode']

            # Get the current time from the API response
            current_time = current_weather['time']
            print(f"Current Time: {current_time}")  # Debug print

            # Find the corresponding humidity value from the hourly data
            hourly_data = weather_data.get('hourly', {})
            time_list = hourly_data.get('time', [])
            humidity_list = hourly_data.get('relativehumidity_2m', [])

            print(f"Time List: {time_list}")  # Debug print
            print(f"Humidity List: {humidity_list}")  # Debug print

            # Find the index of the current time in the time list
            try:
                time_index = time_list.index(current_time)
                humidity = humidity_list[time_index]
            except (ValueError, IndexError):
                print("Time not found in hourly data or index out of range")  # Debug print
                # Fallback: Find the closest time match
                closest_index = min(range(len(time_list)), key=lambda i: abs(time_list[i] - current_time))
                humidity = humidity_list[closest_index]
                print(f"Using closest time match: {time_list[closest_index]} with humidity {humidity}%")

            # Convert temperature based on the current unit
            display_temp = convert_temperature(temperature, temperature_unit)

            # Calculate the X position to center the text
            def center_x(text):
                text_width = len(text) * font.WIDTH
                return (tft.width() - text_width) // 2

            # Display humidity and temperature
            humidity_text = f"{humidity}%/"
            temp_text = f"{display_temp:.1f}"
            combined_text = f"{humidity_text}{temp_text}"
            combined_x = center_x(combined_text)
            tft.text(font, humidity_text, combined_x, 45, gc9a01.WHITE, gc9a01.BLACK)
            
            # Calculate the position for the temperature text
            temp_x = combined_x + len(humidity_text) * font.WIDTH
            tft.text(font, temp_text, temp_x, 45, gc9a01.WHITE, gc9a01.BLACK)

            # Display the correct unit image right after the temperature text
            unit_image = "jpg/celsius.jpg" if temperature_unit == "C" else "jpg/fahrenheit.jpg"
            unit_x = temp_x + len(temp_text) * font.WIDTH
            tft.jpg(unit_image, unit_x, 45, 30)

            # Extract city name from geolocation data
            city_name = geolocation_data.get('city', 'Unknown City')

            # Display City
            city_text = city_name
            city_x = center_x(city_text)
            tft.text(font, city_text, city_x, 85, gc9a01.WHITE, gc9a01.BLACK)

            # Display weather condition based on weather code
            weather_condition = get_weather_condition(weather_code)
            condition_x = center_x(weather_condition)
            tft.text(font, weather_condition, condition_x, 125, gc9a01.WHITE, gc9a01.BLACK)

            # Display weather image based on weather code
            image_file = get_weather_image(weather_code)
            tft.jpg(image_file, 80, 160, 75)

    except Exception as e:
        print("Error displaying weather data:", e)
    finally:
        gc.collect()
# Handle touch events
def handle_touch(tft):
    global temperature_unit
    if touch.get_touch():  # Check if the screen is touched
        print("Touch detected!")  # Debug print
        
        # Determine the new unit and the message to display
        new_unit = "F" if temperature_unit == "C" else "C"
        message = f"Changing to {new_unit}"
        message2 =f"in 60 sec"
        
        # Display the message
        tft.fill(gc9a01.BLACK)  # Clear the screen
        tft.text(font, message, 10, 100, gc9a01.WHITE, gc9a01.BLACK)
        tft.text(font, message2, 50, 135, gc9a01.WHITE, gc9a01.BLACK)
        
        # Wait for 60 seconds
        time.sleep(60)
        
        # Change the temperature unit
        temperature_unit = new_unit
        print(f"Switched to {temperature_unit}")
        
        # Clear the message
        tft.fill(gc9a01.BLACK)

def main():
    global temperature_unit

    # Initialize display
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

    # Connect to Wi-Fi
    connect_wifi()

    # Synchronize time with NTP server
    sync_time()

    # Fetch geolocation data
    geolocation_data = fetch_geolocation()
    if not geolocation_data:
        print("Failed to fetch geolocation data. Exiting...")
        return

    lat = geolocation_data.get('lat', geolocation_data.get('latitude'))
    lon = geolocation_data.get('lon', geolocation_data.get('longitude'))

    if lat is None or lon is None:
        print("Invalid latitude or longitude. Exiting...")
        return

    # Main loop
    last_weather_fetch = time.time() - 60  # Force initial fetch
    while True:
        current_time = time.time()

        # Handle touch events more frequently
        handle_touch(tft)

        # Fetch weather data every 60 seconds
        if current_time - last_weather_fetch >= 60:
            weather_data = fetch_weather_data(lat, lon)
            if not weather_data:
                print("No weather data fetched. Retrying in 10 seconds...")
                time.sleep(10)
                continue

            # Display the current weather
            display_weather_data(tft, weather_data, geolocation_data)
            last_weather_fetch = current_time

        # Short sleep to allow for frequent touch checks
        time.sleep(0.1)  # Check for touch every 100ms

        gc.collect()  # Run garbage collection periodically in the main loop

# Run the program
if __name__ == "__main__":
    main()