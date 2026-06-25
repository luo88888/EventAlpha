# Day 2 数据采集层 — 手动测试流程

> 前提：已完成 `pip install -e ".[dev]"`、`cp .env_example .env`、`alembic upgrade head`

---

## 测试 1：服务启动与健康检查

```bash
cd backend

# 启动服务
/home/liuke/miniconda3/envs/agent/bin/uvicorn app.main:app --reload

# 另开终端，验证健康检查
curl http://localhost:8000/health
```

**预期：** `{"status":"ok"}`

---

## 测试 2：首次采集

```bash
curl -s -X POST http://localhost:8000/api/jobs/collect | python3 -m json.tool
```

**预期：**
- HTTP 200（不是 500）
- cnbc 的 `fetched > 0`，`new > 0`
- 其他源 `fetched = 0`（网络不可达，但不崩溃）
- `total_new` = cnbc 的 `new`

记录 cnbc 的 `new` 值，记为 `N`。

---

## 测试 3：去重验证（重复采集）

```bash
# 立即再调一次
curl -s -X POST http://localhost:8000/api/jobs/collect | python3 -m json.tool
```

**预期：**
- cnbc 的 `fetched` 与上次相同，`new = 0`，`skipped = fetched`
- `total_new = 0`

---

## 测试 4：数据库数据验证

```bash
/home/liuke/miniconda3/envs/agent/bin/python -c "
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # 总数
    count = db.execute(text('SELECT count(*) FROM raw_news')).scalar()
    print(f'raw_news 总数: {count}')

    # 按源统计
    rows = db.execute(text('SELECT source, count(*) FROM raw_news GROUP BY source')).fetchall()
    for source, cnt in rows:
        print(f'  {source}: {cnt} 条')

    # 抽样 3 条
    print()
    print('抽样数据:')
    samples = db.execute(text('SELECT source, title, url, content_hash FROM raw_news LIMIT 3')).fetchall()
    for s in samples:
        print(f'  [{s[0]}] {s[1][:60]}')
        print(f'    url: {s[2][:80]}')
        print(f'    hash: {s[3][:16]}...')
finally:
    db.close()
"
```

**预期：**
- 总数 = 测试 2 记录的 `N`
- 只有 cnbc 有数据
- 每条记录都有 title、url、content_hash

---

## 测试 5：字段完整性

```bash
/home/liuke/miniconda3/envs/agent/bin/python -c "
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # 检查必填字段
    nulls = db.execute(text('''
        SELECT
            sum(case when title is null or title = '' then 1 else 0 end) as no_title,
            sum(case when url is null or url = '' then 1 else 0 end) as no_url,
            sum(case when content_hash is null then 1 else 0 end) as no_hash,
            sum(case when source is null then 1 else 0 end) as no_source,
            sum(case when collected_at is null then 1 else 0 end) as no_time
        FROM raw_news
    ''')).fetchone()
    print(f'缺 title:  {nulls[0]}')
    print(f'缺 url:    {nulls[1]}')
    print(f'缺 hash:   {nulls[2]}')
    print(f'缺 source: {nulls[3]}')
    print(f'缺 time:   {nulls[4]}')

    # content_hash 唯一性
    dup_hash = db.execute(text('''
        SELECT content_hash, count(*) FROM raw_news
        GROUP BY content_hash HAVING count(*) > 1
    ''')).fetchall()
    print(f'重复 hash 数: {len(dup_hash)}')

    # url 唯一性
    dup_url = db.execute(text('''
        SELECT url, count(*) FROM raw_news
        GROUP BY url HAVING count(*) > 1
    ''')).fetchall()
    print(f'重复 url 数: {len(dup_url)}')

    assert nulls[0] == 0, '存在空 title'
    assert nulls[1] == 0, '存在空 url'
    assert nulls[2] == 0, '存在空 hash'
    assert len(dup_hash) == 0, 'content_hash 不唯一'
    print()
    print('✅ 字段完整性检查通过')
finally:
    db.close()
"
```

**预期：** 所有字段无空值，content_hash 无重复，打印 `✅ 字段完整性检查通过`

---

## 测试 6：错误隔离验证（模拟源失败）

这个测试需要临时修改代码，验证单个源崩溃不影响其他源。

