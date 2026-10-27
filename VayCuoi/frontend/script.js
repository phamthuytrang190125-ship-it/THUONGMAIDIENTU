const API_BASE = 'http://127.0.0.1:8000/api';
let currentModal;
let allDresses = []; // Biến toàn cục lưu danh sách váy
let currentDressId = null; // Biến lưu ID váy đang xem chi tiết

function checkLoginStatus() {
    const userId = localStorage.getItem('user_id');
    const userName = localStorage.getItem('userName');

    if (userId) {
        // Hiện khu vực user, ẩn khu vực chưa đăng nhập
        document.getElementById('auth-buttons').classList.add('d-none');
        document.getElementById('user-info').classList.remove('d-none');
        document.getElementById('welcome-message').innerText = 'Xin chào, ' + (userName || 'Khách hàng');

        // Logic kiểm tra Admin: Hiện nút "Quản Trị Hệ Thống" nếu tên là Quản Trị Viên
        const adminBtn = document.getElementById('admin-btn');
        if (adminBtn) {
            // Kiểm tra tên hiển thị (như trong hình) hoặc thêm token role nếu có
            if (userName === 'Quản Trị Viên' || userName.toLowerCase().includes('admin')) {
                adminBtn.classList.remove('d-none');
            } else {
                adminBtn.classList.add('d-none');
            }
        }
    } else {
        // Trạng thái chưa đăng nhập
        document.getElementById('auth-buttons').classList.remove('d-none');
        document.getElementById('user-info').classList.add('d-none');
    }
}

function parseJwt(token) {
    try { return JSON.parse(atob(token.split('.')[1])); } catch (e) { return null; }
}

// 1. HÀM LẤY DỮ LIỆU TỪ API (CÓ TÌM KIẾM & LỌC)
async function fetchDresses() {
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    
    const searchQuery = searchInput ? searchInput.value : '';
    const categoryId = categoryFilter ? categoryFilter.value : '';
    
    let url = `${API_BASE}/dresses?`;
    if (searchQuery) url += `search=${searchQuery}&`;
    if (categoryId) url += `category=${categoryId}`;

    try {
        const response = await fetch(url);
        const dresses = await response.json();
        allDresses = dresses; 
        renderDresses(dresses);
    } catch (error) {
        console.error("Lỗi lấy danh sách váy:", error);
    }
}

function searchDresses() {
    fetchDresses();
}

// 2. HÀM VẼ GIAO DIỆN DANH SÁCH VÁY
function renderDresses(dresses) {
    const dressListContainer = document.getElementById('dress-list'); 
    if (!dressListContainer) return;
    
    dressListContainer.innerHTML = ''; 
    
    const localImages = [
        "images/vay-cup-nguc-3d.png",
        "images/vay-cup-nguc-dinh-da.png",
        "images/vay-duoi-ca.png",
        "images/vay-chu-a.png",
        "images/vay-chu-a-tay-bong.png",
        "images/vay-cong-chua-pha-le.png"
    ];

    dresses.forEach((dress, index) => {
        const price = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(dress.rental_price);
        const imageUrl = localImages[index % localImages.length];
        
        dress.display_image = imageUrl;

        const dressCard =`
            <div class="col-md-4 mb-5">
                <div class="card h-100 luxury-card">
                    <div class="img-container">
                        <img src="${imageUrl}" class="mw-100" alt="${dress.name}" onclick="viewDressDetail(${dress.id})" style="cursor: pointer;">
                    </div>
                    
                    <div class="card-body d-flex flex-column text-center px-4 py-4">
                        <h5 class="luxury-title mb-3">${dress.name}</h5>
                        <p class="card-text text-muted small flex-grow-1 px-2" style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; text-overflow: ellipsis;">${dress.description}</p>
                        
                        <div class="d-flex justify-content-between align-items-center mb-4 mt-2">
                            <span class="badge rounded-pill" style="background-color: #4a3b00; color: #fff; padding: 8px 15px; font-size: 0.8rem; letter-spacing: 1px;">SIZE ${dress.size}</span>
                            <span class="luxury-price">${price}</span>
                        </div>
                        
                        <!-- Đã chia thành 2 nút: Chi Tiết và Thuê Ngay -->
                        <div class="d-flex gap-2 mt-auto">
                            <button class="btn btn-outline-luxury w-50" onclick="viewDressDetail(${dress.id})">Chi Tiết</button>
                            <button class="btn btn-luxury w-50" onclick="bookDress(${dress.id})">Thuê Ngay</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        dressListContainer.innerHTML += dressCard;
    });
}

// 3. CÁC HÀM XỬ LÝ MODAL CHI TIẾT SẢN PHẨM
function viewDressDetail(dressId) {
    const dress = allDresses.find(d => d.id === dressId);
    if (!dress) return;
    
    currentDressId = dress.id; 
    
    document.getElementById('detailName').innerText = dress.name;
    document.getElementById('detailPrice').innerText = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(dress.rental_price);
    document.getElementById('detailSize').innerText = dress.size;
    document.getElementById('detailDeposit').innerText = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(dress.deposit_price);
    document.getElementById('detailDescription').innerText = dress.description;
    document.getElementById('detailImage').src = dress.display_image; 
    
    new bootstrap.Modal(document.getElementById('dressDetailModal')).show();
}

function rentFromDetail() {
    const detailModalEl = document.getElementById('dressDetailModal');
    const detailModal = bootstrap.Modal.getInstance(detailModalEl);
    if(detailModal) detailModal.hide();
    
    bookDress(currentDressId); 
}

// 4. LUỒNG THUÊ VÁY (ĐƠN HÀNG) & CẬP NHẬT QR CODE
function bookDress(dressId) {
    if (!localStorage.getItem('user_id')) {
        alert("Vui lòng đăng nhập trước khi thuê váy!");
        new bootstrap.Modal(document.getElementById('loginModal')).show();
        return;
    }

    const dress = allDresses.find(d => d.id === dressId);
    if (dress) {
        // Tính toán tổng tiền
        const rental = dress.rental_price;
        const deposit = dress.deposit_price;
        const total = rental + deposit;

        // In số tiền ra Form HTML
        document.getElementById('orderRentalPrice').innerText = rental.toLocaleString('vi-VN') + ' đ';
        document.getElementById('orderDepositPrice').innerText = deposit.toLocaleString('vi-VN') + ' đ';
        document.getElementById('orderTotalPrice').innerText = total.toLocaleString('vi-VN') + ' đ';

        // Ép Tổng tiền (total) vào mã quét QR VietQR
        const qrImageEl = document.getElementById('qrImage');
        if (qrImageEl) {
            qrImageEl.src = `https://img.vietqr.io/image/vietinbank-104879798041-compact2.png?amount=${total}&addInfo=Thue%20Vay%20Cuoi&accountName=PHAM%20THI%20THUY%20TRANG`;
        }
    }

    document.getElementById('dressId').value = dressId;
    currentModal = new bootstrap.Modal(document.getElementById('orderModal'));
    currentModal.show();
}

