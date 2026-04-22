import time
import uuid
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="社食おすすめ（腸タイプ×SCFA）", layout="centered")

# -------------------------
# 1) Demo: メニュー（素材リストつき）
# -------------------------
MENU = {
    "dateLabel": "今日",
    "mains": [
        {
            "id": "m1",
            "name": "鶏の生姜焼き定食",
            "price": 680,
            "ingredients": ["鶏肉", "生姜", "玉ねぎ", "キャベツ", "醤油", "米"],
        },
        {
            "id": "m2",
            "name": "焼き魚定食",
            "price": 720,
            "ingredients": ["青魚", "大根", "海藻", "味噌", "米"],
        },
        {
            "id": "m3",
            "name": "豚カツ定食",
            "price": 780,
            "ingredients": ["豚肉", "パン粉", "揚げ油", "キャベツ", "ソース", "米"],
        },
    ],
    "sides": [
        {"id": "s1", "name": "ひじき煮", "price": 120, "ingredients": ["ひじき", "大豆", "にんじん"]},
        {"id": "s2", "name": "納豆", "price": 100, "ingredients": ["納豆"]},
        {"id": "s3", "name": "ヨーグルト", "price": 120, "ingredients": ["ヨーグルト"]},
        {"id": "s4", "name": "キムチ", "price": 120, "ingredients": ["キムチ"]},
        {"id": "s5", "name": "サラダ", "price": 120, "ingredients": ["葉物野菜", "豆", "海藻"]},
    ],
}

GUT_TYPES = ["A", "B", "C", "D", "E", "F"]

STATE_OPTIONS = [
    ("default", "いつも通り"),
    ("light", "軽めにしたい"),
    ("sleepy", "午後眠くなりたくない"),
    ("stomach", "お腹にやさしく"),
    ("focus", "午後の集中"),
    ("busy", "とにかく迷いたくない"),
]

