from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import get_db_connection
from security import require_admin
import psycopg2.extras

router = APIRouter()


class DressCreate(BaseModel):
    category_id: int
    name: str
    description: str
    size: str
    quantity: int
    rental_price: int
    deposit_price: int
    status: str
    image_url: Optional[str] = None


class DressUpdate(BaseModel):
    description: str


# API lấy danh sách váy, tìm kiếm và lọc
# Khách hàng chưa đăng nhập vẫn có thể xem
@router.get("/api/dresses")
def get_dresses(search: str = None, category: int = None):
    conn = get_db_connection()
    cur = conn.cursor(
        cursor_factory=psycopg2.extras.RealDictCursor
    )

    try:
        query = "SELECT * FROM Dresses WHERE status = 'AVAILABLE'"
        params = []

        if search:
            query += " AND name ILIKE %s"
            params.append(f"%{search}%")

        if category:
            query += " AND category_id = %s"
            params.append(category)

        query += " ORDER BY id DESC"

        cur.execute(query, tuple(params))
        dresses = cur.fetchall()

        return dresses

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Không thể lấy danh sách váy."
        )

    finally:
        cur.close()
        conn.close()


# API thêm váy - chỉ ADMIN
@router.post("/api/dresses")
def create_dress(
    dress: DressCreate,
    admin: dict = Depends(require_admin)
):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT INTO Dresses (
                category_id, name, description, size,
                quantity, rental_price, deposit_price,
                status, image_url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (
                dress.category_id,
                dress.name,
                dress.description,
                dress.size,
                dress.quantity,
                dress.rental_price,
                dress.deposit_price,
                dress.status,
                dress.image_url
            )
        )

        new_id = cur.fetchone()[0]
        conn.commit()

        return {
            "message": "Thêm váy thành công!",
            "dress_id": new_id
        }

    except Exception as e:
        conn.rollback()
        print("LOI THEM VAY:", repr(e))
        raise HTTPException(
            status_code=500,
            detail="Không thể thêm sản phẩm."
        )

    finally:
        cur.close()
        conn.close()

# API xóa váy - chỉ ADMIN
@router.delete("/api/dresses/{dress_id}")
def delete_dress(
    dress_id: int,
    admin: dict = Depends(require_admin)
):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "DELETE FROM Dresses WHERE id = %s RETURNING id;",
            (dress_id,)
        )
        deleted = cur.fetchone()

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy sản phẩm với ID này."
            )

        conn.commit()

        return {
            "message": f"Đã xóa thành công váy có ID là {dress_id}"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Không thể xóa sản phẩm."
        )

    finally:
        cur.close()
        conn.close()


# API sửa mô tả váy - chỉ ADMIN
@router.put("/api/dresses/{dress_id}")
def update_dress(
    dress_id: int,
    dress: DressUpdate,
    admin: dict = Depends(require_admin)
):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE Dresses
            SET description = %s
            WHERE id = %s
            RETURNING id;
            """,
            (dress.description, dress_id)
        )

        updated = cur.fetchone()

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy sản phẩm với ID này."
            )

        conn.commit()

        return {"message": "Cập nhật mô tả thành công!"}

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail="Không thể cập nhật sản phẩm."
        )

    finally:
        cur.close()
        conn.close()
