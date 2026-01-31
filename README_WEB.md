# Smart Panel UI - Web Version

เวอร์ชันเว็บแอปพลิเคชันของ Smart Panel UI ที่พัฒนาด้วย Flask + HTML/CSS/JavaScript

## 📁 โครงสร้างโปรเจค

```
Lamer/
├── app.py                      # Flask backend server
├── requirements.txt            # Python dependencies
├── templates/
│   └── index.html             # HTML template หลัก
├── static/
│   ├── css/
│   │   └── style.css          # Stylesheet
│   ├── js/
│   │   └── app.js             # JavaScript logic
│   └── images/
│       └── (placeholder images)
└── First.py                   # Tkinter version (original)
```

## 🚀 การติดตั้งและรัน

### 1. ติดตั้ง Dependencies

```bash
# สร้าง virtual environment (แนะนำ)
python -m venv env
source env/bin/activate  # macOS/Linux
# หรือ env\Scripts\activate  # Windows

# ติดตั้ง packages
pip install -r requirements.txt
```

### 2. รันเซิร์ฟเวอร์

```bash
python app.py
```

### 3. เปิดเว็บเบราว์เซอร์

```
http://localhost:5000
```

## 🎯 ฟีเจอร์หลัก

### 📸 Camera Page
- แสดงภาพจากกล้อง real-time
- ปุ่ม Record/Stop สำหรับเริ่ม/หยุดการบันทึก
- สถานะ REC indicator เมื่อกำลังบันทึก
- Scrollbar ควบคุมความสว่างและเสียง

### ⏰ Alarm Page
- Spinbox สำหรับตั้งชั่วโมง (0-23)
- Spinbox สำหรับตั้งนาที (0-59)
- ปุ่ม "Done" เพื่อยืนยันตั้งปลุก
- แสดงเวลาปลุกที่มุมขวาบน

### 🎬 Video Page
- แสดงวิดีโอ playback UI
- ปุ่มควบคุม (Rewind, Play, Pause)
- Progress bar พร้อม scrubber
- แสดงเวลาปัจจุบัน/เวลาทั้งหมด

### 📊 Bottom Bar
- 3 ปุ่มสลับหน้า (Camera, Alarm, Video)
- แสดงวันที่/เวลา real-time
- แสดงอุณหภูมิแบบ real-time (simulated)

## 🔧 เทคโนโลยีที่ใช้

- **Backend**: Flask + Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript (ES6)
- **Camera**: OpenCV (cv2)
- **Real-time Communication**: Socket.IO
- **Styling**: Custom CSS (ตามดีไซน์ mockup)

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | หน้าหลัก |
| `/camera_feed` | GET | Camera streaming (MJPEG) |
| `/api/state` | GET | ดึงข้อมูล state ปัจจุบัน |
| `/api/state` | POST | อัพเดต state |
| `/api/recording/toggle` | POST | เปิด/ปิดการบันทึก |
| `/api/alarm/set` | POST | ตั้งเวลาปลุก |

## 🎨 การปรับแต่ง

### สีและธีม
แก้ไขใน `static/css/style.css` ที่ `:root` variables:

```css
:root {
    --bg-color: #424242;
    --accent-red: #FF3B30;
    --accent-blue: #007AFF;
    /* ... */
}
```

### เพิ่มฟีเจอร์
- แก้ไข `app.py` สำหรับ backend logic
- แก้ไข `static/js/app.js` สำหรับ frontend logic
- แก้ไข `templates/index.html` สำหรับ UI elements

## 🐛 แก้ปัญหา

### กล้องไม่ทำงาน
- ตรวจสอบว่า OpenCV ติดตั้งถูกต้อง
- ตรวจสอบ camera permissions ของระบบ
- ลอง fallback camera index ใน `app.py`

### Socket.IO ไม่เชื่อมต่อ
- ตรวจสอบ CORS settings
- ตรวจสอบ firewall/network settings

## 📝 To-Do / Features ที่จะพัฒนาต่อ

- [ ] บันทึกวิดีโอจริง (ไม่ใช่แค่แสดงภาพ)
- [ ] เล่นวิดีโอย้อนหลัง
- [ ] ระบบ Alarm ที่ทำงานจริง
- [ ] Authentication/Login
- [ ] Mobile responsive improvements
- [ ] PWA support

## 📄 License

สำหรับการเรียนรู้และพัฒนาส่วนบุคคล
