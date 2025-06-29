#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح قاعدة البيانات للنظام المحسن
"""

import sqlite3
import os

def fix_enhanced_database():
    """إصلاح قاعدة البيانات للنظام المحسن"""
    print("🔧 إصلاح قاعدة البيانات للنظام المحسن...")
    
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # التحقق من هيكل جدول المعاملات
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 الأعمدة الحالية في جدول المعاملات: {columns}")
        
        # إضافة العمود المفقود إذا لم يكن موجوداً
        if 'transaction_type' not in columns:
            print("➕ إضافة عمود transaction_type...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN transaction_type TEXT DEFAULT 'transfer'")
            conn.commit()
            print("✅ تم إضافة عمود transaction_type")
        
        # التحقق من هيكل جدول الحسابات
        cursor.execute("PRAGMA table_info(accounts)")
        acc_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 الأعمدة الحالية في جدول الحسابات: {acc_columns}")
        
        if 'account_type' not in acc_columns:
            print("➕ إضافة عمود account_type...")
            cursor.execute("ALTER TABLE accounts ADD COLUMN account_type TEXT DEFAULT 'general'")
            conn.commit()
            print("✅ تم إضافة عمود account_type")
        
        # تنظيف البيانات التجريبية القديمة
        print("🧹 تنظيف البيانات التجريبية القديمة...")
        test_users = [999999, 888888]
        for user_id in test_users:
            cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM accounts WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        conn.commit()
        print("✅ تم تنظيف البيانات التجريبية")
        
        # إعادة إنشاء الجداول بالهيكل الصحيح إذا لزم الأمر
        print("🔄 التحقق من هيكل الجداول...")
        
        # التحقق من وجود جميع الأعمدة المطلوبة
        cursor.execute("PRAGMA table_info(transactions)")
        trans_columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        required_trans_columns = {
            'id': 'INTEGER',
            'user_id': 'INTEGER', 
            'transaction_type': 'TEXT',
            'from_account': 'TEXT',
            'to_account': 'TEXT',
            'amount': 'REAL',
            'description': 'TEXT',
            'created_at': 'TIMESTAMP'
        }
        
        missing_columns = []
        for col_name, col_type in required_trans_columns.items():
            if col_name not in trans_columns:
                missing_columns.append((col_name, col_type))
        
        if missing_columns:
            print(f"➕ إضافة الأعمدة المفقودة: {missing_columns}")
            for col_name, col_type in missing_columns:
                default_value = "DEFAULT ''" if col_type == 'TEXT' else "DEFAULT 0" if col_type in ['INTEGER', 'REAL'] else "DEFAULT CURRENT_TIMESTAMP"
                cursor.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_type} {default_value}")
            conn.commit()
            print("✅ تم إضافة الأعمدة المفقودة")
        
        conn.close()
        print("🎉 تم إصلاح قاعدة البيانات بنجاح!")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إصلاح قاعدة البيانات: {e}")
        return False

def create_fresh_database():
    """إنشاء قاعدة بيانات جديدة بالهيكل الصحيح"""
    print("🆕 إنشاء قاعدة بيانات جديدة...")
    
    try:
        # حذف قاعدة البيانات القديمة إذا كانت موجودة
        if os.path.exists("database.db"):
            os.remove("database.db")
            print("🗑️ تم حذف قاعدة البيانات القديمة")
        
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # إنشاء جدول المستخدمين
        cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY
        )
        """)
        
        # إنشاء جدول الحسابات
        cursor.execute("""
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            balance REAL DEFAULT 0,
            account_type TEXT DEFAULT 'general',
            UNIQUE(user_id, name)
        )
        """)
        
        # إنشاء جدول المعاملات
        cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            transaction_type TEXT DEFAULT 'transfer',
            from_account TEXT,
            to_account TEXT,
            amount REAL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ تم إنشاء قاعدة بيانات جديدة بنجاح!")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")
        return False

if __name__ == "__main__":
    print("🔧 أداة إصلاح قاعدة البيانات للنظام المحسن")
    print("=" * 50)
    
    # محاولة الإصلاح أولاً
    if fix_enhanced_database():
        print("✅ تم الإصلاح بنجاح!")
    else:
        print("⚠️ فشل الإصلاح، سيتم إنشاء قاعدة بيانات جديدة...")
        if create_fresh_database():
            print("✅ تم إنشاء قاعدة بيانات جديدة!")
        else:
            print("❌ فشل في إنشاء قاعدة بيانات جديدة")
    
    print("\n🎯 يمكنك الآن تشغيل الاختبار مرة أخرى:")
    print("   python3 test_enhanced_bot.py")

