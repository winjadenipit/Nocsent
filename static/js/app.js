// Smart Panel UI - JavaScript Logic
// Manages page switching, camera, alarm, and real-time updates

// Global state
let currentPage = 'camera';
let isRecording = false;
let alarmHour = new Date().getHours();
let alarmMinute = new Date().getMinutes();
let alarmSetTime = null;
let brightness = 50;
let volume = 50;

// Initialize socket connection
const socket = io();

// DOM Elements
const pages = {
    camera: document.getElementById('cameraPage'),
    alarm: document.getElementById('alarmPage'),
    video: document.getElementById('videoPage')
};

const navButtons = {
    camera: document.getElementById('btnCamera'),
    alarm: document.getElementById('btnAlarm'),
    video: document.getElementById('btnVideo')
};

const cameraFeed = document.getElementById('cameraFeed');
const cameraPlaceholder = document.getElementById('cameraPlaceholder');
const recIndicator = document.getElementById('recIndicator');
const recordBtn = document.getElementById('recordBtn');

const hourValue = document.getElementById('hourValue');
const minuteValue = document.getElementById('minuteValue');

const brightnessInput = document.getElementById('brightnessInput');
const brightnessThumb = document.getElementById('brightnessThumb');
const volumeInput = document.getElementById('volumeInput');
const volumeThumb = document.getElementById('volumeThumb');

const dateDisplay = document.getElementById('dateDisplay');
const timeDisplay = document.getElementById('timeDisplay');
const tempDisplay = document.getElementById('tempDisplay');

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeUI();
    updateDateTime();
    setInterval(updateDateTime, 1000);

    // Setup event listeners
    setupScrollbars();
    setupRecordButton();

    // Load initial state
    fetchState();
});

// Page Switching
function switchPage(pageName) {
    currentPage = pageName;

    // Hide all pages
    Object.values(pages).forEach(page => {
        page.style.display = 'none';
    });

    // Show selected page
    pages[pageName].style.display = 'block';

    // Update button styles
    Object.values(navButtons).forEach(btn => {
        btn.classList.remove('active');
    });
    navButtons[pageName].classList.add('active');

    // Update video title date if on video page
    if (pageName === 'video') {
        updateVideoTitle();
    }

    // Update server state
    updateServerState({ current_page: pageName });
}

// Recording Control
function setupRecordButton() {
    recordBtn.addEventListener('click', toggleRecording);
}

async function toggleRecording() {
    try {
        const response = await fetch('/api/recording/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();
        isRecording = data.is_recording;

        updateRecordingUI();
    } catch (error) {
        console.error('Error toggling recording:', error);
    }
}

function updateRecordingUI() {
    if (isRecording) {
        recordBtn.classList.add('recording');
        recordBtn.innerHTML = '<span class="btn-icon">⏹</span> Stop';
        recIndicator.style.display = 'flex';
        cameraFeed.classList.add('active');
        cameraFeed.src = '/camera_feed?t=' + new Date().getTime();
        cameraPlaceholder.style.display = 'none';
    } else {
        recordBtn.classList.remove('recording');
        recordBtn.innerHTML = '<span class="btn-icon">⏺</span> Record';
        recIndicator.style.display = 'none';
        cameraFeed.classList.remove('active');
        cameraPlaceholder.style.display = 'block';
    }
}

// Alarm Controls
function adjustAlarm(type, delta) {
    if (type === 'hour') {
        alarmHour = (alarmHour + delta + 24) % 24;
        hourValue.textContent = String(alarmHour).padStart(2, '0');
    } else if (type === 'minute') {
        alarmMinute = (alarmMinute + delta + 60) % 60;
        minuteValue.textContent = String(alarmMinute).padStart(2, '0');
    }

    updateServerState({
        alarm_hour: alarmHour,
        alarm_minute: alarmMinute
    });
}

async function setAlarm() {
    try {
        const response = await fetch('/api/alarm/set', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                hour: alarmHour,
                minute: alarmMinute
            })
        });

        const data = await response.json();
        alarmSetTime = data.alarm_time;

        // Update alarm displays on all pages
        updateAlarmDisplays();

        // Show confirmation
        alert(`✓ Alarm set to ${alarmSetTime}`);
    } catch (error) {
        console.error('Error setting alarm:', error);
    }
}

