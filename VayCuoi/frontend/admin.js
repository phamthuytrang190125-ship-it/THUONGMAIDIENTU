const API_BASE = 'http://127.0.0.1:8000/api';
const token = localStorage.getItem('access_token');
let jwtPayload = null;
let ordersCache = [];
let dressesCache = [];

// 1. Khai báo từ điển dịch trạng thái ở đầu file
const statusTranslate = {
    "PENDING": "Chờ xác nhận",
    "CONFIRMED": "Đã xác nhận",
    "RENTING": "Đang thuê",
    "RETURNED": "Đã trả váy",
    "COMPLETED": "Hoàn thành",
    "CANCELLED": "Đã hủy"
};

function decodeJwt(tokenValue) {
  try {
    const part = tokenValue.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const padded = part + '='.repeat((4 - part.length % 4) % 4);
    return JSON.parse(decodeURIComponent(Array.from(atob(padded), c => '%' + c.charCodeAt(0).toString(16).padStart(2, '0')).join('')));
  } catch (_) { return null; }
}

function guardAdmin() {
  if (!token) {
    alert('Bà vui lòng đăng nhập tài khoản ADMIN trước nha.');
    window.location.replace('index.html');
    return false;
  }
  jwtPayload = decodeJwt(token);
  if (!jwtPayload || !jwtPayload.user_id || !jwtPayload.role || (jwtPayload.exp && jwtPayload.exp * 1000 <= Date.now())) {
    alert('Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.');
    window.location.replace('index.html');
    return false;
  }
  if (jwtPayload.role !== 'ADMIN') {
    alert('Tài khoản của bà không có quyền truy cập trang quản trị.');
    window.location.replace('index.html');
    return false;
  }
  document.getElementById('admin-name').textContent = localStorage.getItem('userName') || 'Quản trị viên';
  return true;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function money(value) {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(Number(value || 0));
}
function showAlert(message, type = 'success') {
  const box = document.getElementById('page-alert');
  box.className = `alert alert-${type}`;
  box.textContent = message;
  box.classList.remove('d-none');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function apiFetch(path, options = {}) {
  const headers = {
      ...(options.headers || {}),
      Authorization: `Bearer ${token}`
  };

  if (options.body && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers: headers });
  const text = await response.text();
  let data = null;

  try { data = text ? JSON.parse(text) : null; } catch (error) { data = { detail: text }; }

  if (response.status === 401 || response.status === 403) {
      throw new Error(response.status === 401 ? 'Token hết hạn hoặc chưa được xác thực (401).' : 'Tài khoản không có quyền ADMIN (403).');
  }

  if (!response.ok) {
      throw new Error(data?.detail || data?.error || data?.message || `API lỗi ${response.status}`);
  }

  return data;
}

function showView(view) {
  document.getElementById('orders-view').classList.toggle('d-none', view !== 'orders');
  document.getElementById('dresses-view').classList.toggle('d-none', view !== 'dresses');
  document.querySelectorAll('[data-view]').forEach(btn => btn.classList.toggle('active', btn.dataset.view === view));
  if (view === 'orders') loadOrders(); else loadDresses();
}

async function loadOrders() {
  const body = document.getElementById('orders-body');
  body.innerHTML = '<tr><td colspan="8" class="text-center muted py-4">Đang tải dữ liệu...</td></tr>';
  try {
    const data = await apiFetch('/orders');
    if (!Array.isArray(data)) throw new Error(data?.error || 'Dữ liệu đơn hàng trả về không đúng định dạng.');
    ordersCache = data;
    document.getElementById('stat-total').textContent = data.length;
    document.getElementById('stat-pending').textContent = data.filter(o => o.status === 'RENTING').length;
    document.getElementById('stat-confirmed').textContent = data.filter(o => o.status === 'CONFIRMED').length;
    renderOrders();
  } catch (error) {
    body.innerHTML = `<tr><td colspan="8" class="text-center text-danger py-4">${escapeHtml(error.message)}</td></tr>`;
  }
}

// 2. Chỉnh sửa lại hàm renderOrders để hiển thị Tiếng Việt và Nút Quyết Toán
function renderOrders() {
  const query = document.getElementById('order-search').value.trim().toLowerCase();
  const rows = ordersCache.filter(o => String(o.order_code || '').toLowerCase().includes(query) || String(o.full_name || '').toLowerCase().includes(query));
  const body = document.getElementById('orders-body');
  
  if (!rows.length) { 
      body.innerHTML = '<tr><td colspan="8" class="text-center muted py-4">Không có đơn hàng phù hợp.</td></tr>'; 
      return; 
  }
  
  const validStatuses = ['PENDING', 'CONFIRMED', 'RENTING', 'RETURNED', 'COMPLETED', 'CANCELLED'];
  
  body.innerHTML = rows.map(order => {
    const currentStatus = validStatuses.includes(order.status) ? order.status : 'CONFIRMED';
    const vietnameseStatus = statusTranslate[order.status] || order.status;

    // HIỂN THỊ NÚT QUYẾT TOÁN NẾU KHÁCH ĐÃ TRẢ VÁY
    let actionHtml = '';
    if (order.status === 'RETURNED') {
        actionHtml = `<button class="btn btn-sm btn-danger w-100 fw-bold" type="button" onclick="openCheckoutModal(${Number(order.id)})">Hoàn Cọc</button>`;
    } else {
        actionHtml = `
        <div class="d-flex gap-2 align-items-center">
            <select class="form-select form-select-sm" style="min-width:140px" id="status-${Number(order.id)}" aria-label="Trạng thái đơn ${Number(order.id)}">
                ${validStatuses.map(s => `<option value="${s}" ${s === currentStatus ? 'selected' : ''}>${statusTranslate[s] || s}</option>`).join('')}
            </select>
            <button class="btn btn-sm btn-gold" type="button" onclick="updateOrderStatus(${Number(order.id)})">Lưu</button>
        </div>`;
    }

    return `<tr>
      <td>${escapeHtml(order.id)}</td>
      <td><strong>${escapeHtml(order.order_code || '—')}</strong></td>
      <td>${escapeHtml(order.full_name || '—')}</td>
      <td>${escapeHtml(order.phone || '—')}</td>
      <td>${money(order.total_amount)}</td>
      <td>${money(order.deposit_amount)}</td>
      <td><span class="status-badge bg-light text-dark border p-1 rounded">${escapeHtml(vietnameseStatus)}</span></td>
      <td>${actionHtml}</td>
    </tr>`;
  }).join('');
}

async function updateOrderStatus(orderId) {
  const select = document.getElementById(`status-${orderId}`);
  if (!select) return;
  const status = select.value;
  const statusVN = statusTranslate[status] || status;
  
  if (!confirm(`Xác nhận cập nhật đơn #${orderId} sang trạng thái "${statusVN}"?`)) return;
  try {
    const result = await apiFetch(`/orders/${orderId}/status`, { method: 'PUT', body: JSON.stringify({ status }) });
    showAlert(`Đã cập nhật trạng thái đơn hàng #${orderId} thành "${statusVN}" thành công.`);
    await loadOrders();
  } catch (error) { showAlert(error.message, 'danger'); }
}

// --- LOGIC QUYẾT TOÁN ĐƠN HÀNG ---
function openCheckoutModal(id) {
    const order = ordersCache.find(o => Number(o.id) === Number(id));
    if (!order) return;
    
    document.getElementById('checkout-order-id').value = id;
    document.getElementById('checkout-deposit').textContent = money(order.deposit_amount);
    document.getElementById('checkout-form').reset();
    
    bootstrap.Modal.getOrCreateInstance(document.getElementById('checkoutModal')).show();
}

async function submitCheckout(event) {
    event.preventDefault();
    const orderId = Number(document.getElementById('checkout-order-id').value);
    
    const payload = {
        return_condition: document.getElementById('checkout-condition').value,
        damage_fee: Number(document.getElementById('checkout-damage').value) || 0,
        late_fee: Number(document.getElementById('checkout-late').value) || 0,
        note: document.getElementById('checkout-note').value.trim()
    };

    if (!confirm(`Bà có chắc chắn muốn chốt quyết toán và hoàn tiền cho đơn #${orderId} không? Hành động này không thể hoàn tác!`)) return;

    try {
        const result = await apiFetch(`/orders/${orderId}/checkout`, { 
            method: 'POST', 
            body: JSON.stringify(payload) 
        });
        
        bootstrap.Modal.getOrCreateInstance(document.getElementById('checkoutModal')).hide();
        showAlert(`Quyết toán thành công! Hệ thống đã hoàn ${money(result.refund_amount)} cho khách hàng.`);
        await loadOrders();
    } catch (error) { 
        showAlert(error.message, 'danger'); 
    }
}

async function loadDresses() {
  const body = document.getElementById('dresses-body');
  body.innerHTML = '<tr><td colspan="9" class="text-center muted py-4">Đang tải dữ liệu...</td></tr>';
  try {
    const data = await apiFetch('/dresses');
    if (!Array.isArray(data)) throw new Error(data?.error || 'Dữ liệu váy trả về không đúng định dạng.');
    dressesCache = data;
    renderDresses();
  } catch (error) {
    body.innerHTML = `<tr><td colspan="9" class="text-center text-danger py-4">${escapeHtml(error.message)}</td></tr>`;
  }
}

function renderDresses() {
  const query = document.getElementById('dress-search').value.trim().toLowerCase();
  const rows = dressesCache.filter(d => String(d.name || '').toLowerCase().includes(query));
  const body = document.getElementById('dresses-body');
  if (!rows.length) { body.innerHTML = '<tr><td colspan="9" class="text-center muted py-4">Không có váy phù hợp.</td></tr>'; return; }
  body.innerHTML = rows.map(d => `<tr>
    <td>${escapeHtml(d.id)}</td><td><strong>${escapeHtml(d.name)}</strong><div class="small muted text-truncate" style="max-width:240px">${escapeHtml(d.description || '')}</div></td>
    <td>${escapeHtml(d.category_id ?? '—')}</td><td>${escapeHtml(d.size || '—')}</td><td>${escapeHtml(d.quantity ?? '—')}</td>
    <td>${money(d.rental_price)}</td><td>${money(d.deposit_price)}</td><td><span class="status-badge">${escapeHtml(d.status || '—')}</span></td>
    <td><div class="d-flex gap-2"><button class="btn btn-sm btn-outline-primary" type="button" onclick="openEditDress(${Number(d.id)})">Sửa chi tiết</button><button class="btn btn-sm btn-outline-danger" type="button" onclick="deleteDress(${Number(d.id)})">Xóa</button></div></td>
  </tr>`).join('');
}

async function createDress(event) {
  event.preventDefault();
  const dress = {
    category_id: Number(document.getElementById('new-category').value),
    name: document.getElementById('new-name').value.trim(),
    description: document.getElementById('new-description').value.trim(),
    size: document.getElementById('new-size').value.trim(),
    quantity: Number(document.getElementById('new-quantity').value),
    rental_price: Number(document.getElementById('new-price').value),
    deposit_price: Number(document.getElementById('new-deposit').value),
    status: document.getElementById('new-status').value,
    image_url: document.getElementById('new-image').value.trim() || null
  };
  try {
    const result = await apiFetch('/dresses', { method: 'POST', body: JSON.stringify(dress) });
    bootstrap.Modal.getOrCreateInstance(document.getElementById('dressCreateModal')).hide();
    document.getElementById('dress-create-form').reset();
    showAlert(`${result?.message || 'Thêm váy thành công.'} ID: ${result?.dress_id ?? '—'}`);
    await loadDresses();
  } catch (error) { showAlert(error.message, 'danger'); }
}

function openEditDress(id) {
  const dress = dressesCache.find(d => Number(d.id) === Number(id));
  if (!dress) return;
  document.getElementById('edit-dress-id').value = dress.id;
  document.getElementById('edit-category').value = dress.category_id;
  document.getElementById('edit-name').value = dress.name;
  document.getElementById('edit-size').value = dress.size;
  document.getElementById('edit-quantity').value = dress.quantity;
  document.getElementById('edit-status').value = dress.status;
  document.getElementById('edit-price').value = dress.rental_price;
  document.getElementById('edit-deposit').value = dress.deposit_price;
  document.getElementById('edit-description').value = dress.description || '';
  document.getElementById('edit-image').value = dress.image_url || '';
  bootstrap.Modal.getOrCreateInstance(document.getElementById('dressEditModal')).show();
}

async function editDress(event) {
  event.preventDefault();
  const id = Number(document.getElementById('edit-dress-id').value);
  const dressUpdateData = {
      category_id: Number(document.getElementById('edit-category').value),
      name: document.getElementById('edit-name').value.trim(),
      description: document.getElementById('edit-description').value.trim(),
      size: document.getElementById('edit-size').value.trim(),
      quantity: Number(document.getElementById('edit-quantity').value),
      rental_price: Number(document.getElementById('edit-price').value),
      deposit_price: Number(document.getElementById('edit-deposit').value),
      status: document.getElementById('edit-status').value,
      image_url: document.getElementById('edit-image').value.trim() || null
  };
  
  try {
    const result = await apiFetch(`/dresses/${id}`, { method: 'PUT', body: JSON.stringify(dressUpdateData) });
    bootstrap.Modal.getOrCreateInstance(document.getElementById('dressEditModal')).hide();
    showAlert(result?.message || 'Cập nhật thông tin váy thành công.');
    await loadDresses();
  } catch (error) { showAlert(error.message, 'danger'); }
}

async function deleteDress(id) {
  const dress = dressesCache.find(d => Number(d.id) === Number(id));
  if (!confirm(`Bà chắc chắn muốn xóa váy “${dress?.name || id}” (ID ${id})? Thao tác này không thể tự hoàn tác.`)) return;
  try {
    const result = await apiFetch(`/dresses/${id}`, { method: 'DELETE' });
    showAlert(result?.message || 'Xóa váy thành công.');
    await loadDresses();
  } catch (error) { showAlert(error.message, 'danger'); }
}

document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => showView(button.dataset.view)));
document.getElementById('refresh-orders').addEventListener('click', loadOrders);
document.getElementById('refresh-dresses').addEventListener('click', loadDresses);
document.getElementById('order-search').addEventListener('input', renderOrders);
document.getElementById('dress-search').addEventListener('input', renderDresses);
document.getElementById('dress-create-form').addEventListener('submit', createDress);
document.getElementById('dress-edit-form').addEventListener('submit', editDress);
// Khai báo sự kiện cho form quyết toán mới
document.getElementById('checkout-form')?.addEventListener('submit', submitCheckout);
document.getElementById('add-dress-btn').addEventListener('click', () => bootstrap.Modal.getOrCreateInstance(document.getElementById('dressCreateModal')).show());
document.getElementById('logout-btn').addEventListener('click', () => {
  localStorage.clear();
  window.location.replace('index.html');
});

if (guardAdmin()) loadOrders();