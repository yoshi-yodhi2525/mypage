import os
import streamlit as st
from firebase_admin import credentials, firestore, auth, initialize_app
import firebase_admin
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Firebase設定（環境変数から取得）
FIREBASE_CONFIG = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n") if os.getenv("FIREBASE_PRIVATE_KEY") else None,
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
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
        
        # 必須フィールドのチェック
        required_fields = ['FIREBASE_PROJECT_ID', 'FIREBASE_PRIVATE_KEY', 'FIREBASE_CLIENT_EMAIL']
        missing_fields = [field for field in required_fields if not os.getenv(field)]
        
        if missing_fields:
            st.error(f"❌ 以下の環境変数が設定されていません: {', '.join(missing_fields)}")
            return False
        
        # 既存のアプリが初期化されているかチェック
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CONFIG)
            initialize_app(cred)
            st.success("✅ Firebase初期化成功")
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