function updateAlarmDisplays() {
    const displays = [
        document.getElementById('alarmDisplay'),
        document.getElementById('alarmDisplayAlarm'),
        document.getElementById('alarmDisplayVideo')
    ];

    displays.forEach(display => {
        if (alarmSetTime) {
            display.textContent = `Alarm: ${alarmSetTime}`;
            display.style.display = 'block';
        } else {
            display.style.display = 'none';
        }
    });
}

// Scrollbar Controls
function setupScrollbars() {
    brightnessInput.addEventListener('input', function(e) {
        brightness = parseInt(e.target.value);
        updateScrollThumb(brightnessThumb, brightness);
        updateServerState({ brightness: brightness });
    });

    volumeInput.addEventListener('input', function(e) {
        volume = parseInt(e.target.value);
        updateScrollThumb(volumeThumb, volume);
        updateServerState({ volume: volume });
    });
}

function updateScrollThumb(thumb, value) {
    // Invert the value (100 = top, 0 = bottom)
    const invertedValue = 100 - value;
    thumb.style.top = invertedValue + '%';
}

// Date/Time Updates
function updateDateTime() {
    const now = new Date();

    // Format date: MM/DD/YYYY
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const year = now.getFullYear();
    dateDisplay.textContent = `${month}/${day}/${year}`;

    // Format time: HH:MM
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    timeDisplay.textContent = `${hours}:${minutes}`;
}

function updateVideoTitle() {
    const now = new Date();
    const day = String(now.getDate()).padStart(2, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const year = now.getFullYear();
    document.getElementById('videoTitle').textContent = `VIDEO : ${day}/${month}/${year}`;
}

// Server Communication
async function fetchState() {
    try {
        const response = await fetch('/api/state');
        const state = await response.json();

        // Update local state
        isRecording = state.is_recording;
        brightness = state.brightness;
        volume = state.volume;
        alarmHour = state.alarm_hour;
        alarmMinute = state.alarm_minute;
        alarmSetTime = state.alarm_set_time;
        currentPage = state.current_page;

        // Update UI
        updateRecordingUI();
        updateScrollThumb(brightnessThumb, brightness);
        updateScrollThumb(volumeThumb, volume);
        brightnessInput.value = brightness;
        volumeInput.value = volume;
        hourValue.textContent = String(alarmHour).padStart(2, '0');
        minuteValue.textContent = String(alarmMinute).padStart(2, '0');
        updateAlarmDisplays();

        // Switch to current page
        if (currentPage) {
            switchPage(currentPage);
        }
    } catch (error) {
        console.error('Error fetching state:', error);
    }
}

async function updateServerState(updates) {
    try {
        await fetch('/api/state', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updates)
        });
    } catch (error) {
        console.error('Error updating state:', error);
    }
}

// Socket.IO Events
socket.on('connect', function() {
    console.log('Connected to server');
});

socket.on('temperature_update', function(data) {
    tempDisplay.textContent = `${data.temperature.toFixed(1)}°C`;
});

socket.on('disconnect', function() {
    console.log('Disconnected from server');
});

// Initialize UI
function initializeUI() {
    // Set initial alarm values
    hourValue.textContent = String(alarmHour).padStart(2, '0');
    minuteValue.textContent = String(alarmMinute).padStart(2, '0');

    // Set initial scrollbar positions
    updateScrollThumb(brightnessThumb, brightness);
    updateScrollThumb(volumeThumb, volume);
}

// Export functions to global scope for onclick handlers
window.switchPage = switchPage;
window.adjustAlarm = adjustAlarm;
window.setAlarm = setAlarm;
