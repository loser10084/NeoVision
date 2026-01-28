"""
tests.test_rag 测试RAG模块
"""

import sys
from pathlib import Path

# 获取根目录
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
from utils import logger
from data_storage import retrieve_documents, get_vectorstore
import config


def test_retrieve_documents():
    """
    测试RAG对外提供的retrieve_documents函数
    """
    # 定义测试场景和预期的关键词
    # 这些 Query 专门针对你数据集中的 GTV, CTV, PTV, OAR 等内容
    test_cases = [
        {
            "query": "GTV、CTV、PTV有什么区别？",
            "tag": "基础概念",
            "expected_id": "FAQ_HN_00001"
        },
        {
            "query": "自动勾画遗漏了结节该怎么办？",
            "tag": "失败案例",
            "expected_id": "FC_HN_SYN_0002"
        },
        {
            "query": "CTV 勾画如何考虑解剖屏障？",
            "tag": "SOP/检查单",
            "expected_id": "HN03"
        },
        {
            "query": "同行评审的结果如何记录？",
            "tag": "流程合规",
            "expected_id": "FAQ_HN_00003"
        }
    ]

    all_case_passed = True
    
    for i, case in enumerate(test_cases, 1):
        query = case["query"]
        logger.info(f"测试用例 {i} [{case['tag']}]: '{query}'")
        
        try:
            # 调用你定义的 retrieve_documents 函数
            docs = retrieve_documents(query)
            
            if not docs:
                # 记录警告：可能是阈值 RAG_SCORE_THRESHOLD 设置过高（如之前的 0.3）
                logger.warning(f"  ✗ 未检索到文档。当前阈值可能过高或内容未命中。")
                all_case_passed = False
                all_tests_passed = False
                logger.warning(f"❌ 用例 {i} 失败: 未达到阈值 {config.RAG_SCORE_THRESHOLD}")
                
                # --- 诊断逻辑：获取最近几条的分数 ---
                logger.info(f"🔍 正在诊断 '{query}' 的原始相似度分数...")
                try:
                    # 强制获取前 3 条结果，不受 threshold 限制
                    vs = get_vectorstore()
                    raw_results = vs.similarity_search_with_relevance_scores(query, k=3)
                    
                    if not raw_results:
                        logger.error("   [诊断] 向量库中完全没有匹配内容（集合可能为空）。")
                    else:
                        logger.debug("   [诊断] 最近的文档分数如下（请根据此调整 RAG_SCORE_THRESHOLD）:")
                        for j, (doc, score) in enumerate(raw_results, 1):
                            doc_id = doc.metadata.get('qa_id') or doc.metadata.get('case_id') or doc.metadata.get('id') or "unknown"
                            content_preview = doc.page_content.replace('\n', ' ')[:50]
                            logger.debug(f"      {j}. Score: {score:.4f} | ID: {doc_id} | 内容: {content_preview}...")
                except Exception as diag_e:
                    logger.error(f"   [诊断] 诊断过程出错: {diag_e}", diag_e)
            else:
                logger.info(f"  ✓ 检索成功，命中 {len(docs)} 条文档")
                # 打印前 2 条命中结果的 metadata 方便核对
                for d in docs[:2]:
                    doc_id = d.metadata.get('qa_id') or d.metadata.get('case_id') or d.metadata.get('id')
                    logger.info(f"    - 命中 ID: {doc_id} | 内容摘要: {d.page_content[:40]}...")
                
                # 可选：验证最相关的文档是否包含预期 ID
                found_expected = any(case["expected_id"] in str(d.metadata) for d in docs)
                if not found_expected:
                    logger.warning(f"  ! 警告：检索结果中未发现预期 ID {case['expected_id']}")
                    
        except Exception as e:
            logger.error(f"  💥 检索过程中发生异常: {e}", e)
            all_case_passed = False
            
    return all_case_passed


def main():
    """主测试函数"""
    logger.info("开始测试多智能体架构（函数式）...")
    
    tests = [
        ("RAG的retrieve_documents函数测试", test_retrieve_documents),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"--- {test_name} ---")
        if test_func():
            passed += 1
            logger.info(f"✓ {test_name} 通过")
        else:
            logger.error(f"✗ {test_name} 失败")
    
    logger.info(f"=== 测试结果 ===")
    logger.info(f"通过: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 所有测试通过！函数式架构可以正常运行")
    else:
        logger.error("⚠️  部分测试失败，请检查相关组件")
    
    return passed == total


if __name__ == "__main__":
    main()