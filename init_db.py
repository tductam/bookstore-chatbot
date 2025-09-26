import sqlite3

# Kết nối tới database (nếu chưa có sẽ tự tạo)
conn = sqlite3.connect('bookstore.db')
cursor = conn.cursor()

# Xóa bảng nếu đã tồn tại (để chạy lại không bị lỗi)
cursor.execute("DROP TABLE IF EXISTS Books")
cursor.execute("DROP TABLE IF EXISTS Orders")

# Tạo bảng Books
cursor.execute("""
CREATE TABLE Books (
    book_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL,
    category TEXT
)
""")

# Tạo bảng Orders
cursor.execute("""
CREATE TABLE Orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    phone TEXT,
    address TEXT,
    book_id INTEGER,
    quantity INTEGER,
    status TEXT,
    FOREIGN KEY (book_id) REFERENCES Books(book_id)
)
""")

# Chèn dữ liệu mẫu vào bảng Books
books_data = [
    ('Đắc Nhân Tâm', 'Dale Carnegie', 120000, 50, 'Kỹ năng sống'),
    ('Nhà Giả Kim', 'Paulo Coelho', 80000, 30, 'Tiểu thuyết'),
    ('Dế Mèn Phiêu Lưu Ký', 'Tô Hoài', 55000, 100, 'Thiếu nhi'),
    ('Tội Ác và Hình Phạt', 'Fyodor Dostoevsky', 150000, 20, 'Văn học cổ điển')
]

cursor.executemany("INSERT INTO Books (title, author, price, stock, category) VALUES (?, ?, ?, ?, ?)", books_data)

print("Database đã được tạo và chèn dữ liệu mẫu thành công!")

# Lưu thay đổi và đóng kết nối
conn.commit()
conn.close()
