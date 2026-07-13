# ============================================================
# 【完全無料】Supabase プロンプト書き換え専用 Webダッシュボード
# ============================================================
# 必要なライブラリ： pip install streamlit supabase
import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Bot Control Panel", layout="centered")

# ------------------------------------------------------------
# 0. 簡易ログインゲート（ID・パスワード固定版）
# ------------------------------------------------------------
def check_auth() -> bool:
    if st.session_state.get("authenticated"):
        return True

    st.title("🔒 ログイン")

    # オーナー指定の固定ID・パスワード
    valid_user = "id4s"
    valid_pass = "1013"

    with st.form("login_form"):
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン")

    if submitted:
        if username == valid_user and password == valid_pass:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("ユーザー名またはパスワードが違います。")

    return False


if not check_auth():
    st.stop()

# ------------------------------------------------------------
# 1. Supabaseの接続情報（Streamlit Cloud の Settings > Secrets から読み込む）
#    Secretsには以下の形式で登録してください。
#    SUPABASE_URL = "https://iomqwzeifmyfrpvezojz.supabase.co"
#    SUPABASE_KEY = "（SupabaseのAPIキー：service_role推奨）"
# ------------------------------------------------------------
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    st.error(
        "SUPABASE_URL または SUPABASE_KEY がSecretsに設定されていません。\n\n"
        "Streamlit CloudのSettings > Secretsに以下を登録してください。\n\n"
        'SUPABASE_URL = "https://iomqwzeifmyfrpvezojz.supabase.co"\n'
        'SUPABASE_KEY = "（SupabaseのAPIキー）"'
    )
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("🤖 ゴリ押しBot プロンプト管理")


def save_persona(persona_id: str, bot_id, label: str, trigger_keyword: str, is_default: bool, system_prompt: str):
    if is_default and bot_id is not None:
        # 同じbotの他のキャラのis_defaultを先に外す（1bot1デフォルトの制約対応）
        supabase.table("bot_personas").update({"is_default": False}).eq(
            "bot_id", bot_id
        ).neq("id", persona_id).execute()

    supabase.table("bot_personas").update(
        {
            "label": label,
            "trigger_keyword": trigger_keyword or None,
            "is_default": is_default,
            "system_prompt": system_prompt,
        }
    ).eq("id", persona_id).execute()


# ============================================================
# セクション1: 全Bot共通のキャラ（bot_id = NULL）
# ============================================================
st.subheader("🌐 全Botで共通のキャラ")
st.caption("ここで編集したキャラは、どのBot（クローン）からもトリガー語で呼び出せます。")

try:
    common_res = (
        supabase.table("bot_personas")
        .select("id, persona_key, label, system_prompt, trigger_keyword, is_default")
        .is_("bot_id", "null")
        .execute()
    )
    common_personas = common_res.data
except Exception as e:
    st.error(f"共通ペルソナ取得エラー: {e}")
    common_personas = []

if common_personas:
    common_labels = {
        f"{p['label'] or p['persona_key']}（{p['persona_key']}）": p for p in common_personas
    }
    selected_common_label = st.selectbox("編集する共通キャラを選択:", list(common_labels.keys()), key="common_select")
    current_common = common_labels[selected_common_label]

    with st.form("edit_common_persona_form"):
        c_label = st.text_input("表示名", value=current_common.get("label") or "", key="c_label")
        c_trigger = st.text_input(
            "切り替えトリガー語（メッセージにこの言葉が含まれると全Bot共通でこのキャラになる）",
            value=current_common.get("trigger_keyword") or "",
            key="c_trigger",
        )
        c_prompt = st.text_area(
            "システムプロンプト（指示内容）:",
            value=current_common.get("system_prompt", ""),
            height=250,
            key="c_prompt",
        )
        c_submitted = st.form_submit_button("共通キャラを保存する", type="primary")

        if c_submitted:
            try:
                save_persona(current_common["id"], None, c_label, c_trigger, False, c_prompt)
                st.success(f"🎉 共通キャラ「{selected_common_label}」を保存しました！")
                st.rerun()
            except Exception as e:
                st.error(f"保存に失敗しました: {e}")
else:
    st.info("まだ共通キャラがありません。下の「新しいキャラを追加」から bot を選ばずに追加できます。")

st.divider()

