// Các biến dùng chung toàn cục (Global)
let modeGrid = new Array(25).fill(0);
let brightGrid = new Array(25).fill(0);
const slider = document.getElementById('slider');

// --- KHỞI TẠO BẢN ĐỒ LED ---
if (document.getElementById('ledGrid')) {
    const grid = document.getElementById('ledGrid');
    for (let i = 0; i < 25; i++) {
        let div = document.createElement('div');
        div.className = 'cell';
        div.onclick = () => {
            modeGrid[i] = (modeGrid[i] + 1) % 5;
            let currentSliderVal = parseInt(slider.value);
            brightGrid[i] = (modeGrid[i] === 0) ? 0 : Math.round((currentSliderVal / 100) * 255);
            updateVisual(div, modeGrid[i], currentSliderVal);
        };
        grid.appendChild(div);
    }
}

function updateVisual(el, mode, opacityPercent) {
    el.className = 'cell ' + (mode === 1 ? 'blue' : (mode === 2 ? 'red' : (mode === 3 ? 'green' : (mode === 4 ? 'yellow' : ''))));
    el.style.opacity = mode !== 0 ? 0.3 + (opacityPercent / 100) * 0.7 : 1;
}

async function clearGrid() {
    modeGrid.fill(0); brightGrid.fill(0);
    document.querySelectorAll('#manualMode .cell').forEach(c => { c.className = 'cell'; c.style.opacity = 1; });
    if (boDemGio) {
        clearInterval(boDemGio); 
        boDemGio = null;
        document.getElementById('timerDisplay').style.display = 'none';
        
        // Trả lại trạng thái nút bấm
        let btnStart = document.getElementById('btnStartTimer');
        if (btnStart) {
            btnStart.innerText = 'Bắt Đầu'; 
            btnStart.style.background = '#28a745';
        }
    }
    await sendData();
}

if (slider) slider.oninput = function () { document.getElementById('val').innerText = this.value; }

async function sendData() {
    try {
        const response = await fetch('/update_leds', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ grid: modeGrid, bright: brightGrid })
        });
        const data = await response.json();
        if (!data.success) { alert("Lỗi: " + data.message); }
    } catch (e) { console.log("Lỗi gửi dữ liệu LED: ", e); }
}

// --- XỬ LÝ PHÁC ĐỒ CHĂM SÓC ---
let phacDoDangChon = ""; let mauLedDangChon = 0;
function chayPhacDo(loai) {
    let phutMacDinh = 0;
    if (loai === 'trimun') { mauLedDangChon = 1; phutMacDinh = 15; phacDoDangChon = 'Trị Mụn'; }
    else if (loai === 'chonglaohoa') { mauLedDangChon = 2; phutMacDinh = 20; phacDoDangChon = 'Chống Lão Hóa'; }
    else if (loai === 'thugian') { mauLedDangChon = 3; phutMacDinh = 10; phacDoDangChon = 'Thư Giãn'; }
    else if (loai === 'sanchac') { mauLedDangChon = 4; phutMacDinh = 12; phacDoDangChon = 'Săn Chắc Da'; }

    document.getElementById('modalTitle').innerText = "Cài đặt: " + phacDoDangChon;
    document.getElementById('modalTime').value = phutMacDinh;
    document.getElementById('modalSlider').value = 10;
    document.getElementById('modalVal').innerText = 10;
    document.getElementById('customModal').style.display = 'flex';
}

function dongModal() { document.getElementById('customModal').style.display = 'none'; }

function xacNhanChayPhacDo() {
    dongModal();
    let phut = parseInt(document.getElementById('modalTime').value);
    let doSangPercent = parseInt(document.getElementById('modalSlider').value);
    if (isNaN(phut) || phut <= 0) phut = 15;

    let doSang = Math.round((doSangPercent / 100) * 255);
    modeGrid.fill(mauLedDangChon); brightGrid.fill(doSang);

    const cells = document.querySelectorAll('#manualMode .cell');
    for (let i = 0; i < 25; i++) { updateVisual(cells[i], modeGrid[i], doSangPercent); }
    document.getElementById('slider').value = doSangPercent;
    document.getElementById('val').innerText = doSangPercent;

    sendData();

    let timerSelect = document.getElementById('timerSelect');
    if (!Array.from(timerSelect.options).some(opt => opt.value == phut)) timerSelect.add(new Option(`${phut} Phút`, phut));
    timerSelect.value = phut;

    if (boDemGio) { clearInterval(boDemGio); boDemGio = null; }
    batDauHenGio();
    switchTab('manual');
    alert(`Đã bật phác đồ: ${phacDoDangChon}\n- Độ sáng: ${doSangPercent}%\n- Hẹn giờ tự tắt: ${phut} phút`);
}

// --- XỬ LÝ HẸN GIỜ ---
let thoiGianConLai = 0; let thoiDiemKetThuc = 0; let boDemGio = null;

function batDauHenGio() {
    const btn = document.getElementById('btnStartTimer');
    const hienThi = document.getElementById('timerDisplay');

    if (boDemGio) {
        clearInterval(boDemGio); boDemGio = null;
        hienThi.style.display = 'none'; btn.innerText = 'Bắt Đầu'; btn.style.background = '#28a745';
        return;
    }

    const phut = parseInt(document.getElementById('timerSelect').value);
    thoiGianConLai = phut * 60; thoiDiemKetThuc = Date.now() + (thoiGianConLai * 1000);
    hienThi.style.display = 'block'; btn.innerText = 'Hủy Hẹn Giờ'; btn.style.background = '#dc3545';
    capNhatHienThiGio();

    boDemGio = setInterval(async () => {
        thoiGianConLai = Math.floor((thoiDiemKetThuc - Date.now()) / 1000);
        if (thoiGianConLai <= 0) {
            thoiGianConLai = 0; capNhatHienThiGio(); clearInterval(boDemGio); boDemGio = null;
            hienThi.style.display = 'none'; btn.innerText = 'Bắt Đầu'; btn.style.background = '#28a745';
            await clearGrid(); setTimeout(() => { alert("Đã hết thời gian! Mặt nạ đã tự động tắt."); }, 300);
        } else { capNhatHienThiGio(); }
    }, 1000);
}

function capNhatHienThiGio() {
    let p = Math.floor(thoiGianConLai / 60); let s = thoiGianConLai % 60;
    document.getElementById('timerDisplay').innerText = (p < 10 ? "0" + p : p) + ":" + (s < 10 ? "0" + s : s);
}