import streamlit as st
from config import initialize_firebase, APP_CONFIG
from auth_utils import *
from database import *
from qr_utils import *
import os

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
        photo_url = st.text_input("写真URL（オプション）")
        
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
                
                # ユーザーデータを準備
                user_data = {
                    'email': email,
                    'password': password,  # パスワードを追加
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
                # デバッグ情報
                st.write(f"APP_CONFIG type: {type(APP_CONFIG)}")
                st.write(f"APP_CONFIG content: {APP_CONFIG}")
                
                if hasattr(APP_CONFIG, 'get') and callable(getattr(APP_CONFIG, 'get')):
                    base_url = APP_CONFIG.get("base_url", "https://mypage-001.streamlit.app")
                else:
                    base_url = "https://mypage-001.streamlit.app"
            except Exception as e:
                st.write(f"Error getting base_url: {e}")
                base_url = "https://mypage-001.streamlit.app"
            
            # QRコード生成のデバッグ情報
            st.write(f"🔍 QRコード生成のデバッグ:")
            st.write(f"  User ID: {user_id}")
            st.write(f"  Base URL: {base_url}")
            st.write(f"  QR Code URL: {base_url}/?user_id={user_id}")
            
            qr_code = generate_user_qr_code(user_id, base_url)
            st.write(f"  QR Code generated: {qr_code is not None}")
            
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
                        
                        if st.button(f"削除 {user['user_id']}", key=f"delete_{user['user_id']}"):
                            if st.button(f"本当に削除しますか？ {user['user_id']}", key=f"confirm_delete_{user['user_id']}"):
                                success, error = delete_user(user['user_id'])
                                if success:
                                    st.success("ユーザーを削除しました。")
                                    st.rerun()
                                else:
                                    st.error(f"削除エラー: {error}")
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
    
    # 戻るボタン
    if st.button("← メインページに戻る"):
        st.rerun()

if __name__ == "__main__":
    main()