```bash
/home/liuke/miniconda3/envs/agent/bin/python -c "
from unittest.mock import patch
from app.collectors.rss_collector import collect_source, collect_all, RSS_SOURCES
from app.core.database import SessionLocal
import feedparser

print('=== 错误隔离测试 ===')

# 构造 3 个源：源1正常、源2网络崩溃、源3正常
def make_feed(title, link):
    e = {'title': title, 'link': link, 'summary': 's', 'published_parsed': None, 'updated_parsed': None}
    f = feedparser.FeedParserDict()
    f['entries'] = [e]
    return f

feed_ok_1 = make_feed('Isolation Test A', 'https://test.isolation/a')
feed_ok_2 = make_feed('Isolation Test B', 'https://test.isolation/b')

call_count = [0]
def mock_fetch(url):
    call_count[0] += 1
    if call_count[0] == 2:
        raise ConnectionError('模拟网络超时')
    if call_count[0] == 1:
        return feed_ok_1
    return feed_ok_2

sources = [
    {'name': 'iso_ok_1', 'url': 'https://fake1/rss'},
    {'name': 'iso_fail', 'url': 'https://fake2/rss'},
    {'name': 'iso_ok_2', 'url': 'https://fake3/rss'},
]

db = SessionLocal()
try:
    with patch('app.collectors.rss_collector._fetch_feed', side_effect=mock_fetch):
        results = collect_all(db, sources)

    for r in results:
        print(f'  {r.source}: fetched={r.fetched}, new={r.new}')

    assert results[0].new == 1, f'源1 应 new=1, 实际 {results[0].new}'
    assert results[1].fetched == 0, f'源2 应 fetched=0, 实际 {results[1].fetched}'
    assert results[2].new == 1, f'源3 应 new=1, 实际 {results[2].new}'
    print('✅ 错误隔离通过：源2 崩溃不影响源1、源3')
finally:
    db.rollback()
    db.close()
"
```

**预期：**
- 源1 new=1，源2 fetched=0（崩溃），源3 new=1
- 打印 `✅ 错误隔离通过`

---

## 测试 7：Feed 内重复条目去重

```bash
/home/liuke/miniconda3/envs/agent/bin/python -c "
from unittest.mock import patch
from app.collectors.rss_collector import collect_source
from app.core.database import SessionLocal
import feedparser

print('=== Feed 内重复条目测试 ===')

# 同一条目出现 3 次
entry = {
    'title': 'Duplicate Entry Test',
    'link': 'https://test.dup/1',
    'summary': '<p>dup</p>',
    'published_parsed': None,
    'updated_parsed': None,
}
feed = feedparser.FeedParserDict()
feed['entries'] = [entry, entry, entry]

db = SessionLocal()
try:
    with patch('app.collectors.rss_collector._fetch_feed', return_value=feed):
        stats = collect_source(db, {'name': 'dup_test', 'url': 'https://fake/rss'})

    print(f'  fetched={stats.fetched}, new={stats.new}, skipped={stats.skipped}')
    assert stats.fetched == 3
    assert stats.new == 1, f'应 new=1, 实际 {stats.new}'
    assert stats.skipped == 2, f'应 skipped=2, 实际 {stats.skipped}'
    print('✅ 重复条目去重通过：3 条相同只插入 1 条')
finally:
    db.rollback()
    db.close()
"
```

**预期：** fetched=3, new=1, skipped=2

---

## 测试 8：清空数据库重采（可选）

如果想从头验证完整流程：

```bash
/home/liuke/miniconda3/envs/agent/bin/python -c "
from app.core.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
count = db.execute(text('SELECT count(*) FROM raw_news')).scalar()
db.execute(text('DELETE FROM raw_news'))
db.commit()
print(f'已清空 {count} 条记录')
db.close()
"
```

然后回到测试 2 重新走一遍。

---

## 测试结果记录表

| 测试 | 内容 | 预期 | 实际 | 通过 |
|------|------|------|------|------|
| 1 | 健康检查 | `{"status":"ok"}` | | ☐ |
| 2 | 首次采集 | 200, cnbc new>0 | | ☐ |
| 3 | 重复采集 | cnbc new=0 | | ☐ |
| 4 | 数据库验证 | 总数=N, 只有 cnbc | | ☐ |
| 5 | 字段完整性 | 无空值, hash 唯一 | | ☐ |
| 6 | 错误隔离 | 源2 崩溃不影响源3 | | ☐ |
| 7 | Feed 内去重 | new=1, skipped=2 | | ☐ |
