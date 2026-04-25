# 🏭 Telethon Factory Bot — Fixed Edition

بوت تلجرام احترافي لإنشاء وإدارة جلسات userbot باستخدام Telethon، مع دعم
**أزرار ملوّنة** (أخضر للتأكيد، أحمر للإلغاء/الرجوع، أزرق للقوائم) حسب آخر
تحديث Bot API 9.4 من تلجرام.

## ✨ المميزات

- 🟢 / 🔴 / 🔵 أزرار ملوّنة (style: success / danger / primary)
- 🛡️ أوامر حماية كاملة (حظر/كتم/رفع مشرف/تنزيل)
- 👋 ترحيب تلقائي + وضع نوم
- 📡 تتبع قنوات كروت الشحن
- 👥 نقل أعضاء بين الجروبات
- 📁 إنشاء مجلدات تلقائية (قنواتي / جروباتي / بوتاتي)
- 💾 تسجيل الرسائل الواردة في chat تخزين
- 🔧 إصلاحات شاملة للـ FloodWait و RuntimeError و session leaks

## 🆕 إصلاحات v4

- ✔ تنصيب اليوزربوت بقى يطبع سبب الفشل بالظبط (PHONE_NUMBER_INVALID, FloodWait, API غلط…)
- ✔ تنظيف رقم التليفون تلقائي (مسافات/شرط/+)
- ✔ رفع ملف `.session` بيشغّل الجلسة تلقائي لو الـ `.json` موجود (مش محتاج /تشغيل_جلسة)
- ✔ ملف الجلسة المرفوع ميتداخلش مع تنصيب جديد جاري (علم `in_conv`)
- ✔ logging مفصّل لكل خطوة في عملية التنصيب — هتشوف الأخطاء واضحة في Railway logs


## 🚀 النشر على Railway

1. ارفع المجلد ده على GitHub (راجع الخطوات أسفل).
2. في Railway: **New Project → Deploy from GitHub repo**.
3. اختار الريبو ده.
4. ضيف المتغيرات (Variables) من tab **Variables**:

```
API_ID=your_api_id_here
API_HASH=your_api_hash_here
BOT_TOKEN=your_bot_token_here
DEVELOPER_ID=1923931101
```

> اسأل الـ API_ID/API_HASH من https://my.telegram.org
> والـ BOT_TOKEN من [@BotFather](https://t.me/BotFather)

5. Railway هيقرأ `nixpacks.toml` و `Procfile` تلقائياً ويشغّل `python main.py`.

## 🛠️ التشغيل المحلي

```bash
pip install -r requirements.txt
cp .env.example .env
# عدّل .env وحط الـ keys
python main.py
```

## 📂 بنية الملفات

```
.
├── main.py              # البوت الرئيسي (مصنع الجلسات + أزرار ملوّنة)
├── userbot.py           # منطق الـ userbot (الأوامر الفعلية)
├── colored_buttons.py   # patch لإضافة style لأزرار تلجرام
├── requirements.txt     # المكتبات
├── Procfile             # أمر التشغيل لـ Railway/Heroku
├── runtime.txt          # نسخة Python
├── nixpacks.toml        # إعدادات بناء Railway
├── railway.json         # إعدادات النشر
├── .env.example         # نموذج المتغيرات
└── .gitignore
```

## 🐛 الأخطاء المُصلَحة في هذه النسخة

### `userbot.py`
- ✅ نقل `DEVELOPER_ID` لأعلى الملف لتجنب `NameError` في أمر `.تحويل`
- ✅ إصلاح normalization لـ `tracked_channels` (دالة `_normalize_chat_id` موحّدة)
- ✅ حماية من loop لانهائي في `log_messages` لو chat التخزين هو نفس chat الرسالة
- ✅ تنظيف `muted_admins[chat_id]` لو فضي بعد فك الكتم
- ✅ تصحيح منطق `sleep_disable_on_reply`

### `main.py`
- ✅ إصلاح `RuntimeError` في `clear_user_store` (background task بدل run_until_complete)
- ✅ معالجة `FloodWaitError` و `RetryAfter` بشكل شامل
- ✅ Group ID calculation باستخدام `abs()`
- ✅ إصلاح `finalize_setup` (ما بيشيلش clients نشطة)
- ✅ تثبيت نسخ مكتبات مستقرة في `requirements.txt`

### `colored_buttons.py`
- ✅ Patch لـ `InlineKeyboardButton.to_dict` لإضافة `style` (success/danger/primary)

## 📤 رفع على GitHub

```bash
cd Telethon-Factory-Fixed
git init
git add .
git commit -m "Initial commit: Telethon Factory Fixed"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO_NAME.git
git push -u origin main
```

ثم في Railway اربط الريبو.

## 📝 الترخيص

استخدام شخصي/تعليمي. المطور: [@FY_TF](https://t.me/FY_TF)
