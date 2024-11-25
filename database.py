from datetime import datetime
import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2 import OperationalError

# Postgres'ga ulanish
def get_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="bot_database",
            user="bot_user",
            password="Pa$$w0rd"
        )
        return conn
    except OperationalError as e:
        print(f"Database connection error: {e}")
        return None  # Agar ulanishda xatolik bo'lsa, None qaytaramiz

# Foydalanuvchini bazaga qo'shish funksiyasi
def add_user(user_id, viloyat, tuman, full_name, lavozim):
    conn = get_connection()  # Ulanishni olish
    if conn is None:  # Agar ulanish amalga oshmagan bo'lsa, xato chiqaramiz
        print("Failed to connect to the database.")
        return  # Ulanish muvaffaqiyatsiz bo'lsa, funksiyani to'xtatish
    with conn.cursor() as cursor:
        query = sql.SQL("""
            INSERT INTO users (user_id, viloyat, tuman, full_name, lavozim, registered_at)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE
                SET viloyat = EXCLUDED.viloyat,
                    tuman = EXCLUDED.tuman,
                    full_name = EXCLUDED.full_name,
                    lavozim = EXCLUDED.lavozim,
                    registered_at = EXCLUDED.registered_at
        """)
        cursor.execute(query, (user_id, viloyat, tuman, full_name, lavozim))
    conn.commit()  # O'zgarishlarni bazaga saqlash
    conn.close()  # Ulanishni yopish

# Foydalanuvchini ID orqali qidirish funksiyasi
def get_user_by_id(user_id):
    connection = get_connection()  # Ma'lumotlar bazasiga ulanish
    if connection is None:
        return None  # Agar ulanish amalga oshmagan bo'lsa, None qaytarish

    try:
        with connection.cursor() as cursor:
            # Foydalanuvchini ID bo'yicha qidirish
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()  # Faqat bitta foydalanuvchini olish

        return user  # Agar foydalanuvchi bo'lsa, uni qaytarish
    finally:
        connection.close()  # Ulanishni yopish
        
def get_user_from_url_log(user_id):
    connection = get_connection()  # Ma'lumotlar bazasiga ulanish
    if connection is None:
        return None  # Agar ulanish amalga oshmagan bo'lsa, None qaytarish

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM url_log WHERE user_id = %s", (user_id,))
            user_log = cursor.fetchone()  # Faqat bitta logni olish
        return user_log  # Agar log mavjud bo'lsa, uni qaytarish
    finally:
        connection.close()  # Ulanishni yopish

# URL loglash funksiyasi
def log_url_action(user_id, button_name, url):
    conn = get_connection()  # Ma'lumotlar bazasiga ulanish
    if conn is None:
        print("Failed to connect to the database.")
        return

    try:
        with conn.cursor() as cursor:
            # URL loglash uchun yozuvni qo'shish
            cursor.execute("""
                INSERT INTO url_log (user_id, button_name, url)
                VALUES (%s, %s, %s)
            """, (user_id, button_name, url))
        conn.commit()  # O'zgarishlarni saqlash
    except Exception as e:
        print(f"Error while logging URL action: {e}")
    finally:
        conn.close()  # Ulanishni yopish
        
# Respublika bo'yicha umumiy hisobotni yaratish SQL so'rovi
def get_republic_report_sql():
    return """
    SELECT
        ROW_NUMBER() OVER (ORDER BY u.viloyat, u.tuman) AS raqam,
        u.viloyat,
        u.tuman,
        COUNT(ul.button_name) AS tuman_button_count
    FROM
        users u
    LEFT JOIN
        url_log ul ON u.user_id = ul.user_id
    GROUP BY
        u.viloyat, u.tuman
    ORDER BY
        u.viloyat, u.tuman;
    """


# Viloyatlar ro'yxatini olish SQL so'rovi
def get_regions_sql():
    return "SELECT DISTINCT viloyat FROM users"

        
# Tanlangan viloyat bo'yicha hisobotni yaratish SQL so'rovi
def get_region_report_sql(region):
    return """
    SELECT
        ROW_NUMBER() OVER (ORDER BY u.viloyat, u.tuman) AS raqam,
        u.viloyat,
        u.tuman,
        COUNT(ul.button_name) AS tuman_button_count
    FROM
        users u
    LEFT JOIN
        url_log ul ON u.user_id = ul.user_id
    WHERE
        u.viloyat = %s
    GROUP BY
        u.viloyat, u.tuman
    ORDER BY
        u.tuman;
    """

        
def get_total_users_count():
    try:
        # Postgres ma'lumotlar bazasiga ulanish
        conn = get_connection()
        if conn is None:
            return "Foydalanuvchilar sonini olishda xatolik: Bazaga ulanib bo'lmadi"

        # SQL so'rovi: users jadvalidagi "user_id" ustuni bo'yicha jami foydalanuvchilarni olish
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(user_id) FROM users")
            result = cursor.fetchone()
            
            if result and result[0]:
                return result[0]  # Foydalanuvchilar soni
            else:
                return 0  # Agar ma'lumotlar bazasida foydalanuvchilar bo'lmasa, 0 qaytaring

    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
        return "Xatolik yuz berdi. Foydalanuvchilar soni olishda muammo bor."
    finally:
        if conn:
            conn.close()
