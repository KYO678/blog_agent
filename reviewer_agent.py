import yaml
import openai
from langchain import LLMChain, PromptTemplate
from langchain.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI
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

def setup_reviewer_chain(openai_api_key: str, prompt_template: str) -> LLMChain:
    os.environ["OPENAI_API_KEY"] = openai_api_key

    llm = ChatOpenAI(
        model_name="gpt-4o", #gpt-4o-mini-2024-07-18
        temperature=0.1
    )

    prompt = PromptTemplate(
        input_variables=["blog_text"],
        template=prompt_template
    )

    chain = LLMChain(llm=llm, prompt=prompt)

    return chain

def evaluate_blog_post(chain: LLMChain, blog_text: str) -> str:
    evaluation = chain.run(blog_text=blog_text)
    return evaluation
