"""
Enhanced Simulation Module for EagleWings System
===============================================

This module provides battery monitoring, ArUco marker detection, and automatic
charging spot navigation for the EagleWings drone system.

Features:
- Real-time battery monitoring with configurable thresholds
- ArUco marker detection for charging spot identification
- Automatic navigation to charging spots when battery is low
- Integration with main EagleWings system
- Thread-safe operations
- Comprehensive logging and error handling
"""

import cv2
import time
import logging
import threading
import numpy as np
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger('EagleWings.Simulation')

class BatteryStatus(Enum):
    """Battery status enumeration"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    CHARGING = "charging"

@dataclass
class BatteryConfig:
    """Battery configuration settings"""
    warning_threshold: int = 20  # Warning at 20%
    critical_threshold: int = 10  # Critical at 10%
    charging_threshold: int = 5   # Start charging at 5%
    check_interval: float = 5.0   # Check battery every 5 seconds

@dataclass
class ArUcoConfig:
    """ArUco marker configuration"""
    dictionary_type: int = cv2.aruco.DICT_4X4_50
    marker_size: float = 0.05  # 5cm
    search_timeout: float = 30.0  # 30 seconds to find marker
    approach_distance: int = 30  # 30cm approach distance

class EnhancedSimulation:
    """Enhanced simulation module with battery monitoring and ArUco detection"""
    
    def __init__(self, tello_instance, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the enhanced simulation module
        
        Args:
            tello_instance: Tello drone instance
            config: Configuration dictionary
        """
        self.tello = tello_instance
        self.config = config or {}
        
        self.battery_config = BatteryConfig(
            warning_threshold=self.config.get('warning_threshold', 20),
            critical_threshold=self.config.get('critical_threshold', 10),
            charging_threshold=self.config.get('charging_threshold', 5),
            check_interval=self.config.get('check_interval', 5.0)
        )
        
        self.aruco_config = ArUcoConfig(
            dictionary_type=self.config.get('aruco_dict', cv2.aruco.DICT_4X4_50),
            marker_size=self.config.get('marker_size', 0.05),
            search_timeout=self.config.get('search_timeout', 30.0),
            approach_distance=self.config.get('approach_distance', 30)
        )
        
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(self.aruco_config.dictionary_type)
        self.aruco_detector = cv2.aruco.ArucoDetector(
            self.aruco_dict, 
            cv2.aruco.DetectorParameters()
        )
        
        self.is_running = False
        self.is_monitoring = False
        self.current_battery_status = BatteryStatus.NORMAL
        self.last_battery_level = 100
        self.charging_spot_found = False
        self.charging_spot_position = None
        
        self.monitor_thread = None
        self.lock = threading.Lock()
        
        self.battery_callback = None
        self.charging_callback = None
        self.status_callback = None
        
        logger.info("[SIMULATION] Enhanced simulation module initialized")
    
    def set_callbacks(self, battery_callback=None, charging_callback=None, status_callback=None):
        """Set callback functions for events"""
        self.battery_callback = battery_callback
        self.charging_callback = charging_callback
        self.status_callback = status_callback
        logger.info("[SIMULATION] Callbacks configured")
    
    def start_monitoring(self):
        """Start battery monitoring in background thread"""
        if self.is_monitoring:
            logger.warning("[SIMULATION] Battery monitoring already running")
            return False
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._battery_monitor_loop,
            daemon=True,
            name="BatteryMonitor"
        )
        self.monitor_thread.start()
        logger.info("[SIMULATION] Battery monitoring started")
        return True
    
    def stop_monitoring(self):
        """Stop battery monitoring"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        logger.info("[SIMULATION] Battery monitoring stopped")
    
    def _battery_monitor_loop(self):
        """Main battery monitoring loop"""
        while self.is_monitoring:
            try:
                battery_level = self._get_battery_level()
                if battery_level is not None:
                    self._process_battery_level(battery_level)
                
                time.sleep(self.battery_config.check_interval)
            except Exception as e:
                logger.error(f"[SIMULATION] Battery monitoring error: {e}")
                time.sleep(1.0)
    
    def _get_battery_level(self) -> Optional[int]:
        """Get current battery level with error handling"""
        try:
            if hasattr(self.tello, 'get_battery'):
                battery = self.tello.get_battery()
                if battery is not None and 0 <= battery <= 100:
                    logger.debug(f"[SIMULATION] Battery level retrieved: {battery}%")
                    return battery
                else:
                    logger.warning(f"[SIMULATION] Invalid battery level: {battery}")
            else:
                logger.warning("[SIMULATION] Tello instance does not have get_battery method")
        except Exception as e:
            logger.warning(f"[SIMULATION] Battery read error: {e}")
        return None
    
    def _process_battery_level(self, battery_level: int):
        """Process battery level and determine status"""
        with self.lock:
            self.last_battery_level = battery_level
            
            if battery_level <= self.battery_config.charging_threshold:
                new_status = BatteryStatus.CRITICAL
            elif battery_level <= self.battery_config.critical_threshold:
                new_status = BatteryStatus.CRITICAL
            elif battery_level <= self.battery_config.warning_threshold:
                new_status = BatteryStatus.WARNING
            else:
                new_status = BatteryStatus.NORMAL
            
            if new_status != self.current_battery_status:
                old_status = self.current_battery_status
                self.current_battery_status = new_status
                
                logger.info(f"[SIMULATION] Battery status changed: {old_status.value} -> {new_status.value} ({battery_level}%)")
                
                if self.battery_callback:
                    try:
                        self.battery_callback(battery_level, new_status)
                    except Exception as e:
                        logger.error(f"[SIMULATION] Battery callback error: {e}")
                
                if new_status == BatteryStatus.CRITICAL:
                    self._handle_critical_battery()
    
    def _handle_critical_battery(self):
        """Handle critical battery situation"""
        logger.warning("[SIMULATION] Critical battery detected! Initiating charging protocol...")
        
        if self.charging_callback:
            try:
                self.charging_callback(self.last_battery_level)
            except Exception as e:
                logger.error(f"[SIMULATION] Charging callback error: {e}")
        
        self._search_charging_spot()
    
    def _search_charging_spot(self):
        """Search for ArUco marker charging spot"""
        logger.info("[SIMULATION] Starting charging spot search...")
        
        if not hasattr(self.tello, 'get_frame_read'):
            logger.error("[SIMULATION] Tello camera not available for charging spot search")
            return False
        
        try:
            if hasattr(self.tello, 'streamon'):
                self.tello.streamon()
            
            frame_reader = self.tello.get_frame_read()
            start_time = time.time()
            
            while time.time() - start_time < self.aruco_config.search_timeout:
                frame = frame_reader.frame
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                markers_found = self._detect_aruco_markers(frame)
                
                if markers_found:
                    logger.info("[SIMULATION] ArUco marker found! Approaching charging spot...")
                    if self._approach_charging_spot(frame_reader):
                        logger.info("[SIMULATION] Successfully reached charging spot!")
                        return True
                
                if hasattr(self.tello, 'rotate_clockwise'):
                    self.tello.rotate_clockwise(30)
                time.sleep(1.0)
            
            logger.warning("[SIMULATION] Charging spot not found within timeout")
            return False
            
        except Exception as e:
            logger.error(f"[SIMULATION] Charging spot search error: {e}")
            return False
    
    def _detect_aruco_markers(self, frame) -> bool:
        """Detect ArUco markers in frame"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, _ = self.aruco_detector.detectMarkers(gray)
            
            if ids is not None:
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)
                
                for i, corner in enumerate(corners):
                    center = np.mean(corner[0], axis=0)
                    self.charging_spot_position = center
                    self.charging_spot_found = True
                    
                    marker_id = ids[i][0] if ids is not None else "unknown"
                    logger.info(f"[SIMULATION] ArUco marker {marker_id} detected at position {center}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"[SIMULATION] ArUco detection error: {e}")
            return False
    
    def _approach_charging_spot(self, frame_reader) -> bool:
        """Approach the detected charging spot"""
        try:
            approach_distance = self.aruco_config.approach_distance
            
            if hasattr(self.tello, 'move_forward'):
                self.tello.move_forward(approach_distance)
                time.sleep(2.0)  # Allow time for movement
            
            frame = frame_reader.frame
            if frame is not None and self._detect_aruco_markers(frame):
                logger.info("[SIMULATION] Successfully approached charging spot")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"[SIMULATION] Approach charging spot error: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current simulation status"""
        with self.lock:
            return {
                "is_monitoring": self.is_monitoring,
                "battery_level": self.last_battery_level,
                "battery_status": self.current_battery_status.value,
                "charging_spot_found": self.charging_spot_found,
                "charging_spot_position": self.charging_spot_position,
                "config": {
                    "warning_threshold": self.battery_config.warning_threshold,
                    "critical_threshold": self.battery_config.critical_threshold,
                    "charging_threshold": self.battery_config.charging_threshold
                }
            }
    
    def get_battery_info(self) -> Dict[str, Any]:
        """Get detailed battery information"""
        battery_level = self._get_battery_level()
        
        if battery_level is None:
            battery_level = self.last_battery_level
            logger.info(f"[SIMULATION] Using last known battery level: {battery_level}%")
        
        return {
            "current_level": battery_level,
            "status": self.current_battery_status.value,
            "warning_threshold": self.battery_config.warning_threshold,
            "critical_threshold": self.battery_config.critical_threshold,
            "charging_threshold": self.battery_config.charging_threshold,
            "is_low": battery_level is not None and battery_level <= self.battery_config.warning_threshold,
            "is_critical": battery_level is not None and battery_level <= self.battery_config.critical_threshold
        }
    
    def manual_charging_search(self) -> bool:
        """Manually trigger charging spot search"""
        logger.info("[SIMULATION] Manual charging spot search initiated")
        return self._search_charging_spot()
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update configuration settings"""
        with self.lock:
            if 'warning_threshold' in new_config:
                self.battery_config.warning_threshold = new_config['warning_threshold']
            if 'critical_threshold' in new_config:
                self.battery_config.critical_threshold = new_config['critical_threshold']
            if 'charging_threshold' in new_config:
                self.battery_config.charging_threshold = new_config['charging_threshold']
            if 'check_interval' in new_config:
                self.battery_config.check_interval = new_config['check_interval']
            
            logger.info(f"[SIMULATION] Configuration updated: {new_config}")
    
    def reset_charging_spot_status(self):
        """Reset charging spot status after takeoff"""
        with self.lock:
            self.charging_spot_found = False
            self.charging_spot_position = None
            logger.info("[SIMULATION] Charging spot status reset")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_monitoring()
        logger.info("[SIMULATION] Enhanced simulation module cleaned up")


def create_simulation_instance(tello_instance, config: Optional[Dict[str, Any]] = None) -> EnhancedSimulation:
    """Create and configure simulation instance"""
    return EnhancedSimulation(tello_instance, config)

def get_default_config() -> Dict[str, Any]:
    """Get default configuration for simulation module"""
    return {
        "warning_threshold": 20,
        "critical_threshold": 10,
        "charging_threshold": 5,
        "check_interval": 5.0,
        "aruco_dict": cv2.aruco.DICT_4X4_50,
        "marker_size": 0.05,
        "search_timeout": 30.0,
        "approach_distance": 30
    } 