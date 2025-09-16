import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
from message_extractor import MessageExtractor
from config import API_ID, API_HASH, BOT_TOKEN, FULL_SESSION_PATH, FULL_BOT_SESSION_PATH

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageExtractorBot:
    """消息提取Bot处理器"""
    
    def __init__(self):
        self.bot = Client(
            name=FULL_BOT_SESSION_PATH,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN
        )
        self.extractor = MessageExtractor(API_ID, API_HASH, FULL_SESSION_PATH)
        self.setup_handlers()
    
    def setup_handlers(self):
        """设置消息处理器"""
        
        @self.bot.on_message(filters.command("start"))
        async def start_command(client, message: Message):
            """开始命令"""
            welcome_text = """
🤖 **Telegram 消息转发工具**

欢迎使用消息转发工具！

📋 **使用方法**:
1. 发送 Telegram 消息链接给我
2. 我会将原消息完整转发给您

🔗 **支持的链接格式**:
• `https://t.me/channel_name/123`
• `https://t.me/c/123456789/123`
• `t.me/channel_name/123`

📱 **支持的消息类型**:
• 文本消息
• 图片、视频、文档
• 音频、语音消息
• 贴纸、GIF动画
• 媒体组/相册（多媒体组合）

💡 **提示**: 请确保您有权限访问该消息所在的频道或群组。

发送 /help 查看更多帮助信息。
            """
            await message.reply(welcome_text)
        
        @self.bot.on_message(filters.command("help"))
        async def help_command(client, message: Message):
            """帮助命令"""
            help_text = """
🆘 **帮助信息**

**命令列表**:
• `/start` - 开始使用
• `/help` - 显示帮助信息
• `/status` - 检查服务状态

**使用步骤**:
1. 复制要转发的 Telegram 消息链接
2. 直接发送链接给我
3. 我会将原消息完整转发给您

**支持的消息类型**:
✅ 文本消息（保持原格式）
✅ 图片消息（包含说明文字）
✅ 视频消息（保持画质和时长）
✅ 文档文件（保持原文件名）
✅ 音频文件（保持标题和演唱者信息）
✅ 语音消息（保持时长）
✅ 贴纸和GIF动画
✅ 媒体组/相册（多图片/视频组合）

**注意事项**:
⚠️ 只能转发您有权限访问的消息
⚠️ 私人聊天的消息可能无法访问
⚠️ 某些受限频道可能需要额外权限
⚠️ 转发的消息会失去原始的转发标记

**链接示例**:
• `https://t.me/telegram/123`
• `https://t.me/c/1234567890/456`
            """
            await message.reply(help_text)
        
        @self.bot.on_message(filters.command("status"))
        async def status_command(client, message: Message):
            """状态检查命令"""
            try:
                # 检查提取器状态
                if self.extractor.client and self.extractor.client.is_connected:
                    status = "✅ 消息转发服务正常运行"
                else:
                    status = "❌ 消息转发服务未连接"
                
                await message.reply(f"🔍 **服务状态**\n\n{status}")
            except Exception as e:
                await message.reply(f"❌ 检查状态时出错: {str(e)}")
        
        @self.bot.on_message(filters.text & ~filters.command(["start", "help", "status"]))
        async def handle_message_link(client, message: Message):
            """处理消息链接"""
            text = message.text.strip()
            
            # 检查是否包含 t.me 链接
            if "t.me" not in text:
                await message.reply(
                    "❌ 请发送有效的 Telegram 消息链接\n\n"
                    "支持的格式:\n"
                    "• `https://t.me/channel_name/123`\n"
                    "• `https://t.me/c/123456789/123`\n"
                    "• `t.me/channel_name/123`"
                )
                return
            
            # 发送处理中消息
            processing_msg = await message.reply("🔄 正在获取消息信息，请稍候...")
            
            try:
                # 确保提取器已初始化
                if not self.extractor.client or not self.extractor.client.is_connected:
                    await self.extractor.initialize()
                
                # 获取原始消息对象（可能是媒体组）
                messages_to_forward = await self.extractor.get_media_group_messages(text)
                
                if messages_to_forward:
                    # 转发消息（可能是多条）
                    if len(messages_to_forward) > 1:
                        logger.info(f"检测到媒体组，包含 {len(messages_to_forward)} 条消息")
                        # 更新处理消息
                        await processing_msg.edit(f"📸 检测到媒体组（{len(messages_to_forward)} 个文件），正在合并转发...")
                        await self.forward_media_group(message.chat.id, messages_to_forward, text)
                        # 转发成功后删除处理消息和用户消息
                        try:
                            await processing_msg.delete()
                            await message.delete()
                        except:
                            pass
                    else:
                        logger.info("转发单条消息")
                        await processing_msg.edit("🔄 正在转发消息...")
                        await self.forward_original_message(message.chat.id, messages_to_forward[0], text)
                        # 转发成功后删除处理消息和用户消息
                        try:
                            await processing_msg.delete()
                            await message.delete()
                        except:
                            pass
                    
                    logger.info(f"成功为用户 {message.from_user.id} 转发消息")
                else:
                    await processing_msg.edit(
                        "❌ **转发失败**\n\n"
                        "可能的原因:\n"
                        "• 消息链接格式不正确\n"
                        "• 消息不存在或已被删除\n"
                        "• 没有权限访问该消息\n"
                        "• 频道或群组是私有的\n\n"
                        "请检查链接是否正确，并确保您有权限访问该消息。"
                    )
                    logger.warning(f"用户 {message.from_user.id} 的消息转发失败: {text}")
                
            except Exception as e:
                error_msg = (
                    "❌ **处理出错**\n\n"
                    f"错误信息: `{str(e)}`\n\n"
                    "请稍后重试，或联系管理员。"
                )
                await processing_msg.edit(error_msg)
                logger.error(f"处理消息时出错: {e}", exc_info=True)
    
    async def forward_original_message(self, chat_id: int, original_message, original_link: str = None):
        """原样转发消息"""
        try:
            logger.info(f"开始转发消息到聊天 {chat_id}")
            logger.info(f"消息类型: text={bool(original_message.text)}, photo={bool(original_message.photo)}, video={bool(original_message.video)}")
            logger.info(f"原始消息来源: chat_id={original_message.chat.id}, message_id={original_message.id}")
            
            # 创建原始链接文本
            link_text = ""
            if original_link:
                # 确保链接格式正确
                if not original_link.startswith('http'):
                    original_link = f"https://{original_link}"
                link_text = f"\n\n[原始消息]({original_link})"
                logger.info(f"添加原始链接: {original_link}")
            
            # 方法1: 尝试直接使用 Bot 的 copy_message，然后发送链接
            try:
                # 注意：这里改为使用 self.bot 而不是 self.extractor.client
                copied_msg = await self.bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=original_message.chat.id,
                    message_id=original_message.id
                )
                
                # 如果有原始链接，发送链接消息
                if link_text:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=link_text,
                        disable_web_page_preview=True
                    )
                
                logger.info("使用 Bot copy_message 转发成功")
                return
            except Exception as copy_error:
                logger.warning(f"Bot copy_message 失败: {copy_error}")
                # 继续尝试其他方法
            
            # 方法2: 根据消息类型手动发送（改进版）
            if original_message.text:
                # 纯文本消息
                text_content = original_message.text + link_text
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=text_content,
                    disable_web_page_preview=True
                )
                logger.info("文本消息转发成功")
            
            elif original_message.photo:
                # 图片消息 - 使用下载重传的方式
                try:
                    # 先尝试直接使用 file_id
                    caption = (original_message.caption or "") + link_text
                    await self.bot.send_photo(
                        chat_id=chat_id,
                        photo=original_message.photo.file_id,
                        caption=caption
                    )
                    logger.info("图片消息直接转发成功")
                except Exception as photo_error:
                    logger.warning(f"图片直接转发失败: {photo_error}")
                    # 尝试下载后重传
                    await self.download_and_resend_media(chat_id, original_message, "photo", link_text)
            
            elif original_message.video:
                # 视频消息
                try:
                    caption = (original_message.caption or "") + link_text
                    await self.bot.send_video(
                        chat_id=chat_id,
                        video=original_message.video.file_id,
                        caption=caption
                    )
                    logger.info("视频消息直接转发成功")
                except Exception as video_error:
                    logger.warning(f"视频直接转发失败: {video_error}")
                    await self.download_and_resend_media(chat_id, original_message, "video", link_text)
            
            elif original_message.document:
                # 文档消息
                try:
                    caption = (original_message.caption or "") + link_text
                    await self.bot.send_document(
                        chat_id=chat_id,
                        document=original_message.document.file_id,
                        caption=caption
                    )
                    logger.info("文档消息直接转发成功")
                except Exception as doc_error:
                    logger.warning(f"文档直接转发失败: {doc_error}")
                    await self.download_and_resend_media(chat_id, original_message, "document", link_text)
            
            elif original_message.audio:
                # 音频消息
                try:
                    caption = (original_message.caption or "") + link_text
                    await self.bot.send_audio(
                        chat_id=chat_id,
                        audio=original_message.audio.file_id,
                        caption=caption
                    )
                    logger.info("音频消息直接转发成功")
                except Exception as audio_error:
                    logger.warning(f"音频直接转发失败: {audio_error}")
                    await self.download_and_resend_media(chat_id, original_message, "audio", link_text)
            
            elif original_message.voice:
                # 语音消息
                try:
                    caption = (original_message.caption or "") + link_text
                    await self.bot.send_voice(
                        chat_id=chat_id,
                        voice=original_message.voice.file_id,
                        caption=caption
                    )
                    logger.info("语音消息直接转发成功")
                except Exception as voice_error:
                    logger.warning(f"语音直接转发失败: {voice_error}")
                    await self.download_and_resend_media(chat_id, original_message, "voice", link_text)
            
            elif original_message.sticker:
                # 贴纸消息
                try:
                    await self.bot.send_sticker(
                        chat_id=chat_id,
                        sticker=original_message.sticker.file_id
                    )
                    # 贴纸后发送链接
                    if link_text:
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=link_text,
                            disable_web_page_preview=True
                        )
                    logger.info("贴纸消息转发成功")
                except Exception as sticker_error:
                    logger.warning(f"贴纸转发失败: {sticker_error}")
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=f"🎭 贴纸消息转发失败，可能是权限问题{link_text}",
                        disable_web_page_preview=True
                    )
            
            elif original_message.animation:
                # GIF动画
                try:
                    caption = (original_message.caption or "") + link_text
                    await self.bot.send_animation(
                        chat_id=chat_id,
                        animation=original_message.animation.file_id,
                        caption=caption
                    )
                    logger.info("GIF动画转发成功")
                except Exception as gif_error:
                    logger.warning(f"GIF转发失败: {gif_error}")
                    await self.download_and_resend_media(chat_id, original_message, "animation", link_text)
            
            elif original_message.video_note:
                # 视频笔记（圆形视频）
                try:
                    await self.bot.send_video_note(
                        chat_id=chat_id,
                        video_note=original_message.video_note.file_id
                    )
                    # 视频笔记后发送链接
                    if link_text:
                        await self.bot.send_message(
                            chat_id=chat_id,
                            text=link_text,
                            disable_web_page_preview=True
                        )
                    logger.info("视频笔记转发成功")
                except Exception as vn_error:
                    logger.warning(f"视频笔记转发失败: {vn_error}")
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=f"📹 视频笔记转发失败，可能是权限问题{link_text}",
                        disable_web_page_preview=True
                    )
            
            else:
                # 其他类型或空消息
                logger.warning("未知消息类型或空消息")
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ 该消息类型暂不支持转发，或消息为空。"
                )
                
        except Exception as e:
            logger.error(f"转发消息时出错: {e}", exc_info=True)
            await self.bot.send_message(
                chat_id=chat_id,
                text=f"❌ 转发消息时出错: {str(e)}"
            )
    
    async def download_and_resend_media(self, chat_id: int, original_message, media_type: str, link_text: str = ""):
        """下载媒体文件并重新发送"""
        try:
            logger.info(f"尝试下载并重传 {media_type} 媒体...")
            
            # 下载文件到临时位置
            file_path = await self.extractor.client.download_media(original_message)
            
            if file_path:
                logger.info(f"文件下载成功: {file_path}")
                
                # 根据类型重新发送
                if media_type == "photo":
                    caption = (original_message.caption or "") + link_text
                    await self.bot.send_photo(
                        chat_id=chat_id,
                        photo=file_path,
                        caption=caption
                    )
                elif media_type == "video":
                    caption = (original_message.caption or "") + link_text
                    await self.bot.send_video(
                        chat_id=chat_id,
                        video=file_path,
                        caption=caption
                    )
                elif media_type == "document":
                    caption = (original_message.caption or "") + link_text
                    await self.bot.send_document(
                        chat_id=chat_id,
                        document=file_path,
                        caption=caption
                    )
                elif media_type == "audio":
                    caption = (original_message.caption or "") + link_text
                    await self.bot.send_audio(
                        chat_id=chat_id,
                        audio=file_path,
                        caption=caption
                    )
                elif media_type == "voice":
                    caption = (original_message.caption or "") + link_text
                    await self.bot.send_voice(
                        chat_id=chat_id,
                        voice=file_path,
                        caption=caption
                    )
                elif media_type == "animation":
                    caption = (original_message.caption or "") + link_text
                    await self.bot.send_animation(
                        chat_id=chat_id,
                        animation=file_path,
                        caption=caption
                    )
                
                logger.info(f"{media_type} 重传成功")
                
                # 删除临时文件
                import os
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"临时文件已删除: {file_path}")
            else:
                raise Exception("文件下载失败")
                
        except Exception as e:
            logger.error(f"下载重传失败: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text=f"❌ 媒体文件转发失败: {str(e)}"
            )
    
    async def download_and_send_media_group(self, chat_id: int, messages: list, link_text: str = ""):
        """下载媒体文件并重新组合为媒体组发送"""
        try:
            logger.info(f"开始下载 {len(messages)} 个媒体文件...")
            media_list = []
            downloaded_files = []
            
            # 获取第一条消息的说明文字
            first_caption = ""
            for msg in messages:
                if msg.caption:
                    first_caption = msg.caption
                    break
            
            for i, msg in enumerate(messages):
                try:
                    # 下载媒体文件
                    file_path = await self.extractor.client.download_media(msg)
                    
                    if file_path:
                        logger.info(f"文件 {i+1} 下载成功: {file_path}")
                        downloaded_files.append(file_path)
                        
                        # 只在第一个媒体上添加说明文字和链接
                        caption = (first_caption + link_text) if i == 0 else ""
                        
                        # 根据消息类型创建媒体项
                        if msg.photo:
                            media_item = InputMediaPhoto(
                                media=file_path,
                                caption=caption
                            )
                        elif msg.video:
                            media_item = InputMediaVideo(
                                media=file_path,
                                caption=caption
                            )
                        elif msg.document:
                            # 根据MIME类型判断
                            if msg.document.mime_type and msg.document.mime_type.startswith('image/'):
                                media_item = InputMediaPhoto(
                                    media=file_path,
                                    caption=caption
                                )
                            elif msg.document.mime_type and msg.document.mime_type.startswith('video/'):
                                media_item = InputMediaVideo(
                                    media=file_path,
                                    caption=caption
                                )
                            else:
                                media_item = InputMediaDocument(
                                    media=file_path,
                                    caption=caption
                                )
                        elif msg.audio:
                            media_item = InputMediaAudio(
                                media=file_path,
                                caption=caption
                            )
                        else:
                            logger.warning(f"未知媒体类型，跳过文件 {i+1}")
                            continue
                        
                        media_list.append(media_item)
                        logger.info(f"媒体项 {i+1} 准备完成: {type(media_item).__name__}")
                        
                    else:
                        logger.error(f"文件 {i+1} 下载失败")
                        
                except Exception as download_error:
                    logger.error(f"下载文件 {i+1} 时出错: {download_error}")
            
            # 发送媒体组
            if len(media_list) > 1:
                logger.info(f"发送媒体组，包含 {len(media_list)} 个媒体文件")
                await self.bot.send_media_group(
                    chat_id=chat_id,
                    media=media_list
                )
                logger.info("媒体组发送成功")
            elif len(media_list) == 1:
                logger.info("只有一个媒体文件，单独发送")
                # 单独发送一个媒体文件
                media_item = media_list[0]
                if isinstance(media_item, InputMediaPhoto):
                    await self.bot.send_photo(
                        chat_id=chat_id,
                        photo=media_item.media,
                        caption=media_item.caption
                    )
                elif isinstance(media_item, InputMediaVideo):
                    await self.bot.send_video(
                        chat_id=chat_id,
                        video=media_item.media,
                        caption=media_item.caption
                    )
                elif isinstance(media_item, InputMediaDocument):
                    await self.bot.send_document(
                        chat_id=chat_id,
                        document=media_item.media,
                        caption=media_item.caption
                    )
                elif isinstance(media_item, InputMediaAudio):
                    await self.bot.send_audio(
                        chat_id=chat_id,
                        audio=media_item.media,
                        caption=media_item.caption
                    )
            else:
                raise Exception("没有成功下载任何媒体文件")
            
            # 清理临时文件
            import os
            for file_path in downloaded_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"临时文件已删除: {file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败: {cleanup_error}")
            
        except Exception as e:
            logger.error(f"下载并发送媒体组失败: {e}")
            raise e
    
    async def forward_media_group(self, chat_id: int, messages: list, original_link: str = None):
        """转发媒体组（相册）"""
        try:
            logger.info(f"开始转发媒体组，包含 {len(messages)} 条消息")
            
            # 创建原始链接文本
            link_text = ""
            if original_link:
                # 确保链接格式正确
                if not original_link.startswith('http'):
                    original_link = f"https://{original_link}"
                link_text = f"\n\n[原始消息]({original_link})"
            
            # 方法1: 尝试使用 Bot 的 copy_messages 批量复制，然后发送链接
            try:
                message_ids = [msg.id for msg in messages]
                from_chat_id = messages[0].chat.id
                
                # 注意：这里改为使用 self.bot 而不是 self.extractor.client
                await self.bot.copy_messages(
                    chat_id=chat_id,
                    from_chat_id=from_chat_id,
                    message_ids=message_ids
                )
                
                # 如果有原始链接，发送链接消息
                if link_text:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=link_text,
                        disable_web_page_preview=True
                    )
                
                logger.info("使用 Bot copy_messages 批量转发成功")
                return
            except Exception as copy_error:
                logger.warning(f"Bot copy_messages 批量转发失败: {copy_error}")
                # 继续尝试其他方法
            
            # 方法2: 尝试发送媒体组（使用file_id）
            try:
                media_list = []
                
                # 获取第一条消息的说明文字
                first_caption = ""
                for msg in messages:
                    if msg.caption:
                        first_caption = msg.caption
                        break
                
                for i, msg in enumerate(messages):
                    media_item = None
                    # 只在第一个媒体上添加说明文字和链接
                    caption = (first_caption + link_text) if i == 0 else ""
                    
                    if msg.photo:
                        media_item = InputMediaPhoto(
                            media=msg.photo.file_id,
                            caption=caption
                        )
                    elif msg.video:
                        media_item = InputMediaVideo(
                            media=msg.video.file_id,
                            caption=caption
                        )
                    elif msg.document and msg.document.mime_type and msg.document.mime_type.startswith('image/'):
                        # 将图片类型的文档作为图片处理
                        media_item = InputMediaPhoto(
                            media=msg.document.file_id,
                            caption=caption
                        )
                    elif msg.document and msg.document.mime_type and msg.document.mime_type.startswith('video/'):
                        # 将视频类型的文档作为视频处理
                        media_item = InputMediaVideo(
                            media=msg.document.file_id,
                            caption=caption
                        )
                    elif msg.audio:
                        media_item = InputMediaAudio(
                            media=msg.audio.file_id,
                            caption=caption
                        )
                    
                    if media_item:
                        media_list.append(media_item)
                        logger.info(f"添加媒体项 {i+1}: {type(media_item).__name__}")
                
                if media_list and len(media_list) > 1:
                    logger.info(f"准备发送媒体组，包含 {len(media_list)} 个媒体项")
                    await self.bot.send_media_group(
                        chat_id=chat_id,
                        media=media_list
                    )
                    logger.info("使用 send_media_group 转发成功")
                    return
                elif len(media_list) == 1:
                    # 只有一个媒体项，直接发送
                    logger.info("只有一个媒体项，使用单独发送")
                    await self.forward_original_message(chat_id, messages[0])
                    return
                else:
                    raise Exception("无法创建媒体列表")
                    
            except Exception as media_group_error:
                logger.warning(f"send_media_group 转发失败: {media_group_error}")
                # 尝试下载重传的媒体组方法
            
            # 方法3: 下载后重新组合媒体组发送
            try:
                logger.info("尝试下载媒体文件并重新组合发送...")
                await self.download_and_send_media_group(chat_id, messages, link_text)
                return
            except Exception as download_error:
                logger.warning(f"下载重传媒体组失败: {download_error}")
            
            # 方法4: 逐个转发每条消息（最后的备选方案）
            logger.info("尝试逐个转发媒体组中的每条消息...")
            success_count = 0
            
            for i, msg in enumerate(messages):
                try:
                    # 只在第一条消息上添加原始链接
                    msg_link = original_link if i == 0 else None
                    await self.forward_original_message(chat_id, msg, msg_link)
                    success_count += 1
                    logger.info(f"媒体组消息 {i+1}/{len(messages)} 转发成功")
                    
                    # 添加小延迟避免频率限制
                    if i < len(messages) - 1:
                        await asyncio.sleep(0.5)
                        
                except Exception as single_error:
                    logger.error(f"媒体组消息 {i+1} 转发失败: {single_error}")
            
            if success_count > 0:
                logger.info(f"媒体组转发完成，成功 {success_count}/{len(messages)} 条消息")
            else:
                raise Exception("所有媒体组消息转发都失败了")
                
        except Exception as e:
            logger.error(f"媒体组转发失败: {e}")
            await self.bot.send_message(
                chat_id=chat_id,
                text=f"❌ 媒体组转发失败: {str(e)}"
            )
    
    async def start(self):
        """启动Bot"""
        try:
            # 初始化消息提取器
            await self.extractor.initialize()
            
            # 启动Bot
            await self.bot.start()
            logger.info("消息提取Bot已启动")
            
            # 获取Bot信息
            me = await self.bot.get_me()
            logger.info(f"Bot信息: @{me.username} ({me.first_name})")
            
            # 保持运行
            await asyncio.Event().wait()
            
        except KeyboardInterrupt:
            logger.info("收到停止信号")
        except Exception as e:
            logger.error(f"Bot启动失败: {e}", exc_info=True)
        finally:
            await self.stop()
    
    async def stop(self):
        """停止Bot"""
        try:
            if self.extractor:
                await self.extractor.close()
            if self.bot:
                await self.bot.stop()
            logger.info("消息提取Bot已停止")
        except Exception as e:
            logger.error(f"停止Bot时出错: {e}")


if __name__ == "__main__":
    bot = MessageExtractorBot()
    asyncio.run(bot.start())
