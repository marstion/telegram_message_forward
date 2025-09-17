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
            logger.info(f"尝试获取消息: chat_id={parsed['chat_id']}, message_id={parsed['message_id']}, type={parsed['type']}")
            
            # 获取原始消息
            original_message = await self.client.get_messages(
                chat_id=parsed['chat_id'],
                message_ids=parsed['message_id']
            )
            
            logger.info(f"get_messages 返回结果类型: {type(original_message)}")
            
            if not original_message:
                logger.error(f"未找到消息: chat_id={parsed['chat_id']}, message_id={parsed['message_id']}")
                return None
            
            logger.info(f"成功获取消息: {original_message.id} from {original_message.chat.title or original_message.chat.id}")
            
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
                
                # 过滤掉None消息
                valid_messages = [msg for msg in media_group_messages if msg is not None]
                return valid_messages if valid_messages else [original_message]
            else:
                # 不是媒体组，返回单个消息
                return [original_message]
            
        except Exception as e:
            logger.error(f"获取媒体组消息时出错: {e}")
            return None
