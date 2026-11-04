# 第2回 宿題（実装）: ノートブック「2. 架空 FAQ と教師データの生成」のセルをこの内容で丸ごと置き換える。
# 題材: 架空の会社の職場ルール（内容はすべて架空）。JSON の形式と needs_review の設計はノートブックのまま。

FAQ = {
    "start_time": "始業時刻は 9:30 で、コアタイムは 11:00〜15:00 です。",
    "paid_leave": "有給休暇は取得日の 3 営業日前までに勤怠システムで申請します。",
    "expense": "経費は月末締めで、翌月 10 日までに領収書を添えて経理に提出します。",
    "meeting_room": "会議室は共有カレンダーから予約し、1 回最長 2 時間まで使えます。",
    "remote_work": "在宅勤務は週 2 日までで、前日 17:00 までに上長へ連絡します。",
}
FAQ_TEXT = "\n".join(f"- {v}" for v in FAQ.values())

# 根拠あり: (FAQ キー, 質問テンプレート群, 正解の answer に含まれるべき語)
# テンプレートは先頭 2 つが train、3 つ目が valid、4 つ目が test に固定される（ノートブックの split_templates）
GROUNDED = {
    "start_time": (["始業時刻は何時ですか", "何時に出社すればいいですか", "コアタイムは何時から何時までですか", "勤務開始の時間を教えてください"], ["9:30", "コアタイム"]),
    "paid_leave": (["有給休暇はどうやって申請しますか", "有給はいつまでに申請すればいいですか", "休暇申請の締切を教えてください", "有給を取りたいときの手続きは？"], ["3 営業日", "勤怠システム"]),
    "expense": (["経費精算の締切はいつですか", "経費はどこに提出しますか", "立て替えた費用はいつまでに精算しますか", "領収書の提出先と期限を教えてください"], ["10 日", "経理"]),
    "meeting_room": (["会議室はどうやって予約しますか", "会議室は何時間まで使えますか", "会議室の予約方法を教えてください", "会議室を押さえたいときはどうすればいいですか"], ["共有カレンダー", "2 時間"]),
    "remote_work": (["在宅勤務は週に何日までできますか", "在宅勤務をするときは誰にいつ連絡しますか", "リモートワークのルールを教えてください", "在宅で働きたい日はどうすればいいですか"], ["週 2 日", "前日"]),
}
# 根拠なし: FAQ に無いので needs_review=true が正解。
# 「近いけど書いていない」（FAQ の項目に関係はあるが答えが無い）と「まったく別」（FAQ の話題外）の 2 種類を混ぜる。
# ノートブックの仕組みで、並び順に train, train, valid, test の繰り返しで振り分けられる。
UNGROUNDED = [
    "お昼休みの時間は勤怠上どう扱われますか",   # 近い（始業時刻）→ train
    "社員食堂はありますか",                       # 別 → train
    "残業したときの手当はどうなりますか",         # 近い（始業時刻）→ valid
    "服装の規定はありますか",                     # 別 → test
    "有給休暇は最大何日連続で取れますか",         # 近い（有給休暇）→ train
    "駐車場は利用できますか",                     # 別 → train
    "健康診断はいつ実施されますか",               # 別 → valid
    "経費に上限はありますか",                     # 近い（経費精算）→ test
]

# test 専用の追加質問（train / valid には入れない）
TEST_EXTRA_GROUNDED = {
    "start_time": ["朝は何時までに来る必要がありますか", "必ず在席していないといけない時間帯はありますか"],
    "paid_leave": ["有給休暇の申請期限と申請方法を教えてください", "休みを取る場合は何日前までに申請が必要ですか"],
    "expense": ["経費の精算はどのように行いますか", "経費精算の提出期限は毎月何日ですか"],
    "meeting_room": ["会議室の利用時間に上限はありますか", "会議室の予約はどこから行い、最長何時間使えますか"],
    "remote_work": ["在宅勤務の上限日数と連絡の期限を教えてください", "テレワークは何日まで可能ですか"],
}
TEST_EXTRA_UNGROUNDED = [
    "会議室を 2 回に分けて予約すれば、続けて 4 時間使えますか",   # 近い（会議室予約）
    "在宅勤務中の休憩は自由に取れますか",                         # 近い（在宅勤務）
    "社内のサークル活動はありますか",                             # 別
    "名刺の発注はどこに頼めばいいですか",                         # 別
]
UNGROUNDED_ANSWER = "この FAQ には記載がありません。運営に確認が必要です。"

def make_example(question: str, answer: str, needs_review: bool) -> dict:
    target = json.dumps({"answer": answer, "needs_review": needs_review}, ensure_ascii=False)
    return {"question": question, "faq": FAQ_TEXT, "target": target, "needs_review": needs_review}

def split_templates(templates):
    # テンプレートの先頭 2 つを train、3 つ目を valid、4 つ目を test に固定（言い換えを跨がせない）
    return templates[:2], templates[2:3], templates[3:4]

train, valid, test, gold = [], [], [], {}
for key, (templates, must_include) in GROUNDED.items():
    tr, va, te = split_templates(templates)
    for q in tr: train.append(make_example(q, FAQ[key], False))
    for q in va: valid.append(make_example(q, FAQ[key], False))
    for q in te + TEST_EXTRA_GROUNDED[key]:
        test.append(make_example(q, FAQ[key], False)); gold[q] = {"needs_review": False, "must_include": must_include}
for i, q in enumerate(UNGROUNDED):
    ex = make_example(q, UNGROUNDED_ANSWER, True)
    bucket = [train, train, valid, test][i % 4]   # 根拠なしの質問は 4 問ごとに train 2 / valid 1 / test 1 に振る
    bucket.append(ex)
    if bucket is test: gold[q] = {"needs_review": True, "must_include": ["確認"]}
for q in TEST_EXTRA_UNGROUNDED:
    test.append(make_example(q, UNGROUNDED_ANSWER, True)); gold[q] = {"needs_review": True, "must_include": ["確認"]}

# train は 14 件（根拠あり 10、根拠なし 4）。同じ例を何回学習するかは、データを複製せず、セクション 4 の num_train_epochs で決める
all_questions = [r["question"] for r in train + valid + test]
assert len(set(all_questions)) == len(all_questions), "質問が train / valid / test のどこかで重複しています。テンプレートを見直してください"
print(f"train={len(train)} valid={len(valid)} test={len(test)} gold={len(gold)}")
print("学習例の 1 件 | 質問:", train[0]["question"], "| 望ましい出力:", train[0]["target"])
_ = (WORK / "train.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in train), encoding="utf-8")
_ = (WORK / "test.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in test), encoding="utf-8")
_ = (WORK / "gold.json").write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
