"""add extract_status to raw_news

Revision ID: a1b2c3d4e5f6
Revises: 4bb970b491d0
Create Date: 2026-07-12 10:00:00.000000

给 raw_news 加 extract_status 字段（pending/extracted/noise/failed），处理层据此
跳过已处理/噪声/失败新闻。批模式重建表 + 索引 + 回填存量（已有关联的设 extracted）。
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "4bb970b491d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 批模式重建 raw_news：COPY 数据用 server_default 填 pending，所有现有行先变 pending
    with op.batch_alter_table("raw_news", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "extract_status",
                sa.String(length=16),
                nullable=False,
                server_default="pending",
            )
        )
        batch_op.create_index("ix_raw_news_extract_status", ["extract_status"], unique=False)

    # 回填存量：已写入 event_sources 关联的 raw_news 视为已处理，标 extracted
    op.execute(
        "UPDATE raw_news SET extract_status='extracted' "
        "WHERE id IN (SELECT raw_news_id FROM event_sources)"
    )


def downgrade() -> None:
    with op.batch_alter_table("raw_news", schema=None) as batch_op:
        batch_op.drop_index("ix_raw_news_extract_status")
        batch_op.drop_column("extract_status")
