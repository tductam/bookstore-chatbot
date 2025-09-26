import sqlite3
import json

def get_db_connection():
    """Tạo kết nối tới database."""
    conn = sqlite3.connect('bookstore.db')
    conn.row_factory = sqlite3.Row # Giúp trả về kết quả dạng dictionary
    return conn

def search_book(title: str = None, author: str = None):
    """
    Tra cứu thông tin sách trong cơ sở dữ liệu dựa trên tên sách hoặc tác giả.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT title, author, price, stock, category FROM Books WHERE 1=1"
    params = []
    
    if title:
        query += " AND title LIKE ?"
        params.append(f"%{title}%")
    if author:
        query += " AND author LIKE ?"
        params.append(f"%{author}%")
        
    cursor.execute(query, params)
    books = cursor.fetchall()
    conn.close()
    
    if not books:
        return json.dumps({"message": "Không tìm thấy sách phù hợp."})
    
    # Chuyển kết quả thành list of dicts để dễ xử lý
    result = [dict(book) for book in books]
    return json.dumps(result)


def create_order(customer_name: str, phone: str, address: str, book_title: str, quantity: int):
    """
    Tạo một đơn hàng mới. Kiểm tra số lượng tồn kho trước khi tạo đơn.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Tìm book_id và kiểm tra tồn kho
    cursor.execute("SELECT book_id, stock, title FROM Books WHERE title LIKE ?", (f"%{book_title}%",))
    book = cursor.fetchone()
    
    if not book:
        conn.close()
        return json.dumps({"status": "failed", "message": f"Không tìm thấy sách có tên '{book_title}'."})
    
    book_id = book['book_id']
    exact_title = book['title']
    stock = book['stock']
    
    if stock < quantity:
        conn.close()
        return json.dumps({
            "status": "failed",
            "message": f"Rất tiếc, sách '{exact_title}' chỉ còn {stock} cuốn, không đủ số lượng bạn yêu cầu."
        })
        
    # 2. Tạo đơn hàng mới
    try:
        cursor.execute(
            "INSERT INTO Orders (customer_name, phone, address, book_id, quantity, status) VALUES (?, ?, ?, ?, ?, ?)",
            (customer_name, phone, address, book_id, quantity, 'pending')
        )
        order_id = cursor.lastrowid
        
        # 3. Cập nhật lại tồn kho
        new_stock = stock - quantity
        cursor.execute("UPDATE Books SET stock = ? WHERE book_id = ?", (new_stock, book_id))
        
        conn.commit()
        conn.close()
        
        return json.dumps({
            "status": "success",
            "message": f"Đã tạo đơn hàng thành công với mã #{order_id} cho sách '{exact_title}'. Cảm ơn bạn!",
            "order_id": order_id
        })
    except Exception as e:
        conn.rollback()
        conn.close()
        return json.dumps({"status": "error", "message": f"Đã có lỗi xảy ra: {e}"})
