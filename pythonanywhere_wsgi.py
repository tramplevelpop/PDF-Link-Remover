#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 WSGI Configuration for PythonAnywhere
استخدم هذا الملف كـ WSGI application على PythonAnywhere
"""

import sys
import os

# إضافة مسار المشروع
project_home = '/home/hamedozer/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# استيراد التطبيق من app_gateway
from app_gateway import app as application

# لا تضع أي شيء آخر هنا
# PythonAnywhere سيستخدم 'application' تلقائياً
