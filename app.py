# -*- coding: utf-8 -*-
import streamlit as st
import os
import base64
from datetime import datetime
import time

# インポート
from database import authenticate_user, create_user, get_user_by_id, update_user_profile
from database import get_all_users, delete_user, promote_to_admin, demote_from_admin
from database import create_admin_user, check_user_has_password, reset_user_password
from auth_utils import create_user_session, clear_user_session, get_current_user_id, is_authenticated, is_admin
from qr_utils import generate_user_qr_code, display_qr_code
from config import APP_CONFIG

# ページ設定
st.set_page_config(
    page_title=APP_CONFIG["page_title"],
    page_icon=APP_CONFIG["page_icon"],
    layout="wide"
)

def display_profile_image(image_data, caption="プロフィール写真", width=200):
    """プロフィール写真を安全に表示する"""
    if image_data:
        try:
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                st.image(image_data, caption=caption, width=width, use_container_width=True)
            elif isinstance(image_data, str) and image_data.startswith('http'):
                st.image(image_data, caption=caption, width=width, use_container_width=True)
            else:
                st.warning("画像データの形式が正しくありません")
        except Exception as e:
            st.error(f"画像表示エラー: {e}")
    else:
        st.info("プロフィール写真が設定されていません")

def main():
    """メイン関数"""
    st.title(APP_CONFIG["app_name"])
    
    # URLパラメータの確認
    user_id_param = st.query_params.get("user_id", None)
    
    if user_id_param:
        # 個別ユーザーページを表示
        show_public_user_page(user_id_param)
    else:
        # 通常のナビゲーション
        if is_authenticated():
            show_authenticated_navigation()
        else:
            show_unauthenticated_navigation()
        
        # メインコンテンツ
        if is_authenticated():
            show_main_content()
        else:
            show_login_register()

def show_authenticated_navigation():
    """認証済みユーザー用のナビゲーション"""
    st.sidebar.title("メニュー")
    
    if is_admin():
        st.sidebar.success("👑 管理者モード")
        page = st.sidebar.selectbox(
            "ページを選択",
            ["マイページ", "管理者パネル", "ログアウト"]
        )
    else:
        page = st.sidebar.selectbox(
            "ページを選択",
            ["マイページ", "プロフィール編集", "ログアウト"]
        )
    
    if page == "ログアウト":
        if st.sidebar.button("ログアウト"):
            clear_user_session()
            st.rerun()
    elif page == "管理者パネル" and is_admin():
        show_admin_panel()
    elif page == "プロフィール編集":
        show_profile_edit()
    else:
        show_mypage()

def show_unauthenticated_navigation():
    """未認証ユーザー用のナビゲーション"""
    st.sidebar.title("メニュー")
    page = st.sidebar.selectbox(
        "ページを選択",
        ["ログイン・新規登録"]
    )

def show_login_register():
    """ログイン・新規登録画面"""
    tab1, tab2 = st.tabs(["ログイン", "新規登録"])
    
    with tab1:
        show_login_form()
    
    with tab2:
        show_register_form()

def show_login_form():
    """ログインフォーム"""
    st.header("ログイン")
    
    # 管理者ログイン用のタブ
    login_tab, admin_tab = st.tabs(["一般ユーザー", "管理者"])
    
    with login_tab:
        with st.form("login_form"):
            email = st.text_input("メールアドレス")
            password = st.text_input("パスワード", type="password")
            submit = st.form_submit_button("ログイン")
            
            if submit:
                if email and password:
                    user, error = authenticate_user(email, password)
                    if user:
                        create_user_session(
                            user['user_id'],
                            user['email'],
                            user['display_name'],
                            user.get('is_admin', False)
                        )
                        st.success("ログインしました！")
                        if "show_login" in st.session_state:
                            del st.session_state.show_login
                        st.rerun()
                    else:
                        st.error(f"ログインエラー: {error}")
                else:
                    st.error("メールアドレスとパスワードを入力してください。")
    
    with admin_tab:
        st.info("管理者の方はこちらからログインしてください。")
        
        with st.form("admin_login_form"):
            admin_email = st.text_input("管理者メールアドレス")
            admin_password = st.text_input("管理者パスワード", type="password")
            admin_submit = st.form_submit_button("管理者ログイン")
            
            if admin_submit:
                if admin_email and admin_password:
                    user, error = authenticate_user(admin_email, admin_password)
                    if user and user.get('is_admin', False):
                        create_user_session(
                            user['user_id'],
                            user['email'],
                            user['display_name'],
                            True
                        )
                        st.success("管理者としてログインしました！")
                        st.rerun()
                    else:
                        st.error("管理者認証に失敗しました。")
                else:
                    st.error("メールアドレスとパスワードを入力してください。")