# -------------------------
# 2) SCFA根拠：タイプ別「素材→SCFAスコア＋根拠（短文）」
#    ※ここは“仮データ”。あなたの自社DB値に置換できる形にしてあります。
# -------------------------
TYPE_INGREDIENT_SCFA = {
    "A": {
        "海藻": {"scfa_score": +3, "reason": "多糖が発酵基質になりやすく、SCFAが伸びやすい傾向（デモ）"},
        "大豆": {"scfa_score": +2, "reason": "発酵/食物繊維の文脈でSCFAに寄与しやすい傾向（デモ）"},
        "ひじき": {"scfa_score": +2, "reason": "海藻系の発酵基質としてSCFA側に寄りやすい傾向（デモ）"},
        "葉物野菜": {"scfa_score": +1, "reason": "食物繊維がSCFAの基質になりやすい傾向（デモ）"},
        "揚げ油": {"scfa_score": -2, "reason": "脂質偏重だとSCFA寄与が出にくい傾向（デモ）"},
        "パン粉": {"scfa_score": -1, "reason": "精製寄りの炭水化物はSCFA寄与が弱い扱い（デモ）"},
    },
    "B": {
        "納豆": {"scfa_score": +3, "reason": "発酵食品の相性が高く、SCFAが伸びやすい傾向（デモ）"},
        "キムチ": {"scfa_score": +2, "reason": "発酵×食物繊維の組み合わせがプラスに働きやすい（デモ）"},
        "大豆": {"scfa_score": +2, "reason": "発酵/繊維の文脈でSCFA寄与が出やすい（デモ）"},
        "海藻": {"scfa_score": +1, "reason": "多糖が発酵基質になりSCFA側に寄りやすい（デモ）"},
        "揚げ油": {"scfa_score": -2, "reason": "脂質偏重でSCFA寄与が下がりやすい（デモ）"},
    },
    "C": {
        "葉物野菜": {"scfa_score": +3, "reason": "繊維が効きやすくSCFAが上がりやすい傾向（デモ）"},
        "海藻": {"scfa_score": +2, "reason": "多糖が発酵基質として効きやすい（デモ）"},
        "大豆": {"scfa_score": +1, "reason": "繊維/発酵の文脈で補助的に寄与（デモ）"},
        "揚げ油": {"scfa_score": -3, "reason": "揚げ物寄りだとSCFA寄与が落ちやすい傾向（デモ）"},
        "パン粉": {"scfa_score": -1, "reason": "精製寄り炭水化物はSCFA寄与が弱い扱い（デモ）"},
        "ヨーグルト": {"scfa_score": -1, "reason": "乳製品が合わない場合がありブレ要因（デモ）"},
    },
    "D": {
        "納豆": {"scfa_score": +3, "reason": "発酵の相性が高くSCFAが伸びやすい（デモ）"},
        "キムチ": {"scfa_score": +2, "reason": "発酵食品がプラスに働きやすい（デモ）"},
        "海藻": {"scfa_score": +1, "reason": "多糖がSCFA基質になりやすい（デモ）"},
        "揚げ油": {"scfa_score": -2, "reason": "脂質偏重でSCFA寄与が落ちやすい（デモ）"},
    },
    "E": {
        "海藻": {"scfa_score": +3, "reason": "海藻多糖の発酵でSCFAが伸びやすい（デモ）"},
        "ひじき": {"scfa_score": +2, "reason": "海藻系の発酵基質としてSCFA寄与が出やすい（デモ）"},
        "葉物野菜": {"scfa_score": +2, "reason": "繊維でSCFAを押し上げやすい（デモ）"},
        "揚げ油": {"scfa_score": -2, "reason": "揚げ物寄りでSCFA寄与が下がりやすい（デモ）"},
    },
    "F": {
        "大豆": {"scfa_score": +2, "reason": "繊維/発酵の文脈でSCFA側に寄せやすい（デモ）"},
        "海藻": {"scfa_score": +2, "reason": "多糖が基質になりSCFAを押し上げやすい（デモ）"},
        "葉物野菜": {"scfa_score": +1, "reason": "繊維で底上げしやすい（デモ）"},
        "鶏肉": {"scfa_score": +1, "reason": "主菜で満足を確保しつつ小鉢でSCFAを伸ばしやすい（デモ）"},
        "揚げ油": {"scfa_score": -1, "reason": "脂質偏重だとSCFA寄与が伸びにくい（デモ）"},
    },
}

# -------------------------
# 3) 気分（状態）による“選択のしやすさ”補正（UX演出）
# -------------------------
STATE_INGREDIENT_BOOST = {
    "default": {},
    "light": {"揚げ油": -2, "パン粉": -1, "葉物野菜": +1, "海藻": +1},
    "sleepy": {"揚げ油": -2, "パン粉": -1, "葉物野菜": +1, "海藻": +1},
    "stomach": {"揚げ油": -2, "キムチ": -1, "ヨーグルト": -1, "海藻": +1, "葉物野菜": +1},
    "focus": {"鶏肉": +1, "青魚": +1, "揚げ油": -1},
    "busy": {},
}

# -------------------------
# 4) ロジック
# -------------------------
def confidence(scores):
    avg = sum(scores) / max(1, len(scores))
    top = max(scores)
    d = top - avg
    return "強" if d >= 2 else ("中" if d >= 1 else "参考")


def score_item_scfa(gut_type, state_id, item):
    base_map = TYPE_INGREDIENT_SCFA.get(gut_type, {})
    boost = STATE_INGREDIENT_BOOST.get(state_id, {})

    total = 0.0
    contrib = []  # (ingredient, score, reason)

    for ing in item.get("ingredients", []):
        base = base_map.get(ing, {"scfa_score": 0, "reason": "（この素材は中立扱い：デモ）"})
        s = float(base["scfa_score"]) + float(boost.get(ing, 0))
        total += s
        if s != 0:
            contrib.append((ing, s, base["reason"]))

    return round(total, 2), contrib


def top_scfa_driver(contrib):
    positives = [c for c in contrib if c[1] > 0]
    if not positives:
        return None
    return max(positives, key=lambda x: x[1])  # (ingredient, score, reason)


