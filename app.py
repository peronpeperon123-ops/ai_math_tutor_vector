import streamlit as st
import google.generativeai as genai
from PIL import Image
import os
import glob
from cryptography.fernet import Fernet

# パス設定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRANSCRIPTIONS_DIR = os.path.join(BASE_DIR, "transcriptions")

st.set_page_config(page_title="AI数学ティーチャー (平面ベクトル)", page_icon="🧑‍🏫", layout="wide")

st.title("🧑‍🏫 ぺろん＠灘卒 AI数学ティーチャー (平面ベクトル)")
st.markdown("平面ベクトルの問題をアップロードしてください。私の独自の指導ノウハウに基づく解く方針と、詳しい解説を提供します。")

# シークレットから各種設定を読み込む
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    app_password = st.secrets["APP_PASSWORD"]
    data_key = st.secrets["DATA_KEY"]
except Exception as e:
    st.error("設定エラー: .streamlit/secrets.tomlが見つからないか、環境変数が設定されていません。")
    st.stop()

if api_key:
    genai.configure(api_key=api_key)

# パスワード認証機能
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.info("🔒 このAIティーチャーはnoteメンバーシップ会員限定です。記事内に記載のパスワードを入力してください。")
        pwd = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            if pwd == app_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが間違っています。")
        return False
    return True

if not check_password():
    st.stop()

# 認証完了時：プライバシー免責事項
st.success("✅ **【プライバシー保護について】**\n\n入力された質問やアップロードされた画像は、サーバーに保存されることは一切ありません。ブラウザを閉じると履歴は完全に消去されます。また、入力データがGoogleのAI学習に利用されることもありませんので安心してお使いください。")

# (システム状態の表示は非公開のため削除)

# 知識ベース（暗号化された18個の文字起こしデータ）の読み込み
@st.cache_data
def load_knowledge_base():
    try:
        enc_path = os.path.join(BASE_DIR, "knowledge_base.enc")
        with open(enc_path, "rb") as f:
            encrypted_data = f.read()
        fernet = Fernet(data_key.encode('utf-8'))
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data.decode('utf-8'), 18
    except Exception as e:
        return "", 0

try:
    kb_text, count = load_knowledge_base()
    if count == 0:
        st.error("知識ベースが見つかりません、または復号キーが間違っています。")
        st.stop()
except Exception as e:
    st.error(f"知識ベース読み込みエラー: {e}")
    kb_text = ""
    st.stop()

# システムプロンプトの構築
system_instruction = f"""
あなたは「ぺろん＠灘卒」としての思考を持つ優秀なAI数学講師です。
以下の「平面ベクトル」に関する実際の授業の文字起こしデータを知識ベースとして深く理解し、生徒の質問や問題に対して、この授業の解法のエッセンスを踏まえて回答してください。

【語調・キャラクター設定の厳格なルール】
- 常に「です・ます」調を用いた、丁寧でわかりやすい敬語で解説してください。
- 文字起こしデータ内にある「〜するぜ！」「〜だろ？」といったフランクすぎる砕けた語尾や口調は絶対に真似せず、使用しないでください。プロ講師としての落ち着いた丁寧なトーンを必ず保つこと。

【情報漏洩・著作権保護の絶対ルール】
- 知識ベース内に含まれるファイル名、授業の管理タグ、見出し記号（例：「【H1 40 ベクトル（２） 1】」「J334」など）は、内部の機密情報です。
- いかなる場合でも、これらの内部タグやファイルの存在、出所をユーザーに絶対に明かさないでください。回答に含めることは固く禁じます。
- 「知識ベースによると」「ファイルに書いてある通り」などのメタ発言も控え、「私（AIチューター）のノウハウとして」自然に解説してください。

【知識ベース】
{kb_text}

【回答のルール】
ユーザーから数学の問題（テキストおよび画像）が提示されます。あなたは以下の2つのセクションに分けて、マークダウン形式でわかりやすく解説を提供してください。

【数式出力の厳格なルール】
- Streamlit 環境で正しく表示するため、独立した数式のブロックは必ず `$$` と `$$` で囲んでください。
- 文中の数式は必ず `$数式$` のように `$` で囲んでください。
- `\\begin{{cases}}` 等のLaTeXタグを使う際は、必ず `\\end{{cases}}` のように適切にペアで閉じてください。数式ブロックの途中で出力を切らないでください。

1. 【解く方針】 (Policy to solve)
   - 問題を解くための考え方、着眼点、使用する公式や定理をまず明らかにします。
   - 特に、知識ベース（授業の内容）で強調されているアプローチや考え出し方が適用できる場合は、それを取り入れて解説してください。
2. 【解答・解説】 (Solution and Explanation)
   - 方針に従って、ステップバイステップで丁寧な解答と解説を記述します。
   - 途中式を省かず、初学者でも理解できるように詳しく説明してください。解答の最後はわかりやすく結論をまとめること。
"""

# チャット状態の初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# 過去の会話を表示
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image" in msg:
            st.image(msg["image"], width=400)

# 画像アップローダーとテキスト入力
uploaded_file = st.file_uploader("問題の画像（あれば）をアップロード", type=["png", "jpg", "jpeg"])
user_input = st.chat_input("問題のテキストや質問を入力してください")

if user_input or uploaded_file:
    # ユーザー入力を構築
    content = []
    
    img = None
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        content.append(img)
    
    if user_input:
        content.append(user_input)
    else:
        content.append("この問題の解く方針と解答・解説をお願いします。")

    # ユーザーのメッセージを画面に表示＆保存
    user_msg_content = user_input if user_input else "（画像をアップロードして質問）"
    st.session_state.messages.append({"role": "user", "content": user_msg_content, **({"image": img} if img else {})})
    
    with st.chat_message("user"):
        st.markdown(user_msg_content)
        if img:
            st.image(img, width=400)

    # Gemini API リクエスト
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            # 最新の gemini-2.5-flash モデルを使用（数学的推論と精度に優れています）
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction
            )
            response = model.generate_content(content, stream=True)
            
            full_response = ""
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
            
            # アシスタントのメッセージを保存
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            st.error("入力が長すぎる、またはAPIの制限に達した可能性があります。")
