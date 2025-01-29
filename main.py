import time
from machine import Pin, SPI, RTC
import gc9a01
from bitmap import vga1_bold_16x32 as font
import network
import urequests
import gc
import cst816

# Initialize touch
touch = cst816.CST816()

# Wi-Fi credentials
WIFI_SSID = "Your WIFI SSID"
WIFI_PASSWORD = "WIFI Password"

# API URLs
GEOLOCATION_API_URL = "http://ip-api.com/json/"
WORLD_TIME_API_URL = "https://worldtimeapi.org/api/timezone/{timezone}"
WEATHER_API_URL = "http://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=relativehumidity_2m"

# Global variables
temperature_unit = "C"  # Default to Celsius
last_touch_time = None  # For touch message handling

def truncate_to_hour(time_str):
    """Truncate time string to hourly format (YYYY-MM-DDTHH:00)"""
    try:
        date_part, time_part = time_str.split('T', 1)
        time_part = time_part.split('+')[0].split('-')[0]
        hour = time_part.split(':')[0]
        return f"{date_part}T{hour}:00"
    except:
        return time_str

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(15):  # 15-second timeout
            if wlan.isconnected():
                break
            time.sleep(1)
    if wlan.isconnected():
        print("Connected to Wi-Fi")
        print("IP:", wlan.ifconfig()[0])
        return True
    print("Wi-Fi connection failed")
    return False

