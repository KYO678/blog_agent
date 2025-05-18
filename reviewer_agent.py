from langchain import LLMChain, PromptTemplate
from langchain_community.chat_models import ChatOpenAI
import os


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
