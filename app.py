import streamlit as st
from config import initialize_firebase, APP_CONFIG
from auth_utils import *
from database import *
from qr_utils import *
import os
import time

def display_profile_image(image_data, caption="プロフィール写真", width=200):
    """プロフィール画像を安全に表示する"""
    try:
        if image_data:
            if image_data.startswith('data:image'):
                # base64エンコードされた画像
                st.image(image_data, caption=caption, use_container_width=True, width=width)
            elif image_data.startswith('http'):
                # URLの画像
                st.image(image_data, caption=caption, use_container_width=True, width=width)
            else:
                # その他の形式
                st.image(image_data, caption=caption, use_container_width=True, width=width)
        else:
            # デフォルト画像
            st.image("https://via.placeholder.com/200x200?text=No+Photo", 
                    caption="プロフィール写真なし", use_container_width=True, width=width)
    except Exception as e:
        st.error(f"画像の表示に失敗しました: {e}")
        # エラー時はデフォルト画像を表示
        st.image("https://via.placeholder.com/200x200?text=Error", 
                caption="画像表示エラー", use_container_width=True, width=width)

# ページ設定
st.set_page_config(
    page_title=APP_CONFIG["page_title"],
    page_icon=APP_CONFIG["page_icon"],
    layout="wide"
)

# Firebase初期化
if not initialize_firebase():
    st.error("Firebaseの初期化に失敗しました。設定を確認してください。")
    st.stop()

# セッション状態の初期化
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def main():
    st.title(APP_CONFIG["app_name"])
    
    # セッション状態でログイン画面の表示を制御
    if st.session_state.get("show_login", False):
        # ログイン画面を表示
        show_login_register()
        return
    
    # メインページに戻るフラグの処理
    if st.session_state.get("return_to_main", False):
        # フラグをクリア
        del st.session_state.return_to_main
        # 通常のナビゲーションを表示
        if is_authenticated():
            show_authenticated_navigation()
        else:
            show_unauthenticated_navigation()
        
        # メインコンテンツ
        if is_authenticated():
            show_main_content()
        else:
            show_login_register()
        return
    
    # URLパラメータでユーザーIDをチェック
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
                    # 新しい認証システムを使用
                    user, error = authenticate_user(email, password)
                    if user:
                        # 認証成功
                        create_user_session(
                            user['user_id'],
                            user['email'],
                            user['display_name'],
                            user.get('is_admin', False)
                        )
                        st.success("ログインしました！")
                        # ログイン画面表示フラグをリセット
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
                    # 新しい認証システムを使用
                    user, error = authenticate_user(admin_email, admin_password)
                    if user and user.get('is_admin', False):
                        # 管理者としてセッションを作成
                        create_user_session(
                            user['user_id'],
                            user['email'],
                            user['display_name'],
                            True  # 管理者フラグをTrueに設定
                        )
                        st.success("管理者としてログインしました！")
                        st.rerun()
                    elif user and not user.get('is_admin', False):
                        st.error("このアカウントは管理者権限がありません。")
                    else:
                        st.error(f"ログインエラー: {error}")
                else:
                    st.error("管理者メールアドレスとパスワードを入力してください。")

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
        uploaded_photo = st.file_uploader(
            "プロフィール写真（オプション）", 
            type=['png', 'jpg', 'jpeg'], 
            help="PNG、JPG、JPEG形式の画像をアップロードできます。推奨サイズ: 200x200px以上、最大5MB"
        )
        
        # アップロードされた写真のプレビュー
        if uploaded_photo is not None:
            st.image(uploaded_photo, caption="アップロードされた写真", width=200)
            st.info("📸 写真がアップロードされました")
        
        # 写真URL（オプション）
        photo_url = st.text_input("写真URL（オプション）", help="画像をアップロードするか、URLを直接入力してください")
        
        # SNSアカウント
        st.subheader("SNSアカウント（オプション）")
        twitter = st.text_input("Twitter")
        instagram = st.text_input("Instagram")
        facebook = st.text_input("Facebook")
        
        submit = st.form_submit_button("登録")
        
        if submit:
            if email and password and display_name:
                if password != confirm_password:
                    st.error("パスワードが一致しません。")
                    return
                
                # アップロードされた写真をbase64に変換
                final_photo_url = photo_url
                if uploaded_photo is not None:
                    try:
                        # ファイルサイズチェック（5MB制限）
                        file_size = len(uploaded_photo.getvalue())
                        max_size = 5 * 1024 * 1024  # 5MB
                        
                        if file_size > max_size:
                            st.error(f"❌ ファイルサイズが大きすぎます。5MB以下のファイルを選択してください。（現在: {file_size / (1024*1024):.1f}MB）")
                            return
                        
                        # 画像をbase64エンコード
                        import base64
                        from io import BytesIO
                        
                        # 画像を読み込み
                        image = uploaded_photo.read()
                        image_base64 = base64.b64encode(image).decode()
                        
                        # MIMEタイプを取得
                        file_extension = uploaded_photo.name.split('.')[-1].lower()
                        mime_type = f"image/{file_extension}"
                        if file_extension == 'jpg':
                            mime_type = "image/jpeg"
                        
                        # data URL形式で保存
                        final_photo_url = f"data:{mime_type};base64,{image_base64}"
                        
                        st.success("📸 写真が正常にアップロードされました！")
                        
                        # アップロードされた写真がある場合は、URL入力を無視
                        if photo_url:
                            st.info("ℹ️ アップロードされた写真が優先されます。URL入力は無視されました。")
                    except Exception as e:
                        st.error(f"❌ 写真のアップロードに失敗しました: {e}")
                        return
                
                # ユーザーデータを準備
                user_data = {
                    'email': email,
                    'password': password,  # パスワードを追加
                    'display_name': display_name,
                    'profile': profile,
                    'interests': interests,
                    'photo_url': final_photo_url,
                    'sns_accounts': {
                        'twitter': twitter,
                        'instagram': instagram,
                        'facebook': facebook
                    }
                }
                
                # ユーザーを作成
                user_id, error = create_user(user_data)
                if user_id:
                    st.success("登録が完了しました！ログインしてください。")
                    st.rerun()
                else:
                    st.error(f"登録エラー: {error}")
            else:
                st.error("必須項目を入力してください。")

