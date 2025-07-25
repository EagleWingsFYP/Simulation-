import cv2
import time
import logging
from djitellopy import Tello, TelloException

# --- Logger Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)

# --- ArUco Detector Setup ---
ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
DETECTOR = cv2.aruco.ArucoDetector(ARUCO_DICT, cv2.aruco.DetectorParameters())

# --- Safe Command Wrapper ---
def safe_command(command_func, *args, retries=3, delay=1, description="command"):
    for attempt in range(1, retries + 1):
        try:
            command_func(*args)
            logging.info(f"{description.capitalize()} successful.")
            return True
        except TelloException as e:
            logging.warning(f"Failed {description} attempt {attempt}/{retries}: {e}")
            time.sleep(delay)
    logging.error(f"Could not complete {description} after {retries} attempts.")
    return False

# --- Safe Battery Retrieval ---
def get_battery_level(drone, retries=3, delay=1):
    for attempt in range(1, retries + 1):
        try:
            battery = drone.get_battery()
            logging.info(f"Battery level: {battery}%")
            return battery
        except TelloException as e:
            logging.warning(f"Battery check failed attempt {attempt}/{retries}: {e}")
            time.sleep(delay)
    logging.error("Failed to retrieve battery level after retries.")
    return None

# --- Main Drone Logic ---
def main():
    logging.info("Connecting to Tello drone...")
    drone = Tello()

    try:
        drone.connect()
        battery = get_battery_level(drone)
        if battery is None:
            logging.error("Aborting mission due to battery read failure.")
            return

        if not safe_command(drone.streamon, description="start video stream"):
            return

        frame_reader = drone.get_frame_read()

        if not safe_command(drone.takeoff, description="takeoff"):
            return

        logging.info("Stabilizing drone...")
        time.sleep(2)

        battery = get_battery_level(drone)
        if battery is None:
            logging.error("Could not verify battery level. Proceeding to land.")
            safe_command(drone.land, description="emergency landing")
            return

        if battery >= 45:
            logging.info("Battery level sufficient. Proceeding to land safely.")
            safe_command(drone.land, description="landing")
        else:
            logging.warning("Battery low. Initiating ArUco marker search before landing.")
            found = False
            attempts = 0

            while not found and attempts < 12:
                frame = frame_reader.frame
                if frame is None:
                    logging.warning("No frame received from camera.")
                    time.sleep(0.5)
                    attempts += 1
                    continue

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                corners, ids, _ = DETECTOR.detectMarkers(gray)

                display_frame = frame.copy()
                if ids is not None:
                    cv2.aruco.drawDetectedMarkers(display_frame, corners, ids)

                cv2.imshow("Tello Camera Feed", display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logging.info("Manual quit detected. Landing...")
                    safe_command(drone.land, description="manual landing")
                    break

                if ids is not None:
                    logging.info("ArUco marker detected. Approaching marker...")
                    if safe_command(drone.move_forward, 30, description="move forward"):
                        time.sleep(2)
                        logging.info("Reached marker. Landing now.")
                        safe_command(drone.land, description="landing on marker")
                    else:
                        logging.warning("Failed to approach marker.")
                    found = True
                else:
                    logging.info(f"Marker not found. Rotating... ({attempts + 1}/12)")
                    safe_command(drone.rotate_clockwise, 30, description="rotate clockwise")
                    time.sleep(1)

                attempts += 1

            if not found:
                logging.warning("Marker not found after 12 attempts. Landing as fallback.")
                safe_command(drone.land, description="fallback landing")

        # --- Cleanup ---
        safe_command(drone.streamoff, description="stop video stream")
        cv2.destroyAllWindows()
        drone.end()
        logging.info("Drone mission completed successfully.")

    except KeyboardInterrupt:
        logging.info("Keyboard interrupt detected. Landing and shutting down...")
        safe_command(drone.land, description="emergency landing")
        safe_command(drone.streamoff, description="stop video stream")
        cv2.destroyAllWindows()
        drone.end()

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        safe_command(drone.land, description="emergency landing")
        safe_command(drone.streamoff, description="stop video stream")
        cv2.destroyAllWindows()
        drone.end()

# --- Entry Point ---
if __name__ == "__main__":
    main()
