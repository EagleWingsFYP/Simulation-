# 🔋 Enhanced Simulation Module - Battery Monitoring & ArUco Charging

## Overview

The Enhanced Simulation Module provides intelligent battery monitoring and automatic charging spot navigation for the EagleWings drone system. It integrates seamlessly with the main chatbot system to provide real-time battery status, automatic warnings, and ArUco marker-based charging spot detection.

## 🚀 Features

### **Battery Monitoring**
- **Real-time monitoring** with configurable thresholds
- **Automatic warnings** at 20% battery level
- **Critical alerts** at 10% battery level
- **Emergency charging** at 5% battery level
- **Thread-safe operations** with background monitoring

### **ArUco Marker Detection**
- **Automatic charging spot search** using ArUco markers
- **Visual marker detection** with OpenCV
- **Intelligent navigation** to charging spots
- **Configurable search parameters** (timeout, approach distance)
- **Fallback mechanisms** for failed detection

### **Chatbot Integration**
- **Natural language commands** for battery queries
- **Automatic responses** to battery status changes
- **Voice-controlled charging** spot search
- **AIML pattern matching** for intuitive interaction

### **API Endpoints**
- **RESTful API** for programmatic control
- **Real-time status** monitoring
- **Configuration management** via API
- **Manual control** over charging operations

## 📋 Requirements

### **Dependencies**
```bash
pip install opencv-python numpy flask aiml python-dotenv
```

### **Hardware Requirements**
- **Tello Drone** (or compatible drone with battery monitoring)
- **ArUco Markers** (4x4 dictionary, printable)
- **Camera** (drone camera or webcam for marker detection)

### **Software Requirements**
- **Python 3.7+**
- **OpenCV 4.5+**
- **EagleWings System** (main chatbot system)

## 🔧 Installation

### **1. Module Setup**
The simulation module is already integrated into the EagleWings system. No additional installation is required.

### **2. ArUco Marker Setup**
1. **Print ArUco markers** from the provided PDF (`Aruco Marker.pdf`)
2. **Place markers** in designated charging spots
3. **Ensure good lighting** for marker detection
4. **Test marker visibility** from drone camera angles

### **3. Configuration**
The module uses default configuration that can be customized:

```python
# Default configuration
{
    "warning_threshold": 20,      # Warning at 20%
    "critical_threshold": 10,     # Critical at 10%
    "charging_threshold": 5,      # Start charging at 5%
    "check_interval": 5.0,        # Check every 5 seconds
    "aruco_dict": cv2.aruco.DICT_4X4_50,
    "marker_size": 0.05,          # 5cm marker size
    "search_timeout": 30.0,       # 30 seconds to find marker
    "approach_distance": 30       # 30cm approach distance
}
```

## 🎯 Usage

### **1. Starting the System**
```bash
cd EagleWings
python Chatbot.py
```

### **2. Chatbot Commands**
The system responds to natural language commands:

#### **Battery Status**
- `"Check battery"` - Get current battery level
- `"Battery status"` - Detailed battery information
- `"How much battery"` - Quick battery check

#### **Charging Control**
- `"Find charging spot"` - Search for ArUco markers
- `"Go to charging"` - Navigate to charging spot
- `"Search charging"` - Manual charging spot search

#### **Monitoring Control**
- `"Start battery monitoring"` - Enable automatic monitoring
- `"Stop battery monitoring"` - Disable monitoring
- `"Battery info"` - Get configuration details

#### **Emergency Commands**
- `"Emergency landing"` - Perform emergency landing
- `"Safe landing"` - Land safely due to battery concerns

### **3. API Usage**

#### **Start Battery Monitoring**
```bash
curl -X POST http://localhost:5000/start_simulation \
  -H "Content-Type: application/json"
```

#### **Get Battery Status**
```bash
curl http://localhost:5000/battery_status
```

#### **Find Charging Spot**
```bash
curl -X POST http://localhost:5000/find_charging_spot \
  -H "Content-Type: application/json"
```

#### **Update Configuration**
```bash
curl -X POST http://localhost:5000/update_simulation_config \
  -H "Content-Type: application/json" \
  -d '{"warning_threshold": 25, "critical_threshold": 15}'
```

## 🔍 How It Works

### **1. Battery Monitoring Loop**
```python
# Background thread continuously monitors battery
while monitoring_active:
    battery_level = get_battery_level()
    process_battery_level(battery_level)
    time.sleep(check_interval)
```

### **2. Status Classification**
- **Normal**: > 20% - No action required
- **Warning**: 10-20% - User notification
- **Critical**: 5-10% - Automatic charging search
- **Emergency**: < 5% - Immediate action required

### **3. ArUco Detection Process**
```python
# 1. Capture frame from drone camera
frame = drone.get_frame_read().frame

# 2. Convert to grayscale
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# 3. Detect ArUco markers
corners, ids, _ = aruco_detector.detectMarkers(gray)

# 4. If markers found, navigate to them
if ids is not None:
    navigate_to_marker(corners[0])
```

