import sqlite3

def check_products():
    """Kiểm tra và hiển thị tất cả sản phẩm"""
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()

    # Lấy tất cả sản phẩm
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    print(f"\n{'='*80}")
    print(f"📦 TOTAL PRODUCTS: {len(products)}")
    print(f"{'='*80}\n")

    if products:
        # Lấy tên cột
        cursor.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # In header
        print(" | ".join(columns))
        print("-" * 80)
        
        # In từng sản phẩm
        for product in products:
            print(" | ".join(str(item) for item in product))
    else:
        print("⚠️  No products found in database!")

    conn.close()
    return len(products)

def remove_duplicates():
    """Xóa các sản phẩm trùng lặp"""
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()

    print("\n🔧 Đang xóa sản phẩm trùng lặp...")
    
    # Xóa các bản ghi trùng lặp, giữ lại ID nhỏ nhất
    cursor.execute("""
        DELETE FROM products 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM products 
            GROUP BY name, description, price, category
        )
    """)

    conn.commit()
    deleted_count = cursor.rowcount
    
    if deleted_count > 0:
        print(f"✅ Đã xóa {deleted_count} sản phẩm trùng lặp")
    else:
        print(f"✅ Không có sản phẩm trùng lặp")

    # Kiểm tra lại số lượng
    cursor.execute("SELECT COUNT(*) FROM products")
    remaining = cursor.fetchone()[0]
    print(f"📦 Còn lại: {remaining} sản phẩm\n")

    conn.close()
    return deleted_count

def reset_auto_increment():
    """Reset auto increment ID sau khi xóa"""
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    
    # Lấy ID lớn nhất hiện tại
    cursor.execute("SELECT MAX(id) FROM products")
    max_id = cursor.fetchone()[0]
    
    if max_id:
        # Reset sqlite_sequence
        cursor.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = 'products'", (max_id,))
        conn.commit()
        print(f"✅ Đã reset auto increment ID về {max_id}")
    
    conn.close()

if __name__ == "__main__":
    # Hiển thị sản phẩm hiện tại
    print("📊 TRƯỚC KHI DỌN DẸP:")
    initial_count = check_products()
    
    # Xóa trùng lặp
    deleted = remove_duplicates()
    
    # Reset auto increment
    if deleted > 0:
        reset_auto_increment()
    
    # Hiển thị lại sau khi dọn dẹp
    print("\n📊 SAU KHI DỌN DẸP:")
    final_count = check_products()
    
    print(f"\n{'='*80}")
    print(f"✨ HOÀN TẤT!")
    print(f"   - Số sản phẩm ban đầu: {initial_count}")
    print(f"   - Đã xóa: {deleted}")
    print(f"   - Còn lại: {final_count}")
    print(f"{'='*80}\n")