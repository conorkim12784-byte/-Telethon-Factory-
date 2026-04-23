import os
import asyncio
import logging
import re
from telethon import events, TelegramClient
from telethon.errors import ChatAdminRequiredError, FloodWaitError
from telethon.tl.functions.channels import (
    EditAdminRequest, InviteToChannelRequest, GetParticipantRequest
)
from telethon.tl.types import (
    ChannelParticipantsAdmins, ChatAdminRights,
    DialogFilter, InputPeerChannel, InputPeerChat
)
from telethon.tl.functions.messages import UpdateDialogFilterRequest, GetDialogFiltersRequest
from telethon.errors.rpcerrorlist import UserNotParticipantError, UserIdInvalidError

logging.basicConfig(
    filename='userbot_errors.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ══════════════════════════════════════════
#              الثوابت الثابتة
# ══════════════════════════════════════════
OFFICIAL_CHANNEL_LINK = "https://t.me/I0_I6"
WELCOME_GIF = "https://i.postimg.cc/wxV3PspQ/1756574872401.gif"

SOURCE_TAG = """
╭──⌁𝗧𝗲𝗟𝗲𝗧𝗵𝗢𝗻⌁──⟤
│╭───────────⟢
╞╡   Date of establishment 2022
╞╡ 
╞╡This is the simplest thing we have
│╰────────────╮
│╭────────────╯
╞╡      Source code in Python
│╰───────────⟢
╰──⌁𝗧𝗲𝗟𝗲𝗧𝗵𝗢𝗻⌁──⟤"""

COMMANDS_TEXT = """
📌 **قائمة الأوامر**
──────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁──────

🛡️ **الحماية:**
`.حظر` — حظر عضو (رد / @يوزر / ID)
`.فك حظر` — فك حظر (رد / @يوزر / ID)
`.كتم` — تقييد عضو وحذف رسائله
`.فك كتم` — فك التقييد
`.كتم مشرف` — كتم مشرف (رد / @يوزر / ID)
`.فك كتم مشرف` — فك كتم مشرف (رد / @يوزر / ID)
`.رفع مشرف @يوزر <لقب>` — رفع مشرف بصلاحيات كاملة
`.تنزيل كل المشرفين` — إزالة إشراف كل المشرفين اللي إنت رفعتهم
`.حد حظر <عدد>` — حد أقصى للحظر لكل مشرف
`.الغ حد` — إلغاء حد الحظر

──────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁──────

👋 **الترحيب:**
`.ترحيب تشغيل` — تفعيل الترحيب
`.ترحيب ايقاف` — تعطيل الترحيب
`.ترحيب نص <نص>` — تغيير نص الترحيب
`.ترحيب صورة <رابط>` — تغيير صورة الترحيب
`.ترحيب gif <رابط>` — تغيير GIF الترحيب
`.ترحيب تنسيق <markdown/html/none>` — تغيير التنسيق
`.ترحيب زر سورس` — إظهار زر سورس تلاشاني
`.ترحيب زر سورس ايقاف` — إخفاء زر سورس تلاشاني
`.ترحيب زر اضف نص | رابط` — إضافة زر مخصص
`.ترحيب زر شيل` — إزالة الزر المخصص
`.ترحيب اعدادات` — عرض الإعدادات الحالية
`.قبول` — إيقاف الترحيب لمستخدم وحذف رسالته

──────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁──────

😴 **وضع النوم:**
`.نايم` — تفعيل وضع النوم
`.نايم <رسالة>` — تفعيل برسالة مخصصة
`.صحيت` — إيقاف وضع النوم

──────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁──────

📢 **الإذاعة:**
`.اذاعة خاص <رسالة>` — إرسال لكل المحادثات الخاصة
`.اذاعة جروب <رسالة>` — إرسال لكل المجموعات

──────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁──────

📡 **تتبع القنوات:**
`.تتبع قناة <@مصدر> <@استلام>` — بدء التتبع
`.وقف التتبع` — إيقاف التتبع

──────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁──────

📁 **المجلدات:**
`.مجلد قنواتي [اسم]` — مجلد القنوات
`.مجلد جروباتي [اسم]` — مجلد الجروبات
`.مجلد بوتاتي [اسم]` — مجلد البوتات

──────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁──────

👥 **نقل الأعضاء:**
`.نقل اعضاء @مصدر @استلام` — نقل أعضاء من جروب لجروب

──────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁──────

🔧 **إعدادات البوت:**
`.سورس تشغيل` — تفعيل الرد على كلمة سورس
`.سورس ايقاف` — تعطيل الرد على كلمة سورس

──────⌁𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆⌁──────
"""

# ══════════════════════════════════════════
#              الدالة الرئيسية
# ══════════════════════════════════════════
async def start_userbot(client: TelegramClient, target_chat, user_data_store):
    # ✔ الإصلاح الجوهري: امنع تسجيل الهاندلرز أكتر من مرة على نفس الكلاينت.
    # ده كان السبب اللي بيخلي الأوامر ترد 3 مرات لما الجلسة تنقطع وترجع،
    # لأن keep_alive_monitor كان بينادي start_userbot تاني فيتسجلوا تاني.
    if getattr(client, "_handlers_registered", False):
        logging.info("ℹ️ الهاندلرز متسجلة قبل كده على الكلاينت ده — هنتخطى التسجيل")
        # نضمن إن الكلاينت متصل ونسيب الهاندلرز القديمة شغالة
        try:
            if not client.is_connected():
                await client.connect()
        except Exception as e:
            logging.error(f"✘ فشل إعادة الاتصال داخل start_userbot: {e}")
        # نفضل مستنيين عشان ما نخرجش ونخلّي الـ task يتنهي
        try:
            await client.run_until_disconnected()
        except Exception as e:
            logging.error(f"✘ run_until_disconnected انتهى: {e}")
        return

    me = await client.get_me()
    owner_id = me.id
    logging.info(f"✔ يوزربوت شغال: {me.first_name} ({owner_id})")
    print(f"✔ يوزربوت شغال: {me.first_name} ({owner_id})")

    # ✔ deduplication للأحداث: لو نفس message id جه مرتين، نتجاهله
    processed_event_ids = set()
    processed_order = []

    def _seen(event):
        try:
            key = (event.chat_id, event.id)
        except Exception:
            return False
        if key in processed_event_ids:
            return True
        processed_event_ids.add(key)
        processed_order.append(key)
        # نحافظ على حجم محدود (آخر 2000 حدث)
        if len(processed_order) > 2000:
            old_key = processed_order.pop(0)
            processed_event_ids.discard(old_key)
        return False

    # ✔ Wrapper لتغليف client.on بحيث يفحص deduplication تلقائياً
    _original_on = client.on
    def _safe_on(event_filter):
        def decorator(handler):
            async def wrapped(event):
                try:
                    if _seen(event):
                        return
                except Exception:
                    pass
                return await handler(event)
            wrapped.__name__ = getattr(handler, "__name__", "handler")
            return _original_on(event_filter)(wrapped)
        return decorator
    client.on = _safe_on

    # ══ الحالات الداخلية ══
    muted_admins = {}
    welcomed_users = {}
    accepted_users = set()
    tracked_channels = {}
    sleep_mode = False
    sleep_replied = set()
    sleep_state = {"active": False, "msg": "😴 أنا نايم دلوقتي، هرد عليك لما أصحى!"}
    ban_limits = {}
    admin_ban_count = {}
    source_state = {"active": True}   # تفعيل/تعطيل السورس
    welcome_state = {
        "active": True,
        "text": "أهلاً وسهلاً بيك! 🔥\n\nسيب رسالتك وهنرد عليك في أقرب وقت 💬",
        "photo": "",
        "gif": WELCOME_GIF,
        "use_photo": False,
        "parse_mode": "markdown",
        "btn_source": {"text": "𝗧𝗹𝗔𝘀𝗛𝗮𝗡𝘆 ", "url": "https://t.me/FY_TF", "active": True},
        "btn_custom": {"text": "", "url": "", "active": False},
    }

    # ══════════════════════════════════════════
    #         وظائف مساعدة مشتركة
    # ══════════════════════════════════════════
    async def reply_or_edit(event, text, **kwargs):
        try:
            if event.out:
                await event.edit(text, **kwargs)
            else:
                await event.respond(text, **kwargs)
        except Exception:
            try:
                await event.respond(text, **kwargs)
            except Exception as e:
                logging.error(f"فشل الرد: {e}")

    async def resolve_target(event, args):
        """
        يرجع user_id من:
        - رد على رسالة
        - يوزرنيم (@someone)
        - ID رقمي
        """
        if event.is_reply:
            reply = await event.get_reply_message()
            return reply.sender_id
        if args:
            target = args[0].strip()
            try:
                entity = await client.get_entity(target.lstrip('@') if target.startswith('@') else int(target))
                return entity.id
            except Exception as e:
                await reply_or_edit(event, f"✘ مش قادر أجيب المستخدم: {e}")
                return None
        await reply_or_edit(event, "⚠️ استخدم: رد على رسالة أو اكتب @يوزر أو ID")
        return None

    async def is_admin(chat_id, user_id):
        try:
            admins = await client.get_participants(chat_id, filter=ChannelParticipantsAdmins)
            return any(a.id == user_id for a in admins)
        except Exception:
            return False

    # ══════════════════════════════════════════
    #         متابعة القنوات (كروت الشحن)
    # ══════════════════════════════════════════
    @client.on(events.NewMessage(incoming=True))
    async def monitor_channels(event):
        """يراقب القنوات ويستخرج الكود + الوحدات فقط، يحذفهم بعد 5 دقايق"""
        if not tracked_channels:
            return
        # normalize: تيليجرام بيبعت -100XXXXX أو XXXXX - نوحدهم
        raw_id = event.chat_id
        normalized = int(str(raw_id).replace("-100", "")) if str(raw_id).startswith("-100") else raw_id
        if normalized not in tracked_channels and raw_id not in tracked_channels:
            return
        chat_id = normalized if normalized in tracked_channels else raw_id

        text = event.raw_text or ""

        # يمسك الكود في أي صيغة (نص عادي أو داخل code block)
        codes = re.findall(r'\*858\*(\d+)#', text)
        if not codes:
            return

        # يستخرج الوحدات لو موجودة
        units_matches = re.findall(r'(\d[\d,]*)\s*UNITS?', text, re.IGNORECASE)

        dest_channel = tracked_channels[chat_id]

        for i, code_number in enumerate(codes):
            card_code = f"*858*{code_number}#"
            units = units_matches[i] if i < len(units_matches) else None
            if units:
                msg = (
                    f"╭────═⌁TALASHNY⌁═──⟤\n"
                    f"│╭✦───✦──────✦─⟢\n"
                    f"╞╡ Units ➜ وحدة {units}\n"
                    f"│╰✦─⟐─✦────✦╮\n"
                    f"│╭✦─⟐─✦────✦╯\n"
                    f"╞╡ Code ➜ `{card_code}`\n"
                    f"│╰✦───✦──────✦─⟢\n"
                    f"╰────═⌁TALASHNY⌁═──⟤"
                )
            else:
                msg = (
                    f"╭────═⌁TALASHNY⌁═──⟤\n"
                    f"│╭✦───✦──────✦─⟢\n"
                    f"╞╡ Code ➜ `{card_code}`\n"
                    f"│╰✦───✦──────✦─⟢\n"
                    f"╰────═⌁TALASHNY⌁═──⟤"
                )

            try:
                sent = await client.send_message(dest_channel, msg, parse_mode="markdown")
                logging.info(f"✔ ارسل: {msg}")

                async def delete_after(sent_msg, delay=300):
                    await asyncio.sleep(delay)
                    try:
                        await sent_msg.delete()
                    except Exception as ex:
                        logging.error(f"فشل الحذف: {ex}")

                asyncio.create_task(delete_after(sent))

            except Exception as e:
                logging.error(f"فشل ارسال الكرت: {e}")

    # ══════════════════════════════════════════
    #         الترحيب التلقائي في الخاص
    # ══════════════════════════════════════════
    @client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
    async def auto_welcome(event):
        try:
            if not welcome_state["active"]:
                return
            sender_id = event.sender_id
            if sender_id in welcomed_users or sender_id in accepted_users:
                return
            # تجاهل النفس
            me = await client.get_me()
            if sender_id == me.id:
                return
            sender = await event.get_sender()
            if not sender or getattr(sender, 'bot', False):
                return
            logging.info(f"👋 محاولة ترحيب user_id={sender_id} في chat={event.chat_id}")
            sent = await _send_welcome_to(event.chat_id, sender_id)
            if sent:
                logging.info(f"✔ تم إرسال الترحيب لـ {sender_id}")
            else:
                logging.error(f"✘ ترحيب فشل للـ {sender_id}")
        except Exception as e:
            logging.error(f"✘ auto_welcome error: {e}", exc_info=True)

    async def _send_welcome_to(chat_id, sender_id=None):
        """يبعت رسالة الترحيب لأي شات — مع دعم Markdown inline links [نص](رابط)."""
        from telethon.tl.custom import Button

        welcome_text = welcome_state["text"] + f"\n\n{SOURCE_TAG}"
        pm = welcome_state["parse_mode"] or "markdown"

        # بناء الأزرار باستخدام Button.url (الطريقة الصحيحة في Telethon)
        btn_row = []
        if welcome_state["btn_custom"]["active"] and welcome_state["btn_custom"]["url"]:
            btn_row.append(Button.url(
                welcome_state["btn_custom"]["text"] or "🔗 رابط",
                welcome_state["btn_custom"]["url"]
            ))
        if welcome_state["btn_source"]["active"]:
            btn_row.append(Button.url(
                welcome_state["btn_source"]["text"],
                welcome_state["btn_source"]["url"]
            ))
        buttons = [btn_row] if btn_row else None

        sent = None
        last_error = None

        # محاولة 1: ميديا + أزرار + parse_mode المختار
        try:
            media = welcome_state["photo"] if welcome_state["use_photo"] else welcome_state["gif"]
            if media:
                sent = await client.send_file(
                    chat_id, media,
                    caption=welcome_text, parse_mode=pm,
                    buttons=buttons, link_preview=False
                )
            else:
                sent = await client.send_message(
                    chat_id, welcome_text,
                    parse_mode=pm, buttons=buttons, link_preview=False
                )
        except Exception as e:
            last_error = e
            logging.warning(f"⚠ ترحيب محاولة 1 فشلت: {e}")

        # محاولة 2: نص + أزرار بدون ميديا
        if sent is None:
            try:
                sent = await client.send_message(
                    chat_id, welcome_text,
                    parse_mode=pm, buttons=buttons, link_preview=False
                )
            except Exception as e:
                last_error = e
                logging.warning(f"⚠ ترحيب محاولة 2 فشلت: {e}")

        # محاولة 3: نص فقط بدون أزرار وبدون parse_mode
        if sent is None:
            try:
                sent = await client.send_message(chat_id, welcome_text)
            except Exception as e:
                last_error = e
                logging.error(f"✘ ترحيب فشل نهائياً: {e}", exc_info=True)
                return None

        if sent and sender_id is not None:
            welcomed_users[sender_id] = sent.id
        return sent

    # ══════════════════════════════════════════
    #              معالج الأوامر
    # ══════════════════════════════════════════
    @client.on(events.NewMessage(outgoing=True))
    async def handle_commands(event):
        text = event.raw_text.strip()
        if not text:
            return

        parts = text.split()
        cmd = parts[0].lower()
        args = parts[1:]
        cmd2 = " ".join(parts[:2]).lower() if len(parts) >= 2 else ""
        cmd3 = " ".join(parts[:3]).lower() if len(parts) >= 3 else ""
        cmd4 = " ".join(parts[:4]).lower() if len(parts) >= 4 else ""

        # ════ قائمة الأوامر ════
        if cmd in (".الاوامر", ".ا"):
            await reply_or_edit(event, COMMANDS_TEXT, parse_mode='markdown')
            return

        # ════ قبول (إيقاف ترحيب لمستخدم معين + حذف رسالة الترحيب) ════
        if cmd == ".قبول" and event.is_reply:
            reply = await event.get_reply_message()
            target_id = reply.sender_id
            accepted_users.add(target_id)
            # احذف رسالة الترحيب لو موجودة
            if target_id in welcomed_users:
                try:
                    await client.delete_messages(event.chat_id, welcomed_users[target_id])
                except Exception:
                    pass
                del welcomed_users[target_id]
            # احذف أمر .قبول نفسه
            try:
                await event.delete()
            except Exception:
                pass
            return

        # ════ إذاعة خاص ════
        if cmd2 == ".اذاعة خاص":
            args = parts[2:]
            if not args:
                await reply_or_edit(event, "⚠️ الاستخدام: `.اذاعة خاص <الرسالة>`")
                return
            msg = " ".join(args)
            count = 0
            await reply_or_edit(event, "📢 جاري الإذاعة للمحادثات الخاصة...")
            async for dialog in client.iter_dialogs():
                if dialog.is_user and dialog.entity.id != owner_id and not getattr(dialog.entity, 'bot', False):
                    try:
                        await client.send_message(dialog.entity, msg)
                        count += 1
                        await asyncio.sleep(1)
                    except Exception:
                        pass
            await reply_or_edit(event, f"✔ تم الإرسال لـ {count} محادثة خاصة!")
            return

        # ════ إذاعة جروب ════
        if cmd2 == ".اذاعة جروب":
            args = parts[2:]
            if not args:
                await reply_or_edit(event, "⚠️ الاستخدام: `.اذاعة جروب <الرسالة>`")
                return
            msg = " ".join(args)
            count = 0
            await reply_or_edit(event, "📢 جاري الإذاعة للمجموعات...")
            async for dialog in client.iter_dialogs():
                if dialog.is_group:
                    try:
                        await client.send_message(dialog.entity, msg)
                        count += 1
                        await asyncio.sleep(1)
                    except Exception:
                        pass
            await reply_or_edit(event, f"✔ تم الإرسال لـ {count} مجموعة!")
            return

        # ════ تتبع قناة ════
        if cmd2 == ".تتبع قناة":
            args = parts[2:]
            if len(args) < 2:
                await reply_or_edit(event, "⚠️ الاستخدام: `.تتبع قناة @قناة_المصدر @قناة_الاستلام`")
                return
            try:
                src = await client.get_entity(args[0].lstrip('@'))
                dst = await client.get_entity(args[1].lstrip('@'))
                src_id = src.id
                dst_id = dst.id
                tracked_channels[src_id] = dst_id
                if hasattr(src, 'access_hash'):
                    tracked_channels[int(f"-100{src_id}")] = dst_id
                await reply_or_edit(event,
                    f"✔ بدأ التتبع!\n"
                    f"📡 المصدر: {src.title}\n"
                    f"📥 الاستلام: {dst.title}\n\n"
                    f"🔍 هيستخرج أي رقم بصيغة `*858*XXXXXX#` تلقائياً"
                )
            except Exception as e:
                await reply_or_edit(event, f"✘ خطأ: {e}")
            return

        # ════ وقف التتبع ════
        if cmd2 == ".وقف التتبع":
            tracked_channels.clear()
            await reply_or_edit(event, "🛑 تم إيقاف تتبع القنوات!")
            return

        # ══════════════════════════════════════════
        #         دالة مساعدة لإنشاء المجلد
        # ══════════════════════════════════════════
        async def make_folder(folder_name, peers, names):
            from telethon.tl.types import (
                DialogFilter as TLDialogFilter,
                TextWithEntities
            )
            if not peers:
                return None
            try:
                existing_filters = await client(GetDialogFiltersRequest())
                used_ids = [f.id for f in existing_filters.filters if hasattr(f, 'id')]
                new_id = max(used_ids, default=1) + 1
                if new_id > 255:
                    new_id = 2
            except Exception:
                new_id = 10

            dialog_filter = TLDialogFilter(
                id=new_id,
                title=TextWithEntities(text=folder_name, entities=[]),
                pinned_peers=[],
                include_peers=peers,
                exclude_peers=[],
                contacts=False,
                non_contacts=False,
                groups=False,
                broadcasts=False,
                bots=False,
                exclude_muted=False,
                exclude_read=False,
                exclude_archived=False,
            )
            await client(UpdateDialogFilterRequest(id=new_id, filter=dialog_filter))
            names_text = "\n".join(names[:20])
            extra = f"\n... و{len(names) - 20} أكتر" if len(names) > 20 else ""
            return f"📊 العدد: **{len(peers)}**\n\n{names_text}{extra}"

        # ════ مجلد قنواتي ════
        if cmd2 == ".مجلد قنواتي":
            folder_name = " ".join(parts[2:]) if len(parts) > 2 else "قنواتي 📢"
            await reply_or_edit(event, "📁 جاري جمع قنواتك...\n⏳ استنى ثواني...")
            try:
                from telethon.tl.types import Channel, InputPeerChannel, ChannelParticipantCreator
                from telethon.tl.functions.channels import GetParticipantRequest as GetChannelParticipant
                peers, names = [], []
                async for dialog in client.iter_dialogs():
                    entity = dialog.entity
                    if isinstance(entity, Channel) and not entity.megagroup:
                        try:
                            part = await client(GetChannelParticipant(channel=entity, participant=me))
                            if isinstance(part.participant, ChannelParticipantCreator):
                                peers.append(InputPeerChannel(entity.id, entity.access_hash))
                                names.append(f"📢 {entity.title}")
                        except Exception:
                            pass
                if not peers:
                    await reply_or_edit(event, "✘ مش لاقي أي قناة إنت مالكها!")
                    return
                result = await make_folder(folder_name, peers, names)
                await reply_or_edit(event, f"✔ تم إنشاء مجلد **{folder_name}**!\n\n{result}", parse_mode='markdown')
            except Exception as e:
                await reply_or_edit(event, f"✘ حصل خطأ: {e}")
            return

        # ════ مجلد جروباتي ════
        if cmd2 == ".مجلد جروباتي":
            folder_name = " ".join(parts[2:]) if len(parts) > 2 else "جروباتي 👥"
            await reply_or_edit(event, "📁 جاري جمع جروباتك...\n⏳ استنى ثواني...")
            try:
                from telethon.tl.types import Channel, Chat, InputPeerChannel, InputPeerChat, ChannelParticipantCreator
                from telethon.tl.functions.channels import GetParticipantRequest as GetChannelParticipant
                peers, names = [], []
                async for dialog in client.iter_dialogs():
                    entity = dialog.entity
                    # سوبرجروبات
                    if isinstance(entity, Channel) and entity.megagroup:
                        try:
                            part = await client(GetChannelParticipant(channel=entity, participant=me))
                            if isinstance(part.participant, ChannelParticipantCreator):
                                peers.append(InputPeerChannel(entity.id, entity.access_hash))
                                names.append(f"👥 {entity.title}")
                        except Exception:
                            pass
                    # جروبات عادية
                    elif isinstance(entity, Chat):
                        if getattr(entity, 'creator', False):
                            peers.append(InputPeerChat(entity.id))
                            names.append(f"👥 {entity.title}")
                if not peers:
                    await reply_or_edit(event, "✘ مش لاقي أي جروب إنت مالكه!")
                    return
                result = await make_folder(folder_name, peers, names)
                await reply_or_edit(event, f"✔ تم إنشاء مجلد **{folder_name}**!\n\n{result}", parse_mode='markdown')
            except Exception as e:
                await reply_or_edit(event, f"✘ حصل خطأ: {e}")
            return

        # ════ مجلد بوتاتي ════
        if cmd2 == ".مجلد بوتاتي":
            folder_name = " ".join(parts[2:]) if len(parts) > 2 else "بوتاتي 🤖"
            await reply_or_edit(event, "📁 جاري جمع البوتات...\n⏳ استنى ثواني...")
            try:
                from telethon.tl.types import User, InputPeerUser
                peers, names = [], []
                async for dialog in client.iter_dialogs():
                    entity = dialog.entity
                    if isinstance(entity, User) and entity.bot:
                        peers.append(InputPeerUser(entity.id, entity.access_hash))
                        names.append(f"🤖 {entity.first_name or entity.username or str(entity.id)}")
                if not peers:
                    await reply_or_edit(event, "✘ مش لاقي أي بوت!")
                    return
                result = await make_folder(folder_name, peers, names)
                await reply_or_edit(event, f"✔ تم إنشاء مجلد **{folder_name}**!\n\n{result}", parse_mode='markdown')
            except Exception as e:
                await reply_or_edit(event, f"✘ حصل خطأ: {e}")
            return

        # ════ تحكم في السورس ════
        if cmd2 == ".سورس تشغيل":
            source_state["active"] = True
            await reply_or_edit(event, "✔ تم تفعيل رد السورس!")
            return
        if cmd2 == ".سورس ايقاف":
            source_state["active"] = False
            await reply_or_edit(event, "🔴 تم تعطيل رد السورس!")
            return

        # ════ تحكم في الترحيب ════
        if cmd2 == ".ترحيب تشغيل":
            welcome_state["active"] = True
            await reply_or_edit(event, "✔ تم تفعيل رسالة الترحيب!")
            return
        if cmd2 == ".ترحيب ايقاف":
            welcome_state["active"] = False
            await reply_or_edit(event, "🔴 تم تعطيل رسالة الترحيب!")
            return

        # ════ تغيير نص الترحيب ════
        if cmd2 == ".ترحيب نص":
            if len(parts) < 3:
                await reply_or_edit(event, "⚠️ الاستخدام: `.ترحيب نص <النص الجديد>`")
                return
            welcome_state["text"] = " ".join(parts[2:])
            await reply_or_edit(event, f"✔ تم تغيير نص الترحيب!\n\n{welcome_state['text']}")
            return

        # ════ تغيير صورة/GIF الترحيب ════
        if cmd2 == ".ترحيب صورة":
            if len(parts) < 3:
                await reply_or_edit(event, "⚠️ الاستخدام: `.ترحيب صورة <رابط أو file_id>`")
                return
            welcome_state["photo"] = " ".join(parts[2:]).strip()
            welcome_state["use_photo"] = True
            await reply_or_edit(event, f"✔ تم تغيير صورة الترحيب!\n🔗 {welcome_state['photo']}")
            return
        if cmd2 == ".ترحيب gif":
            if len(parts) < 3:
                await reply_or_edit(event, "⚠️ الاستخدام: `.ترحيب gif <رابط أو file_id>`")
                return
            welcome_state["gif"] = " ".join(parts[2:]).strip()
            welcome_state["use_photo"] = False
            await reply_or_edit(event, f"✔ تم تغيير GIF الترحيب!\n🔗 {welcome_state['gif']}")
            return

        # ════ جرب الترحيب فوراً (إرسال للنفس عشان تتأكد إنه شغال) ════
        if cmd2 == ".ترحيب جرب":
            await reply_or_edit(event, "📤 بابعت رسالة الترحيب لنفسك دلوقتي...")
            try:
                me = await client.get_me()
                sent = await _send_welcome_to(me.id, sender_id=None)
                if sent:
                    await reply_or_edit(event, "✔ تم! شوف رسالتك في المحفوظات/الخاص.")
                else:
                    await reply_or_edit(event, "✘ فشل إرسال الترحيب — شوف اللوج.")
            except Exception as e:
                await reply_or_edit(event, f"✘ خطأ: {e}")
            return

        # ════ تغيير تنسيق الترحيب ════
        if cmd2 == ".ترحيب تنسيق":
            if len(parts) < 3 or parts[2] not in ["markdown", "html", "none"]:
                await reply_or_edit(event, "⚠️ الاستخدام: `.ترحيب تنسيق markdown` أو `html` أو `none`")
                return
            welcome_state["parse_mode"] = None if parts[2] == "none" else parts[2]
            await reply_or_edit(event, f"✔ تم تغيير التنسيق إلى: {parts[2]}")
            return

        # ════ تحكم في زر السورس ════
        if cmd3 == ".ترحيب زر سورس":
            if cmd4 == ".ترحيب زر سورس ايقاف":
                welcome_state["btn_source"]["active"] = False
                await reply_or_edit(event, "🔴 تم إخفاء زر سورس تلاشاني من الترحيب!")
            else:
                welcome_state["btn_source"]["active"] = True
                await reply_or_edit(event, "✔ تم إظهار زر سورس تلاشاني في الترحيب!")
            return

        # ════ إضافة/تعديل زر مخصص ════
        if cmd3 == ".ترحيب زر اضف":
            rest = " ".join(parts[3:])
            if "|" not in rest:
                await reply_or_edit(event, "⚠️ الاستخدام: `.ترحيب زر اضف نص الزر | https://رابط`")
                return
            btn_text, btn_url = rest.split("|", 1)
            welcome_state["btn_custom"]["text"] = btn_text.strip()
            welcome_state["btn_custom"]["url"] = btn_url.strip()
            welcome_state["btn_custom"]["active"] = True
            await reply_or_edit(event, f"✔ تم إضافة الزر!\n\n🔘 {btn_text.strip()}\n🔗 {btn_url.strip()}")
            return

        # ════ إزالة الزر المخصص ════
        if cmd3 == ".ترحيب زر شيل":
            welcome_state["btn_custom"]["active"] = False
            welcome_state["btn_custom"]["text"] = ""
            welcome_state["btn_custom"]["url"] = ""
            await reply_or_edit(event, "✔ تم إزالة الزر المخصص من الترحيب!")
            return

        # ════ عرض إعدادات الترحيب الحالية ════
        if cmd2 == ".ترحيب اعدادات":
            status = "✔ مفعل" if welcome_state["active"] else "🔴 معطل"
            media_type = "صورة 🖼" if welcome_state["use_photo"] else "GIF 🎞"
            src_btn = "✔ ظاهر" if welcome_state["btn_source"]["active"] else "🔴 مخفي"
            custom_btn = f"✔ {welcome_state['btn_custom']['text']}" if welcome_state["btn_custom"]["active"] else "🔴 مش موجود"
            await reply_or_edit(event,
                f"⚙️ **إعدادات الترحيب:**\n\n"
                f"الحالة: {status}\n"
                f"النوع: {media_type}\n"
                f"التنسيق: {welcome_state['parse_mode'] or 'بدون'}\n\n"
                f"**الأزرار:**\n"
                f"سورس تلاشاني: {src_btn}\n"
                f"الزر المخصص: {custom_btn}\n\n"
                f"**النص:**\n{welcome_state['text']}",
                parse_mode='markdown'
            )
            return
        if cmd == ".هدية":
            await reply_or_edit(event, "🎁 جاري جمع الهدية اليومية...")
            try:
                from telethon.tl.custom import Button

                bot = await client.get_entity("psjbot")

                # خطوة 1: ابعت /start
                await client.send_message(bot, "/start")
                await asyncio.sleep(2)

                # خطوة 2: اضغط "تجميع نقاط"
                msgs = await client.get_messages(bot, limit=5)
                clicked = False
                for msg in msgs:
                    if msg.buttons:
                        for row in msg.buttons:
                            for btn in row:
                                if "تجميع" in (btn.text or ""):
                                    await btn.click()
                                    clicked = True
                                    break
                        if clicked:
                            break

                if not clicked:
                    await reply_or_edit(event, "✘ مش لاقي زرار تجميع نقاط!")
                    return

                await asyncio.sleep(2)

                # خطوة 3: اضغط "الهدية اليومية"
                msgs = await client.get_messages(bot, limit=5)
                clicked2 = False
                for msg in msgs:
                    if msg.buttons:
                        for row in msg.buttons:
                            for btn in row:
                                if "الهدية" in (btn.text or "") or "هدية" in (btn.text or ""):
                                    await btn.click()
                                    clicked2 = True
                                    break
                        if clicked2:
                            break

                if not clicked2:
                    await reply_or_edit(event, "✘ مش لاقي زرار الهدية اليومية!")
                    return

                await asyncio.sleep(2)

                # خطوة 4: اقرأ الرد
                msgs = await client.get_messages(bot, limit=3)
                result_text = ""
                for msg in msgs:
                    if msg.text and ("حصلت" in msg.text or "رصيد" in msg.text or "نقاط" in msg.text or "بنجاح" in msg.text):
                        result_text = msg.text
                        break

                if result_text:
                    await reply_or_edit(event, f"✔ تم!\n\n{result_text}")
                else:
                    await reply_or_edit(event, "✔ تم الضغط على الهدية اليومية!")

            except Exception as e:
                await reply_or_edit(event, f"✘ خطأ: {e}")
            return

        # ════ تحويل النقاط لـ psjbot ════
        if cmd == ".تحويل":
            await reply_or_edit(event, "💸 جاري تحويل النقاط...")
            try:
                import re as _re
                bot = await client.get_entity("psjbot")

                # خطوة 1: /start
                await client.send_message(bot, "/start")
                await asyncio.sleep(2)

                # خطوة 2: اضغط "تحويل نقاط"
                msgs = await client.get_messages(bot, limit=5)
                clicked1 = False
                for m in msgs:
                    if m.buttons:
                        for row in m.buttons:
                            for btn in row:
                                if "تحويل" in (btn.text or ""):
                                    await btn.click()
                                    clicked1 = True
                                    break
                        if clicked1:
                            break
                if not clicked1:
                    await reply_or_edit(event, "✘ مش لاقي زرار تحويل نقاط!")
                    return

                await asyncio.sleep(2)

                # خطوة 3: اقرأ الرصيد من رسالة البوت
                msgs = await client.get_messages(bot, limit=5)
                balance = 0
                for m in msgs:
                    if m.text and ("نقاطك" in m.text or "الحالية" in m.text or "الحالي" in m.text):
                        match = _re.search(r'(\d+(?:\.\d+)?)', m.text)
                        if match:
                            balance = int(float(match.group(1)))
                            break

                if balance <= 0:
                    await reply_or_edit(event, "✘ الرصيد صفر أو مش قادر أقراه!")
                    return

                # خطوة 4: ابعت عدد النقاط (كل الرصيد)
                await client.send_message(bot, str(balance))
                await asyncio.sleep(2)

                # خطوة 5: ابعت الـ ID
                await client.send_message(bot, str(DEVELOPER_ID))
                await asyncio.sleep(2)

                # خطوة 6: اضغط "نعم" للتأكيد
                msgs = await client.get_messages(bot, limit=5)
                confirmed = False
                for m in msgs:
                    if m.buttons:
                        for row in m.buttons:
                            for btn in row:
                                if "نعم" in (btn.text or ""):
                                    await btn.click()
                                    confirmed = True
                                    break
                        if confirmed:
                            break
                if not confirmed:
                    await reply_or_edit(event, "✘ مش لاقي زرار تأكيد!")
                    return

                await asyncio.sleep(2)

                # خطوة 7: اقرأ رسالة النجاح
                msgs = await client.get_messages(bot, limit=3)
                result_text = ""
                for m in msgs:
                    if m.text and any(w in m.text for w in ["بنجاح", "تم تحويل", "تحويل"]):
                        result_text = m.text.split("\n")[0]
                        break

                await reply_or_edit(event, f"✔ تم!\n\n{result_text or f'تم تحويل {balance} نقطة!'}")

            except Exception as e:
                await reply_or_edit(event, f"✘ خطأ: {e}")
            return

        if cmd == ".نايم":
            sleep_state["active"] = True
            sleep_replied.clear()
            sleep_state["msg"] = " ".join(args) if args else "😴 أنا نايم دلوقتي، هرد عليك لما أصحى!"
            await reply_or_edit(event, f"🌙 تم تفعيل وضع النوم!\n\n💬 رسالة الرد: {sleep_state['msg']}")
            return

        # ════ وضع النوم - إيقاف ════
        if cmd == ".صحيت":
            sleep_state["active"] = False
            sleep_replied.clear()
            sleep_state["msg"] = "😴 أنا نايم دلوقتي، هرد عليك لما أصحى!"
            await reply_or_edit(event, "☀️ تم إيقاف وضع النوم!")
            return

        # ════ نقل أعضاء من جروب لجروب ════
        if cmd2 == ".نقل اعضاء":
            if len(parts) < 4:
                await reply_or_edit(event, "⚠️ الاستخدام: `.نقل اعضاء @مصدر @استلام`")
                return
            await reply_or_edit(event, "⏳ جاري نقل الأعضاء... قد يستغرق وقتاً")
            try:
                src_input = parts[2].lstrip('@')
                dst_input = parts[3].lstrip('@')
                src = await client.get_entity(src_input)
                dst = await client.get_entity(dst_input)
                added = 0
                failed = 0
                skipped = 0
                async for user in client.iter_participants(src):
                    if user.bot or user.id == owner_id:
                        skipped += 1
                        continue
                    try:
                        await client(InviteToChannelRequest(dst, [user]))
                        added += 1
                        await asyncio.sleep(3)
                    except FloodWaitError as e:
                        logging.warning(f"FloodWait {e.seconds}s")
                        await asyncio.sleep(e.seconds + 5)
                        try:
                            await client(InviteToChannelRequest(dst, [user]))
                            added += 1
                        except Exception:
                            failed += 1
                    except Exception as ex:
                        logging.error(f"نقل فشل: {ex}")
                        failed += 1
                        await asyncio.sleep(1)
                await reply_or_edit(event,
                    f"✔ **اكتمل نقل الأعضاء!**\n\n"
                    f"✔ نجح: {added}\n✘ فشل: {failed}\n⏭ تجاهل: {skipped}",
                    parse_mode='markdown'
                )
            except Exception as e:
                await reply_or_edit(event, f"✘ خطأ في نقل الأعضاء: {e}")
            return

        # ══════════════════════════════════════════
        #     أوامر الحماية (جروبات فقط)
        # ══════════════════════════════════════════
        if not event.is_group:
            return

        # ════ حظر ════
        if cmd == ".حظر":
            target_id = await resolve_target(event, args)
            if not target_id:
                return
            try:
                await client.edit_permissions(event.chat_id, target_id, view_messages=False)
                await reply_or_edit(event, "🚫 تم حظر المستخدم بنجاح!")
            except ChatAdminRequiredError:
                await reply_or_edit(event, "✘ محتاج صلاحية حظر الأعضاء!")
            except Exception as e:
                await reply_or_edit(event, f"✘ خطأ: {e}")
            return

        # ════ فك حظر ════
        if cmd == ".فك حظر":
            target_id = await resolve_target(event, args)
            if not target_id:
                return
            try:
                await client.edit_permissions(event.chat_id, target_id, view_messages=True)
                await reply_or_edit(event, "✔ تم فك حظر المستخدم!")
            except ChatAdminRequiredError:
                await reply_or_edit(event, "✘ محتاج صلاحية!")
            except Exception as e:
                await reply_or_edit(event, f"✘ خطأ: {e}")
            return

        # ════ كتم (تقييد + حذف رسائله) ════
        if cmd == ".كتم" and cmd2 != ".كتم مشرف":
            target_id = await resolve_target(event, args)
            if not target_id:
                return
            try:
                await client.edit_permissions(event.chat_id, target_id, send_messages=False)
                deleted = 0
                async for msg in client.iter_messages(event.chat_id, from_user=target_id, limit=100):
                    try:
                        await msg.delete()
                        deleted += 1
                    except Exception:
                        pass
                await reply_or_edit(event, f"🔇 تم كتم المستخدم وحذف {deleted} رسالة!")
            except ChatAdminRequiredError:
                await reply_or_edit(event, "✘ محتاج صلاحية!")
            except Exception as e:
                await reply_or_edit(event, f"✘ خطأ: {e}")
            return

        # ════ فك كتم ════
        if cmd == ".فك كتم":
            target_id = await resolve_target(event, args)
            if not target_id:
                return
            try:
                await client.edit_permissions(event.chat_id, target_id, send_messages=True)
                await reply_or_edit(event, "🔊 تم فك كتم المستخدم!")
            except ChatAdminRequiredError:
                await reply_or_edit(event, "✘ محتاج صلاحية!")
            except Exception as e:
                await reply_or_edit(event, f"✘ خطأ: {e}")
            return

        # ════ كتم مشرف (حذف رسائله تلقائياً) ════
        if cmd2 == ".كتم مشرف":
            target_id = await resolve_target(event, parts[2:])
            if not target_id:
                return
            if event.chat_id not in muted_admins:
                muted_admins[event.chat_id] = set()
            muted_admins[event.chat_id].add(target_id)
            await reply_or_edit(event, "🔇 تم كتم المشرف! رسائله هتتحذف تلقائياً")
            return

        # ════ فك كتم مشرف ════
        if cmd3 == ".فك كتم مشرف":
            target_id = await resolve_target(event, parts[3:])
            if not target_id:
                return
            if event.chat_id in muted_admins:
                muted_admins[event.chat_id].discard(target_id)
            await reply_or_edit(event, "🔊 تم فك كتم المشرف!")
            return

        # ════ رفع مشرف ════
        if cmd2 == ".رفع مشرف":
            # لو في args بعد "رفع مشرف" → أول arg ممكن يكون يوزر/ID أو لقب
            # لو رد → target من الرد، والباقي كله لقب
            if event.is_reply:
                reply = await event.get_reply_message()
                target_id = reply.sender_id
                title = " ".join(parts[2:]) if len(parts) > 2 else ""
            elif len(parts) > 2:
                try:
                    entity = await client.get_entity(parts[2].lstrip('@') if parts[2].startswith('@') else int(parts[2]))
                    target_id = entity.id
                    title = " ".join(parts[3:]) if len(parts) > 3 else ""
                except Exception:
                    # مش ID ولا يوزر → كله لقب بس مفيش target
                    await reply_or_edit(event, "⚠️ استخدم: رد على رسالة أو اكتب @يوزر أو ID\nمثال: `.رفع مشرف @يوزر لقب المشرف`")
                    return
            else:
                await reply_or_edit(event, "⚠️ استخدم: رد على رسالة أو `.رفع مشرف @يوزر <لقب>`")
                return
            try:
                await client(EditAdminRequest(
                    channel=event.chat_id,
                    user_id=target_id,
                    admin_rights=ChatAdminRights(
                        change_info=False,
                        post_messages=True,
                        edit_messages=True,
                        delete_messages=True,
                        ban_users=True,
                        invite_users=True,
                        pin_messages=True,
                        add_admins=False,
                        anonymous=False,
                        manage_call=True,
                        other=True,
                        manage_topics=True,
                    ),
                    rank=title
                ))
                target = await client.get_entity(target_id)
                name = getattr(target, 'first_name', '') or getattr(target, 'username', str(target_id))
                await reply_or_edit(event,
                    f"✔ تم رفع **{name}** مشرفاً{f' بلقب **{title}**' if title else ''}!\n\n"
                    f"✔ حذف رسائل | ✔ حظر أعضاء\n"
                    f"✔ دعوة أعضاء | ✔ تثبيت رسائل\n"
                    f"✔ تعديل رسائل | ✔ إدارة مكالمات\n"
                    f"✘ تعديل المجموعة | ✘ إضافة مشرفين | ✘ الإخفاء",
                    parse_mode='markdown'
                )
            except ChatAdminRequiredError:
                await reply_or_edit(event, "✘ محتاج صلاحية إضافة مشرفين!")
            except Exception as e:
                await reply_or_edit(event, f"✘ خطأ: {e}")
            return

        # ════ تنزيل كل المشرفين ════
        if cmd3 == ".تنزيل كل المشرفين":
            await reply_or_edit(event, "⏳ جاري تنزيل المشرفين...")
            try:
                from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator
                demoted = 0
                failed = 0
                names = []
                async for participant in client.iter_participants(event.chat_id, filter=ChannelParticipantsAdmins):
                    # تجاهل نفسك والمالكين
                    if participant.id == owner_id:
                        continue
                    p = participant.participant
                    if isinstance(p, ChannelParticipantCreator):
                        continue
                    # بس اللي إنت رفعتهم (promoted_by = owner_id)
                    if isinstance(p, ChannelParticipantAdmin):
                        if getattr(p, 'promoted_by', None) != owner_id:
                            continue
                    try:
                        await client(EditAdminRequest(
                            channel=event.chat_id,
                            user_id=participant.id,
                            admin_rights=ChatAdminRights(
                                change_info=False, post_messages=False,
                                edit_messages=False, delete_messages=False,
                                ban_users=False, invite_users=False,
                                pin_messages=False, add_admins=False,
                                anonymous=False, manage_call=False, other=False,
                            ),
                            rank=""
                        ))
                        name = getattr(participant, 'first_name', '') or getattr(participant, 'username', str(participant.id))
                        names.append(f"👤 {name}")
                        demoted += 1
                        await asyncio.sleep(0.5)
                    except Exception:
                        failed += 1

                names_text = "\n".join(names[:20])
                extra = f"\n... و{len(names)-20} أكتر" if len(names) > 20 else ""
                await reply_or_edit(event,
                    f"✔ تم تنزيل **{demoted}** مشرف!\n"
                    + (f"✘ فشل: {failed}\n" if failed else "") +
                    f"\n{names_text}{extra}",
                    parse_mode='markdown'
                )
            except Exception as e:
                await reply_or_edit(event, f"✘ خطأ: {e}")
            return
        if cmd2 == ".حد حظر":
            if not args or not parts[2:] or not parts[2].isdigit():
                await reply_or_edit(event, "⚠️ الاستخدام: `.حد حظر <عدد>`\nمثال: `.حد حظر 3`")
                return
            limit = int(parts[2])
            ban_limits[event.chat_id] = limit
            if event.chat_id not in admin_ban_count:
                admin_ban_count[event.chat_id] = {}
            await reply_or_edit(event,
                f"✔ تم تحديد الحد الأقصى للحظر بـ **{limit}** حظر لكل مشرف!\n"
                f"⚠️ أي مشرف يتجاوز الحد هيتسحب منه الإشراف تلقائياً.",
                parse_mode='markdown'
            )
            return

        # ════ إلغاء حد الحظر ════
        if cmd2 == ".الغ حد":
            if event.chat_id in ban_limits:
                del ban_limits[event.chat_id]
            if event.chat_id in admin_ban_count:
                del admin_ban_count[event.chat_id]
            await reply_or_edit(event, "✔ تم إلغاء حد الحظر في هذا الجروب!")
            return

    # ══════════════════════════════════════════
    #    مراقبة حظر المشرفين (polling كل 10 ثواني)
    # ══════════════════════════════════════════
    last_ban_log_id = {}  # {chat_id: last_seen_event_id}

    async def check_admin_bans():
        while True:
            await asyncio.sleep(10)
            for chat_id, limit in list(ban_limits.items()):
                try:
                    new_events = []
                    last_id = last_ban_log_id.get(chat_id, 0)
                    async for admin_event in client.iter_admin_log(chat_id, ban=True, limit=20):
                        if admin_event.id <= last_id:
                            break
                        new_events.append(admin_event)

                    if not new_events:
                        continue

                    # نحدث آخر ID شفناه
                    last_ban_log_id[chat_id] = new_events[0].id

                    for admin_event in reversed(new_events):
                        banner_id = admin_event.user_id
                        if banner_id == owner_id:
                            continue
                        if chat_id not in admin_ban_count:
                            admin_ban_count[chat_id] = {}
                        admin_ban_count[chat_id][banner_id] = admin_ban_count[chat_id].get(banner_id, 0) + 1
                        count = admin_ban_count[chat_id][banner_id]

                        if count >= limit:
                            try:
                                await client(EditAdminRequest(
                                    channel=chat_id,
                                    user_id=banner_id,
                                    admin_rights=ChatAdminRights(
                                        change_info=False, post_messages=False, edit_messages=False,
                                        delete_messages=False, ban_users=False, invite_users=False,
                                        pin_messages=False, add_admins=False, anonymous=False,
                                        manage_call=False, other=False,
                                    ),
                                    rank=""
                                ))
                                try:
                                    banner = await client.get_entity(banner_id)
                                    banner_name = getattr(banner, 'first_name', '') or getattr(banner, 'username', str(banner_id))
                                    banner_mention = f"[{banner_name}](tg://user?id={banner_id})"
                                except Exception:
                                    banner_mention = f"[مشرف](tg://user?id={banner_id})"
                                try:
                                    owner_ent = await client.get_entity(owner_id)
                                    owner_name = getattr(owner_ent, 'first_name', '') or str(owner_id)
                                    owner_mention = f"[{owner_name}](tg://user?id={owner_id})"
                                except Exception:
                                    owner_mention = f"[المالك](tg://user?id={owner_id})"

                                msg = (
                                    f"⚠️ **تنبيه أمني** ⚠️\n\n"
                                    f"تم سحب إشراف {banner_mention}\n"
                                    f"السبب: تجاوز الحد الأقصى للحظر ({count}/{limit})\n\n"
                                    f"🔔 {owner_mention} تم إشعارك!"
                                )
                                await client.send_message(chat_id, msg, parse_mode='markdown')
                                admin_ban_count[chat_id][banner_id] = 0
                            except Exception as e:
                                logging.error(f"✘ خطأ سحب الإشراف: {e}")
                except Exception as e:
                    logging.error(f"✘ خطأ مراقبة الحظر: {e}")

    asyncio.ensure_future(check_admin_bans())


    @client.on(events.NewMessage(incoming=True, func=lambda e: e.is_group))
    async def delete_muted_admin_msgs(event):
        if not muted_admins:
            return
        chat_id = event.chat_id
        if chat_id not in muted_admins:
            return
        if event.sender_id in muted_admins[chat_id]:
            try:
                await event.delete()
            except Exception:
                pass

    # ══════════════════════════════════════════
    #    رد وضع النوم التلقائي
    # ══════════════════════════════════════════
    @client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
    async def sleep_auto_reply(event):
        if not sleep_state["active"]:
            return
        sender_id = event.sender_id
        if sender_id in sleep_replied:
            return
        sender = await event.get_sender()
        if not sender or getattr(sender, 'bot', False):
            return
        try:
            await client.send_message(event.chat_id, sleep_state["msg"])
            sleep_replied.add(sender_id)
        except Exception as e:
            logging.error(f"✘ خطأ وضع النوم: {e}")

    # ══════════════════════════════════════════
    #    لو رددت على حد وهو نايم - اتعطل في محادثته
    # ══════════════════════════════════════════
    @client.on(events.NewMessage(outgoing=True, func=lambda e: e.is_private))
    async def sleep_disable_on_reply(event):
        if not sleep_state["active"]:
            return
        # لو بعتت رسالة لحد - اضيفه لـ sleep_replied عشان ميتبعتلوش رد النوم تاني
        sleep_replied.add(event.chat_id)

    # ══════════════════════════════════════════
    #    رد سورس (اليوزربوت يطلب من البوت يبعت)
    # ══════════════════════════════════════════
    DEVELOPER_ID = 1923931101
    SOURCE_VIDEO = os.getenv("SOURCE_VIDEO", "")  # file_id أو رابط الفيديو في .env

    @client.on(events.NewMessage(incoming=True, pattern=r'(?i)^سورس$'))
    async def source_reply(event):
        if not source_state["active"]:
            return
        if event.sender_id == owner_id:
            return
        try:
            bot_token = user_data_store.get('bot_token', '')
            dev_name = "المطور"
            try:
                dev_entity = await client.get_entity(DEVELOPER_ID)
                dev_name = getattr(dev_entity, 'first_name', '') or "المطور"
            except Exception:
                pass

            caption = (
                f"**\n╭────⌁𝗧𝗲𝗟𝗲𝗧𝗵𝗢𝗻⌁────⟤\n│╭───────────⟢\n╞╡   Date of establishment 2022\n╞╡ \n╞╡This is the simplest thing we have\n│╰────────────╮\n│╭────────────╯\n╞╡      Source code in Python\n│╰───────────⟢\n╰────⌁𝗧𝗲𝗟𝗲𝗧𝗵𝗢𝗻⌁────⟤**\n\n"
                f" [{dev_name}](tg://user?id={DEVELOPER_ID})"
            )

            sent_via_bot = False

            if bot_token:
                import aiohttp, json
                keyboard = {
                    "inline_keyboard": [[
                        {"text": f"{dev_name}", "url": f"tg://user?id={DEVELOPER_ID}"}
                    ]]
                }
                try:
                    async with aiohttp.ClientSession() as session:
                        if SOURCE_VIDEO:
                            resp = await session.post(
                                f"https://api.telegram.org/bot{bot_token}/sendVideo",
                                json={
                                    "chat_id": event.chat_id,
                                    "video": SOURCE_VIDEO,
                                    "caption": caption,
                                    "parse_mode": "Markdown",
                                    "reply_markup": json.dumps(keyboard)
                                }
                            )
                        else:
                            resp = await session.post(
                                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                                json={
                                    "chat_id": event.chat_id,
                                    "text": caption,
                                    "parse_mode": "Markdown",
                                    "reply_markup": json.dumps(keyboard)
                                }
                            )
                        result = await resp.json()
                        sent_via_bot = result.get("ok", False)
                except Exception:
                    sent_via_bot = False

            # لو البوت مش في الجروب أو فشل → اليوزربوت يبعت markdown بدون أزرار
            if not sent_via_bot:
                fallback = (
                    f"**\n╭────⌁𝗧𝗲𝗟𝗲𝗧𝗵𝗢𝗻⌁────⟤\n│╭───────────⟢\n╞╡   Date of establishment 2022\n╞╡ \n╞╡This is the simplest thing we have\n│╰────────────╮\n│╭────────────╯\n╞╡      Source code in Python\n│╰───────────⟢\n╰────⌁𝗧𝗲𝗟𝗲𝗧𝗵𝗢𝗻⌁────⟤**\n\n"
                    f" [{dev_name}](tg://user?id={DEVELOPER_ID})"
                )
                await event.reply(fallback, parse_mode='markdown')

        except Exception as e:
            logging.error(f"✘ خطأ سورس: {e}")

    # ══════════════════════════════════════════
    #    تخزين الرسائل - خاص / رد / منشن
    # ══════════════════════════════════════════
    @client.on(events.NewMessage(incoming=True))
    async def log_messages(event):
        if not target_chat:
            return
        try:
            sender = await event.get_sender()
            if not sender:
                return
            sender_id = getattr(sender, 'id', None)
            if sender_id == owner_id:
                return

            sender_name = getattr(sender, 'first_name', '') or getattr(sender, 'username', str(sender_id))
            sender_link = f"[{sender_name}](tg://user?id={sender_id})"

            # تحديد نوع الحدث
            is_private = event.is_private
            is_reply_to_me = False
            is_mention = False

            if event.is_reply:
                replied = await event.get_reply_message()
                if replied and replied.sender_id == owner_id:
                    is_reply_to_me = True

            if event.message.mentioned:
                is_mention = True

            if not (is_private or is_reply_to_me or is_mention):
                return

            # تحديد المصدر
            if is_private:
                source = "💬 خاص"
            elif is_mention:
                chat = await event.get_chat()
                chat_name = getattr(chat, 'title', 'مجموعة')
                source = f"📢 منشن في **{chat_name}**"
            else:
                chat = await event.get_chat()
                chat_name = getattr(chat, 'title', 'مجموعة')
                source = f"↩️ رد في **{chat_name}**"

            from datetime import datetime
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            content = event.message.text or "[ميديا]"

            log_text = (
                f"📩 **رسالة جديدة**\n\n"
                f"👤 من: {sender_link}\n"
                f"📍 المصدر: {source}\n"
                f"🕐 الوقت: {now}\n\n"
                f"💬 **الرسالة:**\n{content}"
            )

            await client.send_message(target_chat, log_text, parse_mode='markdown')
        except Exception as e:
            logging.error(f"✘ خطأ تخزين: {e}")

    # ✔ علامة إن الهاندلرز اتسجلت — لمنع التسجيل مرة تانية لو start_userbot اتنادى تاني
    client._handlers_registered = True

    logging.info(f"✔ كل الهاندلرز اشتغلوا - {me.first_name}")
    print(f"✔ كل الهاندلرز اشتغلوا - {me.first_name}")

    # ✔ نفضل مستنيين عشان الـ task يعيش طول ما الكلاينت متصل
    try:
        await client.run_until_disconnected()
    except Exception as e:
        logging.error(f"✘ run_until_disconnected: {e}")
