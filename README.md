# イベント参加者マイページシステム

StreamlitとFirebaseを使用して構築されたイベント参加者のマイページ機能です。

## 機能

### ユーザー機能
- 新規登録（メールアドレス・パスワード、Googleアカウント対応予定）
- ログイン・ログアウト
- マイページ表示
- プロフィール編集
- QRコード生成（マイページURL用）

### 管理者機能
- 全ユーザー情報の閲覧・編集
- ユーザー削除
- 管理者権限の付与・削除

### 登録項目
- メールアドレス（必須）
- パスワード（必須）
- 表示名（必須）
- プロフィール（オプション）
- 興味のあるジャンル（オプション）
- 写真URL（オプション）
- SNSアカウント（オプション）
  - Twitter
  - Instagram
  - Facebook

## セットアップ

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. Firebase設定
1. [Firebase Console](https://console.firebase.google.com/)でプロジェクトを作成
2. Firestore Databaseを有効化
3. サービスアカウントキーを生成
4. `config.py`の`FIREBASE_CONFIG`を実際の設定値で更新

### 3. 環境変数の設定
`.env`ファイルを作成し、Firebase設定を記述：
```
FIREBASE_TYPE=service_account
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-client-email
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=your-client-cert-url
```

### 4. アプリケーションの起動
```bash
streamlit run app.py
```

## 使用方法

### 新規ユーザー
1. 「新規登録」タブで必要情報を入力
2. 登録完了後、ログイン
3. マイページでプロフィール確認・編集

### 管理者
1. 管理者権限を持つユーザーでログイン
2. サイドバーから「管理者パネル」を選択
3. 全ユーザーの管理・編集

## ファイル構成

```
├── app.py              # メインアプリケーション
├── config.py           # Firebase設定
├── auth_utils.py       # 認証・セッション管理
├── database.py         # データベース操作
├── qr_utils.py         # QRコード生成
├── requirements.txt    # 依存関係
└── README.md          # このファイル
```

## 注意事項

- 現在の実装では簡易的な認証システムを使用しています
- 本格的な運用では、Firebase Authenticationの実装が必要です
- パスワードのハッシュ化やセキュリティ対策を追加してください

## 今後の拡張予定

- Firebase Authenticationの完全実装
- Googleアカウントでのログイン
- 画像アップロード機能
- イベント管理機能
- 通知システム