def show_main_content():
    """メインコンテンツ"""
    if is_admin():
        st.success("管理者としてログインしています")
    else:
        st.success(f"ようこそ、{st.session_state.display_name}さん！")

def show_mypage():
    """マイページ表示"""
    st.header("マイページ")
    
    user_id = get_current_user_id()
    user = get_user_by_id(user_id)
    
    if user:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            display_profile_image(user.get('photo_url'), "プロフィール写真", 200)
            
            # QRコード生成
            # 設定ファイルからbase_urlを取得、失敗時はデフォルト値を使用
            try:
                if hasattr(APP_CONFIG, 'get') and callable(getattr(APP_CONFIG, 'get')):
                    base_url = APP_CONFIG.get("base_url", "https://mypage-001.streamlit.app")
                else:
                    base_url = "https://mypage-001.streamlit.app"
            except Exception as e:
                base_url = "https://mypage-001.streamlit.app"
            
            qr_code = generate_user_qr_code(user_id, base_url)
            
            if qr_code:
                # QRコードを直接表示
                st.subheader("マイページQRコード")
                st.image(qr_code, caption="マイページQRコード", use_container_width=True, width=200)
                
                # QRコードのURLも表示
                qr_url = f"{base_url}/?user_id={user_id}"
                st.write(f"**QRコードのURL:** {qr_url}")
                st.write(f"**マイページアクセス方法:** このQRコードをスキャンすると、あなたの公開用マイページに直接アクセスできます。他のユーザーもこのQRコードであなたのプロフィールを見ることができます。")
                
                # ダウンロードボタン
                download_qr_code_button(qr_code, f"qr_{user_id}.png", "QRコードをダウンロード")
            else:
                st.error("QRコードの生成に失敗しました")
        
        with col2:
            st.subheader("基本情報")
            st.write(f"**ID:** {user['user_id']}")
            st.write(f"**メールアドレス:** {user['email']}")
            st.write(f"**表示名:** {user['display_name']}")
            
            st.subheader("プロフィール")
            st.write(user.get('profile', 'プロフィールが設定されていません。'))
            
            st.subheader("興味のあるジャンル")
            interests = user.get('interests', [])
            if interests:
                for interest in interests:
                    st.write(f"• {interest}")
            else:
                st.write("興味のあるジャンルが設定されていません。")
            
            st.subheader("SNSアカウント")
            sns_accounts = user.get('sns_accounts', {})
            if sns_accounts:
                for platform, account in sns_accounts.items():
                    if account:
                        st.write(f"**{platform.title()}:** {account}")
            else:
                st.write("SNSアカウントが設定されていません。")
            
            # 友達リスト
            st.subheader("👥 友達リスト")
            friends = user.get('friends', [])
            if friends:
                st.write(f"**友達数:** {len(friends)}人")
                for friend_id in friends:
                    friend = get_user_by_id(friend_id)
                    if friend:
                        friend_url = f"{base_url}/?user_id={friend_id}"
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"• [{friend.get('display_name', 'Unknown')}]({friend_url})")
                        with col2:
                            if st.button(f"削除", key=f"remove_friend_{friend_id}"):
                                # 友達リストから削除
                                friends.remove(friend_id)
                                update_data = {'friends': friends}
                                success, error = update_user(user_id, update_data)
                                if success:
                                    st.success("友達を削除しました")
                                    st.rerun()
                                else:
                                    st.error(f"削除エラー: {error}")
            else:
                st.info("友達がいません。他のユーザーの公開マイページで「友達になる」ボタンを押して友達を追加してください。")