def recommend(gut, state):
    mains = []
    for m in MENU["mains"]:
        s, contrib = score_item_scfa(gut, state, m)
        jitter = (ord(m["id"][-1]) % 7) * 0.02
        s = round(s + jitter, 2)
        mains.append({**m, "score": s, "contrib": contrib})
    mains.sort(key=lambda x: x["score"], reverse=True)

    top_main = mains[0]
    alt_main = mains[1] if len(mains) > 1 else mains[0]

    complement_bonus = {}
    if "揚げ油" in top_main.get("ingredients", []):
        complement_bonus.update({"海藻": +1.0, "ひじき": +1.0, "大豆": +0.8, "葉物野菜": +0.8})

    sides = []
    for s in MENU["sides"]:
        base, contrib = score_item_scfa(gut, state, s)
        bonus = sum(complement_bonus.get(ing, 0) for ing in s.get("ingredients", []))
        score = round(base + bonus, 2)
        sides.append({**s, "score": score, "contrib": contrib, "bonus": round(bonus, 2)})
    sides.sort(key=lambda x: x["score"], reverse=True)

    conf = confidence([m["score"] for m in mains])
    return top_main, sides[0], alt_main, conf, mains, sides


def recommend_with_forced_main(gut, state, forced_main):
    """
    主菜を forced_main に固定して、
    その主菜に応じた補完（complement_bonus）で小鉢を再計算して返す。
    """
    complement_bonus = {}
    if "揚げ油" in forced_main.get("ingredients", []):
        complement_bonus.update({"海藻": +1.0, "ひじき": +1.0, "大豆": +0.8, "葉物野菜": +0.8})

    sides = []
    for s in MENU["sides"]:
        base, contrib = score_item_scfa(gut, state, s)
        bonus = sum(complement_bonus.get(ing, 0) for ing in s.get("ingredients", []))
        score = round(base + bonus, 2)
        sides.append({**s, "score": score, "contrib": contrib, "bonus": round(bonus, 2)})
    sides.sort(key=lambda x: x["score"], reverse=True)

    best_side = sides[0]
    conf = "参考"  # 主菜3択の比較ではなくなるため簡略
    return best_side, conf


def rationale_text(gut, state, main, side):
    state_label = dict(STATE_OPTIONS).get(state, "いつも通り")

    def top_lines(contrib, k=2):
        if not contrib:
            return "- （この料理はSCFA寄与が中立に近い構成：デモ）"
        contrib_sorted = sorted(contrib, key=lambda x: abs(x[1]), reverse=True)[:k]
        lines = []
        for ing, sc, reason in contrib_sorted:
            arrow = "↑" if sc > 0 else "↓"
            lines.append(f"- {ing}：SCFA {arrow}（{reason}）")
        return "\n".join(lines)

    return (
        f"根拠は **短鎖脂肪酸（SCFA）スコア**。腸タイプ（Type {gut}）× 優先（{state_label}）で、"
        f"主菜3択＋小鉢を **SCFA寄与**で並べ替えています。\n\n"
        f"**主菜の根拠（上位）**\n{top_lines(main.get('contrib', []))}\n\n"
        f"**小鉢の根拠（上位）**\n{top_lines(side.get('contrib', []))}"
    )


# -------------------------
# 5) セッション（チャット）
# -------------------------
if "chat" not in st.session_state:
    st.session_state.chat = []
if "step" not in st.session_state:
    st.session_state.step = "ask_gut"  # ask_gut -> ask_state -> show
if "gut" not in st.session_state:
    st.session_state.gut = "A"
if "state" not in st.session_state:
    st.session_state.state = "default"
if "history" not in st.session_state:
    st.session_state.history = []
if "uid" not in st.session_state:
    st.session_state.uid = str(uuid.uuid4())[:8]

# 提案を保持して「このまま/代替」を確定できるようにする
if "pending" not in st.session_state:
    st.session_state.pending = None
if "final_choice" not in st.session_state:
    st.session_state.final_choice = None  # "keep" or "alt"