def show_register_form():
    """新規登録フォーム"""
    st.header("新規登録")
    
    with st.form("register_form"):
        email = st.text_input("メールアドレス")
        password = st.text_input("パスワード", type="password")
        confirm_password = st.text_input("パスワード（確認）", type="password")
        display_name = st.text_input("表示名")
        profile = st.text_area("プロフィール")
        interests = st.multiselect(
            "興味のあるジャンル",
            ["技術", "音楽", "スポーツ", "料理", "旅行", "アート", "ゲーム", "その他"]
        )
        
        # 写真アップロード
        uploaded_file = st.file_uploader("プロフィール写真", type=['png', 'jpg', 'jpeg'], key="register_photo")
        
        submit = st.form_submit_button("登録")
        
        if submit:
            if email and password and display_name:
                if password != confirm_password:
                    st.error("パスワードが一致しません。")
                    return
                
                if len(password) < 8:
                    st.error("パスワードは8文字以上で入力してください。")
                    return
                
                # 写真の処理
                photo_data = None
                if uploaded_file is not None:
                    try:
                        if uploaded_file.size > 5 * 1024 * 1024:
                            st.error("ファイルサイズは5MB以下にしてください。")
                            return
                        
                        photo_bytes = uploaded_file.read()
                        photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
                        photo_data = f"data:image/{uploaded_file.type};base64,{photo_base64}"
                        st.success("写真がアップロードされました")
                    except Exception as e:
                        st.error(f"❌ 写真のアップロードに失敗しました: {e}")
                        return
                
                # ユーザーデータを準備
                user_data = {
                    'email': email,
                    'password': password,
                    'display_name': display_name,
                    'profile': profile,
                    'interests': interests,
                    'photo': photo_data
                }
                
                # ユーザーを作成
                user_id, error = create_user(user_data)
                if user_id:
                    st.success("登録が完了しました！")
                    st.balloons()
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error(f"登録エラー: {error}")
            else:
                st.error("必須項目を入力してください。")

def show_main_content():
    """メインコンテンツ"""
    st.success("ログインしました！")

def show_mypage():
    """マイページ"""
    st.header("マイページ")
    
    user_id = get_current_user_id()
    user = get_user_by_id(user_id)
    
    if user:
        # プロフィール情報
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("プロフィール写真")
            if user.get('photo'):
                display_profile_image(user['photo'], "プロフィール写真", 200)
            else:
                st.info("プロフィール写真が設定されていません")
        
        with col2:
            st.subheader("基本情報")
            st.write(f"**表示名:** {user.get('display_name', '未設定')}")
            st.write(f"**メールアドレス:** {user.get('email', '未設定')}")
            st.write(f"**プロフィール:** {user.get('profile', '未設定')}")
            
            if user.get('interests'):
                st.write("**興味のあるジャンル:**")
                for interest in user['interests']:
                    st.write(f"• {interest}")
        
        # QRコード
        st.subheader("QRコード")
        qr_code = generate_user_qr_code(user_id)
        if qr_code:
            display_qr_code(qr_code, f"{user.get('display_name', 'ユーザー')}のQRコード")
            st.info(f"このQRコードを読み取ると、あなたの公開ページにアクセスできます")
        else:
            st.error("QRコードの生成に失敗しました")
        
        # 友達リスト
        st.subheader("友達リスト")
        friends = user.get('friends', [])
        if friends:
            for friend_id in friends:
                friend = get_user_by_id(friend_id)
                if friend:
                    col_friend1, col_friend2 = st.columns([3, 1])
                    with col_friend1:
                        st.write(f"• **{friend.get('display_name', 'Unknown')}** ({friend.get('email', 'No email')})")
                        if st.button(f"👤 公開ページを見る", key=f"view_friend_{friend_id}"):
                            st.query_params["user_id"] = friend_id
                            st.rerun()
                    with col_friend2:
                        if st.button(f"❌ 友達削除", key=f"remove_friend_{friend_id}"):
                            if 'friends' in user:
                                user['friends'].remove(friend_id)
                                update_user_profile(user_id, {'friends': user['friends']})
                                st.success("友達を削除しました")
                                st.rerun()
        else:
            st.info("友達がいません。他のユーザーのQRコードを読み取って友達になりましょう！")
    else:
        st.error("ユーザー情報の取得に失敗しました")

