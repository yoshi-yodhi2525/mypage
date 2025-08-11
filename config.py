import os
import streamlit as st
from firebase_admin import credentials, firestore, auth, initialize_app
import firebase_admin
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def get_firebase_config():
    """Firebase設定を取得する（環境変数から）"""
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    private_key = os.getenv("FIREBASE_PRIVATE_KEY")
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
    
    # 必須フィールドのチェック
    if not all([project_id, private_key, client_email]):
        return None
    
    # private_keyの改行文字を正しく処理
    if private_key:
        private_key = private_key.replace("\\n", "\n")
    
    return {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": private_key,
        "client_email": client_email,
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
        "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
        "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
    }

# アプリケーション設定
APP_CONFIG = {
    "app_name": "イベント参加者マイページ",
    "page_title": "イベント参加者マイページ",
    "page_icon": "🎫"
}

def initialize_firebase():
    """Firebaseを初期化する"""
    try:
        # 環境変数のデバッグ情報を表示
        st.write("🔍 Firebase設定のデバッグ情報:")
        st.write(f"Project ID: {os.getenv('FIREBASE_PROJECT_ID')}")
        st.write(f"Client Email: {os.getenv('FIREBASE_CLIENT_EMAIL')}")
        st.write(f"Private Key ID: {os.getenv('FIREBASE_PRIVATE_KEY_ID')}")
        st.write(f"Private Key: {'設定済み' if os.getenv('FIREBASE_PRIVATE_KEY') else '未設定'}")
        
        # 環境変数の詳細チェック
        st.write("📋 環境変数の詳細:")
        for key in ['FIREBASE_PROJECT_ID', 'FIREBASE_PRIVATE_KEY', 'FIREBASE_CLIENT_EMAIL']:
            value = os.getenv(key)
            if value:
                if key == 'FIREBASE_PRIVATE_KEY':
                    st.write(f"  {key}: {'設定済み（長さ: ' + str(len(value)) + '文字）'}")
                else:
                    st.write(f"  {key}: {value}")
            else:
                st.write(f"  {key}: ❌ 未設定")
        
        # Firebase設定を取得
        firebase_config = get_firebase_config()
        if not firebase_config:
            st.error("❌ Firebase設定の取得に失敗しました。必須の環境変数が設定されていません。")
            return False
        
        # 既存のアプリが初期化されているかチェック
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_config)
            initialize_app(cred)
            st.success("✅ Firebase初期化成功")
        return True
    except Exception as e:
        st.error(f"Firebase初期化エラー: {e}")
        st.write("詳細なエラー情報:", str(e))
        return False

def get_firestore_client():
    """Firestoreクライアントを取得する"""
    try:
        return firestore.client()
    except Exception as e:
        st.error(f"Firestore接続エラー: {e}")
        return None
