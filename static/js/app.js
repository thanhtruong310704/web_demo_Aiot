// --- QUẢN LÝ TAB ---
function switchTab(mode) {
    document.getElementById('manualMode').style.display = mode === 'manual' ? 'block' : 'none';
    document.getElementById('autoMode').style.display = mode === 'auto' ? 'block' : 'none';
    document.getElementById('historyMode').style.display = mode === 'history' ? 'block' : 'none';
    document.getElementById('deviceMode').style.display = mode === 'device' ? 'block' : 'none';
    document.getElementById('regimenMode').style.display = mode === 'regimen' ? 'block' : 'none';

    document.getElementById('btnManual').classList.toggle('active', mode === 'manual');
    document.getElementById('btnAuto').classList.toggle('active', mode === 'auto');
    document.getElementById('btnHistory').classList.toggle('active', mode === 'history');
    document.getElementById('btnDevice').classList.toggle('active', mode === 'device');
    document.getElementById('btnRegimen').classList.toggle('active', mode === 'regimen');

    if (mode === 'device') updateDeviceStats();
}

// --- KẾT NỐI VÀ QUẢN LÝ THIẾT BỊ ---
function bindDevice() {
    const deviceId = document.getElementById('deviceIdInput').value.trim();
    const pin = document.getElementById('pinInput').value.trim();
    if (!deviceId || !pin) { alert("Vui lòng nhập đầy đủ Mã thiết bị và Mã PIN!"); return; }
    fetch('/bind_device', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device_id: deviceId, pin: pin })
    }).then(r => r.json()).then(data => {
        if (data.success) { alert("" + data.message); location.reload(); }
        else { alert("Lỗi: " + data.message); }
    }).catch(e => { alert("Đã xảy ra lỗi khi kết nối với máy chủ!"); });
}

function unbindDevice() {
    if (!confirm("Bạn có chắc chắn muốn ngắt kết nối với chiếc mặt nạ này không?")) return;
    fetch('/unbind_device', { method: 'POST', headers: { 'Content-Type': 'application/json' } }).then(r => r.json())
        .then(data => { if (data.success) { alert("" + data.message); location.reload(); } else { alert("Lỗi: " + data.message); } })
        .catch(error => { alert("Không thể thực hiện yêu cầu!"); });
}

function kichHoatOTA() {
    if (!confirm("Hệ thống sẽ nạp bản phần mềm mới nhất cho mặt nạ.\n\nKHÔNG TẮT NGUỒN HAY MẠNG!\n\nTiếp tục?")) return;
    fetch('/trigger_ota', { method: 'POST', headers: { 'Content-Type': 'application/json' } }).then(r => r.json())
        .then(data => {
            if (data.success) { alert("" + data.message); document.getElementById('otaAlertBox').style.display = 'none'; updateDeviceStats(); }
            else { alert("Lỗi: " + data.message); }
        }).catch(e => { alert("Không thể gửi yêu cầu cập nhật!"); });
}

async function updateDeviceStats() {
    try {
        const response = await fetch('/get_device_stats'); const data = await response.json();
        if (data.success) {
            document.getElementById('stat-battery').innerText = data.battery + (data.battery !== '--' ? '%' : '');
            document.getElementById('stat-last-used').innerText = data.last_used;
            document.getElementById('stat-firmware').innerText = data.firmware;
            if (data.pending_version && data.pending_version !== data.firmware) {
                document.getElementById('otaAlertBox').style.display = 'block'; document.getElementById('valNewFirmware').innerText = data.pending_version;
            } else { document.getElementById('otaAlertBox').style.display = 'none'; }
        }
    } catch (error) { console.error("Lỗi cập nhật thiết bị:", error); }
}

window.addEventListener('load', () => { setInterval(updateDeviceStats, 15000); });