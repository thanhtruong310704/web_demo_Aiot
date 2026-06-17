const video = document.getElementById('videoElement');
const previewImg = document.getElementById('previewImage');
const canvas = document.getElementById('canvasElement');
const resultImg = document.getElementById('resultImage');
const downloadBtn = document.getElementById('downloadBtn');

function moCamera() {
    previewImg.style.display = 'none'; video.style.display = 'block';

    navigator.mediaDevices.getUserMedia({
        video: {
            facingMode: "user",
            width: { ideal: 1280, max: 1920 },
            height: { ideal: 720, max: 1080 },
            advanced: [{ focusMode: "continuous" }]
        }
    })
        .then(stream => { video.srcObject = stream; })
        .catch(err => {
            // Nếu điện thoại yếu, lùi về cấu hình camera mặc định
            navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } })
                .then(stream => { video.srcObject = stream; })
                .catch(e => alert("Không thể truy cập camera."));
        });
}
function taiAnhLen(event) {
    const file = event.target.files[0];
    if (!file) return;
    if (video.srcObject) { video.srcObject.getTracks().forEach(t => t.stop()); }
    video.style.display = 'none'; previewImg.style.display = 'block';
    const reader = new FileReader();
    reader.onload = function (e) { previewImg.src = e.target.result; }
    reader.readAsDataURL(file);
}

async function xuLyAnh() {
    let nguonAnh; let laCamera = false;
    if (video.style.display === 'block' && video.srcObject) { nguonAnh = video; laCamera = true; }
    else if (previewImg.style.display === 'block' && previewImg.src) { nguonAnh = previewImg; laCamera = false; }
    else { return alert("Hãy Mở Camera hoặc Tải Ảnh Lên trước!"); }

    canvas.width = 512; canvas.height = 512;
    const ctx = canvas.getContext('2d');

    if (laCamera) {
        const scaleX = nguonAnh.videoWidth / nguonAnh.clientWidth;
        const scaleY = nguonAnh.videoHeight / nguonAnh.clientHeight;
        ctx.save(); ctx.scale(-1, 1); ctx.translate(-canvas.width, 0);
        ctx.drawImage(nguonAnh, (nguonAnh.clientWidth - 240) / 2 * scaleX, (nguonAnh.clientHeight - 320) / 2 * scaleY, 240 * scaleX, 320 * scaleY, 0, 0, 512, 512);
        ctx.restore();
    } else { ctx.drawImage(nguonAnh, 0, 0, canvas.width, canvas.height); }

    let anhDaXuLy = canvas.toDataURL('image/png');
    resultImg.src = ""; resultImg.alt = "Đang phân tích...";
    downloadBtn.style.display = 'none';

    try {
        const response = await fetch('/process_image', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: anhDaXuLy })
        });
        if (!response.ok) { return alert("Lỗi từ server Python (Mã " + response.status + ")."); }
        const data = await response.json();
        if (data.success) {
            resultImg.src = data.image; downloadBtn.href = data.image; downloadBtn.style.display = 'block';

            // Cập nhật biến global bên file led.js
            modeGrid = data.led_grid; brightGrid = data.bright_grid;
            const cells = document.querySelectorAll('#manualMode .cell');
            for (let i = 0; i < 25; i++) { updateVisual(cells[i], modeGrid[i], (brightGrid[i] / 255) * 100 || 100); }
            setTimeout(() => { alert("Hoàn tất! Dữ liệu đã được gửi tới mặt nạ và lưu lịch sử.") }, 300);
        } else { alert("Lỗi: " + data.message); }
    } catch (error) { alert("Không thể đọc kết quả từ server!"); }
}