def show_profile_edit():
    """プロフィール編集"""
    st.header("プロフィール編集")
    
    user_id = get_current_user_id()
    user = get_user_by_id(user_id)
    
    if user:
        with st.form("profile_edit_form"):
            new_display_name = st.text_input("表示名", value=user.get('display_name', ''))
            new_profile = st.text_area("プロフィール", value=user.get('profile', ''))
            new_interests = st.multiselect(
                "興味のあるジャンル",
                ["技術", "音楽", "スポーツ", "料理", "旅行", "アート", "ゲーム", "その他"],
                default=user.get('interests', [])
            )
            
            # 写真アップロード
            uploaded_file = st.file_uploader("プロフィール写真", type=['png', 'jpg', 'jpeg'], key="edit_photo")
            
            submit = st.form_submit_button("更新")
            
            if submit:
                update_data = {
                    'display_name': new_display_name,
                    'profile': new_profile,
                    'interests': new_interests
                }
                
                # 写真の処理
                if uploaded_file is not None:
                    try:
                        if uploaded_file.size > 5 * 1024 * 1024:
                            st.error("ファイルサイズは5MB以下にしてください。")
                            return
                        
                        photo_bytes = uploaded_file.read()
                        photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')
                        photo_data = f"data:image/{uploaded_file.type};base64,{photo_base64}"
                        update_data['photo'] = photo_data
                        st.success("写真がアップロードされました")
                    except Exception as e:
                        st.error(f"❌ 写真のアップロードに失敗しました: {e}")
                        return
                
                success, error = update_user_profile(user_id, update_data)
                if success:
                    st.success("プロフィールを更新しました！")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"更新エラー: {error}")
    else:
        st.error("ユーザー情報の取得に失敗しました")

