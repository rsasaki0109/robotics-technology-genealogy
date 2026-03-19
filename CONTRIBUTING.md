# Contributing / コントリビューションガイド

Thanks for your interest in contributing! This guide explains how to add domains, methods, and relations.

コントリビューションに興味を持っていただきありがとうございます！このガイドでは、ドメイン・手法・関係の追加方法を説明します。

---

## Adding a New Domain / 新しいドメインの追加

Create a YAML file in `domains/` (e.g. `domains/my_new_topic.yaml`):

`domains/` にYAMLファイルを作成してください（例: `domains/my_new_topic.yaml`）:

```yaml
name: My New Topic
description: Brief description of the domain.
source_awesome_lists:
  - https://github.com/example/awesome-list
methods:
  - name: MethodA
    paper: "Full paper title"
    arxiv: "2301.00000"
    year: 2023
    code: owner/repo
    stars: 1234
    license: MIT
    open_source: open          # open / research / partial / closed
    tags: [tag1, tag2]
    parents: []
    description: Short one-line description.
```

Then register your domain in `scripts/build_site.py`'s `CATEGORY_MAP` under the appropriate category.

その後、`scripts/build_site.py` の `CATEGORY_MAP` に適切なカテゴリで登録してください。

## Adding Methods to an Existing Domain / 既存ドメインへの手法追加

Open the relevant YAML in `domains/` and append to the `methods` list. Required fields:

`domains/` 内の該当YAMLを開き、`methods` リストに追記してください。必須フィールド:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique method name |
| `year` | Yes | Publication year |
| `paper` | No | Full paper title |
| `arxiv` | No | arXiv ID (e.g. `2301.00000`) |
| `code` | No | GitHub `owner/repo` |
| `stars` | No | GitHub star count |
| `license` | No | e.g. `MIT`, `Apache-2.0` |
| `open_source` | No | `open` / `research` / `partial` / `closed` |
| `tags` | No | List of keyword tags |
| `parents` | No | List of parent relations |
| `description` | No | One-line description |

## Relation Types / 関係タイプ

Each entry in `parents` has a `name` (referencing another method) and a `relation`:

`parents` の各エントリは `name`（他の手法を参照）と `relation` を持ちます:

| Relation | When to Use | Example |
|----------|-------------|---------|
| `extends` | Directly builds on / improves the parent | LeGO-LOAM **extends** LOAM |
| `combines` | Merges ideas from multiple parents | LIO-SAM **combines** LOAM + IMU preintegration |
| `replaces` | Designed as a successor/replacement | PointPillars **replaces** VoxelNet for speed |
| `inspires` | Loosely inspired, different approach | NDT **inspires** ICP (shared registration goal) |

Default is `extends` if omitted. Use `inspires` (shown as dashed edges) for loose conceptual links.

デフォルトは `extends` です。緩い概念的なつながりには `inspires`（破線で表示）を使ってください。

```yaml
parents:
  - name: LOAM
    relation: extends
  - name: IMUPreintegration
    relation: combines
```

## Running Locally / ローカル実行

```bash
# Install the package
# パッケージのインストール
pip install -e ".[dev,web]"

# Build the static site
# 静的サイトのビルド
python scripts/build_site.py
# Then open docs/index.html in your browser
# docs/index.html をブラウザで開いてください

# CLI: list domains
# CLI: ドメイン一覧
robotics-technology-genealogy list

# CLI: show a specific domain
# CLI: 特定ドメインの表示
robotics-technology-genealogy show "LiDAR Odometry & SLAM"

# Streamlit web app (optional)
# Streamlit ウェブアプリ（任意）
streamlit run web/app.py
```

## PR Process / PRの流れ

1. Fork the repo and create a feature branch.
   リポジトリをフォークし、フィーチャーブランチを作成。

2. Make your changes (add/edit YAML, update `CATEGORY_MAP` if needed).
   変更を行う（YAML追加・編集、必要に応じて `CATEGORY_MAP` を更新）。

3. Run tests to validate YAML schema:
   テストを実行してYAMLスキーマを検証:
   ```bash
   pytest
   ```

4. Build the site locally and check it looks correct:
   ローカルでサイトをビルドし、表示を確認:
   ```bash
   python scripts/build_site.py
   ```

5. Open a Pull Request with a brief description of what you added/changed.
   追加・変更内容の簡単な説明を添えてPull Requestを作成。

That's it -- welcome aboard!

以上です。ようこそ！
