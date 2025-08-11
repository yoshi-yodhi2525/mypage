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
    "page_icon": "🎫",
    "base_url": "https://mypage-001.streamlit.app"
}

def initialize_firebase():
    """Firebaseを初期化する"""
    try:
        # Firebase設定を取得
        firebase_config = get_firebase_config()
        if not firebase_config:
            st.error("❌ Firebase設定の取得に失敗しました。必須の環境変数が設定されていません。")
            return False
        
        # 既存のアプリが初期化されているかチェック
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_config)
            initialize_app(cred)
        return True
    except Exception as e:
        st.error(f"Firebase初期化エラー: {e}")
        return False

def get_firestore_client():
    """Firestoreクライアントを取得する"""
    try:
        return firestore.client()
    except Exception as e:
        st.error(f"Firestore接続エラー: {e}")
        return None
