# import lybraries
import time
from threading import Thread
import database
import detection
import alerts
import os
import platform
from datetime import datetime

conn = database.init_db()
picam = detection.init_camera()

def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def main_loop():
    clear_screen()
  
    while True:
        # Check light (stub: time-based)
        now_hour = datetime.now().hour
        low_light = now_hour < 7 or now_hour > 19
        
        frame = detection.capture_frame(picam, low_light)
        plate, car_type, color = detection.extract_plate_number(frame)
        
        if plate:
            vehicle = database.search_existing_plate(conn, plate)
            if not vehicle:
                vehicle_id = database.add_new_plate(conn, plate, car_type, color)
            else:
                vehicle_id = vehicle['id']
            
            entry_time = datetime.now()
            database.log_vehicle_entry(conn, vehicle_id, entry_time)
            alerts.check_watchlist(conn, plate)
        
        time.sleep(1)  # Process every second for Pi 4 efficiency

if __name__ == '__main__':
    Thread(target=main_loop).start()
    print("Monitoring started. Run web_app.py for dashboard.")
