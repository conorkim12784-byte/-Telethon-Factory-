"""
colored_buttons.py - دعم أزرار تيليجرام الملونة (Bot API 9.4 - فيفري 2026)

تيليجرام أضافت حقل `style` على InlineKeyboardButton بـ 3 قيم:
  - "success" → 🟢 أخضر  (للتأكيد، الحفظ، النجاح)
  - "danger"  → 🔴 أحمر   (للإلغاء، الحذف، التحذيرات)
  - "primary" → 🔵 أزرق   (للقوائم والتنقل العادي)

مكتبة python-telegram-bot لسه ما ضافتش الحقل ده رسمياً (Issue #5136)،
فبنحقن `style` يدوياً عن طريق api_kwargs على كائن الزر بعد إنشاءه.

طريقة الاستعمال:
    from colored_buttons import SuccessBtn, DangerBtn, PrimaryBtn

    keyboard = InlineKeyboardMarkup([
        [SuccessBtn("✔ تأكيد", callback_data="confirm")],
        [DangerBtn("✘ إلغاء", callback_data="cancel")],
        [PrimaryBtn("📊 الإحصائيات", callback_data="stats")],
    ])
"""

from telegram import InlineKeyboardButton


def _styled(style_value: str, *args, **kwargs) -> InlineKeyboardButton:
    """ينشئ InlineKeyboardButton مع حقن style في الـ api_kwargs."""
    btn = InlineKeyboardButton(*args, **kwargs)
    # نحقن style على الـ api_kwargs - python-telegram-bot بيضيفها للـ JSON المرسل
    try:
        if not hasattr(btn, 'api_kwargs') or btn.api_kwargs is None:
            object.__setattr__(btn, 'api_kwargs', {})
        btn.api_kwargs['style'] = style_value
    except Exception:
        # لو الـ library الإصدار القديم - الزر يشتغل عادي بدون style
        pass

    # نخزن الـ style كـ attribute عشان نقدر نعمل serialization صح
    try:
        object.__setattr__(btn, '_lov_style', style_value)
    except Exception:
        pass
    return btn


def SuccessBtn(*args, **kwargs) -> InlineKeyboardButton:
    """🟢 زرار أخضر - للتأكيد، الحفظ، التشغيل، نعم."""
    return _styled("success", *args, **kwargs)


def DangerBtn(*args, **kwargs) -> InlineKeyboardButton:
    """🔴 زرار أحمر - للإلغاء، الحذف، الرجوع، الرفض، التعطيل."""
    return _styled("danger", *args, **kwargs)


def PrimaryBtn(*args, **kwargs) -> InlineKeyboardButton:
    """🔵 زرار أزرق - للقوائم والتنقل والإعدادات."""
    return _styled("primary", *args, **kwargs)


# ════════════════════════════════════════════
# Patch: نضمن إن style بيتبعت في الـ JSON الفعلي
# ════════════════════════════════════════════
# python-telegram-bot بيستخدم .to_dict() عند الإرسال.
# بنعمل override يضيف style لو متخزن.
_original_to_dict = InlineKeyboardButton.to_dict


def _patched_to_dict(self, recursive: bool = True) -> dict:
    data = _original_to_dict(self, recursive=recursive) if 'recursive' in _original_to_dict.__code__.co_varnames else _original_to_dict(self)
    style = getattr(self, '_lov_style', None)
    if style:
        data['style'] = style
    return data


InlineKeyboardButton.to_dict = _patched_to_dict
