# nametag

[![CI](https://github.com/eastyou/nametag/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/nametag/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

开学第一课，把名单变成桌上的姓名牌。一条命令生成 A4 折叠桌牌，打印、对折、立起来就能用。**零依赖，不联网，单文件 HTML。**

每张桌牌上下两半，上半张旋转 180°。沿中间虚线对折后，前后两面都是正的，不用胶水也能立在桌上。

## 特性

- **名单即数据**：CSV 两列「姓名,班级」，表头可有可无
- **两面镜像**：上半张自动旋转 180°，折叠后两面文字都朝上
- **自动排版**：默认每页 2×2 共 4 张，可调 1~4 行列，自动分页
- **字号自适应**：按姓名长度和卡片尺寸计算字号，长名字不会溢出
- **编码兼容**：自动识别 UTF-8（含 BOM）与 GBK，Excel 导出的 CSV 直接能用
- **数据校验**：空姓名、超长姓名、多余列都会指出具体行号
- **重名提示**：同班同名会列出所在行；加 `--strict` 可直接中止
- **68 个单元测试**：覆盖名单解析、编码、重名与 HTML 输出

## 安装

```bash
pip install nametag
```

也可以直接下载源码，在项目目录里运行：

```bash
python -m nametag --help
```

## 用法

用示例名单生成 2×2 桌牌：

```bash
nametag -i examples/students.csv -o 姓名桌牌.html
```

每页 3 列 2 行，适合人数较多的班级：

```bash
nametag -i 名单.csv --columns 3 --rows 2 -o 桌牌_3x2.html
```

发现重名时直接中止，先把名单核对清楚：

```bash
nametag -i 名单.csv --strict -o 桌牌.html
```

## 名单格式

默认读取前两列：第一列姓名，第二列班级。班级可以省略。

```csv
姓名,班级
张小明,初二(3)班
李雨欣,初二(3)班
```

- 表头支持 `姓名` / `名字` / `学生姓名` / `name`，第二列支持 `班级` / `班` / `班别` / `class`
- 空行自动跳过；行首行尾的空格会被清理
- 姓名最多 20 个字符，班级最多 20 个字符
- 超过两列且第三列以后有内容时，会提示具体行号，避免误把备注当班级

## 参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `-i, --input` | 必填 | 名单 CSV 路径 |
| `-o, --output` | `姓名桌牌.html` | 输出文件路径 |
| `--columns` | `2` | 每页列数，1~4 |
| `--rows` | `2` | 每页行数，1~4 |
| `--title` | `姓名桌牌` | 文档标题与屏幕提示 |
| `--strict` | 关闭 | 发现同班重名时报错中止 |

## 打印与折叠

1. 浏览器打开 HTML，按 `Ctrl/Cmd + P`
2. 纸张选 A4、纵向，边距选「无」，缩放 100%
3. 打印后沿每张卡片中间的虚线对折
4. 上半张已经被旋转过，折好后两面都是正的

建议使用 160g 以上的卡纸，立得更稳；普通纸可以夹一个回形针或放进透明桌牌套。

## 开发

```bash
python -m unittest discover -s tests -v
```

## License

[MIT](LICENSE) © 2026 eastyou
