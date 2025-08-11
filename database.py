import streamlit as st
from firebase_admin import firestore
from config import get_firestore_client
import uuid
from datetime import datetime
import hashlib
import os

def hash_password(password):
    """パスワードをハッシュ化する"""
    salt = os.urandom(32)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt + hash_obj

def verify_password(password, stored_hash):
    """パスワードを検証する"""
    try:
        salt = stored_hash[:32]
        stored_hash = stored_hash[32:]
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return hash_obj == stored_hash
    except:
        return False

def create_user(user_data):
    """新規ユーザーを作成する"""
    try:
        db = get_firestore_client()
        if not db:
            return None, "データベース接続エラー"
        
        # メールアドレスの重複チェック
        existing_user = get_user_by_email(user_data['email'])
        if existing_user:
            return None, "このメールアドレスは既に登録されています"
        
        # ユーザーIDを生成
        user_id = str(uuid.uuid4())
        
        # パスワードをハッシュ化
        password_hash = hash_password(user_data['password'])
        
        # ユーザーデータを準備
        user_doc = {
            'user_id': user_id,
            'email': user_data['email'],
            'password_hash': password_hash,  # ハッシュ化されたパスワード
            'display_name': user_data['display_name'],
            'profile': user_data.get('profile', ''),
            'interests': user_data.get('interests', []),
            'photo_url': user_data.get('photo_url', ''),
            'sns_accounts': user_data.get('sns_accounts', {}),
            'is_admin': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Firestoreに保存
        db.collection('users').document(user_id).set(user_doc)
        return user_id, None
        
    except Exception as e:
        return None, f"ユーザー作成エラー: {e}"

def create_admin_user(user_data):
    """管理者ユーザーを作成する"""
    try:
        db = get_firestore_client()
        if not db:
            return None, "データベース接続エラー"
        
        # メールアドレスの重複チェック
        existing_user = get_user_by_email(user_data['email'])
        if existing_user:
            return None, "このメールアドレスは既に登録されています"
        
        # ユーザーIDを生成
        user_id = str(uuid.uuid4())
        
        # パスワードをハッシュ化
        password_hash = hash_password(user_data['password'])
        
        # 管理者ユーザーデータを準備
        user_doc = {
            'user_id': user_id,
            'email': user_data['email'],
            'password_hash': password_hash,  # ハッシュ化されたパスワード
            'display_name': user_data['display_name'],
            'profile': user_data.get('profile', ''),
            'interests': user_data.get('interests', []),
            'photo_url': user_data.get('photo_url', ''),
            'sns_accounts': user_data.get('sns_accounts', {}),
            'is_admin': True,  # 管理者フラグをTrueに設定
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Firestoreに保存
        db.collection('users').document(user_id).set(user_doc)
        return user_id, None
        
    except Exception as e:
        return None, f"管理者ユーザー作成エラー: {e}"

def authenticate_user(email, password):
    """ユーザー認証を行う"""
    try:
        user = get_user_by_email(email)
        if user and user.get('password_hash'):
            if verify_password(password, user['password_hash']):
                return user, None
            else:
                return None, "パスワードが正しくありません"
        else:
            return None, "ユーザーが見つかりません"
    except Exception as e:
        return None, f"認証エラー: {e}"

def promote_to_admin(user_id):
    """既存のユーザーを管理者に昇格させる"""
    try:
        db = get_firestore_client()
        if not db:
            return False, "データベース接続エラー"
        
        # ユーザーを管理者に昇格
        db.collection('users').document(user_id).update({
            'is_admin': True,
            'updated_at': datetime.now()
        })
        return True, None
        
    except Exception as e:
        return False, f"管理者昇格エラー: {e}"

def demote_from_admin(user_id):
    """管理者の権限を削除する"""
    try:
        db = get_firestore_client()
        if not db:
            return False, "データベース接続エラー"
        
        # 管理者権限を削除
        db.collection('users').document(user_id).update({
            'is_admin': False,
            'updated_at': datetime.now()
        })
        return True, None
        
    except Exception as e:
        return False, f"管理者権限削除エラー: {e}"

def get_user_by_id(user_id):
    """ユーザーIDでユーザー情報を取得する"""
    try:
        db = get_firestore_client()
        if not db:
            return None
        
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            return user_doc.to_dict()
        return None
        
    except Exception as e:
        st.error(f"ユーザー取得エラー: {e}")
        return None

def get_user_by_email(email):
    """メールアドレスでユーザー情報を取得する"""
    try:
        db = get_firestore_client()
        if not db:
            return None
        
        users = db.collection('users').where('email', '==', email).limit(1).stream()
        for user in users:
            return user.to_dict()
        return None
        
    except Exception as e:
        st.error(f"ユーザー取得エラー: {e}")
        return None

def update_user(user_id, update_data):
    """ユーザー情報を更新する"""
    try:
        db = get_firestore_client()
        if not db:
            return False, "データベース接続エラー"
        
        # 更新日時を追加
        update_data['updated_at'] = datetime.now()
        
        # Firestoreを更新
        db.collection('users').document(user_id).update(update_data)
        return True, None
        
    except Exception as e:
        return False, f"ユーザー更新エラー: {e}"

def update_user_password(user_id, new_password):
    """ユーザーのパスワードを更新する"""
    try:
        db = get_firestore_client()
        if not db:
            return False, "データベース接続エラー"
        
        # 新しいパスワードをハッシュ化
        password_hash = hash_password(new_password)
        
        # パスワードを更新
        db.collection('users').document(user_id).update({
            'password_hash': password_hash,
            'updated_at': datetime.now()
        })
        return True, None
        
    except Exception as e:
        return False, f"パスワード更新エラー: {e}"

def reset_user_password(user_id, new_password):
    """ユーザーのパスワードをリセットする（管理者用）"""
    try:
        # デバッグ情報
        print(f"パスワードリセット開始: ユーザーID={user_id}")
        
        db = get_firestore_client()
        if not db:
            print("データベース接続エラー")
            return False, "データベース接続エラー"
        
        print("データベース接続成功")
        
        # ユーザーの存在確認
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            print(f"ユーザーが見つかりません: {user_id}")
            return False, f"ユーザーID {user_id} が見つかりません"
        
        print("ユーザー存在確認完了")
        
        # 新しいパスワードをハッシュ化
        password_hash = hash_password(new_password)
        print("パスワードハッシュ化完了")
        
        # パスワードをリセット
        update_data = {
            'password_hash': password_hash,
            'updated_at': datetime.now()
        }
        
        print(f"更新データ: {update_data}")
        
        db.collection('users').document(user_id).update(update_data)
        print("データベース更新完了")
        
        return True, None
        
    except Exception as e:
        print(f"パスワードリセットエラー: {e}")
        return False, f"パスワードリセットエラー: {e}"

def check_user_has_password(user_id):
    """ユーザーがパスワードを持っているかチェックする"""
    try:
        db = get_firestore_client()
        if not db:
            return False
        
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            return 'password_hash' in user_data and user_data['password_hash'] is not None
        return False
        
    except Exception as e:
        st.error(f"パスワードチェックエラー: {e}")
        return False

def get_all_users():
    """すべてのユーザーを取得する（管理者用）"""
    try:
        db = get_firestore_client()
        if not db:
            return []
        
        users = db.collection('users').stream()
        return [user.to_dict() for user in users]
        
    except Exception as e:
        st.error(f"ユーザー一覧取得エラー: {e}")
        return []

def delete_user(user_id):
    """ユーザーを削除する（管理者用）"""
    try:
        db = get_firestore_client()
        if not db:
            return False, "データベース接続エラー"
        
        db.collection('users').document(user_id).delete()
        return True, None
        
    except Exception as e:
        return False, f"ユーザー削除エラー: {e}"

def search_users_by_interests(interests):
    """興味のあるジャンルでユーザーを検索する"""
    try:
        db = get_firestore_client()
        if not db:
            return []
        
        users = db.collection('users').where('interests', 'array_contains_any', interests).stream()
        return [user.to_dict() for user in users]
        
    except Exception as e:
        st.error(f"ユーザー検索エラー: {e}")
        return []
