import qrcode
import streamlit as st
from io import BytesIO
import base64
from PIL import Image

def generate_qr_code(data, size=10):
    """QRコードを生成する"""
    try:
        # QRコードを生成
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # PIL Imageとして生成
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # BytesIOに変換
        buffer = BytesIO()
        qr_image.save(buffer, format="PNG")
        buffer.seek(0)
        
        return buffer
    except Exception as e:
        st.error(f"QRコード生成エラー: {e}")
        return None

def generate_user_qr_code(user_id, base_url):
    """ユーザーのマイページURL用のQRコードを生成する"""
    # ユーザー固有のマイページURLを生成
    user_url = f"{base_url}/user/{user_id}"
    return generate_qr_code(user_url)

def display_qr_code(qr_buffer, caption="QRコード"):
    """QRコードをStreamlitで表示する"""
    if qr_buffer:
        st.image(qr_buffer, caption=caption, use_container_width=True)
        return True
    return False

def get_qr_code_as_base64(qr_buffer):
    """QRコードをbase64エンコードされた文字列として取得する"""
    if qr_buffer:
        qr_buffer.seek(0)
        qr_data = qr_buffer.read()
        return base64.b64encode(qr_data).decode()
    return None

def download_qr_code_button(qr_buffer, filename="qr_code.png", button_text="QRコードをダウンロード"):
    """QRコードのダウンロードボタンを表示する"""
    if qr_buffer:
        qr_buffer.seek(0)
        st.download_button(
            label=button_text,
            data=qr_buffer.read(),
            file_name=filename,
            mime="image/png"
        )
        return True
    return False
