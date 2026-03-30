# landing-page/ specs

## index.html
LeakAid の需要検証用ランディングページ。単一HTMLファイルで完結。

### ページ構成（上から順）

- **Nav**: 固定ヘッダー（backdrop-filter blur）。ロゴ（Inter フォント、`<a>`リンク）+ 「先行登録受付中」バッジ。`aria-label` 付き
- **Hero**: キャッチコピー「あなたの画像を、あなたの意思で取り下げる。」+ サブタイトル「いますぐ、誰にも知られず、チャットするだけ。」（青色テキスト）+ Formspree連携のメール登録フォーム（ボタン:「無料で先行登録」）
- **Mockups**: スマホモックアップ2台（CSS製）
  - 左: AIチャット画面 — 会話のやりとりサンプル + メッセージ入力UI
  - 右: 進捗ダッシュボード — 4件の削除申請の状況（削除済み・対応中・送信済み）
- **Trust**: 安心感セクション。3カラムグリッド（対面・電話は不要 / スマホだけでOK / 24時間いつでも対応）。各項目にSVGアイコン付き
- **Steps**: 3ステップ説明（チャットで状況整理 → 削除申請を自動作成 → 進捗をリアルタイム追跡）
  - 「スタッフ」等の人的対応表現は使用しない（全てAI処理）
  - 「作成・送信をサポート」表記で非弁行為に抵触しない表現
  - 「削除を保証」と読めないようトーン調整済み
- **Bottom CTA**: ダークセクション（#16213e背景）にメール登録フォーム（ボタン:「無料で先行登録」）+ サブコピー「登録は10秒。メールアドレスだけで完了します。」
- **Footer**: コピーライト + "San Francisco, California"

### フォーム
- Formspree連携: `https://formspree.io/f/xbdporzg`
- ページ内に2箇所（Hero + Bottom CTA）
- Ajax送信（ページ遷移なし）、送信後にメッセージ表示
- JS: `handleForm()` 共通関数で両フォームを処理

### SEO
- title / description にターゲットキーワード含む
- OGP (Open Graph) メタタグ
- Twitter Card メタタグ
- canonical URL: `https://www.leakaid.me/`
- 構造化データ (JSON-LD): WebApplication スキーマ
- keywords メタタグ: 画像削除, リベンジポルノ, 非同意性的画像 等

### アナリティクス
- Google Analytics GA4: 測定ID `G-ZHVZ15N203`
- Google Search Console: GA4経由で所有権自動認証済み

### 技術仕様
- 外部依存: Google Fonts（Inter・Noto Sans JP・Noto Serif JP）+ GA4
- CSS: `<style>` タグ内に全記述、レスポンシブ対応（600px ブレークポイント）
- JS: フォーム送信処理のみ（Ajax / Fetch API）
- セマンティックHTML: `<main>`, `<nav aria-label>`, `<section>`, `<footer>`

### デプロイ
- ホスティング: Vercel
- 本番URL: https://www.leakaid.me
- デプロイ方法: `cd landing-page && npx vercel --prod --yes`
- GitHub連携による自動デプロイは未設定（Vercel Login Connection設定待ち）

## vercel.json
SPA 風のリライト設定。すべてのパスを index.html にルーティング。

## sitemap.xml
サイトマップ。`https://www.leakaid.me/` を priority 1.0 で登録。

## robots.txt
全クローラー許可。サイトマップURLを記載。
