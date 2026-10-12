# 来源、文件完整性与整理记录

| 文件 | 用途 |
| --- | --- |
| [original_yearbook_file_index.csv](original_yearbook_file_index.csv) | 外部年鉴原件和表格索引 |
| [withheld_source_index.csv](withheld_source_index.csv) | 外部原件的来源信息、获取线索与未随仓库分发的材料 |
| [file_manifest.csv](file_manifest.csv) | 发布文件的物理路径、逻辑路径、存储形式及SHA-256 |
| [release_receipt.json](release_receipt.json) | 当前发布范围、文件数量及清单散列 |
| [repository_cleanup_20261012.csv](repository_cleanup_20261012.csv) | 本轮删除、移动和代码路径调整；旧路径可用于读取历史来源记录 |
| [repository_audit_20261012.json](repository_audit_20261012.json) | 仓库整理后的检查项目与执行结果 |
| [publication_transformations.json](publication_transformations.json) | 初次发布时的路径脱敏等历史处理记录 |

原值CSV、原始附件和保留的CSV统计结果保持原字节。目录调整记录旧路径与新路径；原始证据中的旧路径按形成时的信息保存，可借助整理记录定位现存文件。代码和描述性元数据中的执行路径则随本轮目录调整同步更新。

清单同时登记gzip文件及其解压后逻辑内容的散列。运行`python tools/verify_release.py`校核文件完整性；运行`python tools/materialize_data.py`恢复两份大CSV。

发布清单不包含自身及由其生成的`release_receipt.json`，以避免循环散列。Git内部文件、环境、缓存和解压副本不属于发布文件。
