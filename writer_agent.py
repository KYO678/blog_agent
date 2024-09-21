import yaml
import openai
from langchain.agents import initialize_agent, Tool, AgentExecutor
from langchain.agents import AgentType
#from langchain.llms import OpenAI
from langchain_community.llms import OpenAI
from langchain.utilities import SerpAPIWrapper
from langchain_openai import ChatOpenAI
import os

def read_config(config_path: str) -> dict:
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"設定ファイル {config_path} が見つかりません。")
        return {}
    except yaml.YAMLError as e:
        print(f"YAMLファイルの解析エラー: {e}")
        return {}

def setup_agent(openai_api_key: str, serpapi_api_key: str) -> any:
    os.environ["OPENAI_API_KEY"] = openai_api_key
    os.environ["SERPAPI_API_KEY"] = serpapi_api_key

    llm = ChatOpenAI(
        model_name="gpt-4o", #gpt-4o-mini-2024-07-18
        temperature=0.7
    )
    
    search = SerpAPIWrapper()
    
    tools = [
        Tool(
            name="Search",
            func=search.run,
            description="最新の情報やウェブ上の情報を取得するための検索エンジン。"
        )
    ]
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=False,  # デバッグ時は True に
        max_iterations=10  # 必要に応じて調整
    )

    # AgentExecutor に handle_parsing_errors=True を設定
    if isinstance(agent, AgentExecutor):
        agent.handle_parsing_errors = True
    else:
        print("Agent is not an instance of AgentExecutor. Cannot set handle_parsing_errors.")
    
    return agent

def generate_blog_post(agent: any, keywords: list, feedback: str = "") -> str:
    prompt = (
        f"以下のキーワードを使用して、情報を収集し、魅力的なブログ記事を書いてください。4000文字~5000文字程度を目安としてください。\n"
        f"キーワード: {', '.join(keywords)}\n\n"
    )
    if feedback:
        prompt += f"以下のフィードバックを考慮して記事を改善してください:\n{feedback}\n\n"
    prompt += "ブログ記事を生成してください。"
    
    print(f"DEBUG: 使用するプロンプト:\n{prompt}")  # デバッグ用ログ
    
    try:
        blog_post = agent.run(prompt)
        print("DEBUG: ブログ記事が正常に生成されました。")
        return blog_post
    except Exception as e:
        print(f"DEBUG: ブログ記事生成中にエラーが発生しました: {e}")
        return ""