# ============================================================
# セクション2: Botごとの個別キャラ
# ============================================================
try:
    response = supabase.table("bots").select("id, bot_name, bot_type").execute()
    bots_data = response.data
except Exception as e:
    st.error(f"データ取得エラー: {e}")
    bots_data = []

if not bots_data:
    st.warning("botsテーブルにレコードが見つかりません。")
    st.stop()

bot_options = {b["bot_name"]: b for b in bots_data}
selected_bot_name = st.selectbox("Botを選択:", list(bot_options.keys()))
current_bot = bot_options[selected_bot_name]
bot_id = current_bot["id"]

st.subheader(f"🎭「{selected_bot_name}」専用のキャラ")

try:
    persona_res = (
        supabase.table("bot_personas")
        .select("id, persona_key, label, system_prompt, trigger_keyword, is_default")
        .eq("bot_id", bot_id)
        .order("is_default", desc=True)
        .execute()
    )
    personas_data = persona_res.data
except Exception as e:
    st.error(f"ペルソナ取得エラー: {e}")
    personas_data = []

if personas_data:
    persona_labels = {
        f"{p['label'] or p['persona_key']}（{p['persona_key']}）": p for p in personas_data
    }
    selected_label = st.selectbox("編集するキャラを選択:", list(persona_labels.keys()), key="bot_persona_select")
    current_persona = persona_labels[selected_label]

    with st.form("edit_persona_form"):
        label = st.text_input("表示名", value=current_persona.get("label") or "")
        trigger_keyword = st.text_input(
            "切り替えトリガー語（メッセージにこの言葉が含まれるとこのキャラになる）",
            value=current_persona.get("trigger_keyword") or "",
            help="通常キャラは基本トリガー不要（is_defaultで判定）。追加キャラ用に使ってください。",
        )
        is_default = st.checkbox(
            "これを通常時（初期状態）のキャラにする",
            value=bool(current_persona.get("is_default")),
        )
        system_prompt = st.text_area(
            "システムプロンプト（指示内容）:",
            value=current_persona.get("system_prompt", ""),
            height=300,
        )

        submitted = st.form_submit_button("このキャラを保存する", type="primary")

        if submitted:
            try:
                save_persona(current_persona["id"], bot_id, label, trigger_keyword, is_default, system_prompt)
                st.success(f"🎉 「{selected_label}」を保存しました！")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"保存に失敗しました: {e}")
else:
    st.info("このBotにはまだ専用キャラが登録されていません。下から新規追加してください。")

st.divider()

# ============================================================
# セクション3: 新しいキャラを追加（Bot専用 or 全Bot共通）
# ============================================================
with st.expander("➕ 新しいキャラを追加"):
    with st.form("new_persona_form", clear_on_submit=True):
        scope = st.radio(
            "適用範囲",
            [f"「{selected_bot_name}」専用", "全Bot共通"],
            horizontal=True,
        )
        new_key = st.text_input("persona_key（英数字。例: serious / mental）")
        new_label = st.text_input("表示名（例: メンヘラモード）")
        new_trigger = st.text_input("切り替えトリガー語（例: 病んで）")
        new_prompt = st.text_area("システムプロンプト", height=200)
        new_is_default = st.checkbox(
            "これを通常時のキャラにする（Bot専用の場合のみ有効）", value=False
        )

        add_submitted = st.form_submit_button("追加する")

        if add_submitted:
            if not new_key or not new_prompt:
                st.error("persona_key と システムプロンプトは必須です。")
            else:
                try:
                    is_common = scope == "全Bot共通"
                    target_bot_id = None if is_common else bot_id
                    effective_is_default = False if is_common else new_is_default

                    if effective_is_default:
                        supabase.table("bot_personas").update({"is_default": False}).eq(
                            "bot_id", target_bot_id
                        ).execute()

                    supabase.table("bot_personas").insert(
                        {
                            "bot_id": target_bot_id,
                            "persona_key": new_key,
                            "label": new_label or new_key,
                            "trigger_keyword": new_trigger or None,
                            "is_default": effective_is_default,
                            "system_prompt": new_prompt,
                        }
                    ).execute()
                    st.success(f"🎉 「{new_label or new_key}」を追加しました！")
                    st.rerun()
                except Exception as e:
                    st.error(f"追加に失敗しました: {e}")