def fetch_geolocation():
    try:
        print("Fetching geolocation...")
        response = urequests.get(GEOLOCATION_API_URL, timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print("Geolocation error:", e)
        return None
    finally:
        gc.collect()

def sync_time(timezone):
    try:
        print(f"Syncing time for: {timezone}")
        encoded_tz = timezone.replace(" ", "_")
        response = urequests.get(WORLD_TIME_API_URL.format(timezone=encoded_tz), timeout=10)
        if response.status_code == 200:
            time_data = response.json()
            dt_str = time_data['datetime'].split('.')[0]
            year, month, day = map(int, dt_str[:10].split('-'))
            hour, minute, second = map(int, dt_str[11:19].split(':'))
            RTC().datetime((year, month, day, 0, hour, minute, second, 0))
            print("Time synced successfully")
        else:
            print("Time sync failed:", response.status_code)
    except Exception as e:
        print("Time sync error:", e)
    finally:
        gc.collect()

def fetch_weather_data(lat, lon):
    try:
        print(f"Fetching weather for {lat},{lon}")
        response = urequests.get(WEATHER_API_URL.format(lat=lat, lon=lon), timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print("Weather fetch error:", e)
        return None
    finally:
        gc.collect()

def get_weather_condition(code):
    conditions = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
        55: "Dense drizzle", 56: "Freezing drizzle", 57: "Dense freezing drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        66: "Freezing rain", 67: "Heavy freezing rain", 71: "Slight snow",
        73: "Moderate snow", 75: "Heavy snow", 77: "Snow grains",
        80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
        85: "Snow showers", 86: "Heavy snow showers", 95: "Thunderstorm",
        96: "Thunderstorm w/hail", 99: "Severe thunderstorm"
    }
    return conditions.get(code, "Unknown")

def get_weather_image(code):
    images = {
        0: "jpg/clear_sky.jpg", 1: "jpg/mainly_clear.jpg", 
        2: "jpg/partly_cloudy.jpg", 3: "jpg/overcast.jpg",
        45: "jpg/fog.jpg", 48: "jpg/fog.jpg", 51: "jpg/drizzle.jpg",
        53: "jpg/drizzle.jpg", 55: "jpg/drizzle.jpg", 56: "jpg/freezing.jpg",
        57: "jpg/freezing.jpg", 61: "jpg/rain.jpg", 63: "jpg/rain.jpg",
        65: "jpg/rain.jpg", 66: "jpg/freezing.jpg", 67: "jpg/freezing.jpg",
        71: "jpg/snow.jpg", 73: "jpg/snow.jpg", 75: "jpg/snow.jpg",
        77: "jpg/snow.jpg", 80: "jpg/showers.jpg", 81: "jpg/showers.jpg",
        82: "jpg/showers.jpg", 85: "jpg/snow.jpg", 86: "jpg/snow.jpg",
        95: "jpg/thunder.jpg", 96: "jpg/thunder.jpg", 99: "jpg/thunder.jpg"
    }
    return images.get(code, "jpg/unknown.jpg")

def display_weather_data(tft, weather_data, geo_data):
    global temperature_unit
    try:
        tft.fill(gc9a01.BLACK)
        if not weather_data or 'current_weather' not in weather_data:
            return

        current = weather_data['current_weather']
        temp = current['temperature']
        code = current['weathercode']
        current_time = current['time']

        # Process humidity data
        hourly = weather_data.get('hourly', {})
        times = [truncate_to_hour(t) for t in hourly.get('time', [])]
        humidities = hourly.get('relativehumidity_2m', [])
        
        try:
            idx = times.index(truncate_to_hour(current_time))
            humidity = humidities[idx]
        except (ValueError, IndexError):
            humidity = humidities[0] if humidities else "N/A"

        # Temperature conversion and unit
        display_temp = (temp * 9/5) + 32 if temperature_unit == "F" else temp
        unit_char = "F" if temperature_unit == "F" else "C"

        # Display layout calculations
        def center(text):
            return (tft.width() - len(text) * font.WIDTH) // 2

        # Humidity & Temperature display
        hum_text = f"{humidity}%/"
        temp_text = f"{display_temp:.1f}{unit_char}"
        combined_text = hum_text + temp_text
        x_pos = center(combined_text)
        
        tft.text(font, hum_text, x_pos, 45, gc9a01.WHITE)
        temp_x = x_pos + len(hum_text) * font.WIDTH
        tft.text(font, temp_text, temp_x, 45, gc9a01.WHITE)

        # City & Condition
        city = geo_data.get('city', 'Unknown')[:15]
        tft.text(font, city, center(city), 85, gc9a01.WHITE)
        condition = get_weather_condition(code)
        tft.text(font, condition, center(condition), 125, gc9a01.WHITE)

        # Weather image
        tft.jpg(get_weather_image(code), 80, 160, 75)

    except Exception as e:
        print("Display error:", e)
    finally:
        gc.collect()

def handle_touch(tft):
    global temperature_unit, last_touch_time
    if touch.get_touch():
        temperature_unit = "F" if temperature_unit == "C" else "C"
        tft.fill(gc9a01.BLACK)
        tft.text(font, "Changing to", 30, 90, gc9a01.WHITE)
        tft.text(font, f"{temperature_unit} on refresh", 20, 125, gc9a01.WHITE)
        last_touch_time = time.time()
        print(f"Changed unit to {temperature_unit}")

def main():
    global last_touch_time

    # Display initialization
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

    # Network connection
    if not connect_wifi():
        tft.text(font, "Wi-Fi Failed", 40, 100, gc9a01.RED)
        return

    # Get location data
    geo_data = fetch_geolocation()
    if not geo_data:
        tft.text(font, "Geo Failed", 40, 100, gc9a01.RED)
        return

    # Extract coordinates
    lat = geo_data.get('lat') or geo_data.get('latitude')
    lon = geo_data.get('lon') or geo_data.get('longitude')
    tz = geo_data.get('timezone')
    if None in (lat, lon, tz):
        tft.text(font, "Invalid Data", 40, 100, gc9a01.RED)
        return

    # Time synchronization
    sync_time(tz)

    # Main loop
    last_update = 0
    while True:
        try:
            now = time.time()
            
            # Clear touch message after 2 seconds
            if last_touch_time and (now - last_touch_time > 2):
                tft.fill(gc9a01.BLACK)
                last_touch_time = None
                
            # Handle user input
            handle_touch(tft)
            
            # Update weather every 60 seconds
            if now - last_update >= 60:
                if weather := fetch_weather_data(lat, lon):
                    display_weather_data(tft, weather, geo_data)
                    last_update = now
                else:
                    print("Weather update failed")
                
            time.sleep(0.1)
            gc.collect()
            
        except Exception as e:
            print("Main loop error:", e)
            time.sleep(5)

if __name__ == "__main__":
    main()
