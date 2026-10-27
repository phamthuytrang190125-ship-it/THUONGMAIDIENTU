from security import get_current_user, require_admin
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_db_connection
from schemas import OrderCreate, OrderStatusUpdate, OrderCheckout
import psycopg2
import psycopg2.extras
import jwt
from datetime import datetime

router = APIRouter()

# Phải giống SECRET_KEY và ALGORITHM trong auth.py
SECRET_KEY = "khoa_bi_mat_cua_du_an"
ALGORITHM = "HS256"

security = HTTPBearer()


# ==================================================
# 1. API TẠO ĐƠN THUÊ
# ==================================================
@router.post("/api/orders")
def create_order(
    order: OrderCreate,
    user: dict = Depends(get_current_user)
    ):
    if order.start_date > order.end_date:
        raise HTTPException(
            status_code=400,
            detail="Ngày bắt đầu không được lớn hơn ngày kết thúc."
        )

    conn = get_db_connection()
    cur = conn.cursor(
        cursor_factory=psycopg2.extras.DictCursor
    )

    try:
        # Kiểm tra váy có bị trùng lịch thuê không
        check_query = """
            SELECT ro.id
            FROM RentalOrders ro
            JOIN RentalOrderItems roi
                ON ro.id = roi.order_id
            WHERE roi.dress_id = %s
              AND ro.status IN ('CONFIRMED', 'RENTING')
              AND roi.start_date <= %s
              AND roi.end_date >= %s;
        """

        cur.execute(
            check_query,
            (
                order.dress_id,
                order.end_date,
                order.start_date
            )
        )

        if cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Váy này đã có người thuê trong thời gian bạn chọn."
            )

        # Lấy giá thuê và tiền cọc
        cur.execute(
            """
            SELECT rental_price, deposit_price
            FROM Dresses
            WHERE id = %s;
            """,
            (order.dress_id,)
        )

        dress = cur.fetchone()

        if not dress:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy váy."
            )

        total_amount = dress["rental_price"]
        deposit_amount = dress["deposit_price"]

        # Tạo mã đơn hàng
        order_code = f"VN{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Tạo đơn thuê
        cur.execute(
            """
            INSERT INTO RentalOrders
                (user_id, order_code, total_amount,
                 deposit_amount, shipping_address)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
            user["user_id"],
            order_code,
            total_amount,
            deposit_amount,
            order.shipping_address
        )
        )

        new_order_id = cur.fetchone()[0]

        # Tạo chi tiết đơn thuê
        cur.execute(
            """
            INSERT INTO RentalOrderItems
                (order_id, dress_id, start_date, end_date,
                 quantity, rental_price, deposit_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            (
                new_order_id,
                order.dress_id,
                order.start_date,
                order.end_date,
                1,
                dress["rental_price"],
                dress["deposit_price"]
            )
        )

        # Tạo thông tin thanh toán
        cur.execute(
            """
            INSERT INTO Payments (order_id, payment_method)
            VALUES (%s, %s);
            """,
            (new_order_id, order.payment_method)
        )

        conn.commit()

        return {
            "message": "Tạo đơn đặt váy thành công!",
            "order_id": new_order_id,
            "order_code": order_code
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        print("Lỗi tạo đơn thuê:", str(e))
        raise HTTPException(
            status_code=500,
            detail="Không thể tạo đơn thuê. Vui lòng kiểm tra Backend."
        )

    finally:
        cur.close()
        conn.close()



# ==================================================
# 2. API LẤY DANH SÁCH ĐƠN THUÊ CỦA KHÁCH ĐANG ĐĂNG NHẬP
# GET /api/my-orders
# ==================================================
@router.get("/api/my-orders")
def get_my_orders(
    user: dict = Depends(get_current_user)
):
    # Lấy user_id từ thông tin người dùng trong token
    user_id = user["user_id"]

    conn = get_db_connection()
    cur = conn.cursor(
        cursor_factory=psycopg2.extras.RealDictCursor
    )

    try:
        cur.execute(
            """
            SELECT
                ro.id,
                ro.order_code,
                ro.total_amount,
                ro.deposit_amount,
                ro.status,
                ro.created_at,
                ro.shipping_address,
                d.name AS dress_name,
                roi.start_date,
                roi.end_date,
                roi.quantity,
                t.amount AS refund_amount,
                t.note AS refund_note,
                p.payment_method
            FROM RentalOrders ro
            JOIN RentalOrderItems roi
                ON ro.id = roi.order_id
            JOIN Dresses d
                ON roi.dress_id = d.id
            LEFT JOIN Transactions t 
                ON ro.id = t.order_id AND t.transaction_type = 'REFUND'
            LEFT JOIN Payments p 
                ON ro.id = p.order_id
            WHERE ro.user_id = %s
            ORDER BY ro.created_at DESC;
            """,
            (user_id,)
        )

        orders = cur.fetchall()
        return orders

    except Exception as e:
        print("Lỗi lấy đơn thuê của khách:", str(e))
        raise HTTPException(
            status_code=500,
            detail="Không thể lấy danh sách đơn thuê."
        )

    finally:
        cur.close()
        conn.close()


# ==================================================
# 3. API LẤY TẤT CẢ ĐƠN THUÊ (CHO ADMIN)
# ==================================================
@router.get("/api/orders")
def get_all_orders(admin: dict = Depends(require_admin)):
    conn = get_db_connection()
    cur = conn.cursor(
        cursor_factory=psycopg2.extras.RealDictCursor
    )

    try:
        cur.execute(
            """
            SELECT
                ro.id,
                ro.order_code,
                ro.total_amount,
                ro.deposit_amount,
                ro.status,
                ro.created_at,
                u.full_name,
                u.phone
            FROM RentalOrders ro
            JOIN Users u
                ON ro.user_id = u.id
            ORDER BY ro.created_at DESC;
            """
        )

        return cur.fetchall()

    except Exception as e:
        print("Lỗi lấy danh sách đơn thuê:", str(e))
        raise HTTPException(
            status_code=500,
            detail="Không thể lấy danh sách đơn thuê."
        )

    finally:
        cur.close()
        conn.close()


# ==================================================
# 4. API CẬP NHẬT TRẠNG THÁI ĐƠN THUÊ (CHO ADMIN) & HOÀN TIỀN
# ==================================================
@router.put("/api/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    admin: dict = Depends(require_admin)
):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT status FROM RentalOrders WHERE id = %s;", (order_id,))
        order_info = cur.fetchone()
        
        if not order_info:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng.")
            
        current_status = order_info[0]
        new_status = status_data.status

        # Cập nhật trạng thái
        cur.execute(
            "UPDATE RentalOrders SET status = %s WHERE id = %s RETURNING id;",
            (new_status, order_id)
        )

        # Lưu lịch sử thay đổi vào bảng OrderLogs
        cur.execute(
            """
            INSERT INTO OrderLogs (order_id, old_status, new_status, note)
            VALUES (%s, %s, %s, %s)
            """,
            (order_id, current_status, new_status, "Admin cập nhật trạng thái đơn hàng")
        )

        conn.commit()
        return {"message": f"Đã cập nhật trạng thái đơn hàng thành {new_status}."}

    except Exception as e:
        conn.rollback()
        print("Lỗi cập nhật trạng thái đơn:", str(e))
        raise HTTPException(status_code=500, detail="Không thể cập nhật trạng thái đơn thuê.")
    finally:
        cur.close()
        conn.close()


# ==================================================
# 5. API QUYẾT TOÁN & HOÀN CỌC (API MỚI ĐỂ THẦY CHẤM ĐIỂM)
# ==================================================
@router.post("/api/orders/{order_id}/checkout")
def checkout_order(
    order_id: int,
    checkout_data: OrderCheckout,
    admin: dict = Depends(require_admin)
):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 1. Lấy tiền cọc và trạng thái hiện tại
        cur.execute(
            "SELECT status, deposit_amount FROM RentalOrders WHERE id = %s;",
            (order_id,)
        )
        order_info = cur.fetchone()
        
        if not order_info:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng.")
            
        current_status = order_info[0]
        deposit_amount = float(order_info[1])
        
        if current_status == "COMPLETED":
            raise HTTPException(status_code=400, detail="Đơn hàng này đã được quyết toán rồi!")

        # 2. Tính toán tiền hoàn lại (Cọc - Phạt hư - Phạt trễ)
        refund_amount = deposit_amount - checkout_data.damage_fee - checkout_data.late_fee
        if refund_amount < 0:
            refund_amount = 0 # Nếu tiền phạt lớn hơn tiền cọc thì hoàn 0 đồng

        # 3. Cập nhật bảng RentalOrders (Chuyển sang COMPLETED và lưu tiền phạt)
        cur.execute(
            """
            UPDATE RentalOrders
            SET status = 'COMPLETED',
                return_condition = %s,
                damage_fee = %s,
                late_fee = %s
            WHERE id = %s;
            """,
            (checkout_data.return_condition, checkout_data.damage_fee, checkout_data.late_fee, order_id)
        )

        # 4. Ghi nhận giao dịch Hoàn tiền vào bảng Transactions
        note_transaction = f"Tình trạng váy: {checkout_data.return_condition}. Phạt hư hỏng: {checkout_data.damage_fee}đ. Phạt trễ: {checkout_data.late_fee}đ. Ghi chú: {checkout_data.note}"
        cur.execute(
            """
            INSERT INTO Transactions (order_id, amount, transaction_type, note)
            VALUES (%s, %s, %s, %s)
            """,
            (order_id, refund_amount, 'REFUND', note_transaction)
        )

        # 5. Lưu vào OrderLogs
        cur.execute(
            """
            INSERT INTO OrderLogs (order_id, old_status, new_status, note)
            VALUES (%s, %s, %s, %s)
            """,
            (order_id, current_status, 'COMPLETED', "Admin đã kiểm tra và quyết toán hoàn cọc")
        )

        conn.commit()
        return {
            "message": "Quyết toán thành công!",
            "refund_amount": refund_amount
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print("Lỗi quyết toán đơn:", str(e))
        raise HTTPException(status_code=500, detail="Không thể quyết toán đơn hàng.")
    finally:
        cur.close()
        conn.close()


# ==================================================
# 6. API KHÁCH HÀNG TỰ HỦY ĐƠN HÀNG (KHI CHỜ XÁC NHẬN)
# ==================================================
@router.put("/api/orders/{order_id}/cancel")
def customer_cancel_order(
    order_id: int,
    current_user: dict = Depends(get_current_user)
):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # 1. Kiểm tra đơn hàng có tồn tại và thuộc về user này không
        cur.execute(
            "SELECT status FROM RentalOrders WHERE id = %s AND user_id = %s;",
            (order_id, current_user['user_id'])
        )
        order_info = cur.fetchone()
        
        if not order_info:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng.")
            
        current_status = order_info[0]
        
        # 2. Chặn không cho hủy nếu Admin đã xác nhận hoặc đang thuê
        if current_status != "PENDING":
            raise HTTPException(status_code=400, detail="Không thể tự hủy! Đơn hàng đã được xử lý, vui lòng liên hệ cửa hàng.")

        # 3. Cập nhật trạng thái thành CANCELLED
        cur.execute(
            "UPDATE RentalOrders SET status = 'CANCELLED' WHERE id = %s;",
            (order_id,)
        )

        # 4. Ghi Log lịch sử
        cur.execute(
            """
            INSERT INTO OrderLogs (order_id, old_status, new_status, note)
            VALUES (%s, %s, %s, %s)
            """,
            (order_id, current_status, 'CANCELLED', "Khách hàng tự đổi ý và hủy đơn")
        )

        conn.commit()
        return {"message": "Đã hủy đơn hàng thành công!"}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print("Lỗi hủy đơn:", str(e))
        raise HTTPException(status_code=500, detail="Không thể hủy đơn hàng.")
    finally:
        cur.close()
        conn.close()