def show_profile_edit():
    """プロフィール編集画面"""
    st.header("プロフィール編集")
    
    user_id = get_current_user_id()
    user = get_user_by_id(user_id)
    
    if user:
        with st.form("profile_edit_form"):
            display_name = st.text_input("表示名", value=user.get('display_name', ''))
            profile = st.text_area("プロフィール", value=user.get('profile', ''))
            interests = st.multiselect(
                "興味のあるジャンル",
                ["技術", "音楽", "スポーツ", "料理", "旅行", "アート", "ゲーム", "その他"],
                default=user.get('interests', [])
            )
            # プロフィール写真のアップロード
            st.subheader("プロフィール写真")
            
            # 現在の写真を表示
            display_profile_image(user.get('photo_url'), "現在の写真", 200)
            
            # ファイルアップローダー
            uploaded_file = st.file_uploader(
                "新しい写真をアップロード",
                type=['png', 'jpg', 'jpeg', 'gif'],
                help="PNG, JPG, JPEG, GIF形式のファイルをアップロードできます"
            )
            
            # アップロードされたファイルを処理
            photo_url = user.get('photo_url', '')
            if uploaded_file is not None:
                # ファイルを一時的に保存してURLを取得
                try:
                    # ファイルの内容を取得
                    file_content = uploaded_file.read()
                    file_name = uploaded_file.name
                    
                    # ファイルの拡張子を取得
                    file_extension = file_name.split('.')[-1].lower()
                    
                    # プレビュー表示
                    st.image(file_content, caption="アップロードされた写真", use_container_width=True, width=200)
                    
                    # ファイルをbase64エンコードして保存（簡易的な実装）
                    import base64
                    photo_url = f"data:image/{file_extension};base64,{base64.b64encode(file_content).decode()}"
                    
                    st.success(f"写真がアップロードされました: {file_name}")
                except Exception as e:
                    st.error(f"写真のアップロードに失敗しました: {e}")
                    photo_url = user.get('photo_url', '')
            
            st.subheader("SNSアカウント")
            sns_accounts = user.get('sns_accounts', {})
            twitter = st.text_input("Twitter", value=sns_accounts.get('twitter', ''))
            instagram = st.text_input("Instagram", value=sns_accounts.get('instagram', ''))
            facebook = st.text_input("Facebook", value=sns_accounts.get('facebook', ''))
            
            submit = st.form_submit_button("更新")
            
            if submit:
                update_data = {
                    'display_name': display_name,
                    'profile': profile,
                    'interests': interests,
                    'photo_url': photo_url,
                    'sns_accounts': {
                        'twitter': twitter,
                        'instagram': instagram,
                        'facebook': facebook
                    }
                }
                
                success, error = update_user(user_id, update_data)
                if success:
                    st.success("プロフィールを更新しました！")
                    # セッション情報も更新
                    st.session_state.display_name = display_name
                    st.rerun()
                else:
                    st.error(f"更新エラー: {error}")