def show_admin_panel():
    """管理者パネル"""
    st.header("👑 管理者パネル")
    
    # 管理者ユーザー作成
    st.subheader("管理者ユーザー作成")
    with st.form("create_admin_form"):
        admin_email = st.text_input("管理者メールアドレス")
        admin_password = st.text_input("管理者パスワード", type="password")
        admin_display_name = st.text_input("表示名")
        submit_admin = st.form_submit_button("管理者ユーザー作成")
        
        if submit_admin:
            if admin_email and admin_password and admin_display_name:
                if len(admin_password) < 8:
                    st.error("パスワードは8文字以上で入力してください。")
                else:
                    user_id, error = create_admin_user(admin_email, admin_password, admin_display_name)
                    if user_id:
                        st.success("管理者ユーザーを作成しました！")
                        st.balloons()
                    else:
                        st.error(f"管理者ユーザー作成エラー: {error}")
            else:
                st.error("すべての項目を入力してください。")
    
    # ユーザー管理
    st.subheader("ユーザー管理")
    users = get_all_users()
    
    if users:
        for user in users:
            with st.expander(f"👤 {user.get('display_name', 'Unknown')} ({user.get('email', 'No email')})"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**ユーザーID:** {user.get('user_id', 'Unknown')}")
                    st.write(f"**管理者:** {'✅' if user.get('is_admin', False) else '❌'}")
                    st.write(f"**登録日:** {user.get('created_at', 'Unknown')}")
                
                with col2:
                    if user.get('is_admin', False):
                        if st.button("👤 一般ユーザーに変更", key=f"demote_{user['user_id']}"):
                            success, error = demote_from_admin(user['user_id'])
                            if success:
                                st.success("一般ユーザーに変更しました")
                                st.rerun()
                            else:
                                st.error(f"変更エラー: {error}")
                    else:
                        if st.button("👑 管理者に昇格", key=f"promote_{user['user_id']}"):
                            success, error = promote_to_admin(user['user_id'])
                            if success:
                                st.success("管理者に昇格しました")
                                st.rerun()
                            else:
                                st.error(f"昇格エラー: {error}")
                
                with col3:
                    if st.button("❌ 削除", key=f"delete_{user['user_id']}"):
                        if st.checkbox(f"本当に {user.get('display_name', 'Unknown')} を削除しますか？"):
                            success, error = delete_user(user['user_id'])
                            if success:
                                st.success("ユーザーを削除しました")
                                st.rerun()
                            else:
                                st.error(f"削除エラー: {error}")
                
                # パスワードリセット
                if check_user_has_password(user['user_id']):
                    st.info("このユーザーはパスワードを設定済みです")
                else:
                    st.warning("このユーザーはパスワードを設定していません")
                    with st.form(f"reset_password_{user['user_id']}"):
                        new_password = st.text_input("新しいパスワード", type="password", key=f"new_pass_{user['user_id']}")
                        confirm_password = st.text_input("パスワード確認", type="password", key=f"confirm_pass_{user['user_id']}")
                        reset_submit = st.form_submit_button("パスワードリセット")
                        
                        if reset_submit:
                            if not new_password or not confirm_password:
                                st.error("新しいパスワードと確認パスワードを入力してください")
                            elif new_password != confirm_password:
                                st.error("パスワードが一致しません")
                            elif len(new_password) < 8:
                                st.error("パスワードは8文字以上で入力してください")
                            else:
                                st.info("パスワードリセット処理を開始します...")
                                
                                success, error = reset_user_password(user['user_id'], new_password)
                                
                                if success:
                                    st.success("✅ パスワードをリセットしました！")
                                    st.info("新しいパスワードでログインできるようになりました。")
                                    st.balloons()
                                    time.sleep(3)
                                    st.rerun()
                                else:
                                    st.error(f"❌ パスワードリセットエラー: {error}")
    else:
        st.info("ユーザーが見つかりません")

def show_user_edit_form(user):
    """ユーザー編集フォーム"""
    st.subheader(f"ユーザー編集: {user.get('display_name', 'Unknown')}")
    
    with st.form(f"user_edit_{user['user_id']}"):
        new_display_name = st.text_input("表示名", value=user.get('display_name', ''))
        new_profile = st.text_area("プロフィール", value=user.get('profile', ''))
        new_interests = st.multiselect(
            "興味のあるジャンル",
            ["技術", "音楽", "スポーツ", "料理", "旅行", "アート", "ゲーム", "その他"],
            default=user.get('interests', [])
        )
        
        submit = st.form_submit_button("更新")
        
        if submit:
            update_data = {
                'display_name': new_display_name,
                'profile': new_profile,
                'interests': new_interests
            }
            
            success, error = update_user_profile(user['user_id'], update_data)
            if success:
                st.success("ユーザー情報を更新しました！")
                st.rerun()
            else:
                st.error(f"更新エラー: {error}")

def show_public_user_page(user_id):
    """公開ユーザーページ"""
    user = get_user_by_id(user_id)
    
    if user:
        st.header(f"👤 {user.get('display_name', 'ユーザー')}のプロフィール")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("プロフィール写真")
            if user.get('photo'):
                display_profile_image(user['photo'], "プロフィール写真", 200)
            else:
                st.info("プロフィール写真が設定されていません")
        
        with col2:
            st.subheader("基本情報")
            st.write(f"**表示名:** {user.get('display_name', '未設定')}")
            st.write(f"**プロフィール:** {user.get('profile', '未設定')}")
            
            if user.get('interests'):
                st.write("**興味のあるジャンル:**")
                for interest in user['interests']:
                    st.write(f"• {interest}")
        
        # 友達機能
        if is_authenticated():
            current_user_id = get_current_user_id()
            if current_user_id != user_id:
                current_user = get_user_by_id(current_user_id)
                if current_user:
                    friends = current_user.get('friends', [])
                    
                    if user_id in friends:
                        st.success("✅ 既に友達です")
                        if st.button("❌ 友達削除", key=f"remove_friend_{user_id}"):
                            friends.remove(user_id)
                            update_user_profile(current_user_id, {'friends': friends})
                            st.success("友達を削除しました")
                            st.rerun()
                    else:
                        if st.button("🤝 友達になる", key=f"add_friend_{user_id}"):
                            if 'friends' not in current_user:
                                current_user['friends'] = []
                            current_user['friends'].append(user_id)
                            update_user_profile(current_user_id, {'friends': current_user['friends']})
                            
                            st.session_state.friend_added = True
                            st.success("友達になりました！")
                            st.rerun()
            else:
                st.info("これはあなたのプロフィールです")
        else:
            st.info("ログインすると友達機能が利用できます")
            if st.button("🔐 ログイン"):
                st.session_state.show_login = True
                st.rerun()
        
        if st.button("🏠 メインページへ戻る"):
            st.query_params.clear()
            st.rerun()
        
        if st.session_state.get('friend_added', False):
            st.success("🎉 友達になりました！")
            st.info("友達リストに追加されました")
            if st.button("🏠 メインページへ戻る"):
                st.session_state.return_to_main = True
                st.query_params.clear()
                st.rerun()
    else:
        st.error("ユーザーが見つかりません")
        
        if st.button("🏠 メインページへ戻る"):
            st.query_params.clear()
            st.rerun()

if __name__ == "__main__":
    main()
