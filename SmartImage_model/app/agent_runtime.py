from langchain.agents import AgentExecutor, create_openai_functions_agent, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from . import config
from . import llm
from . import history
from . import tools


def build_agent_executor(user_id: str, provided_messages=None, streaming: bool = False):
    chat_llm = llm.build_llm(streaming=streaming, model_name=config.MODEL_NAME)
    memory = history.build_memory(user_id, chat_llm, provided_messages=provided_messages)
    tool_list = tools.build_tools()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", config.SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    model_name = llm._normalize_model_name(config.MODEL_NAME).lower()
    if model_name.startswith("gpt-5"):
        agent = create_openai_tools_agent(chat_llm, tool_list, prompt)
    else:
        agent = create_openai_functions_agent(chat_llm, tool_list, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tool_list,
        memory=memory,
        verbose=False,
        handle_parsing_errors=True,
    )
    return executor, memory
