import streamlit as st
import firebase_admin
from firebase_admin import auth, firestore
from config import get_firestore_client

def check_admin_status(user_id):
    """ユーザーが管理者かどうかをチェックする"""
    try:
        db = get_firestore_client()
        if db:
            user_doc = db.collection('users').document(user_id).get()
            if user_doc.exists:
                return user_doc.to_dict().get('is_admin', False)
        return False
    except Exception as e:
        st.error(f"管理者権限チェックエラー: {e}")
        return False

def create_user_session(user_id, email, display_name, is_admin=False):
    """ユーザーセッションを作成する"""
    st.session_state.user_id = user_id
    st.session_state.email = email
    st.session_state.display_name = display_name
    st.session_state.is_admin = is_admin
    st.session_state.authenticated = True

def clear_user_session():
    """ユーザーセッションをクリアする"""
    if 'user_id' in st.session_state:
        del st.session_state.user_id
    if 'email' in st.session_state:
        del st.session_state.email
    if 'display_name' in st.session_state:
        del st.session_state.display_name
    if 'is_admin' in st.session_state:
        del st.session_state.is_admin
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated

def is_authenticated():
    """ユーザーが認証されているかチェックする"""
    return st.session_state.get('authenticated', False)

def is_admin():
    """現在のユーザーが管理者かチェックする"""
    return st.session_state.get('is_admin', False)

def get_current_user_id():
    """現在のユーザーIDを取得する"""
    return st.session_state.get('user_id', None)

def require_auth():
    """認証が必要なページで使用するデコレータ的な関数"""
    if not is_authenticated():
        st.error("ログインが必要です。")
        st.stop()
    return True
