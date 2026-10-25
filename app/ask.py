"""第1回: 会話履歴を保持して質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "東京大学について簡単に説明してください。"


def ask(chat, question: str) -> str:
    response = chat.send_message(question)

    usage = response.usage_metadata
    if usage is not None:
        print(f"[入力トークン数] {usage.prompt_token_count}")
        print(f"[出力トークン数] {usage.candidates_token_count}")

    return response.text


def main() -> None:
    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)

    print(f"[model] {MODEL}")
    print("終了するには exit と入力してください。")

    try:
        while True:
            question = input("\n質問> ").strip()

            if question.lower() in {"exit", "quit"}:
                break
            if not question:
                continue

            print(ask(chat, question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)

if __name__ == "__main__":
    main()
