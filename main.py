#!/usr/bin/env python3
"""
Telegram 消息转发工具
使用 Pyrogram 实现的消息转发和Bot回复功能
"""

import asyncio
import logging
import sys
import os
from bot_handler import MessageExtractorBot

# 设置日志格式
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


def check_environment():
    """检查环境配置"""
    required_vars = ['API_ID', 'API_HASH', 'BOT_TOKEN']
    missing_vars = []
    
    # 检查 .env 文件是否存在
    if not os.path.exists('.env'):
        logger.error(".env 文件不存在")
        logger.info("请复制 env_example.txt 为 .env 并填入您的配置")
        return False
    
    # 检查环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.info("请在 .env 文件中设置这些变量")
        return False
    
    return True


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("Telegram 消息转发工具启动")
    logger.info("=" * 50)
    
    # 检查环境配置
    if not check_environment():
        logger.error("环境配置检查失败，程序退出")
        sys.exit(1)
    
    # 创建并启动Bot
    bot = MessageExtractorBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)
    finally:
        logger.info("程序结束")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被强制中断")
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)
