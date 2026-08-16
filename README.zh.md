# 微软雅黑 TTC 精简工具

简体中文 | [English](README.md)

本项目用于构建精简的 Microsoft YaHei 6.31 TTC，同时保留 TrueType hinting、本地化名称，以及“微软雅黑”和“微软雅黑 UI”两个字体面的共享表。

## 字符集文件

构建脚本读取以下 Unicode 清单，每行一个 `U+XXXX` 码位：

- `unicode/msyh-unicode-superset.txt`：微软雅黑（共 13736 个字符）
- `unicode/msyhui-unicode-superset.txt`：微软雅黑 UI（共 13759 个字符）

注：只会保留输入 TTC 本身存在的字符。输入字体不支持的请求码位会在构建时报告，无法凭空生成对应字形。

## 环境要求

- Python 3.12 或更高版本
- [FontTools](https://github.com/fonttools/fonttools)

创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 构建命令

```powershell
build.py <输入字体.ttc> <输出字体.ttc>
```

示例：

```powershell
build.py .\msyh.ttc .\target\msyh.ttc
```

输出文件保留 `cvt `、`fpgm`、`prep`、`gasp` 等 hinting 数据，删除设备相关度量表 `hdmx`、`LTSH`、`VDMX`；同时保留“微软雅黑”的简中本地化名称，并让两个字体面共享核心字形和布局表。

## 许可证

MIT License

## 贡献

欢迎贡献！请随时提交问题或拉取请求。