def show_admin_panel():
    """管理者パネル"""
    st.header("管理者パネル")
    
    if not is_admin():
        st.error("管理者権限が必要です。")
        return
    
    # 管理者機能のタブ
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["ユーザー一覧", "ユーザー管理", "新規管理者作成"])
    
    with admin_tab1:
        # ユーザー一覧
        st.subheader("ユーザー一覧")
        users = get_all_users()
        
        if users:
            for user in users:
                with st.expander(f"{user['display_name']} ({user['email']})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**ID:** {user['user_id']}")
                        st.write(f"**プロフィール:** {user.get('profile', '')}")
                        st.write(f"**興味:** {', '.join(user.get('interests', []))}")
                        st.write(f"**登録日:** {user.get('created_at', '')}")
                        if user.get('is_admin', False):
                            st.success("👑 管理者")
                        else:
                            st.info("一般ユーザー")
                    
                    with col2:
                        if st.button(f"編集 {user['user_id']}", key=f"edit_{user['user_id']}"):
                            show_user_edit_form(user)
                        
                        # 削除確認の状態管理
                        delete_key = f"delete_{user['user_id']}"
                        confirm_key = f"confirm_delete_{user['user_id']}"
                        
                        if delete_key not in st.session_state:
                            st.session_state[delete_key] = False
                        
                        if st.session_state[delete_key]:
                            # 削除確認モード
                            st.warning(f"⚠️ ユーザー '{user['display_name']}' を削除しますか？")
                            col_confirm1, col_confirm2 = st.columns(2)
                            
                            with col_confirm1:
                                if st.button("✅ 削除する", key=f"yes_delete_{user['user_id']}"):
                                    success, error = delete_user(user['user_id'])
                                    if success:
                                        st.success("ユーザーを削除しました。")
                                        # セッション状態をクリア
                                        del st.session_state[delete_key]
                                        st.rerun()
                                    else:
                                        st.error(f"削除エラー: {error}")
                            
                            with col_confirm2:
                                if st.button("❌ キャンセル", key=f"cancel_delete_{user['user_id']}"):
                                    st.session_state[delete_key] = False
                                    st.rerun()
                        else:
                            # 通常の削除ボタン
                            if st.button(f"🗑️ 削除", key=f"delete_btn_{user['user_id']}"):
                                st.session_state[delete_key] = True
                                st.rerun()
        else:
            st.info("ユーザーが登録されていません。")
    
    with admin_tab2:
        # ユーザー管理
        st.subheader("ユーザー権限管理")
        users = get_all_users()
        
        if users:
            for user in users:
                if user['user_id'] != get_current_user_id():  # 自分自身は除外
                    with st.expander(f"{user['display_name']} ({user['email']})"):
                        current_admin_status = user.get('is_admin', False)
                        st.write(f"**現在の権限:** {'管理者' if current_admin_status else '一般ユーザー'}")
                        
                        if current_admin_status:
                            if st.button(f"管理者権限を削除 {user['user_id']}", key=f"demote_{user['user_id']}"):
                                success, error = demote_from_admin(user['user_id'])
                                if success:
                                    st.success("管理者権限を削除しました。")
                                    st.rerun()
                                else:
                                    st.error(f"権限削除エラー: {error}")
                        else:
                            if st.button(f"管理者に昇格 {user['user_id']}", key=f"promote_{user['user_id']}"):
                                success, error = promote_to_admin(user['user_id'])
                                if success:
                                    st.success("管理者に昇格しました。")
                                    st.rerun()
                                else:
                                    st.error(f"昇格エラー: {error}")
        else:
            st.info("ユーザーが登録されていません。")
    
    with admin_tab3:
        # 新規管理者作成
        st.subheader("新規管理者作成")
        st.info("新しい管理者ユーザーを作成します。")
        
        with st.form("create_admin_form"):
            admin_email = st.text_input("メールアドレス")
            admin_password = st.text_input("パスワード", type="password")
            admin_confirm_password = st.text_input("パスワード（確認）", type="password")
            admin_display_name = st.text_input("表示名")
            admin_profile = st.text_area("プロフィール")
            admin_interests = st.multiselect(
                "興味のあるジャンル",
                ["技術", "音楽", "スポーツ", "料理", "旅行", "アート", "ゲーム", "その他"]
            )
            
            submit = st.form_submit_button("管理者ユーザーを作成")
            
            if submit:
                if admin_email and admin_password and admin_display_name:
                    if admin_password != admin_confirm_password:
                        st.error("パスワードが一致しません。")
                        return
                    
                    # 管理者ユーザーデータを準備
                    admin_data = {
                        'email': admin_email,
                        'password': admin_password,  # パスワードを追加
                        'display_name': admin_display_name,
                        'profile': admin_profile,
                        'interests': admin_interests
                    }
                    
                    # 管理者ユーザーを作成
                    user_id, error = create_admin_user(admin_data)
                    if user_id:
                        st.success("管理者ユーザーを作成しました！")
                        st.rerun()
                    else:
                        st.error(f"作成エラー: {error}")
                else:
                    st.error("必須項目を入力してください。")

