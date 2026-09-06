# changelog.d/ (可选发版工具)

平时单人日常开发**无需**在此创建文件。

仅在准备打正式 Release 标签、希望自动生成结构化更新日志时，可选择性在其中添加 `<type>-<desc>.md` 碎片，然后运行 `python scripts/compile_changelog.py` 自动汇总归档到根目录 `CHANGELOG.md`。
