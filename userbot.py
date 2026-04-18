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
╭━─━─━Source━─━─━➾
        @I0_I6
╰━─━─━Source━─━─━➾"""

COMMANDS_TEXT = """📌 **قائمة الأوامر** 📌
━━━━━━━━━━━━━━━━━━━━

🛡️ **الحماية (جروبات):**
`.حظر` — حظر عضو (رد / يوزر / ID)
`.فكحظر` — فك حظر عضو
`.كتم` — تقييد العضو من الإرسال + حذف رسائله
`.فككتم` — فك التقييد
`.كتم مشرف` — حذف رسائل مشرف تلقائياً
`.فك كتم مشرف` — إيقاف حذف رسائل المشرف
`.رفع مشرف <لقب>` — رفع المرد عليه مشرف بلقب مخصص وكل الصلاحيات
`.حد حظر <عدد>` — تحديد الحد الأقصى للحظر لكل مشرف (يتسحب منه الإشراف لو تجاوز)
`.الغ حد` — إلغاء حد الحظر في الجروب

━━━━━━━━━━━━━━━━━━━━

📢 **الإذاعة:**
`.اذاعة خاص <رسالة>` — إرسال لكل المحادثات الخاصة
`.اذاعة جروب <رسالة>` — إرسال لكل المجموعات

━━━━━━━━━━━━━━━━━━━━

📡 **متابعة القناة (كروت الشحن):**
`.تتبع قناة <@قناة_المصدر> <@قناة_الاستلام>` — بدء التتبع
`.وقف التتبع` — إيقاف التتبع

━━━━━━━━━━━━━━━━━━━━

👋 **الترحيب (خاص):**
يتفعل تلقائياً عند أول رسالة
`.قبول` (رد على رسالة) — إيقاف الترحيب + حذف رسالة الترحيب تلقائياً

━━━━━━━━━━━━━━━━━━━━

😴 **وضع النوم:**
`.نايم` — تفعيل وضع النوم (رد تلقائي لكل من يكلمك)
`.نايم <رسالة>` — نفس الأمر برسالة مخصصة
`.صحيت` — إيقاف وضع النوم

━━━━━━━━━━━━━━━━━━━━

📁 **المجلدات:**
`.مجلد قنواتي` — يجمع قنواتك في مجلد
`.مجلد جروباتي` — يجمع جروباتك في مجلد
`.مجلد بوتاتي` — يجمع البوتات في مجلد
> يمكن إضافة اسم مخصص: `.مجلد قنواتي اسم المجلد`

