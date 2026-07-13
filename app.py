# ============================================================
# 【完全無料】Supabase プロンプト書き換え専用 Webダッシュボード
# ============================================================
# 必要なライブラリ： pip install streamlit supabase
import streamlit as st
from supabase import create_client, Client

# 1. Supabaseの接続情報（Streamlit Cloud の Settings > Secrets から読み込む）
#    Secretsには以下の形式で登録してください。
#    SUPABASE_URL = "https://iomqwzeifmyfrpvezojz.supabase.co"
#    SUPABASE_KEY = "（SupabaseのAPIキー）"
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

st.set_page_config(page_title="Bot Control Panel", layout="centered")
st.title("🤖 ゴリ押しBot プロンプト管理")

# 2. データベースから既存のBot一覧をシュッと取得
try:
    response = supabase.table("bots").select("id, bot_name, system_prompt").execute()
    bots_data = response.data
except Exception as e:
    st.error(f"データ取得エラー: {e}")
    bots_data = []

if bots_data:
    # スマホでも選びやすいセレクトボックス（Bot名の一覧）
    bot_options = {b["bot_name"]: b for b in bots_data}
    selected_bot_name = st.selectbox("書き換えるBotを選択:", list(bot_options.keys()))

    current_bot = bot_options[selected_bot_name]

    # 現在のプロンプトをテキストエリアに表示（ここで自由に編集）
    new_prompt = st.text_area(
        label="システムプロンプト（指示内容）:",
        value=current_bot.get("system_prompt", ""),
        height=300
    )

    # 3. 保存ボタンがポチッと押されたらSupabaseへUpdateをブチ込む
    if st.button("このプロンプトで確定（Supabaseへ保存）", type="primary"):
        try:
            supabase.table("bots").update({"system_prompt": new_prompt}).eq("id", current_bot["id"]).execute()
            st.success(f"🎉 {selected_bot_name} の脳みそを正常にハッキング（上書き）しました！")
            st.balloons()
        except Exception as e:
            st.error(f"保存に失敗しました: {e}")
else:
    st.warning("botsテーブルにレコードが見つかりません。")

# ============================================================
# 【インフラ配管】どうやってスマホからこれを開くの？
# ============================================================
# 1. オーナーのVPSサーバー（またはローカルPC）で上記のコードを `app.py` として保存する。
# 2. `streamlit run app.py` を実行して、ポート「8501」でWebアプリを着火。
# 3. いつもの「Cloudflare Tunnel（cloudflared）」を使って、適当なサブドメイン
#    （例: bot-panel.pages.dev 的なドメイン、または独自ドメイン）をポート8501に土管として繋ぐ。
# 4. スマホのブラウザからそのURLを開けば、いつでもどこでもワンタップでプロンプトの書き換えが完了！
