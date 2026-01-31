"""
Smart Panel Web Application
Flask backend with camera streaming support
"""

from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO
import cv2
import datetime
import time
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart-panel-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
state = {
    'current_page': 'camera',
    'is_recording': False,
    'brightness': 50,
    'volume': 50,
    'alarm_hour': datetime.datetime.now().hour,
    'alarm_minute': datetime.datetime.now().minute,
    'alarm_set_time': None,
    'temperature': 20.0
}

# Camera setup
camera = None
camera_lock = threading.Lock()

def init_camera():
    """Initialize camera with fallback support"""
    global camera
    if camera is not None:
        return camera

    camera_configs = [
        (0, cv2.CAP_AVFOUNDATION),
        (1, cv2.CAP_AVFOUNDATION),
        (0, cv2.CAP_ANY),
        (1, cv2.CAP_ANY),
    ]

    for cam_index, backend in camera_configs:
        try:
            cap = cv2.VideoCapture(cam_index, backend)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                ret, frame = cap.read()
                if ret and frame is not None:
                    camera = cap
                    print(f"✓ Camera {cam_index} initialized")
                    return camera
                cap.release()
        except Exception as e:
            print(f"✗ Camera {cam_index} failed: {e}")

    print("⚠ No camera available")
    return None

def get_camera_frame():
    """Get current camera frame as JPEG"""
    global camera
    with camera_lock:
        if camera is None or not state['is_recording']:
            # Return placeholder image
            return None

        ret, frame = camera.read()
        if not ret:
            return None

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ret:
            return buffer.tobytes()
    return None

def generate_camera_stream():
    """Generate camera frames for streaming"""
    while True:
        frame = get_camera_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            # Send placeholder or wait
            time.sleep(0.1)

# Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/camera_feed')
def camera_feed():
    """Video streaming route"""
    return Response(generate_camera_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/state', methods=['GET'])
def get_state():
    """Get current application state"""
    return jsonify(state)

@app.route('/api/state', methods=['POST'])
def update_state():
    """Update application state"""
    data = request.json
    for key in data:
        if key in state:
            state[key] = data[key]
    return jsonify({'success': True, 'state': state})

@app.route('/api/recording/toggle', methods=['POST'])
def toggle_recording():
    """Toggle recording state"""
    state['is_recording'] = not state['is_recording']
    if state['is_recording']:
        init_camera()
    return jsonify({'success': True, 'is_recording': state['is_recording']})

@app.route('/api/alarm/set', methods=['POST'])
def set_alarm():
    """Set alarm time"""
    data = request.json
    state['alarm_hour'] = data.get('hour', state['alarm_hour'])
    state['alarm_minute'] = data.get('minute', state['alarm_minute'])
    state['alarm_set_time'] = f"{state['alarm_hour']:02d}:{state['alarm_minute']:02d}"
    return jsonify({'success': True, 'alarm_time': state['alarm_set_time']})

# Background task for temperature simulation
def update_temperature():
    """Simulate temperature updates"""
    while True:
        state['temperature'] = 20.0 + 0.8 * (time.time() % 60) / 60.0
        socketio.emit('temperature_update', {'temperature': state['temperature']})
        time.sleep(1)

if __name__ == '__main__':
    # Start temperature update thread
    temp_thread = threading.Thread(target=update_temperature, daemon=True)
    temp_thread.start()

    # Run Flask app
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
