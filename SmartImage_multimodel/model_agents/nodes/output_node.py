from utils import logger



def output_node(state):
    last_message = state['messages'][-1]
    
    # Extract and log token usage information
    token_usage_info = {}
    
    # Check for token usage in response metadata
    if hasattr(last_message, 'response_metadata') and 'token_usage' in last_message.response_metadata:
        token_usage = last_message.response_metadata.get('token_usage', {})
        token_usage_info.update({
            'prompt_tokens': token_usage.get('prompt_tokens'),
            'completion_tokens': token_usage.get('completion_tokens'),
            'total_tokens': token_usage.get('total_tokens'),
            'cached_tokens': token_usage.get('prompt_tokens_details', {}).get('cached_tokens')
        })
    
    # Also check for usage metadata
    if hasattr(last_message, 'usage_metadata'):
        usage_metadata = last_message.usage_metadata
        token_usage_info.update({
            'input_tokens': usage_metadata.get('input_tokens'),
            'output_tokens': usage_metadata.get('output_tokens'),
            'total_tokens_from_usage': usage_metadata.get('total_tokens')
        })
    
    # Log the token usage information
    logger.info(f"输出节点执行ing")
    if token_usage_info:
        logger.warning(f"Token 使用详情: {token_usage_info}")
    else:
        logger.warning("未找到 Token 使用信息")

    logger.debug(f"输出节点执行完成，输出内容: {last_message.content}") 
    return {"output": last_message.content}