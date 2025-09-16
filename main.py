#!/usr/bin/env python3
"""
Telegram 消息转发工具
使用 Pyrogram 实现的消息转发和Bot回复功能
"""

import asyncio
import logging
import sys
import os

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("Telegram 消息转发工具启动")
    logger.info("=" * 50)
    
    try:
        # 导入配置和Bot类（环境变量检查在config.py中自动执行）
        from bot_handler import MessageExtractorBot
        
        # 创建并启动Bot
        bot = MessageExtractorBot()
    except ValueError as e:
        # 捕获配置错误
        logger.error("配置错误:")
        print(str(e))
        sys.exit(1)
    except ImportError as e:
        logger.error(f"导入错误: {e}")
        sys.exit(1)
    
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