st.title("社食おすすめ（腸タイプ×SCFA）— チャット風デモ")
st.caption(
    "腸タイプと気分を選ぶだけで、今日の主菜3択＋小鉢から“迷わないセット”を提案します。評価根拠＝短鎖脂肪酸（SCFA）スコア。"
)

# チャット描画
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


def bot(text):
    st.session_state.chat.append({"role": "assistant", "content": text})


def user(text):
    st.session_state.chat.append({"role": "user", "content": text})


# 初回メッセージ
if len(st.session_state.chat) == 0:
    bot(f"こんにちは。{MENU['dateLabel']}の社食、迷ってますか？まずは腸タイプを選んでください。")


# チップ風ボタン行
def chip_row(options, key, format_func=None):
    cols = st.columns(len(options))
    chosen = None
    for i, opt in enumerate(options):
        label = format_func(opt) if format_func else str(opt)
        if cols[i].button(label, key=f"{key}_{opt}"):
            chosen = opt
    return chosen


if st.session_state.step == "ask_gut":
    chosen = chip_row(GUT_TYPES, "gut", format_func=lambda x: f"Type {x}")
    if chosen:
        st.session_state.gut = chosen
        user(f"腸タイプは Type {chosen} です。")
        bot("了解です。次に、今の気分（任意）を選んでください。")
        st.session_state.step = "ask_state"
        st.rerun()

elif st.session_state.step == "ask_state":
    state_ids = [x[0] for x in STATE_OPTIONS]
    chosen = chip_row(state_ids, "state", format_func=lambda x: dict(STATE_OPTIONS)[x])
    if chosen:
        st.session_state.state = chosen
        user(f"今日は「{dict(STATE_OPTIONS)[chosen]}」でお願いします。")

        with st.chat_message("assistant"):
            with st.spinner("考え中…"):
                time.sleep(0.8)

        top_main, top_side, alt_main, conf, mains, sides = recommend(st.session_state.gut, st.session_state.state)

        driver = top_scfa_driver(top_main.get("contrib", []))
        if driver is None:
            driver = top_scfa_driver(top_side.get("contrib", []))
        driver_label = driver[0] if driver else "（該当なし）"

        # 提案内容を保持
        st.session_state.pending = {
            "gut": st.session_state.gut,
            "state": st.session_state.state,
            "top_main": top_main,
            "top_side": top_side,
            "alt_main": alt_main,
            "conf": conf,
            "driver_label": driver_label,
        }
        st.session_state.final_choice = None

        total = top_main["price"] + top_side["price"]

        bot(
            f"**あなたの腸内タイプ（{st.session_state.gut}）には（{driver_label}）が最も短鎖脂肪酸スコアが高いです。**\n\n"
            f"**今日の迷わないセット（SCFA根拠）**  \n"
            f"- 主菜：**{top_main['name']}**（¥{top_main['price']} / SCFAスコア：**{top_main['score']}**）  \n"
            f"- 小鉢：**{top_side['name']}**（¥{top_side['price']} / SCFAスコア：**{top_side['score']}**）  \n"
            f"- 代替：{alt_main['name']}  \n\n"
            f"✅ 相性：良（根拠：{conf}） / 合計：**¥{total}**  \n\n"
            f"{rationale_text(st.session_state.gut, st.session_state.state, top_main, top_side)}"
        )

        st.session_state.step = "show"
        st.rerun()

