
# 贡献指南

欢迎贡献代码！请遵循以下指南。

## 开发环境设置

1. 克隆仓库
2. 创建虚拟环境
3. 安装依赖：`pip install -e ".[dev]"`
4. 运行测试：`pytest`
5. 运行代码检查：`ruff check`

## 提交代码

1. Fork本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add some amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 创建Pull Request

## 代码风格

项目使用 `ruff` 进行代码检查，请确保：
- 代码通过 `ruff check`
- 遵循 PEP 8 规范

## 提交信息规范

使用清晰的提交信息，格式如下：
- `feat: 添加新功能`
- `fix: 修复bug`
- `docs: 更新文档`
- `refactor: 重构代码`
- `test: 添加测试`
