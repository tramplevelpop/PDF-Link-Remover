# -*- coding: utf-8 -*-
"""
Hamedoz PDF - Worker Node
هذا الملف هو المسؤول عن سحب المهام من قاعدة البيانات ومعالجتها
"""

import os
import io
import time
import traceback
import uuid
from pyrogram import Client
from dotenv import load_dotenv
from pymongo import MongoClient
import pdf_engine  # تأكد أن هذا الملف موجود في نفس المجلد

# 1. تحميل الإعدادات من ملف .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(env_path)

# 2. استلام المتغيرات وتجهيزها
try:
    API_ID = int(os.getenv("API_ID"))
    API_HASH = os.getenv("API_HASH")
    # نستخدم جلسة مختلفة للـ Worker لتجنب التداخل
    TG_SESSION = os.getenv("TG_SESSION", "worker_session")
    MONGO_URI = os.getenv("MONGO_URI")
    TG_TARGET_CHAT = int(os.getenv("TG_TARGET_CHAT"))
except TypeError:
    print("❌ خطأ: تأكد من ضبط جميع المتغيرات في ملف .env بشكل صحيح")
    exit()

# 3. الاتصال بقاعدة البيانات MongoDB
# قمنا بتعريف 'mongo' أولاً قبل استخدامه لتجنب NameError
try:
    mongo = MongoClient(MONGO_URI)
    db = mongo["pdf_distributed"]
    jobs = db["jobs"]
    print("✅ تم الاتصال بقاعدة البيانات بنجاح")
except Exception as e:
    print(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
    exit()

# 4. تشغيل عميل تليجرام (Pyrogram)
# الـ workdir هو نفس مجلد الملف لسهولة الوصول لملف الـ session
pyro = Client(
    TG_SESSION, 
    api_id=API_ID, 
    api_hash=API_HASH, 
    workdir=BASE_DIR
)

def start_worker():
    print("🚀 الـ Worker بدأ العمل الآن ويراقب المهام...")
    
    with pyro:
        while True:
            try:
                # البحث عن مهمة حالتها 'pending' وتغييرها لـ 'processing'
                job = jobs.find_one_and_update(
                    {"status": "pending"},
                    {"$set": {"status": "processing"}},
                    sort=[("created_at", 1)]
                )

                if not job:
                    # لو مفيش مهام، انتظر ثانيتين وشوف تاني
                    time.sleep(2)
                    continue

                job_id = job["job_id"]
                input_file_id = job["input_file_id"]
                task_type = job.get("task_type", "remove_links")
                
                print(f"📦 جاري معالجة مهمة جديدة: {task_type} (ID: {job_id})")

                # تحميل الملف من تليجرام إلى الذاكرة
                file_bytes = io.BytesIO()
                pyro.download_media(input_file_id, file_bytes)
                file_bytes.seek(0)

                # تنفيذ المعالجة عبر محرك الـ PDF
                # نمرر الـ task_type والملف للمحرك
                output_bytes = pdf_engine.process(task_type, file_bytes)
                output_bytes.seek(0)
                output_bytes.name = f"result_{job_id}.pdf"

                # رفع الملف الناتج لتليجرام
                sent = pyro.send_document(
                    TG_TARGET_CHAT, 
                    output_bytes, 
                    caption=f"✅ تم الانتهاء من المهمة: {task_type}\nJob ID: {job_id}"
                )
                
                # تحديث حالة المهمة في الداتابيز ووضع رابط الملف الجديد
                jobs.update_one(
                    {"job_id": job_id},
                    {"$set": {
                        "status": "completed",
                        "output_file_id": sent.document.file_id,
                        "finished_at": time.time()
                    }}
                )
                print(f"✅ تم إنهاء المهمة {job_id} بنجاح.")

            except Exception as e:
                print(f"⚠️ خطأ أثناء المعالجة: {e}")
                traceback.print_exc()
                if 'job_id' in locals():
                    jobs.update_one(
                        {"job_id": job_id},
                        {"$set": {"status": "failed", "reason": str(e)}}
                    )
                time.sleep(5)

if __name__ == "__main__":
    start_worker()