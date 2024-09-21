# app.py

import streamlit as st
from writer_agent import read_config, setup_agent, generate_blog_post
from reviewer_agent import setup_reviewer_chain, evaluate_blog_post
import yaml

def main():
    st.title("ブログ記事生成・評価アプリ")
    st.write("キーワードを入力して、ブログ記事を生成し、評価を受けましょう。")

    # 設定ファイルの読み込み
    config = read_config("config.yaml")
    openai_api_key = config.get("openai_api_key")
    serpapi_api_key = config.get("serpapi_api_key")

    if not openai_api_key or not serpapi_api_key:
        st.error("設定ファイルにOpenAI APIキーまたは SerpAPI APIキーが見つかりません。")
        return

    # Prompt Templateのファイルパス
    prompt_file_path = "prompt_template.txt"

    # Prompt Templateの読み込みまたはデフォルト設定
    default_prompt = (
        "あなたは優秀なブログ記事レビュアーです。以下のブログ記事を以下の5つの視点で評価し、各項目に対して5点満点でスコアを付けてください。\n"
        "1. 技術的正確性 (5点満点): 情報が最新で正確か\n"
        "2. タイトルの分かりやすさ (5点満点): 初見で目を引くインパクトのあるタイトルになっているか\n"
        "3. 記事の長さ (5点満点): 5000字以上あるか\n"
        "4. 構成と読みやすさ (5点満点): 論理的な構成で、読みやすいか\n"
        "5. 独自性と洞察 (5点満点): 独自の視点や深い洞察が含まれているか\n\n"
        "評価結果は以下の形式で出力してください:\n"
        "1. 技術的正確性: X/5\n"
        "2. タイトルの分かりやすさ: X/5\n"
        "3. 記事の長さ: X/5\n"
        "4. 構成と読みやすさ: X/5\n"
        "5. 独自性と洞察: X/5\n"
        "コメント:\n"
        "{blog_text}"
    )

    if 'prompt_template' not in st.session_state:
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                st.session_state.prompt_template = f.read()
        except FileNotFoundError:
            st.session_state.prompt_template = default_prompt
            with open(prompt_file_path, 'w', encoding='utf-8') as f:
                f.write(default_prompt)

    st.subheader("Reviewer AgentのPrompt Templateを編集")
    prompt_input = st.text_area("Prompt Template:", st.session_state.prompt_template, height=300)
    
    if st.button("Prompt Templateを更新"):
        if prompt_input.strip():
            st.session_state.prompt_template = prompt_input
            # Prompt Templateをファイルに保存
            with open(prompt_file_path, 'w', encoding='utf-8') as f:
                f.write(prompt_input)
            st.success("Prompt Templateを更新しました。")
        else:
            st.warning("Prompt Templateは空にできません。")

    st.markdown("---")

    # キーワード入力フォーム
    keywords_input = st.text_input("ブログ記事に使用するキーワードをカンマ区切りで入力してください:", "")
    
    # イテレーションの最大回数
    MAX_ITERATIONS = 5

    # セッションステートの初期化
    if 'iterations' not in st.session_state:
        st.session_state.iterations = []
    if 'current_iteration' not in st.session_state:
        st.session_state.current_iteration = 0

    # 「記事を生成」ボタン
    if st.button("記事を生成"):
        if not keywords_input.strip():
            st.warning("キーワードを入力してください。")
        else:
            keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
            if not keywords:
                st.warning("有効なキーワードを入力してください。")
            else:
                # エージェントのセットアップ
                writer_agent = setup_agent(openai_api_key, serpapi_api_key)
                reviewer_chain = setup_reviewer_chain(openai_api_key, st.session_state.prompt_template)

                feedback = ""
                for iteration in range(MAX_ITERATIONS):
                    st.session_state.current_iteration += 1
                    st.write(f"### イテレーション {st.session_state.current_iteration}")

                    # ブログ記事の生成
                    blog_post = generate_blog_post(writer_agent, keywords, feedback)
                    if not blog_post:
                        st.error("ブログ記事の生成に失敗しました。プロンプトやAPIキーを確認してください。")
                        break

                    # ブログ記事の表示
                    st.markdown("**生成されたブログ記事:**")
                    st.markdown(blog_post)
                    
                    # ブログ記事の評価
                    evaluation = evaluate_blog_post(reviewer_chain, blog_post)
                    if not evaluation:
                        st.error("ブログ記事の評価に失敗しました。プロンプトやAPIキーを確認してください。")
                        break

                    # 評価結果の表示
                    st.markdown("**評価結果:**")
                    st.text(evaluation)

                    # 評価結果の解析
                    scores = {}
                    comments = ""
                    total_score = 0

                    lines = evaluation.split('\n')
                    for line in lines:
                        if "コメント:" in line:
                            comments = line.split("コメント:")[-1].strip()
                            break
                        else:
                            try:
                                key, value = line.split(":")
                                score = int(value.strip().split("/")[0])
                                scores[key.strip()] = score
                                total_score += score
                            except:
                                continue

                    st.markdown(f"**総合点数:** {total_score}/25")

                    # イテレーションの保存
                    st.session_state.iterations.append({
                        'iteration': st.session_state.current_iteration,
                        'blog_post': blog_post,
                        'evaluation': evaluation,
                        'total_score': total_score
                    })

                    if total_score >= 22:
                        st.success("ブログ記事の生成と評価が完了しました。")
                        break
                    else:
                        st.warning("評価点数が22点未満です。フィードバックを基に記事を改善します。")
                        feedback = comments

                else:
                    st.error(f"最大イテレーション数（{MAX_ITERATIONS}回）に達しました。プロンプトを見直してください。")

    st.markdown("---")

    # イテレーション結果の表示
    if st.session_state.iterations:
        st.header("イテレーション履歴")
        for entry in st.session_state.iterations:
            st.subheader(f"イテレーション {entry['iteration']}")
            st.markdown("**生成されたブログ記事:**")
            st.markdown(entry['blog_post'])
            st.markdown("**評価結果:**")
            st.text(entry['evaluation'])
            st.markdown(f"**総合点数:** {entry['total_score']}/25")
            st.markdown("---")

        # 最終的なブログ記事の表示とダウンロード
        final_entry = st.session_state.iterations[-1]
        if final_entry['total_score'] >= 20:
            st.header("最終的に生成されたブログ記事")
            st.markdown(final_entry['blog_post'])

            # ダウンロードボタンの追加
            st.download_button(
                label="ブログ記事をダウンロード",
                data=final_entry['blog_post'],
                file_name="generated_blog_post.md",
                mime="text/markdown"
            )

if __name__ == "__main__":
    main()
