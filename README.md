# Azure Updates 日本語訳 - メール配信サービス

## 概要

Microsoft 公式の [Azure 更新情報](https://azure.microsoft.com/updates) を毎朝9時 (UTC 0:00) に自動取得し、LLM で日本語に翻訳してメール配信する Azure Functions アプリケーション

## 主な機能

- **タイマー起動 :** 日本時間で毎朝 AM 9:01（UTC 0:01）に実行し、前日に発表された更新情報を自動取得
- **AI 翻訳 :** Azure OpenAI を利用した高品質な日本語翻訳
- **メール配信 :** Azure Communication Services を使用した HTML メール送信

## ディレクトリ構成

```
azure_updates.py        # メインロジック（更新情報取得・翻訳・メール送信）
function_app.py         # Azure Functions エントリポイント（タイマートリガー）
local.settings.json     # ローカル開発用設定（Git管理外）
requirements.txt        # 必要なPythonパッケージ一覧
```

## 必要な環境・サービス

- Python 3.11 以上
- VSCode - Azure Functions Core Tools
- Azure OpenAI Service
- Azure Communication Services (Email)

## セットアップ手順

### 1. リポジトリのクローン
```cmd
git clone <repository-url>
cd azure-updates-func
```

### 2. 仮想環境を作成してアクティブにします:
```sh
python -m venv .venv
source .venv/bin/activate  # Windowsの場合は `.venv\Scripts\activate`
```

### 3. 必要なパッケージのインストール
```cmd
pip install -r requirements.txt
```

### 4. 環境変数の設定

`local.settings.json` ファイルを作成し、以下の設定値を記入：

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_OPENAI_ENDPOINT": "https://your-openai-resource.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "your-openai-api-key",
    "MODEL_DEPLOYMENT_NAME": "gpt-4.1",
    "MAIL_CONNECTION_STRING": "endpoint=https://your-acs.communication.azure.com/;accesskey=your-access-key",
    "SENDER_ADDRESS": "DoNotReply@sender.com",
    "RECIPIENT_ADDRESS": "recipient@example.com"
  }
}
```

### 5. ローカル実行
```cmd
func host start
```

## ログとモニタリング

- Azure Application Insights と連携
- 実行ログとエラー情報を記録
- 翻訳エラー時は「(翻訳エラー: エラー内容)」を表示

## セキュリティ

- API キーや接続文字列は環境変数で管理（Managed ID への変更を推奨）
- `local.settings.json` は Git 管理対象外

## ライセンス
This project is licensed under the MIT License, see the LICENSE file for details