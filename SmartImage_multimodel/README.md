

# 使用指南：
在虚拟环境下安装依赖`pip install -r ./requirements.txt`
查看`.env.example`，修改对应必须配置，然后再把名字改为`.env`
在虚拟环境下执行当前目录下的`.main.py`即可

# CHANGELOG

我简单说一下我改了什么

## No Changed
- 通信架构flask没改
- 通信接口api没改

## refactors
- 原项目几乎所有的.py文件之间的依赖，都是相对导入，没有包（即__init__.py），我重构为包结构了。
- 原项目的模型端的可调用function杂糅在一个tools文件，我改成包了
- 原项目对外接口（网关路由）和模型调用杂糅在一个文件，我拆成两个模块了
- 基本要求：langchain升级为langgraph架构，
  现在这个架构可以比较轻松的拓展了，只需要修改graph.py即可修改工作流程，
  需要新agent只需要去agents\里自己加，写点提示词就差不多。
  需要新tools只需要去tools\里自己加，然后去想要使用这个tools的agent.py里添加即可。

## feats
- 新加了一个Logger，便于快速调试问题。
- 模型调用工具时，会同步向前端发送调用信息，便于前端展示调用过程，可去`.env`配置`SHOW_TOOL_CALLS`。（但存在不会换行的bug）
- 加了一个单元测试模块`tests\`，用于快速测试基础功能
- agent单次循环调用工具有硬上限、和连续次数上限，每个agent单独配置，避免无限循环调用。
- 很多地方加了很多不该有的注释

## other
- RAG里面的初始化和测试脚本，我改名了，改为是`script_init_chroma.py`和`script_test_chroma.py`了

## fixs
- 原项目的embedding模型没有配置，是硬编码的，我改成从配置文件读取了。
- 原项目的依赖`redis==5.0.4`过老，而`langgraph-checkpoint-redis`要求必须是`redis >= 5.2.1`。

## bugs
- 前端上传图片时，调用的是/api/agent/chat接口，这个接口为非流式传输，导致大模型输出是一次性传送给前端。
  而正常文字输入调用的是/api/agent/chat/stream接口，这个接口为流式传输，大模型的输出是逐token返回的。
- 没写异步逻辑，面对前端的并发请求时（如多个客户端同时发送请求）。
    - 一是我记得flask本身就不是专门为了异步而生的，
    - 二是原项目貌似除了流输出那里有多线程并行外，全程都是同步的，全改成异步相当于重构所有内容。
- 路由那块、流式传输那块，我越写越史，越看不下去，只能勉强运行。

``` text
SmartImage_multimodel/
├── api_gateway/          # API网关层(接口没动)
│   ├── app.py           # Flask应用工厂
│   ├── routes/          # API路由
│   └── utils/           # 工具函数
├── model_agents/        # 多智能体系统（和原来的Langchain保持一致）
│   ├── agents/          # 智能体实现
│   ├── nodes/           # 图节点
│   ├── tools/           # 工具函数
│   ├── state.py         # 状态定义（用于存储智能体的状态传递）
│   ├── graph.py         # 图构建（用于实现工作流程图）
│   └── *.md             # 系统提示词
├── data_storage/        # 数据存储层（RAG那玩意迁移到这里了）
├── ├── RAG/             # RAG相关代码
├── utils/               # 整个项目公用的工具函数
├── tests/               # 单元测试案例（很简略的）
├── config.py           # 项目配置
├── main.py             # 应用入口
├── requirements.txt    # 依赖列表
├── README.md           # 项目说明
└── .env.example         # 环境变量示例
```

## 吐槽：
1. 原版没注释，看的头疼
2. 你的模型用的是gpt-5 和 gpt-4，而很多地方有专门为这两个模型写的函数，看的头疼，但这些我一个没动。
   我是用的是三方平台的模型，在其他模型上能正常测试通过。
3. 这破langgraph架构，流式传输写的我头疼，太折磨人了。

## TO-DOs（随便写的，暂不考虑）
- 重构为FastAPI那种异步架构（划去）
- 提供一个./image接口，方面前端上传图片过来，本地临时保存，以解决前端信息有图片时无法进行流式传输的问题。
- 实现多agents辩论，目前只是将架构升级为langgraph，执行逻辑上没有太大的变动。
- 为每一个agents进行单独记忆持久化存储，目前只是依赖于对话上下文。