function toggleQRCode() {
    const paymentMethod = document.getElementById('paymentMethod').value;
    const qrContainer = document.getElementById('qrCodeContainer');
    
    if (paymentMethod === 'BANK_TRANSFER') {
        qrContainer.classList.remove('d-none');
    } else {
        qrContainer.classList.add('d-none');
    }
}

async function submitOrder() {
    // 1. Lấy token từ localStorage
    const token = localStorage.getItem('access_token');
    
    const orderData = {
        user_id: parseInt(localStorage.getItem('user_id')),
        dress_id: parseInt(document.getElementById('dressId').value),
        start_date: document.getElementById('startDate').value,
        end_date: document.getElementById('endDate').value,
        shipping_address: document.getElementById('address').value,
        payment_method: document.getElementById('paymentMethod').value
    };

    try {
        const response = await fetch(`${API_BASE}/orders`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}` // 2. Bổ sung header xác thực vào đây
            },
            body: JSON.stringify(orderData)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Thành công! Mã đơn hàng: ' + result.order_code);
            currentModal.hide(); 
            document.getElementById('orderForm').reset();
            toggleQRCode(); 
            
            // Chuyển hướng khách sang trang Đơn Thuê Của Tôi để xem lịch sử
            window.location.href = "my-orders.html";
        } else {
            alert('Lỗi: ' + result.detail);
        }
    } catch (error) { 
        alert('Lỗi kết nối Backend!'); 
    }
}

// 5. CÁC LUỒNG XÁC THỰC (AUTH)
async function submitRegister() {
    const regData = {
        full_name: document.getElementById('regFullName').value,
        email: document.getElementById('regEmail').value,
        phone: document.getElementById('regPhone').value,
        password: document.getElementById('regPassword').value
    };
    try {
        const response = await fetch(`${API_BASE}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(regData)
        });
        const result = await response.json();
        if (response.ok) {
            alert('Đăng ký thành công!');
            bootstrap.Modal.getInstance(document.getElementById('registerModal')).hide();
            document.getElementById('registerForm').reset();
            new bootstrap.Modal(document.getElementById('loginModal')).show();
        } else { alert('Lỗi: ' + result.detail); }
    } catch (error) { alert('Lỗi Backend!'); }
}

async function submitLogin() {
    const loginData = { email: document.getElementById('loginEmail').value, password: document.getElementById('loginPassword').value };
    try {
        const response = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(loginData)
        });
        const result = await response.json();
        if (response.ok) {
            const payload = parseJwt(result.access_token);
            if (payload) {
                localStorage.setItem('user_id', payload.user_id);
                localStorage.setItem('access_token', result.access_token);
                localStorage.setItem('userName', result.full_name); 

                alert('Đăng nhập thành công!');
                bootstrap.Modal.getInstance(document.getElementById('loginModal')).hide();
                document.getElementById('loginForm').reset();
                checkLoginStatus();
            }
        } else { alert('Lỗi: ' + result.detail); }
    } catch (error) { alert('Lỗi Backend!'); }
}

function logout() {
    localStorage.clear();
    alert('Đã đăng xuất!');
    checkLoginStatus();
}

document.getElementById('togglePassword')?.addEventListener('click', function () {
    const input = document.getElementById('regPassword');
    const icon = document.getElementById('toggleIcon');
    if (input.type === 'password') { input.type = 'text'; icon.classList.replace('bi-eye-slash', 'bi-eye'); }
    else { input.type = 'password'; icon.classList.replace('bi-eye', 'bi-eye-slash'); }
});

document.getElementById('toggleLoginPassword')?.addEventListener('click', function () {
    const input = document.getElementById('loginPassword');
    const icon = document.getElementById('toggleLoginIcon');
    if (input.type === 'password') { input.type = 'text'; icon.classList.replace('bi-eye-slash', 'bi-eye'); }
    else { input.type = 'password'; icon.classList.replace('bi-eye', 'bi-eye-slash'); }
});

// 6. KHỞI TẠO DỮ LIỆU KHI VÀO TRANG
checkLoginStatus();
fetchDresses();