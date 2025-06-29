#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أداة اختبار شاملة للمساعد المحاسبي الذكي المحسن
تاريخ الإنشاء: يونيو 2025
المؤلف: Manus AI
الإصدار: 3.0 (محسن)
"""

import sys
import os
from datetime import datetime

# إضافة المسار الحالي لاستيراد الوحدات
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_functions():
    """اختبار وظائف قاعدة البيانات المحسنة"""
    print("🧪 اختبار وظائف قاعدة البيانات المحسنة...")
    
    try:
        from database_enhanced import (
            create_user, add_account, add_cash_in_transaction, add_cash_out_transaction,
            add_transfer_transaction, get_current_cash_balance, format_balance_status,
            get_user_accounts, delete_account, delete_transaction, update_transaction,
            get_transaction_by_id, calculate_advanced_balances
        )
        
        # إنشاء مستخدم تجريبي
        test_user_id = 999999
        create_user(test_user_id)
        print("✅ إنشاء المستخدم التجريبي")
        
        # إضافة حسابات متنوعة
        accounts_to_add = [
            ("صندوق المحل", "asset"),
            ("بنك الراجحي", "asset"),
            ("عميل أحمد", "for_us"),
            ("مورد القرطاسية", "for_them"),
            ("مصاريف الكهرباء", "expense")
        ]
        
        for acc_name, expected_type in accounts_to_add:
            result = add_account(test_user_id, acc_name)
            if "✅" in result:
                print(f"✅ إضافة حساب: {acc_name} (نوع: {expected_type})")
            else:
                print(f"❌ فشل إضافة حساب: {acc_name} - {result}")
                return False
        
        # اختبار معاملات مختلفة
        transactions_to_test = [
            ("cash_in", None, "صندوق المحل", 5000, "رأس المال الأولي"),
            ("cash_out", "صندوق المحل", None, 1000, "شراء بضاعة"),
            ("transfer", "صندوق المحل", "بنك الراجحي", 2000, "إيداع في البنك"),
            ("transfer", "عميل أحمد", "صندوق المحل", 1500, "دفعة من العميل"),
            ("cash_out", "صندوق المحل", None, 500, "مصاريف متنوعة")
        ]
        
        for trans_type, from_acc, to_acc, amount, desc in transactions_to_test:
            if trans_type == "cash_in":
                result = add_cash_in_transaction(test_user_id, to_acc, str(amount), desc)
            elif trans_type == "cash_out":
                result = add_cash_out_transaction(test_user_id, from_acc, str(amount), desc)
            else:  # transfer
                result = add_transfer_transaction(test_user_id, from_acc, to_acc, str(amount), desc)
            
            if "✅" in result:
                print(f"✅ معاملة {trans_type}: {amount}")
            else:
                print(f"❌ فشل معاملة {trans_type}: {result}")
                return False
        
        # اختبار الرصيد النقدي
        cash_balance = get_current_cash_balance(test_user_id)
        print(f"✅ الرصيد النقدي الحالي: {cash_balance}")
        
        # اختبار تنسيق الأرصدة
        test_balances = [1000, -500, 0, 250.5, -100.75]
        for balance in test_balances:
            formatted = format_balance_status(balance)
            print(f"✅ تنسيق الرصيد {balance}: {formatted}")
        
        # اختبار الحسابات المتقدمة
        advanced_balances = calculate_advanced_balances(test_user_id)
        print(f"✅ الأرصدة المتقدمة: إجمالي النقد = {advanced_balances['total_cash']}")
        
        print("🎉 جميع اختبارات قاعدة البيانات المحسنة نجحت!")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار قاعدة البيانات: {e}")
        return False

def test_enhanced_handlers():
    """اختبار معالجات الأوامر المحسنة"""
    print("🧪 اختبار معالجات الأوامر المحسنة...")
    
    try:
        from handlers_enhanced import (
            parse_transaction_text, extract_accounts_from_text,
            create_commands_inline_keyboard, create_accounts_inline_keyboard,
            format_transaction_details
        )
        
        # اختبار استخراج الحسابات
        test_texts = [
            "@معاملة من @صندوق إلى @بنك 1000",
            "@معاملة دخول إلى @صندوق 500 من العميل",
            "@معاملة خروج من @بنك 300 مصاريف",
            "تحويل @عميل_أحمد @صندوق_المحل 2000"
        ]
        
        for text in test_texts:
            accounts = extract_accounts_from_text(text)
            print(f"✅ استخراج حسابات من '{text[:30]}...': {accounts}")
        
        # اختبار تحليل النصوص المتقدم
        advanced_texts = [
            "دخول إلى @صندوق 1000 من العميل",
            "خروج من @بنك 500 مصاريف",
            "تحويل @صندوق @بنك_الراجحي 2000",
            "من @عميل_أحمد إلى @صندوق 1500",
            "إيداع ل @بنك 800",
            "سحب @صندوق 300 للمورد"
        ]
        
        for text in advanced_texts:
            parsed = parse_transaction_text(text)
            print(f"✅ تحليل: '{text}'")
            print(f"   النوع: {parsed['type']}")
            print(f"   من: {parsed['from_account']}")
            print(f"   إلى: {parsed['to_account']}")
            print(f"   المبلغ: {parsed['amount']}")
        
        # اختبار إنشاء القوائم التفاعلية
        commands_keyboard = create_commands_inline_keyboard()
        if commands_keyboard:
            print("✅ إنشاء قائمة الأوامر التفاعلية")
        else:
            print("❌ فشل إنشاء قائمة الأوامر")
            return False
        
        # اختبار قائمة الحسابات (مع مستخدم تجريبي)
        test_user_id = 999999
        accounts_keyboard = create_accounts_inline_keyboard(test_user_id)
        if accounts_keyboard:
            print("✅ إنشاء قائمة الحسابات التفاعلية")
        else:
            print("⚠️ لا توجد حسابات للمستخدم التجريبي (طبيعي)")
        
        print("🎉 جميع اختبارات المعالجات المحسنة نجحت!")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار المعالجات: {e}")
        return False

def test_edit_delete_functions():
    """اختبار وظائف التعديل والحذف"""
    print("🧪 اختبار وظائف التعديل والحذف...")
    
    try:
        from database_enhanced import (
            create_user, add_account, add_cash_in_transaction,
            update_account, delete_account, get_transaction_by_id,
            update_transaction, delete_transaction, get_user_accounts
        )
        
        # إنشاء مستخدم تجريبي للتعديل والحذف
        test_user_id = 888888
        create_user(test_user_id)
        print("✅ إنشاء مستخدم تجريبي للتعديل والحذف")
        
        # إضافة حساب للاختبار
        add_account(test_user_id, "حساب تجريبي")
        print("✅ إضافة حساب تجريبي")
        
        # اختبار تعديل الحساب
        result = update_account(test_user_id, "حساب تجريبي", "حساب محدث")
        if "✅" in result:
            print("✅ تعديل اسم الحساب")
        else:
            print(f"❌ فشل تعديل الحساب: {result}")
            return False
        
        # إضافة معاملة للاختبار
        add_cash_in_transaction(test_user_id, "حساب محدث", "1000", "معاملة تجريبية")
        print("✅ إضافة معاملة تجريبية")
        
        # الحصول على المعاملة للتعديل
        from database_enhanced import get_user_transactions
        transactions = get_user_transactions(test_user_id, 1)
        if transactions:
            trans_id = transactions[0][0]
            print(f"✅ الحصول على المعاملة #{trans_id}")
            
            # اختبار تعديل المعاملة
            result = update_transaction(test_user_id, trans_id, "cash_in", None, "حساب محدث", "1500", "معاملة محدثة")
            if "✅" in result:
                print("✅ تعديل المعاملة")
            else:
                print(f"❌ فشل تعديل المعاملة: {result}")
                return False
            
            # اختبار حذف المعاملة
            result = delete_transaction(test_user_id, trans_id)
            if "✅" in result:
                print("✅ حذف المعاملة")
            else:
                print(f"❌ فشل حذف المعاملة: {result}")
                return False
        
        # اختبار حذف الحساب
        result = delete_account(test_user_id, "حساب محدث")
        if "✅" in result:
            print("✅ حذف الحساب")
        else:
            print(f"❌ فشل حذف الحساب: {result}")
            return False
        
        print("🎉 جميع اختبارات التعديل والحذف نجحت!")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار التعديل والحذف: {e}")
        return False

def test_interactive_features():
    """اختبار الميزات التفاعلية"""
    print("🧪 اختبار الميزات التفاعلية...")
    
    try:
        from handlers_enhanced import (
            create_commands_inline_keyboard, create_accounts_inline_keyboard,
            create_transactions_inline_keyboard, create_edit_options_keyboard,
            create_delete_options_keyboard, create_transaction_actions_keyboard
        )
        
        # اختبار إنشاء جميع أنواع القوائم التفاعلية
        keyboards_to_test = [
            ("قائمة الأوامر", create_commands_inline_keyboard()),
            ("خيارات التعديل", create_edit_options_keyboard()),
            ("خيارات الحذف", create_delete_options_keyboard()),
            ("إجراءات المعاملة", create_transaction_actions_keyboard("123"))
        ]
        
        for name, keyboard in keyboards_to_test:
            if keyboard:
                print(f"✅ إنشاء {name}")
            else:
                print(f"❌ فشل إنشاء {name}")
                return False
        
        # اختبار قوائم المستخدم (مع مستخدم تجريبي)
        test_user_id = 999999
        user_keyboards = [
            ("قائمة الحسابات", create_accounts_inline_keyboard(test_user_id)),
            ("قائمة المعاملات", create_transactions_inline_keyboard(test_user_id))
        ]
        
        for name, keyboard in user_keyboards:
            if keyboard:
                print(f"✅ إنشاء {name}")
            else:
                print(f"⚠️ {name} فارغة (طبيعي إذا لم توجد بيانات)")
        
        print("🎉 جميع اختبارات الميزات التفاعلية نجحت!")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار الميزات التفاعلية: {e}")
        return False

def test_advanced_reporting():
    """اختبار التقارير المتقدمة"""
    print("🧪 اختبار التقارير المتقدمة...")
    
    try:
        from database_enhanced import (
            get_financial_summary, get_monthly_report, get_accounts_list,
            get_transactions_history, calculate_advanced_balances
        )
        
        test_user_id = 999999
        
        # اختبار التقارير المختلفة
        reports_to_test = [
            ("الملخص المالي", get_financial_summary(test_user_id)),
            ("التقرير الشهري", get_monthly_report(test_user_id)),
            ("قائمة الحسابات", get_accounts_list(test_user_id)),
            ("سجل المعاملات", get_transactions_history(test_user_id, 5))
        ]
        
        for name, report in reports_to_test:
            if report and len(report) > 10:  # تحقق من وجود محتوى
                print(f"✅ إنشاء {name}")
            else:
                print(f"⚠️ {name} فارغ أو قصير")
        
        # اختبار الأرصدة المتقدمة
        advanced_balances = calculate_advanced_balances(test_user_id)
        if isinstance(advanced_balances, dict) and 'total' in advanced_balances:
            print("✅ حساب الأرصدة المتقدمة")
        else:
            print("❌ فشل حساب الأرصدة المتقدمة")
            return False
        
        print("🎉 جميع اختبارات التقارير المتقدمة نجحت!")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار التقارير: {e}")
        return False

def run_comprehensive_test():
    """تشغيل الاختبار الشامل"""
    print("🚀 بدء الاختبار الشامل للمساعد المحاسبي الذكي المحسن")
    print("=" * 70)
    
    tests = [
        ("وظائف قاعدة البيانات المحسنة", test_database_functions),
        ("معالجات الأوامر المحسنة", test_enhanced_handlers),
        ("وظائف التعديل والحذف", test_edit_delete_functions),
        ("الميزات التفاعلية", test_interactive_features),
        ("التقارير المتقدمة", test_advanced_reporting)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_function in tests:
        print(f"\n🧪 {test_name}...")
        try:
            if test_function():
                passed_tests += 1
            else:
                print(f"❌ فشل اختبار: {test_name}")
        except Exception as e:
            print(f"❌ خطأ في اختبار {test_name}: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 نتائج الاختبار: {passed_tests}/{total_tests} اختبارات نجحت")
    
    if passed_tests == total_tests:
        print("🎉 جميع الاختبارات نجحت! النظام المحسن جاهز للاستخدام")
        print("✅ النظام المحسن جاهز للاستخدام!")
        print("يمكنك الآن تشغيل البوت باستخدام:")
        print("   python3 bot_enhanced.py")
        return True
    else:
        print(f"⚠️ {total_tests - passed_tests} اختبارات فشلت. يرجى مراجعة الأخطاء أعلاه.")
        return False

if __name__ == "__main__":
    print("🧪 أداة اختبار المساعد المحاسبي الذكي المحسن")
    print("تاريخ الإنشاء: يونيو 2025")
    print("المؤلف: Manus AI")
    print("الإصدار: 3.0 (محسن)")
    
    success = run_comprehensive_test()
    
    if success:
        print("\n🎯 الخطوات التالية:")
        print("1. تشغيل البوت: python3 bot_enhanced.py")
        print("2. اختبار الميزات الجديدة:")
        print("   • اكتب @ فقط لعرض القائمة التفاعلية")
        print("   • جرب أوامر التعديل والحذف")
        print("   • استخدم القوائم التفاعلية للحسابات")
        print("3. الاستمتاع بالتجربة المحسنة! 🚀")
    else:
        print("\n🔧 يرجى إصلاح الأخطاء قبل الاستخدام")
    
    sys.exit(0 if success else 1)

