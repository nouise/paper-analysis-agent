#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix emojis in publisher.py"""
import codecs

# 读取文件
with codecs.open('wechat_article_skills/wechat-draft-publisher/publisher.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 只替换特定的 emoji 字符
replacements = {
    '\u2713': '[V]',  # checkmark
    '\u2717': '[X]',  # x mark
    '\u26a0': '[!]',  # warning
    '\u2192': '->',  # arrow
    '\U0001f4a1': '[TIP]',  # lightbulb
}

# 替换特定的 emoji
for emoji, replacement in replacements.items():
    count = content.count(emoji)
    if count > 0:
        content = content.replace(emoji, replacement)
        print(f"Replaced {count} occurrences of U+{ord(emoji):04X}")

# 写回文件
with codecs.open('wechat_article_skills/wechat-draft-publisher/publisher.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
