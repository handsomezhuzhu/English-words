# 英语单词学习系统

## 项目介绍

这是一个用于学习和记忆英语单词的Web应用程序，主要功能包括：

- 创建和管理多个单词本
- 添加、编辑和删除单词
- 为单词添加多个翻译和词性
- 导出单词本为CSV文件
- 备份和恢复数据库

## 快速开始

### 环境要求
- Python 3.7+

### 安装步骤
1. 克隆项目仓库
2. 安装依赖：
```bash
pip install -r requirements.txt
```
3. 初始化数据库：
```bash
python init_db.py
```
4. 启动服务：
```bash
python app.py
```
5. 访问 http://localhost:5000 使用系统

## 注意事项

- 默认使用5000端口，请确保端口可用
- 数据存储在SQLite数据库中，位于instance/words.db
- 导出CSV前请确保当前单词本有内容
- 删除单词本操作不可逆，请谨慎操作

## 开发说明

### 项目结构
```
app.py         # 主程序
models.py      # 数据库模型
Baidu_Text_transAPI.py  # 百度翻译API
requirements.txt  # 依赖文件
templates/      # 前端模板
instance/       # 数据库文件
```

### 数据备份与恢复

1. 备份数据库：
   - 访问 `/export_db` 路由，系统会自动下载当前数据库文件
   - 备份文件名为 `words.db`

2. 恢复数据库：
   - 将备份的 `words.db` 文件替换 `instance/words.db`
   - 重启应用即可恢复数据

### 使用注意事项

- 默认单词本无法删除
- 每个单词可以添加多个翻译
- 系统支持同时管理多个单词本
- 建议定期备份数据库文件

### 定期备份数据库

本系统支持每5次单词提交自动备份一次数据库，以确保数据的安全性。备份文件会以时间戳命名，方便您识别和管理。

#### 备份规则
- 每次提交单词时，系统会记录提交次数。
- 当提交次数达到5次时，系统会自动备份数据库。
- 备份文件名格式为 `words_backup_YYYYMMDDHHMMSS.db`，其中 `YYYYMMDDHHMMSS` 是备份时的时间戳。

#### 备份位置
备份文件会存储在 `instance` 目录下。

## 贡献指南

欢迎提交PR，请遵循以下规范：
1. 在开发分支上进行修改
2. 提交清晰的commit message
3. 确保代码风格一致