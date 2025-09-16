import re
import asyncio
from pyrogram import Client
from pyrogram.types import Message
from typing import Optional, Dict, Any
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageExtractor:
    """消息提取器类"""
    
    def __init__(self, api_id: int, api_hash: str, session_name: str = "extractor"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = None
    
    async def initialize(self):
        """初始化客户端"""
        self.client = Client(
            name=self.session_name,
            api_id=self.api_id,
            api_hash=self.api_hash
        )
        await self.client.start()
        logger.info("消息提取客户端已启动")
    
    async def close(self):
        """关闭客户端"""
        if self.client:
            await self.client.stop()
            logger.info("消息提取客户端已关闭")
    
    def parse_message_link(self, link: str) -> Optional[Dict[str, Any]]:
        """解析消息链接
        
        支持的格式:
        - https://t.me/channel_username/message_id
        - https://t.me/c/channel_id/message_id
        - t.me/channel_username/message_id
        """
        # 清理链接
        link = link.strip()
        
        # 正则表达式匹配不同格式的链接
        patterns = [
            # https://t.me/username/123
            r'(?:https?://)?t\.me/([a-zA-Z0-9_]+)/(\d+)',
            # https://t.me/c/123456789/123
            r'(?:https?://)?t\.me/c/(-?\d+)/(\d+)',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, link)
            if match:
                chat_identifier, message_id = match.groups()
                
                # 如果是数字ID，转换为整数
                try:
                    chat_id = int(chat_identifier)
                    # 如果是 /c/ 格式，需要添加 -100 前缀
                    if '/c/' in link and not str(chat_id).startswith('-100'):
                        chat_id = int(f"-100{abs(chat_id)}")
                    return {
                        'chat_id': chat_id,
                        'message_id': int(message_id),
                        'type': 'channel_id'
                    }
                except ValueError:
                    # 如果不是数字，则是用户名
                    return {
                        'chat_id': chat_identifier,
                        'message_id': int(message_id),
                        'type': 'username'
                    }
        
        return None
    
    async def get_original_message(self, link: str):
        """获取原始消息对象（用于转发）"""
        if not self.client:
            raise RuntimeError("客户端未初始化，请先调用 initialize()")
        
        # 解析链接
        parsed = self.parse_message_link(link)
        if not parsed:
            logger.error(f"无法解析消息链接: {link}")
            return None
        
        try:
            # 获取消息
            message = await self.client.get_messages(
                chat_id=parsed['chat_id'],
                message_ids=parsed['message_id']
            )
            
            if not message:
                logger.error("未找到消息")
                return None
            
            return message
            
        except Exception as e:
            logger.error(f"获取消息时出错: {e}")
            return None
    
    async def get_media_group_messages(self, link: str):
        """获取媒体组中的所有消息"""
        if not self.client:
            raise RuntimeError("客户端未初始化，请先调用 initialize()")
        
        # 解析链接
        parsed = self.parse_message_link(link)
        if not parsed:
            logger.error(f"无法解析消息链接: {link}")
            return None
        
        try:
            # 获取原始消息
            original_message = await self.client.get_messages(
                chat_id=parsed['chat_id'],
                message_ids=parsed['message_id']
            )
            
            if not original_message:
                logger.error("未找到消息")
                return None
            
            # 检查是否是媒体组消息
            if hasattr(original_message, 'media_group_id') and original_message.media_group_id:
                logger.info(f"检测到媒体组: {original_message.media_group_id}")
                
                # 获取媒体组中的所有消息
                # 尝试获取前后几条消息来找到完整的媒体组
                media_group_messages = []
                
                # 获取一个范围的消息ID来寻找媒体组
                start_id = max(1, parsed['message_id'] - 10)
                end_id = parsed['message_id'] + 10
                
                messages = await self.client.get_messages(
                    chat_id=parsed['chat_id'],
                    message_ids=list(range(start_id, end_id + 1))
                )
                
                # 筛选出属于同一媒体组的消息
                target_group_id = original_message.media_group_id
                for msg in messages:
                    if (msg and hasattr(msg, 'media_group_id') and 
                        msg.media_group_id == target_group_id):
                        media_group_messages.append(msg)
                
                # 按消息ID排序
                media_group_messages.sort(key=lambda x: x.id)
                logger.info(f"找到媒体组消息数量: {len(media_group_messages)}")
                
                return media_group_messages if media_group_messages else [original_message]
            else:
                # 不是媒体组，返回单个消息
                return [original_message]
            
        except Exception as e:
            logger.error(f"获取媒体组消息时出错: {e}")
            return None

    async def extract_message(self, link: str) -> Optional[Dict[str, Any]]:
        """提取消息内容"""
        if not self.client:
            raise RuntimeError("客户端未初始化，请先调用 initialize()")
        
        # 解析链接
        parsed = self.parse_message_link(link)
        if not parsed:
            logger.error(f"无法解析消息链接: {link}")
            return None
        
        try:
            # 获取消息
            message = await self.client.get_messages(
                chat_id=parsed['chat_id'],
                message_ids=parsed['message_id']
            )
            
            if not message:
                logger.error("未找到消息")
                return None
            
            # 提取消息信息
            result = {
                'message_id': message.id,
                'date': message.date,
                'text': message.text or message.caption or "",
                'media_type': None,
                'file_info': None,
                'from_user': None,
                'chat_info': None,
                'forward_info': None
            }
            
            # 发送者信息
            if message.from_user:
                result['from_user'] = {
                    'id': message.from_user.id,
                    'first_name': message.from_user.first_name,
                    'last_name': message.from_user.last_name,
                    'username': message.from_user.username
                }
            
            # 聊天信息
            if message.chat:
                result['chat_info'] = {
                    'id': message.chat.id,
                    'title': message.chat.title,
                    'username': message.chat.username,
                    'type': str(message.chat.type)
                }
            
            # 转发信息
            if message.forward_from or message.forward_from_chat:
                result['forward_info'] = {
                    'from_user': None,
                    'from_chat': None,
                    'date': message.forward_date
                }
                if message.forward_from:
                    result['forward_info']['from_user'] = {
                        'id': message.forward_from.id,
                        'first_name': message.forward_from.first_name,
                        'username': message.forward_from.username
                    }
                if message.forward_from_chat:
                    result['forward_info']['from_chat'] = {
                        'id': message.forward_from_chat.id,
                        'title': message.forward_from_chat.title,
                        'username': message.forward_from_chat.username
                    }
            
            # 媒体信息
            if message.photo:
                result['media_type'] = 'photo'
                result['file_info'] = {
                    'file_id': message.photo.file_id,
                    'file_size': message.photo.file_size,
                    'width': message.photo.width,
                    'height': message.photo.height
                }
            elif message.video:
                result['media_type'] = 'video'
                result['file_info'] = {
                    'file_id': message.video.file_id,
                    'file_size': message.video.file_size,
                    'duration': message.video.duration,
                    'width': message.video.width,
                    'height': message.video.height
                }
            elif message.document:
                result['media_type'] = 'document'
                result['file_info'] = {
                    'file_id': message.document.file_id,
                    'file_size': message.document.file_size,
                    'file_name': message.document.file_name,
                    'mime_type': message.document.mime_type
                }
            elif message.audio:
                result['media_type'] = 'audio'
                result['file_info'] = {
                    'file_id': message.audio.file_id,
                    'file_size': message.audio.file_size,
                    'duration': message.audio.duration,
                    'title': message.audio.title,
                    'performer': message.audio.performer
                }
            elif message.voice:
                result['media_type'] = 'voice'
                result['file_info'] = {
                    'file_id': message.voice.file_id,
                    'file_size': message.voice.file_size,
                    'duration': message.voice.duration
                }
            elif message.sticker:
                result['media_type'] = 'sticker'
                result['file_info'] = {
                    'file_id': message.sticker.file_id,
                    'file_size': message.sticker.file_size,
                    'width': message.sticker.width,
                    'height': message.sticker.height,
                    'emoji': message.sticker.emoji
                }
            
            logger.info(f"成功提取消息: {parsed['message_id']}")
            return result
            
        except Exception as e:
            logger.error(f"提取消息时出错: {e}")
            return None
    
    def format_message_info(self, message_data: Dict[str, Any]) -> str:
        """格式化消息信息为可读文本"""
        if not message_data:
            return "❌ 无法提取消息信息"
        
        lines = ["📨 **消息信息**", ""]
        
        # 基本信息
        lines.append(f"🆔 **消息ID**: `{message_data['message_id']}`")
        lines.append(f"📅 **时间**: {message_data['date']}")
        
        # 发送者信息
        if message_data['from_user']:
            user = message_data['from_user']
            name = user['first_name']
            if user['last_name']:
                name += f" {user['last_name']}"
            if user['username']:
                name += f" (@{user['username']})"
            lines.append(f"👤 **发送者**: {name}")
        
        # 聊天信息
        if message_data['chat_info']:
            chat = message_data['chat_info']
            chat_name = chat['title'] or chat['username'] or str(chat['id'])
            lines.append(f"💬 **聊天**: {chat_name} ({chat['type']})")
        
        # 转发信息
        if message_data['forward_info']:
            lines.append("🔄 **转发消息**")
            forward = message_data['forward_info']
            if forward['from_user']:
                user = forward['from_user']
                name = user['first_name']
                if user['username']:
                    name += f" (@{user['username']})"
                lines.append(f"   👤 原发送者: {name}")
            if forward['from_chat']:
                chat = forward['from_chat']
                chat_name = chat['title'] or chat['username']
                lines.append(f"   💬 原聊天: {chat_name}")
        
        # 媒体信息
        if message_data['media_type']:
            media_type = message_data['media_type']
            file_info = message_data['file_info']
            
            media_icons = {
                'photo': '🖼️',
                'video': '🎥',
                'document': '📄',
                'audio': '🎵',
                'voice': '🎙️',
                'sticker': '🎭'
            }
            
            icon = media_icons.get(media_type, '📎')
            lines.append(f"{icon} **媒体类型**: {media_type}")
            
            if file_info:
                if 'file_size' in file_info and file_info['file_size']:
                    size_mb = file_info['file_size'] / (1024 * 1024)
                    lines.append(f"📏 **文件大小**: {size_mb:.2f} MB")
                
                if media_type in ['photo', 'video'] and 'width' in file_info:
                    lines.append(f"📐 **尺寸**: {file_info['width']}x{file_info['height']}")
                
                if media_type in ['video', 'audio', 'voice'] and 'duration' in file_info:
                    lines.append(f"⏱️ **时长**: {file_info['duration']} 秒")
                
                if media_type == 'document' and 'file_name' in file_info:
                    lines.append(f"📝 **文件名**: `{file_info['file_name']}`")
        
        # 文本内容
        if message_data['text']:
            lines.append("")
            lines.append("📝 **消息内容**:")
            lines.append("```")
            lines.append(message_data['text'][:1000])  # 限制长度
            if len(message_data['text']) > 1000:
                lines.append("... (内容过长，已截断)")
            lines.append("```")
        
        return "\n".join(lines)
