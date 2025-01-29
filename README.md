# Desktop Weather Display for Waveshare ESP32-S3-Touch-LCD-1.28

This project is a desktop weather display designed for the **Waveshare ESP32-S3-Touch-LCD-1.28** board. It fetches real-time weather data, geolocation, and displays it on the screen. The display includes temperature, humidity, weather conditions, and a visual representation of the weather. The touchscreen functionality allows users to toggle between Celsius and Fahrenheit temperature units.

---

## Features

- **Real-Time Weather Data**: Fetches current weather data from the Open-Meteo API.
- **Geolocation**: Automatically detects your location using the IP-API service.
- **Touchscreen Support**: Toggle between Celsius and Fahrenheit with a simple touch.
- **NTP Time Synchronization**: Automatically syncs the device's time with an NTP server.
- **Weather Icons**: Displays weather conditions with corresponding icons.
- **Wi-Fi Connectivity**: Connects to your Wi-Fi network to fetch data.

---

## Hardware Requirements

- **Waveshare ESP32-S3-Touch-LCD-1.28** board.
- Micro-USB cable for power and programming.
- Wi-Fi network with internet access.

---

## Software Requirements

- **MicroPython** installed on the ESP32-S3 board.
- Required libraries:
  - `gc9a01` (for the display driver).
  - `cst816` (for touchscreen support).
  - `urequests` (for HTTP requests).
  - `ntptime` (for time synchronization).
- Weather icons in JPEG format (stored in a `jpg` directory).

---

## Setup Instructions

1. **Install MicroPython** on the ESP32-S3 board if not already installed.
2. **Upload Required Libraries**: Ensure the following libraries are uploaded to your board:
   - `gc9a01.py`
   - `cst816.py`
   - `bitmap.py` (for font rendering).
   - Weather icons in the `jpg` directory.
3. **Update Wi-Fi Credentials**: Replace `Your SSID` and `Your Password` in the script with your Wi-Fi credentials.
4. **Upload the Script**: Upload the provided Python script to your board.
5. **Run the Script**: Execute the script on your board.

---

## Usage

- **Power On**: Once powered, the device will connect to Wi-Fi, fetch your location, and display the current weather.
- **Touchscreen**: Tap the screen to toggle between Celsius and Fahrenheit. The change will take effect after 60 seconds.
- **Automatic Updates**: The weather data is refreshed every 60 seconds.

---

## API Keys and Services

This project uses the following free APIs:
- **Open-Meteo API**: For weather data.
- **IP-API**: For geolocation.

No API keys are required for these services.

---

## Customization

- **Time Zone**: Adjust the `timezone_offset` variable in the `sync_time()` function to match your time zone.
- **Weather Icons**: Replace the icons in the `jpg` directory with your own images. Ensure the filenames match the weather codes in the `get_weather_image()` function.
- **Fonts**: Modify the `bitmap.py` file to use a different font.

---

## Troubleshooting

- **Wi-Fi Connection Issues**: Ensure the Wi-Fi credentials are correct and the network is within range.
- **No Weather Data**: Check your internet connection and ensure the APIs are accessible.
- **Touchscreen Not Responding**: Verify the `cst816` library is correctly installed and the touchscreen is properly connected.

---

## License

This project is open-source and available under the MIT License. Feel free to modify and distribute it as needed.

---

## Acknowledgments

- **Waveshare** for the ESP32-S3-Touch-LCD-1.28 board.
- **Open-Meteo** and **IP-API** for providing free weather and geolocation services.
- The MicroPython community for their contributions to embedded Python development.

---

## Contributing

Contributions are welcome! If you have suggestions, improvements, or bug fixes, please open an issue or submit a pull request.

---

Enjoy your desktop weather display! 🌤️
