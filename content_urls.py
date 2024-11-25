# content_urls.py

news_ = """
Yangiliklar:

  1. Yangi yangiliklar:
    Bugungi yangiliklar bo'limi yangilandi.

  2. alo aloalsldlsdlkvdflvmdflvmldfmvb
  gibikbnjknklnnlknmkll
  knklnknklnlknlknl
  
  gfnfgnfgfgnhjmnhgmn
"""

# Tashkilot boshqaruvi
org_urls = {
    'org_shifts': 'https://example.com/organization_shifts.pdf',
    'org_transport': 'https://example.com/organization_transport.pdf',
    'org_brigadasi': 'https://example.com/organization_transport.pdf',
    'org_xodimlari': 'https://example.com/organization_transport.pdf',
    'org_ixtisos_guruhi': 'https://example.com/organization_transport.pdf',
    'org_ish_urni': 'https://example.com/organization_transport.pdf'
}

# Personallarni boshqarish
personal_urls = {
    'personnel_schedule': 'https://example.com/personnel_schedule.pdf',
    'personnel_brigade': 'https://example.com/personnel_brigade.pdf'
}

# So'rovlar
surovlar_urls = {
    'requests_incoming': 'https://example.com/incoming_requests.pdf'

}

# Dispetcher-103
dispetcher_urls = {
    'dispatch_call': 'https://example.com/call_accept.pdf',
    'dispatch_direct': 'https://example.com/dispatch_direct.pdf',
    'dispatch_jadvali': 'https://example.com/dispatch_direct.pdf',
    'dispatch_kartalari': 'https://example.com/dispatch_direct.pdf'
}

# Ombor
ombor_urls = {
    'warehouse_yiguvchi': 'https://example.com/warehouse_inventory.pdf',
    'warehouse_serial': 'https://example.com/warehouse_serial.pdf',
    'warehouse_ombor': 'https://example.com/warehouse_serial.pdf',
    'warehouse_kirim': 'https://example.com/warehouse_serial.pdf',
    'warehouse_chiqim': 'https://example.com/warehouse_serial.pdf',
    'warehouse_qoldiq': 'https://example.com/warehouse_serial.pdf',
    'warehouse_inventor': 'https://example.com/warehouse_serial.pdf',
    'warehouse_suralgan_ehtiyoj': 'https://example.com/warehouse_serial.pdf',
    'warehouse_qabul_ehtiyoj': 'https://example.com/warehouse_serial.pdf'
}

# Yotoq xisobi 
yotoq_urls = {
    'yotoq_foydalanuvchilar': '2',
    'yotoq_bulimlar': 'https://example.com/regions.pdf',
    'yotoq_xonalar': 'https://example.com/cities.pdf',
    'yotoq_tushaklar': 'https://example.com/populated_places.pdf',
    'yotoq_yozuvlar': 'https://example.com/callers.pdf'
}

# FAQ savollar 
faq_video_ids = {

    "Savol 1": {"video": "BAACAgIAAxkBAAIKTmc-HK0jsjOGfvj1faa5lNXbaIN2AAKGVgACLl8ZSbJeqSYMo6rnNgQ", "txt": "BQACAgIAAxkBAAIKGGc-ClSDxkkMdeYt5MiNjpwec0kFAAJvVgACL8TxSSt2HcDgERMUNgQ"},
    "Savol 2": {"video": "BAACAgIAAxkBAAIKTmc-HK0jsjOGfvj1faa5lNXbaIN2AAKGVgACLl8ZSbJeqSYMo6rnNgQ", "txt": "BQACAgIAAxkBAAIKGGc-ClSDxkkMdeYt5MiNjpwec0kFAAJvVgACL8TxSSt2HcDgERMUNgQ"},
    "Savol 3": {"video": "BAACAgIAAxkBAAIKTmc-HK0jsjOGfvj1faa5lNXbaIN2AAKGVgACLl8ZSbJeqSYMo6rnNgQ", "txt": "BQACAgIAAxkBAAIKGGc-ClSDxkkMdeYt5MiNjpwec0kFAAJvVgACL8TxSSt2HcDgERMUNgQ"},
    "Savol 4": {"video": "BAACAgIAAxkBAAIKTmc-HK0jsjOGfvj1faa5lNXbaIN2AAKGVgACLl8ZSbJeqSYMo6rnNgQ", "txt": "BQACAgIAAxkBAAIKGGc-ClSDxkkMdeYt5MiNjpwec0kFAAJvVgACL8TxSSt2HcDgERMUNgQ"},
    "Savol 5": {"video": "BAACAgIAAxkBAAIKTmc-HK0jsjOGfvj1faa5lNXbaIN2AAKGVgACLl8ZSbJeqSYMo6rnNgQ", "txt": "BQACAgIAAxkBAAIKGGc-ClSDxkkMdeYt5MiNjpwec0kFAAJvVgACL8TxSSt2HcDgERMUNgQ"},
    
    "admin_global": {
        "video_id": "BAACAgIAAxkBAAIKTmc-HK0jsjOGfvj1faa5lNXbaIN2AAKGVgACLl8ZSbJeqSYMo6rnNgQ",
        "txt_id": "BQACAgIAAxkBAAIKGGc-ClSDxkkMdeYt5MiNjpwec0kFAAJvVgACL8TxSSt2HcDgERMUNgQ"
    },
    "admin_malumotnoma": {
        "video_id": "malumotnoma_video_id_here",
        "txt_id": "malumotnoma_txt_id_here"
    },
    "admin_dinamik": {
        "video_id": "dinamik_video_id_here",
        "txt_id": "dinamik_txt_id_here"
    },
    "admin_sozlamalar": {
        "video_id": "sozlamalar_video_id_here",
        "txt_id": "sozlamalar_txt_id_here"
    },
    "admin_xabarlar": {
        "video_id": "xabarlar_video_id_here",
        "txt_id": "xabarlar_txt_id_here"
    },
    "admin_sinx": {
        "video_id": "sinx_video_id_here",
        "txt_id": "sinx_txt_id_here"
    }
}

# Help bo'limi uchun URL yoki matnli ma'lumot
help_video_url = "https://example.com/video_guide"
help_text = """
      Botdan foydalanish uchun quyidagi ko'rsatmalarni o'qing:

1. **Bosh menyu** orqali asosiy bo'limlarga kirishingiz mumkin.
2. **FAQ** bo'limida sizga kerakli savolni tanlab, javobni olishishingiz mumkin.
3. **Help** bo'limidan siz video yoki matnli qo'llanmalarga murojaat qilishingiz mumkin.
"""
