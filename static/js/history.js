let chartInstance = null;

async function taiLichSu() {
    const container = document.getElementById('historyContainer');
    container.innerHTML = '<p>Đang tải dữ liệu...</p>';
    try {
        const response = await fetch('/get_history'); const data = await response.json();
        if (data.success && data.data.length > 0) veBieuDoVaDanhSach(data.data);
        else { container.innerHTML = '<p>Bạn chưa có lịch sử phân tích nào.</p>'; if (chartInstance) chartInstance.destroy(); }
    } catch (e) { container.innerHTML = '<p style="color:red;">Lỗi tải lịch sử!</p>'; }
}

function veBieuDoVaDanhSach(historyData) {
    const container = document.getElementById('historyContainer'); container.innerHTML = '';
    let thongKeNgay = {};
    historyData.forEach(item => {
        let ngay = item.time.split(" ")[0];
        if (!thongKeNgay[ngay]) thongKeNgay[ngay] = { soLanSuDung: 0, tongDiemLED: 0, xanh_duong: 0, do_red: 0, xanh_la: 0, vang: 0 };
        thongKeNgay[ngay].soLanSuDung += 1;
        let xanh_duong = item.led_grid ? item.led_grid.filter(v => v === 1).length : 0;
        let do_red = item.led_grid ? item.led_grid.filter(v => v === 2).length : 0;
        let xanh_la = item.led_grid ? item.led_grid.filter(v => v === 3).length : 0;
        let vang = item.led_grid ? item.led_grid.filter(v => v === 4).length : 0;
        thongKeNgay[ngay].xanh_duong += xanh_duong; thongKeNgay[ngay].do_red += do_red; thongKeNgay[ngay].xanh_la += xanh_la; thongKeNgay[ngay].vang += vang;
        thongKeNgay[ngay].tongDiemLED += (xanh_duong + do_red + xanh_la + vang);
    });

    let mangNgay = Object.keys(thongKeNgay).sort(); let dataSoLan = []; let dataTongLED = [];
    mangNgay.forEach(ngay => { dataSoLan.push(thongKeNgay[ngay].soLanSuDung); dataTongLED.push(thongKeNgay[ngay].tongDiemLED); });

    let mangNgayNganGon = mangNgay.map(ngay => {
        let parts = ngay.split('-');
        return `${parts[2]}/${parts[1]}`; 
    });

    const ctxChart = document.getElementById('myChart').getContext('2d');
    if (chartInstance) chartInstance.destroy();
    chartInstance = new Chart(ctxChart, {
        type: 'bar',
        data: {
            // Đưa mảng đã rút gọn vào đồ thị thay vì mảng gốc có cả năm
            labels: mangNgayNganGon, 
            datasets: [
                { type: 'line', label: 'Cường độ chiếu sáng', data: dataTongLED, borderColor: '#28a745', backgroundColor: '#28a745', borderWidth: 3, tension: 0.3, yAxisID: 'y1' },
                { type: 'bar', label: 'Số lần dùng mặt nạ', data: dataSoLan, backgroundColor: 'rgba(0, 123, 255, 0.6)', borderColor: '#007bff', borderWidth: 1, yAxisID: 'y' }
            ]
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: false, // Ép đồ thị tự co giãn theo container
            scales: { 
                // 2. Thêm cấu hình chống đè chữ cho trục X
                x: {
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 6, // Chỉ hiển thị tối đa 6 mốc thời gian trên điện thoại
                        maxRotation: 45,  // Cố định nghiêng 45 độ
                        minRotation: 45
                    }
                },
                y: { type: 'linear', position: 'left', beginAtZero: true, ticks: { stepSize: 1 } }, 
                y1: { type: 'linear', position: 'right', beginAtZero: true, grid: { drawOnChartArea: false } } 
            } 
        }
    });

    // Phần render danh sách thẻ lịch sử bên dưới vẫn giữ nguyên mảng gốc để hiện đầy đủ Năm
    mangNgay.reverse().forEach(ngay => {
        let dataNgay = thongKeNgay[ngay]; let [nam, thang, ngayDinhDang] = ngay.split('-');
        let div = document.createElement('div'); div.className = 'history-item';
        div.innerHTML = `<p style="font-size: 16px; color: #007bff;">📅 <b>Ngày: ${ngayDinhDang}/${thang}/${nam}</b></p>
                         <p style="margin-bottom: 5px;"><b>Tần suất:</b> Dùng <b>${dataNgay.soLanSuDung}</b> lần.</p>
                         <p style="font-size: 12px; color: #666; margin-top: 8px;"><i>(🔵 ${dataNgay.xanh_duong} Xanh | 🔴 ${dataNgay.do_red} Đỏ | 🟢 ${dataNgay.xanh_la} Lục | 🟡 ${dataNgay.vang} Vàng)</i></p>`;
        container.appendChild(div);
    });
}