### **4. Navigation Algorithm**
1. **Rotate** to search for markers
2. **Detect** marker position in frame
3. **Calculate** distance and angle
4. **Move** toward marker
5. **Land** on charging spot

## 📊 API Reference

### **Endpoints**

#### **POST /start_simulation**
Start battery monitoring and simulation module.

**Response:**
```json
{
  "message": "✅ Battery monitoring started successfully!"
}
```

#### **POST /stop_simulation**
Stop battery monitoring and simulation module.

**Response:**
```json
{
  "message": "✅ Battery monitoring stopped successfully!"
}
```

#### **GET /battery_status**
Get current battery status and information.

**Response:**
```json
{
  "current_level": 45,
  "status": "normal",
  "warning_threshold": 20,
  "critical_threshold": 10,
  "charging_threshold": 5,
  "is_low": false,
  "is_critical": false
}
```

#### **GET /simulation_status**
Get simulation module status.

**Response:**
```json
{
  "is_monitoring": true,
  "battery_level": 45,
  "battery_status": "normal",
  "charging_spot_found": false,
  "charging_spot_position": null,
  "config": {
    "warning_threshold": 20,
    "critical_threshold": 10,
    "charging_threshold": 5
  }
}
```

#### **POST /find_charging_spot**
Manually trigger charging spot search.

**Response:**
```json
{
  "message": "✅ Charging spot found and approached successfully!"
}
```

#### **POST /update_simulation_config**
Update simulation module configuration.

**Request Body:**
```json
{
  "warning_threshold": 25,
  "critical_threshold": 15,
  "charging_threshold": 8,
  "check_interval": 3.0
}
```

## 🧪 Testing

### **Run Integration Tests**
```bash
cd EagleWings
python test_simulation_integration.py
```

### **Expected Test Output**
```
🚀 Starting Simulation Module Integration Tests...
==================================================
🧪 Testing Module Import...
✅ Simulation module imported successfully
------------------------------
🧪 Testing Configuration...
✅ Default config: {...}
------------------------------
🧪 Testing AIML Integration...
✅ Battery control AIML file loaded
------------------------------
📊 Test Results: 6 passed, 0 failed
🎉 All tests passed! Simulation module integration is working correctly.
```

## 🔧 Configuration

### **Environment Variables**
```bash
# Battery thresholds (optional - defaults used if not set)
SIMULATION_WARNING_THRESHOLD=20
SIMULATION_CRITICAL_THRESHOLD=10
SIMULATION_CHARGING_THRESHOLD=5
SIMULATION_CHECK_INTERVAL=5.0
```

### **Custom Configuration**
```python
from modules.simulation.enhanced_simulation import get_default_config

# Get default config and modify
config = get_default_config()
config.update({
    "warning_threshold": 25,
    "critical_threshold": 15,
    "charging_threshold": 8
})
```

## 🚨 Troubleshooting

### **Common Issues**

#### **1. Module Import Error**
```
❌ Failed to import simulation module: No module named 'enhanced_simulation'
```
**Solution**: Ensure you're running from the EagleWings directory and all dependencies are installed.

#### **2. ArUco Detection Fails**
```
❌ Charging spot search failed. Please check ArUco markers.
```
**Solutions**:
- Check marker visibility and lighting
- Ensure markers are from the correct dictionary (4x4_50)
- Verify marker size and distance
- Test with different camera angles

#### **3. Battery Monitoring Not Working**
```
⚠️ Battery monitoring requested but simulation module not available
```
**Solution**: Check if the simulation module initialized properly in the logs.

#### **4. Camera Access Issues**
```
❌ Tello camera not available for charging spot search
```
**Solution**: Ensure drone is connected and video stream is active.

### **Debug Mode**
Enable detailed logging by setting the log level:
```python
import logging
logging.getLogger('EagleWings.Simulation').setLevel(logging.DEBUG)
```

## 🔮 Future Enhancements

### **Planned Features**
- **Multiple marker support** for complex charging stations
- **Battery prediction** using machine learning
- **Dynamic threshold adjustment** based on usage patterns
- **Wireless charging** integration
- **Multi-drone coordination** for charging

### **Advanced Configuration**
- **Custom ArUco dictionaries** support
- **3D marker positioning** for precise navigation
- **Charging station mapping** and memory
- **Weather-aware** charging decisions

## 📞 Support

For issues or questions:
1. Check the logs in `eaglewings.log`
2. Run `python test_simulation_integration.py` to verify system health
3. Review this documentation for common solutions
4. Check the main EagleWings README for system-wide issues

**Author**: Abdullah Bajwa  
**Version**: 1.0.0 (Enhanced Integration)  
**Last Updated**: 2024 