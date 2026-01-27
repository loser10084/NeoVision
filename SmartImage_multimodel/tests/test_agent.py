# test_multi_agent_functional.py
import sys
import os
from pathlib import Path
# 添加项目根目录到Python路径

ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
sys.path.insert(0, ROOT)

from model_agents.llm import build_common_llm, build_image_llm
from model_agents.graph import create_multi_agent_graph
from utils import logger

def test_image_llm():
    """测试ImageLLM是否能正常构建"""
    logger.info("测试ImageLLM构建...")
    try:
        image_llm = build_image_llm()
        logger.success("✓ ImageLLM构建成功")
        return image_llm
    except Exception as e:
        logger.error(f"✗ ImageLLM构建失败: ", e)
        return None


def test_llm():
    """测试LLM是否能正常构建"""
    logger.info("测试LLM构建...")
    try:
        common_llm = build_common_llm()
        logger.success("✓ CommonLLM构建成功")
        return common_llm
    except Exception as e:
        logger.error(f"✗ CommonLLM构建失败: ", e)
        return None


def test_agents():
    """测试智能体初始化"""
    logger.info("测试智能体初始化...")
    try:
        common_llm = build_common_llm()
        image_llm = build_image_llm()
        
        # 导入并创建智能体函数
        from model_agents.agents.general_agent import create_general_agent
        from model_agents.agents.image_agent import create_image_agent
        
        general_agent = create_general_agent(common_llm)
        logger.success("✓ GeneralAgent函数创建成功")
        
        image_agent = create_image_agent(image_llm)
        logger.success("✓ ImageAgent函数创建成功")
        
        return True
    except Exception as e:
        logger.error(f"✗ 智能体初始化失败: ", e)

        return False


def test_graph():
    """测试图构建"""
    logger.info("测试图构建...")
    try:
        graph = create_multi_agent_graph()
        logger.success("✓ 图构建成功")
        logger.info(f"✓ 节点数量: {len(list(graph.get_graph().nodes))}")
        logger.info(f"✓ 边数量: {len(list(graph.get_graph().edges))}")
        return True
    except Exception as e:
        logger.error(f"✗ 图构建失败: ", e)

        return False


def test_simple_run():
    """测试简单运行"""
    logger.info("测试简单运行...")
    try:
        graph = create_multi_agent_graph()
        
        # 准备初始状态
        from langchain_core.messages import HumanMessage
        test_states = []
        test_states.append({
            "messages": [HumanMessage(content="你好，请调用搜索工具，搜索一次，介绍最新的中南大学")],
            "query": "",
            "image_url": None,
            "context": {},
            "next_agent": "router",
            "result": ""
        })
        test_states.append({
            "messages": [HumanMessage(content="你好，请调用RAG工具，介绍什么是同行评审")],
            "query": "",
            "image_url": None,
            "context": {},
            "next_agent": "router",
            "result": ""
        })
        
        logger.info("正在执行图...")
        for state in test_states:
            logger.info("="*50)
            result = graph.invoke(state)
            if isinstance(result, dict) and "output" in result:
                output = result["output"]
                # 如果 output 为空，再尝试从消息列表最后一条获取（作为兜底）
                if not output and "messages" in result:
                    output = result["messages"][-1].content
            else:
                output = str(result)
            logger.warning(f"✓ ai输出: {output}")
            logger.debug(f"✓ 完整结果: {result}")
        
        logger.success("✓ 图执行成功")
        return True
    except Exception as e:
        logger.error(f"✗ 图执行失败: ", e)

        return False


def main():
    """主测试函数"""
    logger.info("开始测试多智能体架构（函数式）...")
    
    tests = [
        ("CommonLLM构建", test_llm),
        ("ImageLLM构建", test_image_llm),
        ("智能体初始化", test_agents),
        ("图构建", test_graph),
        ("简单运行", test_simple_run)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"--- {test_name} ---")
        if test_func():
            passed += 1
            logger.success(f"✓ {test_name} 通过")
        else:
            logger.error(f"✗ {test_name} 失败")
    
    logger.success(f"=== 测试结果 ===")
    logger.success(f"通过: {passed}/{total}")
    
    if passed == total:
        logger.success("🎉 所有测试通过！函数式架构可以正常运行")
    else:
        logger.error("⚠️  部分测试失败，请检查相关组件")
    
    return passed == total


if __name__ == "__main__":
    main()