━━━━━━━━━━━━━━━━━━━━
"""

# ══════════════════════════════════════════
#              الدالة الرئيسية
# ══════════════════════════════════════════
async def start_userbot(client: TelegramClient, target_chat, user_data_store):
    me = await client.get_me()
    owner_id = me.id
    logging.info(f"✅ يوزربوت شغال: {me.first_name} ({owner_id})")
    print(f"✅ يوزربوت شغال: {me.first_name} ({owner_id})")

    # ══ الحالات الداخلية ══
    muted_admins = {}          # {chat_id: set(user_ids)}
    welcomed_users = {}        # {sender_id: msg_id} - رسايل الترحيب اللي اتبعتت
    accepted_users = set()     # المستخدمين اللي اتعملهم .قبول
    tracked_channels = {}      # {source_channel_id: dest_channel_id}
    sleep_mode = False         # وضع النوم
    sleep_replied = set()      # المحادثات اللي رددت فيها وهو نايم (تتعطل فيها)
    sleep_state = {"active": False, "msg": "😴 أنا نايم دلوقتي، هرد عليك لما أصحى!"}
    ban_limits = {}            # {chat_id: max_bans} - الحد الأقصى للحظر لكل جروب
    admin_ban_count = {}       # {chat_id: {admin_id: count}} - عداد حظر كل مشرف

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
                await reply_or_edit(event, f"❌ مش قادر أجيب المستخدم: {e}")
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
                logging.info(f"✅ ارسل: {msg}")

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
        sender_id = event.sender_id
        if sender_id in welcomed_users or sender_id in accepted_users:
            return
        sender = await event.get_sender()
        if not sender or getattr(sender, 'bot', False):
            return

        welcome_text = (
            f"أهلاً وسهلاً بيك! 🔥\n\n"
            f"سيب رسالتك وهنرد عليك في أقرب وقت 💬\n\n"
            f"{SOURCE_TAG}"
        )
        try:
            sent = await client.send_file(
                event.chat_id,
                WELCOME_GIF,
                caption=welcome_text,
                parse_mode='markdown'
            )
            welcomed_users[sender_id] = sent.id  # نحفظ ID الرسالة عشان نحذفها بعدين
        except Exception:
            try:
                sent = await event.respond(welcome_text, parse_mode='markdown')
                welcomed_users[sender_id] = sent.id
            except Exception as e:
                logging.error(f"❌ خطأ ترحيب: {e}")

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

        # أوامر متعددة الكلمات
        cmd2 = " ".join(parts[:2]).lower() if len(parts) >= 2 else ""
        cmd3 = " ".join(parts[:3]).lower() if len(parts) >= 3 else ""

        # ════ قائمة الأوامر ════
        if cmd in (".الاوامر", ".اوامري"):
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
            await reply_or_edit(event, f"✅ تم الإرسال لـ {count} محادثة خاصة!")
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
            await reply_or_edit(event, f"✅ تم الإرسال لـ {count} مجموعة!")
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
                    f"✅ بدأ التتبع!\n"
                    f"📡 المصدر: {src.title}\n"
                    f"📥 الاستلام: {dst.title}\n\n"
                    f"🔍 هيستخرج أي رقم بصيغة `*858*XXXXXX#` تلقائياً"
                )
            except Exception as e:
                await reply_or_edit(event, f"❌ خطأ: {e}")
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
                    await reply_or_edit(event, "❌ مش لاقي أي قناة إنت مالكها!")
                    return
                result = await make_folder(folder_name, peers, names)
                await reply_or_edit(event, f"✅ تم إنشاء مجلد **{folder_name}**!\n\n{result}", parse_mode='markdown')
            except Exception as e:
                await reply_or_edit(event, f"❌ حصل خطأ: {e}")
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
                    await reply_or_edit(event, "❌ مش لاقي أي جروب إنت مالكه!")
                    return
                result = await make_folder(folder_name, peers, names)
                await reply_or_edit(event, f"✅ تم إنشاء مجلد **{folder_name}**!\n\n{result}", parse_mode='markdown')
            except Exception as e:
                await reply_or_edit(event, f"❌ حصل خطأ: {e}")
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
                    await reply_or_edit(event, "❌ مش لاقي أي بوت!")
                    return
                result = await make_folder(folder_name, peers, names)
                await reply_or_edit(event, f"✅ تم إنشاء مجلد **{folder_name}**!\n\n{result}", parse_mode='markdown')
            except Exception as e:
                await reply_or_edit(event, f"❌ حصل خطأ: {e}")
            return

        # ════ وضع النوم - تفعيل ════
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
                await reply_or_edit(event, "❌ محتاج صلاحية حظر الأعضاء!")
            except Exception as e:
                await reply_or_edit(event, f"❌ خطأ: {e}")
            return

        # ════ فك حظر ════
        if cmd == ".فكحظر":
            target_id = await resolve_target(event, args)
            if not target_id:
                return
            try:
                await client.edit_permissions(event.chat_id, target_id, view_messages=True)
                await reply_or_edit(event, "✅ تم فك حظر المستخدم!")
            except ChatAdminRequiredError:
                await reply_or_edit(event, "❌ محتاج صلاحية!")
            except Exception as e:
                await reply_or_edit(event, f"❌ خطأ: {e}")
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
                await reply_or_edit(event, "❌ محتاج صلاحية!")
            except Exception as e:
                await reply_or_edit(event, f"❌ خطأ: {e}")
            return

        # ════ فك كتم ════
        if cmd == ".فككتم":
            target_id = await resolve_target(event, args)
            if not target_id:
                return
            try:
                await client.edit_permissions(event.chat_id, target_id, send_messages=True)
                await reply_or_edit(event, "🔊 تم فك كتم المستخدم!")
            except ChatAdminRequiredError:
                await reply_or_edit(event, "❌ محتاج صلاحية!")
            except Exception as e:
                await reply_or_edit(event, f"❌ خطأ: {e}")
            return

        # ════ كتم مشرف (حذف رسائله تلقائياً) ════
        if cmd2 == ".كتم مشرف":
            if not event.is_reply:
                await reply_or_edit(event, "⚠️ رد على رسالة المشرف عشان تكتمه!")
                return
            reply = await event.get_reply_message()
            target_id = reply.sender_id
            if event.chat_id not in muted_admins:
                muted_admins[event.chat_id] = set()
            muted_admins[event.chat_id].add(target_id)
            await reply_or_edit(event, "🔇 تم كتم المشرف! رسائله هتتحذف تلقائياً")
            return

        # ════ فك كتم مشرف ════
        if cmd3 == ".فك كتم مشرف":
            if not event.is_reply:
                await reply_or_edit(event, "⚠️ رد على رسالة المشرف عشان تفك كتمه!")
                return
            reply = await event.get_reply_message()
            target_id = reply.sender_id
            if event.chat_id in muted_admins:
                muted_admins[event.chat_id].discard(target_id)
            await reply_or_edit(event, "🔊 تم فك كتم المشرف!")
            return

        # ════ رفع مشرف ════
        if cmd2 == ".رفع مشرف":
            if not event.is_reply:
                await reply_or_edit(event, "⚠️ رد على رسالة العضو عشان ترفعه مشرف!")
                return
            title = " ".join(parts[2:]) if len(parts) > 2 else ""
            reply = await event.get_reply_message()
            target_id = reply.sender_id
            try:
                await client(EditAdminRequest(
                    channel=event.chat_id,
                    user_id=target_id,
                    admin_rights=ChatAdminRights(
                        change_info=False,       # ❌ تعديل معلومات المجموعة
                        post_messages=True,      # ✅ نشر رسائل
                        edit_messages=True,      # ✅ تعديل رسائل
                        delete_messages=True,    # ✅ حذف رسائل
                        ban_users=True,          # ✅ حظر أعضاء
                        invite_users=True,       # ✅ دعوة أعضاء
                        pin_messages=True,       # ✅ تثبيت رسائل
                        add_admins=False,        # ❌ إضافة مشرفين
                        anonymous=False,         # ❌ إخفاء
                        manage_call=True,        # ✅ إدارة المكالمات
                        other=True,
                        manage_topics=True,
                    ),
                    rank=title
                ))
                target = await client.get_entity(target_id)
                name = getattr(target, 'first_name', '') or getattr(target, 'username', str(target_id))
                await reply_or_edit(event,
                    f"✅ تم رفع **{name}** مشرفاً{f' بلقب **{title}**' if title else ''}!\n\n"
                    f"📋 الصلاحيات:\n"
                    f"✅ حذف رسائل | ✅ حظر أعضاء\n"
                    f"✅ دعوة أعضاء | ✅ تثبيت رسائل\n"
                    f"✅ تعديل رسائل | ✅ إدارة مكالمات\n"
                    f"❌ تعديل المجموعة | ❌ إضافة مشرفين | ❌ الإخفاء",
                    parse_mode='markdown'
                )
            except ChatAdminRequiredError:
                await reply_or_edit(event, "❌ محتاج صلاحية إضافة مشرفين!")
            except Exception as e:
                await reply_or_edit(event, f"❌ خطأ: {e}")
            return

        # ════ تحديد حد الحظر للمشرفين ════
        if cmd2 == ".حد حظر":
            if not args or not parts[2:] or not parts[2].isdigit():
                await reply_or_edit(event, "⚠️ الاستخدام: `.حد حظر <عدد>`\nمثال: `.حد حظر 3`")
                return
            limit = int(parts[2])
            ban_limits[event.chat_id] = limit
            if event.chat_id not in admin_ban_count:
                admin_ban_count[event.chat_id] = {}
            await reply_or_edit(event,
                f"✅ تم تحديد الحد الأقصى للحظر بـ **{limit}** حظر لكل مشرف!\n"
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
            await reply_or_edit(event, "✅ تم إلغاء حد الحظر في هذا الجروب!")
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
                                logging.error(f"❌ خطأ سحب الإشراف: {e}")
                except Exception as e:
                    logging.error(f"❌ خطأ مراقبة الحظر: {e}")

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
            logging.error(f"❌ خطأ وضع النوم: {e}")

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
                f"✨ **سورس البوت**\n\n"
                f"🛠 تم التطوير بواسطة: [{dev_name}](tg://user?id={DEVELOPER_ID})"
            )

            sent_via_bot = False

            if bot_token:
                import aiohttp, json
                keyboard = {
                    "inline_keyboard": [[
                        {"text": f"👨‍💻 {dev_name}", "url": f"tg://user?id={DEVELOPER_ID}"}
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
                    f"✨ **سورس البوت**\n\n"
                    f"🛠 تم التطوير بواسطة: [{dev_name}](tg://user?id={DEVELOPER_ID})"
                )
                await event.reply(fallback, parse_mode='markdown')

        except Exception as e:
            logging.error(f"❌ خطأ سورس: {e}")

    logging.info(f"✅ كل الهاندلرز اشتغلوا - {me.first_name}")
    print(f"✅ كل الهاندلرز اشتغلوا - {me.first_name}")