def show_user_edit_form(user):
    """ユーザー編集フォーム（管理者用）"""
    st.subheader(f"ユーザー編集: {user['display_name']}")
    
    # パスワードリセットセクション
    with st.expander("パスワードリセット"):
        st.info("ユーザーのパスワードをリセットできます。")
        with st.form(f"password_reset_{user['user_id']}"):
            new_password = st.text_input("新しいパスワード", type="password")
            confirm_password = st.text_input("新しいパスワード（確認）", type="password")
            reset_submit = st.form_submit_button("パスワードをリセット")
            
            if reset_submit:
                if new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("パスワードが一致しません。")
                    else:
                        success, error = reset_user_password(user['user_id'], new_password)
                        if success:
                            st.success("パスワードをリセットしました！")
                        else:
                            st.error(f"パスワードリセットエラー: {error}")
                else:
                    st.error("新しいパスワードを入力してください。")
    
    # 通常のユーザー編集フォーム
    with st.form(f"admin_user_edit_{user['user_id']}"):
        display_name = st.text_input("表示名", value=user.get('display_name', ''))
        profile = st.text_area("プロフィール", value=user.get('profile', ''))
        interests = st.multiselect(
            "興味のあるジャンル",
            ["技術", "音楽", "スポーツ", "料理", "旅行", "アート", "ゲーム", "その他"],
            default=user.get('interests', [])
        )
        photo_url = st.text_input("写真URL", value=user.get('photo_url', ''))
        is_admin = st.checkbox("管理者権限", value=user.get('is_admin', False))
        
        st.subheader("SNSアカウント")
        sns_accounts = user.get('sns_accounts', {})
        twitter = st.text_input("Twitter", value=sns_accounts.get('twitter', ''))
        instagram = st.text_input("Instagram", value=sns_accounts.get('instagram', ''))
        facebook = st.text_input("Facebook", value=sns_accounts.get('facebook', ''))
        
        submit = st.form_submit_button("更新")
        
        if submit:
            update_data = {
                'display_name': display_name,
                'profile': profile,
                'interests': interests,
                'photo_url': photo_url,
                'is_admin': is_admin,
                'sns_accounts': {
                    'twitter': twitter,
                    'instagram': instagram,
                    'facebook': facebook
                }
            }
            
            success, error = update_user(user['user_id'], update_data)
            if success:
                st.success("ユーザー情報を更新しました！")
                st.rerun()
            else:
                st.error(f"更新エラー: {error}")

