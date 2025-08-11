"""
最初の管理者ユーザーを作成するスクリプト
このスクリプトを実行して、システムの最初の管理者ユーザーを作成してください。
"""

import streamlit as st
from config import initialize_firebase
from database import create_admin_user

def create_first_admin():
    """最初の管理者ユーザーを作成する"""
    st.title("最初の管理者ユーザー作成")
    st.warning("⚠️ このスクリプトは最初の管理者ユーザーを作成するためにのみ使用してください。")
    
    # Firebase初期化
    if not initialize_firebase():
        st.error("Firebaseの初期化に失敗しました。")
        return
    
    with st.form("first_admin_form"):
        st.subheader("管理者情報を入力")
        
        email = st.text_input("メールアドレス", placeholder="admin@example.com")
        password = st.text_input("パスワード", type="password")
        confirm_password = st.text_input("パスワード（確認）", type="password")
        display_name = st.text_input("表示名", placeholder="システム管理者")
        profile = st.text_area("プロフィール", placeholder="システムの管理者です")
        interests = st.multiselect(
            "興味のあるジャンル",
            ["技術", "音楽", "スポーツ", "料理", "旅行", "アート", "ゲーム", "その他"]
        )
        
        st.info("注意: このスクリプトは一度だけ実行してください。")
        submit = st.form_submit_button("管理者ユーザーを作成")
        
        if submit:
            if email and password and display_name:
                if password != confirm_password:
                    st.error("パスワードが一致しません。")
                    return
                
                # 管理者ユーザーデータを準備
                admin_data = {
                    'email': email,
                    'password': password,
                    'display_name': display_name,
                    'profile': profile,
                    'interests': interests
                }
                
                # 管理者ユーザーを作成
                user_id, error = create_admin_user(admin_data)
                if user_id:
                    st.success(f"管理者ユーザーを作成しました！")
                    st.info(f"ユーザーID: {user_id}")
                    st.info(f"メールアドレス: {email}")
                    st.info("このスクリプトは削除して、通常のログイン画面から管理者としてログインしてください。")
                else:
                    st.error(f"作成エラー: {error}")
            else:
                st.error("メールアドレス、パスワード、表示名は必須です。")

if __name__ == "__main__":
    create_first_admin()
