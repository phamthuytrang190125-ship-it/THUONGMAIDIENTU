-- 1. TẠO BẢNG CATEGORIES (Danh mục)
CREATE TABLE Categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- 2. TẠO BẢNG USERS (Người dùng)
CREATE TABLE Users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'CUSTOMER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. TẠO BẢNG DRESSES (Sản phẩm váy)
CREATE TABLE Dresses (
    id SERIAL PRIMARY KEY,
    category_id INT REFERENCES Categories(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    size VARCHAR(10),
    quantity INT DEFAULT 1, -- Bổ sung SoLuong theo ERD
    rental_price NUMERIC(12, 2) NOT NULL,
    deposit_price NUMERIC(12, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'AVAILABLE',
    image_url TEXT
);

-- 4. TẠO BẢNG RENTAL_ORDERS (Đơn thuê)
CREATE TABLE RentalOrders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(id) ON DELETE CASCADE,
    order_code VARCHAR(50) UNIQUE NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    deposit_amount NUMERIC(12, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    shipping_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. TẠO BẢNG RENTAL_ORDER_ITEMS (Chi tiết đơn thuê)
CREATE TABLE RentalOrderItems (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES RentalOrders(id) ON DELETE CASCADE,
    dress_id INT REFERENCES Dresses(id) ON DELETE RESTRICT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    quantity INT DEFAULT 1, -- Bổ sung SoLuong theo ERD
    rental_price NUMERIC(12, 2) NOT NULL,
    deposit_price NUMERIC(12, 2) NOT NULL
);

ALTER TABLE RentalOrders
ADD COLUMN return_condition VARCHAR(255),
ADD COLUMN damage_fee NUMERIC(12, 2) DEFAULT 0,
ADD COLUMN late_fee NUMERIC(12, 2) DEFAULT 0;

CREATE TABLE OrderLogs (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES RentalOrders(id) ON DELETE CASCADE,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. TẠO BẢNG PAYMENTS (Thanh toán)
CREATE TABLE Payments (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES RentalOrders(id) ON DELETE CASCADE,
    payment_method VARCHAR(50),
    payment_status VARCHAR(50) DEFAULT 'UNPAID',
    paid_at TIMESTAMP
);

--7. transaction (lịch sửs)
CREATE TABLE Transactions (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES rentalorders(id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS Transactions; -- Xóa bảng cũ nếu bị lỗi cấu trúc
CREATE TABLE Transactions (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES RentalOrders(id) ON DELETE CASCADE,
    amount DECIMAL(12,2) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SELECT * FROM Payments ORDER BY id DESC;
SELECT * FROM Transactions;
---------------------------------------------------------
-- CHÈN DỮ LIỆU MẪU (SEED DATA)
---------------------------------------------------------
INSERT INTO Categories (name, description) VALUES
('Váy Cúp Ngực', 'Các mẫu váy cưới cúp ngực quyến rũ'),
('Váy Đuôi Cá', 'Váy cưới ôm dáng, đuôi xòe'),
('Váy Chữ A', 'Váy dáng chữ A thanh lịch, dễ mặc');

INSERT INTO Users (full_name, email, phone, password_hash, role) VALUES
('Quản Trị Viên', 'admin@shop.com', '0901234567', 'hashed_password_here', 'ADMIN'),
('Khách Hàng Một', 'khach1@gmail.com', '0912345678', 'hashed_password_here', 'CUSTOMER'),
('Khách Hàng Hai', 'khach2@gmail.com', '0987654321', 'hashed_password_here', 'CUSTOMER');

-- Đã thêm số lượng (quantity)
INSERT INTO Dresses (category_id, name, description, size, quantity, rental_price, deposit_price, status) VALUES
(1, 'Váy Cúp Ngực Đính Hoa 3D', 'Váy xòe bồng bềnh đính hoa nổi cao cấp', 'M', 2, 1500000, 3000000, 'AVAILABLE'),
(1, 'Váy Cúp Ngực Đính Đá Lấp Lánh', 'Form váy chuẩn, đính đá pha lê Swarovski', 'S', 1, 2000000, 4000000, 'AVAILABLE'),
(2, 'Váy Đuôi Cá Trễ Vai Tinh Tế', 'Tôn vóc dáng với thiết kế trễ vai quyến rũ', 'M', 1, 1800000, 3500000, 'AVAILABLE'),
(3, 'Váy Chữ A Tối Giản Thanh Lịch', 'Thiết kế lụa trơn sang trọng, hiện đại', 'L', 3, 1200000, 2000000, 'AVAILABLE'),
(3, 'Váy Chữ A Tay Bồng Cổ Điển', 'Phong cách vintage với tay bồng nhẹ nhàng', 'S', 1, 1300000, 2500000, 'MAINTENANCE');


-- Xem đơn hàng vừa đặt
SELECT * FROM RentalOrders ORDER BY created_at DESC;

-- Xem chi tiết phương thức thanh toán của đơn đó
SELECT * FROM Payments ORDER BY id DESC;

UPDATE Users
SET password_hash = '$2b$12$n/Y0jUZrkkQzfbQED0dypODNkdp03eizTspJo/RGAK7eBdP0aT5nK',
    role = 'ADMIN'
WHERE email = 'admin@shop.com';
-- mk admin ms : AdminVayCuoi@2026
-- Kiểm tra kết quả
SELECT id, full_name, email, role
FROM Users


INSERT INTO Dresses (category_id, name, description, size, quantity, rental_price, deposit_price, status) 
VALUES (1, 'Váy Công Chúa Bồng Bềnh Pha Lê', 'Thiết kế form lộng lẫy, đính pha lê thủ công', 'S', 1, 2500000, 5000000, 'AVAILABLE');

--Kiểm tra bảng Lịch sử trạng thái (OrderLogs)
SELECT * FROM OrderLogs 
WHERE order_id = 11 
ORDER BY created_at ASC;

--Kiểm tra bảng Giao dịch tiền bạc (Transactions)
SELECT * FROM Transactions 
WHERE order_id = 11;

--Kiểm tra bảng Đơn hàng chính (RentalOrders)
SELECT id, status, return_condition, damage_fee, late_fee 
FROM RentalOrders 
WHERE id = 11;