def show_public_user_page(user_id):
    """ユーザーの公開用マイページを表示"""
    st.header("ユーザープロフィール")
    
    # ユーザー情報を取得
    user = get_user_by_id(user_id)
    
    if not user:
        st.error("ユーザーが見つかりません")
        return
    
    # 公開用の情報のみ表示
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # プロフィール写真
        if user.get('photo_url'):
            display_profile_image(user.get('photo_url'), "プロフィール写真", 200)
        else:
            st.image("https://via.placeholder.com/200x200?text=No+Photo", 
                    caption="プロフィール写真なし", use_container_width=True, width=200)
    
    with col2:
        st.subheader("基本情報")
        st.write(f"**表示名:** {user.get('display_name', '未設定')}")
        
        st.subheader("プロフィール")
        st.write(user.get('profile', 'プロフィールが設定されていません。'))
        
        st.subheader("興味のあるジャンル")
        interests = user.get('interests', [])
        if interests:
            for interest in interests:
                st.write(f"• {interest}")
        else:
            st.write("興味のあるジャンルが設定されていません。")
        
        st.subheader("SNSアカウント")
        sns_accounts = user.get('sns_accounts', {})
        if sns_accounts:
            for platform, account in sns_accounts.items():
                if account:
                    st.write(f"**{platform.title()}:** {account}")
        else:
            st.write("SNSアカウントが設定されていません。")
    
    # 友達になるボタン（ログイン済みユーザーのみ表示）
    st.subheader("友達機能")
    
    # デバッグ情報（一時的）
    st.write(f"**デバッグ情報:**")
    st.write(f"  ログイン状態: {is_authenticated()}")
    if is_authenticated():
        current_user_id = get_current_user_id()
        st.write(f"  現在のユーザーID: {current_user_id}")
        st.write(f"  表示中のユーザーID: {user_id}")
        st.write(f"  自分自身か: {current_user_id == user_id}")
    
    if is_authenticated():
        current_user_id = get_current_user_id()
        if current_user_id != user_id:  # 自分自身は友達になれない
            # 既に友達かどうかチェック
            current_user = get_user_by_id(current_user_id)
            friends = current_user.get('friends', [])
            
            # 友達追加後のメッセージ表示
            if st.session_state.get("friend_added", False):
                st.success("友達になりました！")
                del st.session_state.friend_added
            
            if user_id in friends:
                st.success("✓ 既に友達です")
                if st.button("友達を削除"):
                    # 友達リストから削除
                    friends.remove(user_id)
                    update_data = {'friends': friends}
                    success, error = update_user(current_user_id, update_data)
                    if success:
                        st.success("友達を削除しました")
                        st.rerun()
                    else:
                        st.error(f"削除エラー: {error}")
            else:
                if st.button("友達になる"):
                    # 友達リストに追加
                    if 'friends' not in current_user:
                        current_user['friends'] = []
                    current_user['friends'].append(user_id)
                    update_data = {'friends': current_user['friends']}
                    success, error = update_user(current_user_id, update_data)
                    if success:
                        # 友達状態を更新して再表示
                        st.session_state.friend_added = True
                        st.rerun()
                    else:
                        st.error(f"追加エラー: {error}")
        else:
            st.info("これはあなたのプロフィールです。自分自身とは友達になれません。")
    else:
        st.info("友達機能を利用するにはログインが必要です。")
        if st.button("ログインする"):
            # セッション状態を使ってログイン画面に移動
            st.session_state.show_login = True
            st.rerun()
    
    # 戻るボタン
    if st.button("← メインページに戻る"):
        # セッション状態をリセットしてメインページに戻る
        if "show_login" in st.session_state:
            del st.session_state.show_login
        # メインページに戻るフラグを設定
        st.session_state.return_to_main = True
        # URLパラメータをクリアしてメインページに戻る
        st.query_params.clear()
        st.rerun()

if __name__ == "__main__":
    main()
