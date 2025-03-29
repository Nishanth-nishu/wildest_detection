// Initialize Socket.IO connection
const socket = io();

// Global variables
let detectionChart = null;
let classChart = null;
let timeChart = null;
let heatmapChart = null;
let currentModalItem = null;
let isRecording = false;

// DOM Elements
const videoFeed = document.getElementById('videoFeed');
const connectionStatus = document.getElementById('connectionStatus');
const totalDetections = document.getElementById('totalDetections');
const currentFps = document.getElementById('currentFps');
const cpuUsage = document.getElementById('cpuUsage');
const temperature = document.getElementById('temperature');
const recentDetections = document.getElementById('recentDetections');
const detectionsTable = document.getElementById('detectionsTable');
const snapshotsGallery = document.getElementById('snapshotsGallery');
const recordingsContainer = document.getElementById('recordingsContainer');
const modalImage = document.getElementById('modalImage');
const modalVideo = document.getElementById('modalVideo');
const toggleRecording = document.getElementById('toggleRecording');

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize detection activity chart
    const detectionCtx = document.getElementById('detectionChart').getContext('2d');
    detectionChart = new Chart(detectionCtx, {
        type: 'line',
        data: {
            labels: generateTimeLabels(24),
            datasets: [{
                label: 'Detections',
                data: generateEmptyData(24),
                borderColor: '#4361ee',
                backgroundColor: 'rgba(67, 97, 238, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
   
    // Initialize class distribution chart
    const classCtx = document.getElementById('classChart').getContext('2d');
    classChart = new Chart(classCtx, {
        type: 'pie',
        data: {
            labels: ['Person', 'Car', 'Dog', 'Other'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: [
                    '#4361ee',
                    '#4895ef',
                    '#4cc9f0',
                    '#f72585'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
   
    // Initialize time distribution chart
    const timeCtx = document.getElementById('timeChart').getContext('2d');
    timeChart = new Chart(timeCtx, {
        type: 'bar',
        data: {
            labels: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00'],
            datasets: [{
                label: 'Detections by Time',
                data: [0, 0, 0, 0, 0, 0, 0, 0],
                backgroundColor: '#4895ef'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
   
    // Initialize heatmap chart (simplified representation)
    const heatmapCtx = document.getElementById('heatmapChart').getContext('2d');
    heatmapChart = new Chart(heatmapCtx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Detection Density',
                data: [],
                backgroundColor: 'rgba(67, 97, 238, 0.6)',
                pointRadius: 8,
                pointHoverRadius: 12
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    min: 0,
                    max: 16,
                    ticks: {
                        display: false
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    min: 0,
                    max: 12,
                    ticks: {
                        display: false
                    },
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Detections: ${context.raw.v}`;
                        }
                    }
                }
            }
        }
    });
   
    // Load initial data
    loadInitialData();
   
    // Set up event listeners
    setupEventListeners();
});

// Socket.IO event handlers
socket.on('connect', function() {
    connectionStatus.textContent = 'Connected';
    connectionStatus.className = 'badge bg-success';
});

socket.on('disconnect', function() {
    connectionStatus.textContent = 'Disconnected';
    connectionStatus.className = 'badge bg-danger';
});

socket.on('stats_update', function(stats) {
    updateStats(stats);
});

socket.on('detection_alert', function(detections) {
    updateDetections(detections);
});

socket.on('frame_update', function(data) {
    // Update any real-time frame data here
    // This is an alternative to the video_feed endpoint
});

// Utility functions
function generateTimeLabels(hours) {
    const labels = [];
    const now = new Date();
    for (let i = hours - 1; i >= 0; i--) {
        const time = new Date(now);
        time.setHours(now.getHours() - i);
        labels.push(time.getHours() + ':00');
    }
    return labels;
}

function generateEmptyData(count) {
    return Array(count).fill(0);
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
}

// Data loading functions
function loadInitialData() {
    // Load stats
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            updateStats(data);
        })
        .catch(error => console.error('Error loading stats:', error));
   
    // Load recent detections
    fetch('/api/detections')
        .then(response => response.json())
        .then(data => {
            updateDetectionsList(data);
            updateDetectionsTable(data);
            updateAnalyticsCharts(data);
        })
        .catch(error => console.error('Error loading detections:', error));
   
    // Load snapshots
    loadSnapshots();
   
    // Load recordings
    loadRecordings();
   
    // Load camera settings
    fetch('/api/camera_settings')
        .then(response => response.json())
        .then(data => {
            document.getElementById('cameraResolution').value = data.resolution;
            document.getElementById('cameraFps').value = data.fps;
            document.getElementById('cameraBrightness').value = data.brightness;
            document.getElementById('cameraContrast').value = data.contrast;
        })
        .catch(error => console.error('Error loading camera settings:', error));
   
    // Load alert settings
    fetch('/api/alert_settings')
        .then(response => response.json())
        .then(data => {
            document.getElementById('enableAlerts').checked = data.enabled;
            document.getElementById('alertEmail').value = data.email;
            document.getElementById('alertConfidenceThreshold').value = data.confidence_threshold;
            document.getElementById('alertConfidenceValue').textContent = data.confidence_threshold;
            document.getElementById('alertCooldown').value = data.cooldown_period;
           
            if (data.classes_to_alert.includes('person')) {
                document.getElementById('alertPersonCheck').checked = true;
            }
            if (data.classes_to_alert.includes('car')) {
                document.getElementById('alertCarCheck').checked = true;
            }
            if (data.classes_to_alert.includes('dog')) {
                document.getElementById('alertDogCheck').checked = true;
            }
        })
        .catch(error => console.error('Error loading alert settings:', error));
   
    // Load recording settings
    fetch('/api/recording_settings')
        .then(response => response.json())
        .then(data => {
            document.getElementById('enableRecording').checked = data.enabled;
           
            if (data.continuous) {
                document.getElementById('continuousMode').checked = true;
            } else {
                document.getElementById('motionMode').checked = true;
            }
           
            document.getElementById('preRecordSeconds').value = data.pre_record_seconds;
            document.getElementById('postRecordSeconds').value = data.post_record_seconds;
            document.getElementById('maxRecordingDuration').value = data.max_duration;
           
            isRecording = data.is_recording;
            updateRecordingButton();
        })
        .catch(error => console.error('Error loading recording settings:', error));
}

function loadSnapshots() {
    fetch('/api/snapshots')
        .then(response => response.json())
        .then(data => {
            updateSnapshotsGallery(data);
        })
        .catch(error => console.error('Error loading snapshots:', error));
}

function loadRecordings() {
    fetch('/api/recordings')
        .then(response => response.json())
        .then(data => {
            updateRecordingsContainer(data);
        })
        .catch(error => console.error('Error loading recordings:', error));
}

// UI update functions
function updateStats(stats) {
    totalDetections.textContent = stats.total_detections;
    currentFps.textContent = stats.fps.toFixed(1);
    cpuUsage.textContent = stats.cpu_usage.toFixed(1) + '%';
    temperature.textContent = stats.temperature.toFixed(1) + '°C';
   
// ... (continuing from the previous code)

// UI update functions (continued)
function updateRecordingButton() {
    if (isRecording) {
        toggleRecording.innerHTML = '<i class="bx bxs-video-recording"></i> Stop Recording';
        toggleRecording.classList.remove('btn-outline-primary');
        toggleRecording.classList.add('btn-outline-danger');
    } else {
        toggleRecording.innerHTML = '<i class="bx bxs-video-recording"></i> Start Recording';
        toggleRecording.classList.remove('btn-outline-danger');
        toggleRecording.classList.add('btn-outline-primary');
    }
}

function updateDetections(detections) {
    // Update recent detections list
    updateDetectionsList(detections);
   
    // Update detections table
    updateDetectionsTable(detections);
   
    // Update analytics charts
    updateAnalyticsCharts(detections);
}

function updateDetectionsList(detections) {
    recentDetections.innerHTML = '';
   
    detections.slice(0, 5).forEach(detection => {
        const item = document.createElement('div');
        item.className = `detection-item ${detection.class}`;
       
        const time = document.createElement('div');
        time.className = 'text-muted small';
        time.textContent = formatTimestamp(detection.timestamp);
       
        const content = document.createElement('div');
        content.className = 'd-flex justify-content-between align-items-center';
       
        const label = document.createElement('span');
        label.className = 'fw-bold';
        label.textContent = `${detection.class} (${(detection.confidence * 100).toFixed(1)}%)`;
       
        const location = document.createElement('span');
        location.className = 'badge bg-secondary';
        location.textContent = `${detection.x}, ${detection.y}`;
       
        content.appendChild(label);
        content.appendChild(location);
       
        item.appendChild(time);
        item.appendChild(content);
       
        recentDetections.appendChild(item);
    });
}

function updateDetectionsTable(detections) {
    detectionsTable.innerHTML = '';
   
    detections.forEach(detection => {
        const row = document.createElement('tr');
        row.className = detection.class;
       
        const timeCell = document.createElement('td');
        timeCell.textContent = formatTimestamp(detection.timestamp);
       
        const classCell = document.createElement('td');
        classCell.textContent = detection.class;
       
        const confidenceCell = document.createElement('td');
        confidenceCell.textContent = `${(detection.confidence * 100).toFixed(1)}%`;
       
        const locationCell = document.createElement('td');
        locationCell.textContent = `${detection.x}, ${detection.y}`;
       
        const actionsCell = document.createElement('td');
        const viewBtn = document.createElement('button');
        viewBtn.className = 'btn btn-sm btn-outline-primary';
        viewBtn.innerHTML = '<i class="bx bx-show"></i>';
        viewBtn.onclick = () => viewDetection(detection);
       
        actionsCell.appendChild(viewBtn);
       
        row.appendChild(timeCell);
        row.appendChild(classCell);
        row.appendChild(confidenceCell);
        row.appendChild(locationCell);
        row.appendChild(actionsCell);
       
        detectionsTable.appendChild(row);
    });
}

function updateAnalyticsCharts(detections) {
    // Update class distribution chart
    const classCounts = {
        'Person': 0,
        'Car': 0,
        'Dog': 0,
        'Other': 0
    };
   
    detections.forEach(detection => {
        const className = detection.class.charAt(0).toUpperCase() + detection.class.slice(1);
        if (classCounts.hasOwnProperty(className)) {
            classCounts[className]++;
        } else {
            classCounts['Other']++;
        }
    });
   
    classChart.data.datasets[0].data = [
        classCounts['Person'],
        classCounts['Car'],
        classCounts['Dog'],
        classCounts['Other']
    ];
    classChart.update();
   
    // Update time distribution chart
    const timeBuckets = [0, 0, 0, 0, 0, 0, 0, 0]; // 8 buckets for 3-hour intervals
   
    detections.forEach(detection => {
        const date = new Date(detection.timestamp * 1000);
        const hour = date.getHours();
        const bucket = Math.floor(hour / 3);
        timeBuckets[bucket]++;
    });
   
    timeChart.data.datasets[0].data = timeBuckets;
    timeChart.update();
   
    // Update heatmap chart
    const heatmapData = [];
    const gridSize = 4; // 16x12 grid (4x3 aspect ratio)
   
    // Create a grid and count detections in each cell
    for (let x = 0; x < 16; x += gridSize) {
        for (let y = 0; y < 12; y += gridSize) {
            const count = detections.filter(d =>
                d.x >= x && d.x < x + gridSize &&
                d.y >= y && d.y < y + gridSize
            ).length;
           
            if (count > 0) {
                heatmapData.push({
                    x: x + gridSize/2,
                    y: y + gridSize/2,
                    v: count
                });
            }
        }
    }
   
    heatmapChart.data.datasets[0].data = heatmapData;
    heatmapChart.update();
}

function updateSnapshotsGallery(snapshots) {
    snapshotsGallery.innerHTML = '';
   
    snapshots.forEach(snapshot => {
        const item = document.createElement('div');
        item.className = 'gallery-item';
       
        const img = document.createElement('img');
        img.src = `/snapshots/${snapshot.filename}`;
        img.alt = 'Snapshot';
        img.loading = 'lazy';
       
        const info = document.createElement('div');
        info.className = 'gallery-info';
       
        const time = document.createElement('div');
        time.className = 'small text-muted';
        time.textContent = formatTimestamp(snapshot.timestamp);
       
        const actions = document.createElement('div');
        actions.className = 'd-flex justify-content-between mt-2';
       
        const viewBtn = document.createElement('button');
        viewBtn.className = 'btn btn-sm btn-outline-primary';
        viewBtn.innerHTML = '<i class="bx bx-show"></i>';
        viewBtn.onclick = () => openSnapshotModal(snapshot);
       
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-outline-danger';
        deleteBtn.innerHTML = '<i class="bx bx-trash"></i>';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteSnapshot(snapshot.filename);
        };
       
        actions.appendChild(viewBtn);
        actions.appendChild(deleteBtn);
       
        info.appendChild(time);
        info.appendChild(actions);
       
        item.appendChild(img);
        item.appendChild(info);
       
        snapshotsGallery.appendChild(item);
    });
}

function updateRecordingsContainer(recordings) {
    recordingsContainer.innerHTML = '';
   
    recordings.forEach(recording => {
        const col = document.createElement('div');
        col.className = 'col-md-4 mb-4';
       
        const card = document.createElement('div');
        card.className = 'card h-100';
       
        const video = document.createElement('video');
        video.src = `/recordings/${recording.filename}`;
        video.poster = `/recordings/${recording.thumbnail}`;
        video.className = 'card-img-top';
        video.controls = true;
       
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
       
        const title = document.createElement('h5');
        title.className = 'card-title';
        title.textContent = `Recording ${recording.id}`;
       
        const details = document.createElement('div');
        details.className = 'text-muted small mb-2';
       
        const time = document.createElement('div');
        time.textContent = `Start: ${formatTimestamp(recording.start_time)}`;
       
        const duration = document.createElement('div');
        duration.textContent = `Duration: ${recording.duration} seconds`;
       
        const size = document.createElement('div');
        size.textContent = `Size: ${formatFileSize(recording.size)}`;
       
        details.appendChild(time);
        details.appendChild(duration);
        details.appendChild(size);
       
        const buttons = document.createElement('div');
        buttons.className = 'd-flex justify-content-between';
       
        const viewBtn = document.createElement('button');
        viewBtn.className = 'btn btn-sm btn-outline-primary';
        viewBtn.textContent = 'View';
        viewBtn.onclick = () => openRecordingModal(recording);
       
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-outline-danger';
        deleteBtn.textContent = 'Delete';
        deleteBtn.onclick = () => deleteRecording(recording.filename);
       
        buttons.appendChild(viewBtn);
        buttons.appendChild(deleteBtn);
       
        cardBody.appendChild(title);
        cardBody.appendChild(details);
        cardBody.appendChild(buttons);
       
        card.appendChild(video);
        card.appendChild(cardBody);
       
        col.appendChild(card);
        recordingsContainer.appendChild(col);
    });
}

// Modal functions
function openSnapshotModal(snapshot) {
    currentModalItem = snapshot;
    modalImage.src = `/snapshots/${snapshot.filename}`;
   
    const modal = new bootstrap.Modal(document.getElementById('snapshotModal'));
    modal.show();
}

function openRecordingModal(recording) {
    currentModalItem = recording;
    modalVideo.src = `/recordings/${recording.filename}`;
   
    const modal = new bootstrap.Modal(document.getElementById('recordingModal'));
    modal.show();
}

// Action functions
function takeSnapshot() {
    fetch('/api/take_snapshot', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadSnapshots();
                showToast('Snapshot captured successfully', 'success');
            } else {
                showToast('Failed to capture snapshot', 'danger');
            }
        })
        .catch(error => {
            console.error('Error taking snapshot:', error);
            showToast('Error taking snapshot', 'danger');
        });
}

function toggleRecordingStatus() {
    const endpoint = isRecording ? '/api/stop_recording' : '/api/start_recording';
   
    fetch(endpoint, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            isRecording = data.is_recording;
            updateRecordingButton();
           
            const message = isRecording ? 'Recording started' : 'Recording stopped';
            showToast(message, 'success');
           
            if (!isRecording) {
                loadRecordings();
            }
        })
        .catch(error => {
            console.error('Error toggling recording:', error);
            showToast('Error toggling recording', 'danger');
        });
}

function deleteSnapshot(filename) {
    if (!confirm('Are you sure you want to delete this snapshot?')) return;
   
    fetch(`/api/delete_snapshot/${filename}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadSnapshots();
                showToast('Snapshot deleted successfully', 'success');
               
                // Close modal if currently viewing this snapshot
                if (currentModalItem && currentModalItem.filename === filename) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('snapshotModal'));
                    modal.hide();
                }
            } else {
                showToast('Failed to delete snapshot', 'danger');
            }
        })
        .catch(error => {
            console.error('Error deleting snapshot:', error);
            showToast('Error deleting snapshot', 'danger');
        });
}

function deleteRecording(filename) {
    if (!confirm('Are you sure you want to delete this recording?')) return;
   
    fetch(`/api/delete_recording/${filename}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadRecordings();
                showToast('Recording deleted successfully', 'success');
               
                // Close modal if currently viewing this recording
                if (currentModalItem && currentModalItem.filename === filename) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('recordingModal'));
                    modal.hide();
                }
            } else {
                showToast('Failed to delete recording', 'danger');
            }
        })
        .catch(error => {
            console.error('Error deleting recording:', error);
            showToast('Error deleting recording', 'danger');
        });
}

function deleteAllSnapshots() {
    if (!confirm('Are you sure you want to delete ALL snapshots?')) return;
   
    fetch('/api/delete_all_snapshots', { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadSnapshots();
                showToast('All snapshots deleted successfully', 'success');
            } else {
                showToast('Failed to delete snapshots', 'danger');
            }
        })
        .catch(error => {
            console.error('Error deleting snapshots:', error);
            showToast('Error deleting snapshots', 'danger');
        });
}

function deleteAllRecordings() {
    if (!confirm('Are you sure you want to delete ALL recordings?')) return;
   
    fetch('/api/delete_all_recordings', { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadRecordings();
                showToast('All recordings deleted successfully', 'success');
            } else {
                showToast('Failed to delete recordings', 'danger');
            }
        })
        .catch(error => {
            console.error('Error deleting recordings:', error);
            showToast('Error deleting recordings', 'danger');
        });
}

function viewDetection(detection) {
    // This would open a modal or page with more details about the detection
    console.log('Viewing detection:', detection);
    showToast(`Viewing detection of ${detection.class}`, 'info');
}

function saveSettings() {
    const cameraSettings = {
        resolution: document.getElementById('cameraResolution').value,
        fps: document.getElementById('cameraFps').value,
        brightness: document.getElementById('cameraBrightness').value,
        contrast: document.getElementById('cameraContrast').value
    };
   
    const detectionSettings = {
        confidence_threshold: parseFloat(document.getElementById('confidenceThreshold').value),
        iou_threshold: parseFloat(document.getElementById('iouThreshold').value),
        classes_to_detect: []
    };
   
    if (document.getElementById('personCheck').checked) detectionSettings.classes_to_detect.push('person');
    if (document.getElementById('carCheck').checked) detectionSettings.classes_to_detect.push('car');
    if (document.getElementById('dogCheck').checked) detectionSettings.classes_to_detect.push('dog');
   
    const alertSettings = {
        enabled: document.getElementById('enableAlerts').checked,
        email: document.getElementById('alertEmail').value,
        confidence_threshold: parseFloat(document.getElementById('alertConfidenceThreshold').value),
        classes_to_alert: [],
        cooldown_period: parseInt(document.getElementById('alertCooldown').value)
    };
   
    if (document.getElementById('alertPersonCheck').checked) alertSettings.classes_to_alert.push('person');
    if (document.getElementById('alertCarCheck').checked) alertSettings.classes_to_alert.push('car');
    if (document.getElementById('alertDogCheck').checked) alertSettings.classes_to_alert.push('dog');
   
    const recordingSettings = {
        enabled: document.getElementById('enableRecording').checked,
        continuous: document.getElementById('continuousMode').checked,
        pre_record_seconds: parseInt(document.getElementById('preRecordSeconds').value),
        post_record_seconds: parseInt(document.getElementById('postRecordSeconds').value),
        max_duration: parseInt(document.getElementById('maxRecordingDuration').value)
    };
   
    const systemSettings = {
        location: document.getElementById('systemLocation').value,
        log_level: document.getElementById('logLevel').value,
        enable_analytics: document.getElementById('enableAnalytics').checked,
        enable_mobile_api: document.getElementById('enableMobileApi').checked
    };
   
    const settings = {
        camera: cameraSettings,
        detection: detectionSettings,
        alerts: alertSettings,
        recording: recordingSettings,
        system: systemSettings
    };
   
    fetch('/api/save_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Settings saved successfully', 'success');
        } else {
            showToast('Failed to save settings', 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        showToast('Error saving settings', 'danger');
    });
}

function resetSettings() {
    if (!confirm('Are you sure you want to reset all settings to default?')) return;
   
    fetch('/api/reset_settings', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Settings reset to default', 'success');
                loadInitialData(); // Reload the settings to reflect the defaults
            } else {
                showToast('Failed to reset settings', 'danger');
            }
        })
        .catch(error => {
            console.error('Error resetting settings:', error);
            showToast('Error resetting settings', 'danger');
        });
}

function clearCache() {
    if (!confirm('Are you sure you want to clear the cache?')) return;
   
    fetch('/api/clear_cache', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Cache cleared successfully', 'success');
            } else {
                showToast('Failed to clear cache', 'danger');
            }
        })
        .catch(error => {
            console.error('Error clearing cache:', error);
            showToast('Error clearing cache', 'danger');
        });
}

function restartSystem() {
    if (!confirm('Are you sure you want to restart the system?')) return;
   
    fetch('/api/restart_system', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('System restarting...', 'warning');
                // Show a countdown or disable UI until reconnected
            } else {
                showToast('Failed to restart system', 'danger');
            }
        })
        .catch(error => {
            console.error('Error restarting system:', error);
            showToast('Error restarting system', 'danger');
        });
}

// Helper functions
function showToast(message, type) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        // Create toast container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '1100';
        document.body.appendChild(container);
        toastContainer = container;
    }
   
    const toast = document.createElement('div');
    toast.className = `toast show align-items-center text-white bg-${type} border-0`;
    toast.role = 'alert';
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
   
    const toastBody = document.createElement('div');
    toastBody.className = 'd-flex';
   
    const toastMessage = document.createElement('div');
    toastMessage.className = 'toast-body';
    toastMessage.textContent = message;
   
    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'btn-close btn-close-white me-2 m-auto';
    closeBtn.setAttribute('data-bs-dismiss', 'toast');
    closeBtn.setAttribute('aria-label', 'Close');
    closeBtn.onclick = () => toast.remove();
   
    toastBody.appendChild(toastMessage);
    toastBody.appendChild(closeBtn);
    toast.appendChild(toastBody);
    toastContainer.appendChild(toast);
   
    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

function setupEventListeners() {
    // Toggle sidebar on mobile
    document.querySelector('.toggle-sidebar').addEventListener('click', function() {
        document.querySelector('.sidebar').classList.toggle('active');
    });
   
    // Take snapshot button
    document.getElementById('takeSnapshot').addEventListener('click', takeSnapshot);
    document.getElementById('takeSnapshotBtn').addEventListener('click', takeSnapshot);
   
    // Toggle recording button
    toggleRecording.addEventListener('click', toggleRecordingStatus);
    document.getElementById('startRecordingBtn').addEventListener('click', toggleRecordingStatus);
   
    // Delete buttons
    document.getElementById('deleteAllSnapshotsBtn').addEventListener('click', deleteAllSnapshots);
    document.getElementById('deleteAllRecordingsBtn').addEventListener('click', deleteAllRecordings);
    document.getElementById('deleteSnapshotBtn').addEventListener('click', function() {
        if (currentModalItem) deleteSnapshot(currentModalItem.filename);
    });
    document.getElementById('deleteRecordingBtn').addEventListener('click', function() {
        if (currentModalItem) deleteRecording(currentModalItem.filename);
    });
   
    // Download buttons
    document.getElementById('downloadSnapshotBtn').addEventListener('click', function() {
        if (currentModalItem) {
            const link = document.createElement('a');
            link.href = `/snapshots/${currentModalItem.filename}`;
            link.download = `snapshot_${currentModalItem.timestamp}.jpg`;
            link.click();
        }
    });
    document.getElementById('downloadRecordingBtn').addEventListener('click', function() {
        if (currentModalItem) {
            const link = document.createElement('a');
            link.href = `/recordings/${currentModalItem.filename}`;
            link.download = `recording_${currentModalItem.start_time}.mp4`;
            link.click();
        }
    });
   
    // Settings buttons
    document.getElementById('saveSettingsBtn').addEventListener('click', saveSettings);
    document.getElementById('resetSettingsBtn').addEventListener('click', resetSettings);
    document.getElementById('clearCacheBtn').addEventListener('click', clearCache);
    document.getElementById('restartSystemBtn').addEventListener('click', restartSystem);
   
    // Clear detections
    document.getElementById('clearDetections').addEventListener('click', function() {
        if (!confirm('Are you sure you want to clear all detections?')) return;
       
        fetch('/api/clear_detections', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    detectionsTable.innerHTML = '';
                    recentDetections.innerHTML = '';
                    showToast('Detections cleared successfully', 'success');
                } else {
                    showToast('Failed to clear detections', 'danger');
                }
            })
            .catch(error => {
                console.error('Error clearing detections:', error);
                showToast('Error clearing detections', 'danger');
            });
    });
   
    // Export detections
    document.getElementById('exportDetections').addEventListener('click', function() {
        fetch('/api/export_detections')
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'detections_export.csv';
                link.click();
                window.URL.revokeObjectURL(url);
                showToast('Detections exported successfully', 'success');
            })
            .catch(error => {
                console.error('Error exporting detections:', error);
                showToast('Error exporting detections', 'danger');
            });
    });
   
    // Generate report
    document.getElementById('generateReport').addEventListener('click', function() {
        fetch('/api/generate_report')
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'analytics_report.pdf';
                link.click();
                window.URL.revokeObjectURL(url);
                showToast('Report generated successfully', 'success');
            })
            .catch(error => {
                console.error('Error generating report:', error);
                showToast('Error generating report', 'danger');
            });
    });
   
    // Filter detections
    document.querySelectorAll('[data-filter]').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const filter = this.getAttribute('data-filter');
            filterDetections(filter);
        });
    });
   
    // Time range selection
    document.querySelectorAll('[data-range]').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const range = this.getAttribute('data-range');
            updateTimeRange(range);
        });
    });
   
    // Camera controls
    document.getElementById('zoomIn').addEventListener('click', function() {
        fetch('/api/camera/zoom/in', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Zoomed in', 'info');
                }
            });
    });
   
    document.getElementById('zoomOut').addEventListener('click', function() {
        fetch('/api/camera/zoom/out', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast('Zoomed out', 'info');
                }
            });
    });
   
    document.getElementById('fullscreen').addEventListener('click', function() {
        if (videoFeed.requestFullscreen) {
            videoFeed.requestFullscreen();
        } else if (videoFeed.webkitRequestFullscreen) {
            videoFeed.webkitRequestFullscreen();
        } else if (videoFeed.msRequestFullscreen) {
            videoFeed.msRequestFullscreen();
        }
    });
   
    // Settings sliders
    document.getElementById('confidenceThreshold').addEventListener('input', function() {
        document.getElementById('confidenceValue').textContent = this.value;
    });
   
    document.getElementById('iouThreshold').addEventListener('input', function() {
        document.getElementById('iouValue').textContent = this.value;
    });
   
    document.getElementById('alertConfidenceThreshold').addEventListener('input', function() {
        document.getElementById('alertConfidenceValue').textContent = this.value;
    });
}

function filterDetections(filter) {
    const rows = document.querySelectorAll('#detectionsTable tr');
   
    rows.forEach(row => {
        if (filter === 'all') {
            row.style.display = '';
        } else {
            if (row.classList.contains(filter)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    });
   
    document.getElementById('filterDropdown').textContent = `Filter: ${filter.charAt(0).toUpperCase() + filter.slice(1)}`;
}

function updateTimeRange(range) {
    // In a real implementation, this would fetch new data for the selected range
    let label = '';
   
    switch (range) {
        case '24h':
            label = 'Last 24 hours';
            break;
        case '7d':
            label = 'Last 7 days';
            break;
        case '30d':
            label = 'Last 30 days';
            break;
    }
   
    document.getElementById('timerangeDropdown').textContent = label;
    showToast(`Showing data for ${label.toLowerCase()}`, 'info');
}

// Initialize the application
setupEventListeners();