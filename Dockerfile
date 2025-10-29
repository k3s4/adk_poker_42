# Python 3.13ベースイメージを使用
FROM python:3.13-slim

# 作業ディレクトリを設定
WORKDIR /app

# uvをインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# プロジェクトファイルをコピー（依存関係のインストール用）
COPY pyproject.toml uv.lock ./

# 依存関係を事前にインストール（キャッシュ効率化）
RUN uv sync --frozen --no-install-project

# コードはvolumeマウントで提供されるため、ここではコピーしない

# デフォルトのコマンド
CMD ["uv", "run", "python", "main.py"]

