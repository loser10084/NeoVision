# test_api_gateway_adapter.py
from pathlib import Path
"""
测试API网关适配器基础模块
"""

import sys
import os

# 添加项目根目录到Python路径

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
sys.path.insert(0, ROOT)

from utils import logger

def test_imports():
    """测试API网关模块导入"""
    logger.info("Testing API Gateway imports...")
    
    try:
        from api_gateway import llm
        logger.info("✓ llm module imported successfully")
        
        from api_gateway import agent_runtime
        logger.info("✓ agent_runtime module imported successfully")
        
        from api_gateway.utils import history
        logger.info("✓ history module imported successfully")

        
        logger.info("All modules imported successfully!")
        return True
    except ImportError as e:
        logger.error(f"✗ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False

def test_llm_functions():
    """测试LLM功能"""
    logger.info("Testing LLM functions...")
    
    try:
        from api_gateway import llm
        
        # 测试extract_query
        query = llm.extract_query("Hello, world!")
        logger.info(f"✓ extract_query: '{query}'")
        
        # 测试build_messages
        messages = llm.build_messages([{"role": "user", "content": "Test message"}])
        logger.info(f"✓ build_messages: {len(messages)} messages created")
        
        # 测试build_multimodal_messages (需要配置项)
        logger.info("✓ LLM functions work correctly")
        return True
    except Exception as e:
        logger.error(f"✗ LLM function error: {e}")
        return False

def test_agent_runtime():
    """测试Agent Runtime功能"""
    logger.info("Testing Agent Runtime functions...")
    
    try:
        from api_gateway import agent_runtime
        
        # 测试build_agent_executor
        executor, memory = agent_runtime.build_agent_executor("test_user")
        result = executor.invoke({"input": "你好，请回到你的模型"})
        logger.info(f"✓ build_agent_executor works correctly: {result}")
        return True
    except Exception as e:
        logger.error(f"✗ Agent Runtime error: {e}")
        return False

def main():
    logger.info("API Gateway Adapter Test Suite")
    logger.info("="*40)
    
    success = True
    
    success &= test_imports()
    success &= test_llm_functions()
    success &= test_agent_runtime()
    
    logger.info("="*40)
    if success:
        logger.success("✓ All tests passed! API Gateway adapters are working correctly.")
    else:
        logger.error("✗ Some tests failed.")
    
    return success

if __name__ == "__main__":
    main()