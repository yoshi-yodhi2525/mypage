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
        print(f"=== パスワードリセット開始 ===")
        print(f"ユーザーID: {user_id}")
        print(f"パスワード長: {len(new_password)}文字")
        print(f"タイムスタンプ: {datetime.now()}")
        
        # データベース接続
        print("📡 Firebase接続中...")
        db = get_firestore_client()
        if not db:
            print("❌ データベース接続エラー")
            return False, "データベース接続エラー"
        
        print("✅ データベース接続成功")
        
        # ユーザーの存在確認
        print(f"🔍 ユーザー存在確認中...")
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            print(f"❌ ユーザーが見つかりません: {user_id}")
            return False, f"ユーザーID {user_id} が見つかりません"
        
        print("✅ ユーザー存在確認完了")
        
        # 現在のユーザー情報を表示
        current_user = user_doc.to_dict()
        print(f"現在のユーザー情報: {current_user.get('display_name', 'Unknown')} ({current_user.get('email', 'No email')})")
        
        # 新しいパスワードをハッシュ化
        print("🔐 パスワードハッシュ化中...")
        print(f"入力パスワード: {'*' * len(new_password)} ({len(new_password)}文字)")
        print(f"入力パスワードの型: {type(new_password)}")
        
        try:
        password_hash = hash_password(new_password)
            print("✅ パスワードハッシュ化完了")
            print(f"ハッシュ長: {len(password_hash)} bytes")
            print(f"ハッシュの型: {type(password_hash)}")
            print(f"ハッシュ内容: {password_hash[:50]}...")
            
            # ハッシュ化の検証
            if isinstance(password_hash, bytes):
                print("✅ ハッシュはbytes型で正常です")
            else:
                print(f"⚠️ ハッシュの型が予期しない: {type(password_hash)}")
                
        except Exception as hash_error:
            print(f"❌ パスワードハッシュ化でエラー: {hash_error}")
            print(f"エラータイプ: {type(hash_error).__name__}")
            import traceback
            print(f"ハッシュ化エラーのスタックトレース: {traceback.format_exc()}")
            raise hash_error
        
        # パスワードをリセット
        update_data = {
            'password_hash': password_hash,
            'updated_at': datetime.now()
        }
        
        print(f"📝 更新データ準備完了:")
        print(f"  password_hash: {type(password_hash)} = {len(password_hash)} bytes")
        print(f"  updated_at: {type(datetime.now())} = {datetime.now()}")
        print(f"  更新データ全体: {update_data}")
        
        # 更新データの検証
        if 'password_hash' in update_data and update_data['password_hash'] is not None:
            print("✅ 更新データのpassword_hashが正常に設定されています")
        else:
            print("❌ 更新データのpassword_hashが正しく設定されていません")
            print(f"password_hashの値: {update_data.get('password_hash')}")
            print(f"password_hashの型: {type(update_data.get('password_hash'))}")
        
        # データベース更新
        print("💾 データベース更新中...")
        print(f"更新対象ドキュメント: users/{user_id}")
        print(f"更新データ: {update_data}")
        
        # 更新前のデータを確認
        print("🔍 更新前のデータ確認...")
        before_doc = db.collection('users').document(user_id).get()
        if before_doc.exists:
            before_data = before_doc.to_dict()
            print(f"更新前のパスワードハッシュ: {before_data.get('password_hash', 'None')}")
        else:
            print("❌ 更新前のドキュメントが見つかりません")
        
        # 実際の更新処理
        print("🚀 実際の更新処理を開始...")
        try:
            update_result = db.collection('users').document(user_id).update(update_data)
            print(f"更新結果: {update_result}")
            print(f"更新結果の型: {type(update_result)}")
            print("✅ データベース更新完了")
        except Exception as update_error:
            print(f"❌ 更新処理でエラーが発生: {update_error}")
            print(f"エラータイプ: {type(update_error).__name__}")
            import traceback
            print(f"更新エラーのスタックトレース: {traceback.format_exc()}")
            raise update_error
        
        # 更新後の確認
        print("🔍 更新確認中...")
        print("少し待ってから確認を開始します...")
        import time
        time.sleep(1)  # 1秒待機
        
        updated_doc = db.collection('users').document(user_id).get()
        if updated_doc.exists:
            updated_user = updated_doc.to_dict()
            print(f"更新後のユーザー情報: {updated_user.get('display_name', 'Unknown')}")
            print(f"更新後のパスワードハッシュ存在: {'password_hash' in updated_user}")
            
            if 'password_hash' in updated_user:
                print(f"更新後のパスワードハッシュ長: {len(updated_user['password_hash'])} bytes")
                print(f"更新後のパスワードハッシュ内容: {updated_user['password_hash'][:50]}...")
                
                if updated_user['password_hash'] == password_hash:
                    print("✅ パスワード更新確認完了 - ハッシュが一致")
                else:
                    print("⚠️ パスワード更新確認で不一致")
                    print(f"期待されるハッシュ: {password_hash[:50]}...")
                    print(f"実際のハッシュ: {updated_user['password_hash'][:50]}...")
                    
                    # 不一致の詳細調査
                    print("🔍 不一致の詳細調査:")
                    print(f"期待されるハッシュの型: {type(password_hash)}")
                    print(f"実際のハッシュの型: {type(updated_user['password_hash'])}")
                    print(f"期待されるハッシュの長さ: {len(password_hash)}")
                    print(f"実際のハッシュの長さ: {len(updated_user['password_hash'])}")
            else:
                print("❌ 更新後のパスワードハッシュが存在しません")
                print("更新後のユーザーデータの全フィールド:")
                for key, value in updated_user.items():
                    print(f"  {key}: {type(value)} = {value}")
        else:
            print("❌ 更新後のドキュメントが見つかりません")
            print("ドキュメントの存在確認を再試行...")
            # 再試行
            time.sleep(2)
            retry_doc = db.collection('users').document(user_id).get()
            if retry_doc.exists:
                print("✅ 再試行でドキュメントが見つかりました")
            else:
                print("❌ 再試行でもドキュメントが見つかりません")
        
        print("=== パスワードリセット完了 ===")
        return True, None
        
    except Exception as e:
        print(f"=== パスワードリセットエラー ===")
        print(f"エラータイプ: {type(e).__name__}")
        print(f"エラーメッセージ: {str(e)}")
        print(f"エラー詳細: {e}")
        import traceback
        print(f"スタックトレース: {traceback.format_exc()}")
        return False, f"パスワードリセットエラー: {e}"

def check_user_has_password(user_id):
    """ユーザーがパスワードを持っているかチェックする"""
    try:
        print(f"=== パスワード確認開始 ===")
        print(f"ユーザーID: {user_id}")
        
        db = get_firestore_client()
        if not db:
            print("❌ データベース接続エラー")
            return False
        
        print("✅ データベース接続成功")
        
        user_doc = db.collection('users').document(user_id).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            has_password = 'password_hash' in user_data and user_data['password_hash'] is not None
            
            print(f"ユーザー情報: {user_data.get('display_name', 'Unknown')}")
            print(f"パスワードハッシュ存在: {has_password}")
            if has_password:
                print(f"パスワードハッシュ長: {len(user_data['password_hash'])} bytes")
                print(f"パスワードハッシュ内容: {user_data['password_hash'][:50]}...")
            
            print("=== パスワード確認完了 ===")
            return has_password
        else:
            print("❌ ユーザーが見つかりません")
        return False
        
    except Exception as e:
        print(f"=== パスワード確認エラー ===")
        print(f"エラータイプ: {type(e).__name__}")
        print(f"エラーメッセージ: {str(e)}")
        import traceback
        print(f"スタックトレース: {traceback.format_exc()}")
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