elif st.session_state.step == "show":
    pending = st.session_state.pending

    # ワンタップ確定
    if pending:
        st.markdown("### 最後に選ぶ（ワンタップ）")
        keep_col, alt_col = st.columns(2)

        keep_label = f"✅ このまま行く：{pending['top_main']['name']} + {pending['top_side']['name']}"
        alt_label = f"🔁 代替にする：{pending['alt_main']['name']} + {pending['top_side']['name']}"

        if keep_col.button(keep_label):
            st.session_state.final_choice = "keep"
            st.session_state.history.insert(
                0,
                {
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "uid": st.session_state.uid,
                    "gut": pending["gut"],
                    "state": pending["state"],
                    "action": "finalize",
                    "choice": "keep",
                    "main": pending["top_main"]["name"],
                    "side": pending["top_side"]["name"],
                    "total": pending["top_main"]["price"] + pending["top_side"]["price"],
                    "driver": pending["driver_label"],
                },
            )
            bot("了解です。このまま行きましょう。食後のリアクションも教えてください。")
            st.rerun()

        if alt_col.button(alt_label):
            # 代替主菜に合わせて小鉢も再計算
            alt_main = pending["alt_main"]
            best_side_for_alt, _conf2 = recommend_with_forced_main(pending["gut"], pending["state"], alt_main)

            # 「最もSCFAスコアが高い素材」も、代替主菜＋再計算小鉢で取り直す
            driver = top_scfa_driver(alt_main.get("contrib", []))
            if driver is None:
                driver = top_scfa_driver(best_side_for_alt.get("contrib", []))
            driver_label = driver[0] if driver else "（該当なし）"

            total_alt = alt_main["price"] + best_side_for_alt["price"]

            # 確定状態を保存
            st.session_state.final_choice = "alt"
            st.session_state.history.insert(
                0,
                {
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "uid": st.session_state.uid,
                    "gut": pending["gut"],
                    "state": pending["state"],
                    "action": "finalize",
                    "choice": "alt",
                    "main": alt_main["name"],
                    "side": best_side_for_alt["name"],
                    "total": total_alt,
                    "driver": driver_label,
                },
            )

            # 代替セットの根拠を再提示（チャットに出す）
            bot(
                f"了解です。**代替メニューに切り替えました。**\n\n"
                f"**あなたの腸内タイプ（{pending['gut']}）には（{driver_label}）が最も短鎖脂肪酸スコアが高いです。**\n\n"
                f"**代替の迷わないセット（SCFA根拠）**  \n"
                f"- 主菜：**{alt_main['name']}**（¥{alt_main['price']} / SCFAスコア：**{alt_main['score']}**）  \n"
                f"- 小鉢：**{best_side_for_alt['name']}**（¥{best_side_for_alt['price']} / SCFAスコア：**{best_side_for_alt['score']}**）  \n\n"
                f"合計：**¥{total_alt}**  \n\n"
                f"{rationale_text(pending['gut'], pending['state'], alt_main, best_side_for_alt)}"
            )
            st.rerun()

        st.caption("※クリックすると“確定”としてログに残ります（PoC用）。")
        st.divider()

    # 確定後だけリアクションを出す
    if st.session_state.final_choice is None:
        st.info("まずは「このまま行く / 代替にする」で確定してください。")
    else:
        st.markdown("### 食後のリアクション（デモ）")
        c1, c2 = st.columns(2)
        tag = st.selectbox("任意タグ", ["なし", "迷いが減った", "食後軽い", "眠い", "張る", "おいしい"], index=0)

        if c1.button("👍 よかった"):
            st.session_state.history.insert(
                0,
                {
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "uid": st.session_state.uid,
                    "gut": st.session_state.gut,
                    "state": st.session_state.state,
                    "action": "reaction",
                    "kind": "up",
                    "tag": None if tag == "なし" else tag,
                },
            )
            bot("ありがとうございます。次回のおすすめ精度に反映します（デモ）。")
            st.rerun()

        if c2.button("👎 いまいち"):
            st.session_state.history.insert(
                0,
                {
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "uid": st.session_state.uid,
                    "gut": st.session_state.gut,
                    "state": st.session_state.state,
                    "action": "reaction",
                    "kind": "down",
                    "tag": None if tag == "なし" else tag,
                },
            )
            bot("了解です。次は別の組み合わせも出します（デモ）。")
            st.rerun()

    with st.expander("PoCダッシュボード（簡易）"):
        if st.session_state.history:
            df = pd.DataFrame(st.session_state.history)
            st.dataframe(df, use_container_width=True)
        else:
            st.caption("まだログがありません。")
