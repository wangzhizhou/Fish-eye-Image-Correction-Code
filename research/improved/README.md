# research/improved — 改进方案（本研究提出，不是原始代码）

`program/` 未做任何修改。这里是按 REPORT §14/§16 实施的改进，以及与原始实现（经 `research/cpp_harness` 编译运行）的对比。结果见 [`../REPORT.md` §16](../REPORT.md)。

| 文件 | 内容 | 对应建议 |
|---|---|---|
| `cpp/fisheye_improved.{hpp,cpp}` | 改进的校正库：闭式 LCCP（无二分）、经度/纬度可分别选线性或 LCCP(ω)、4 种镜头模型正反向一致、按 FOV 截取范围并屏蔽圆外、输出尺寸由 R 推导、double 圆参数、可分离预计算 + `cv::remap` 双线性、`atan2`、无 static/无 `ret.jpg`；预计算视线的全景浏览器 | T1 T2 T4 I1–I7 |
| `cpp/improved_cli.cpp` | 非交互命令行：`correct` `maps` `roundtrip` `time` `viewer` `statics` | — |
| `cpp/build.sh` | 分别用 OpenCV 4.14 与 5.1 编译；顺便用 OpenCV 5 编译原始 `program/`（记录失败） | I6 |
| `geometry.py` | 与 C++ 相同的映射（Python 版），用于真值光线和交叉检验 | — |
| `projection_metrics.py` | 投影形变度量：形状形变 \|ln(k/h)\|、分辨率均匀度，按立体角加权 | T2 T3 |
| `circle_radial.py` | 无阈值圆域精化：径向剖面上"最外侧偏离背景"的位置 + 最强下降沿亚像素定位 + Huber 几何拟合 | T5 |
| `sphere_stitch.py` | 球面拼接：SIFT → 光线 → 旋转 RANSAC → 全局优化（含共享焦距，即镜头视场自标定）→ 360×180 等距柱状全景 | T6 T4 |
| `synthetic.py` | 抗锯齿合成场景（立方体房间），可精确渲染鱼眼输入和任意投影的理想输出 | 评价用 |
| `compare_improved.py` | 原始 vs 改进的全部对比 → `results/metrics/improved.json`、`results/figures/improved_*` | — |

```bash
brew install opencv@4 opencv            # OpenCV 4.x 与 5.x
bash research/cpp_harness/build.sh      # 原始代码（对照组）
bash research/improved/cpp/build.sh     # 改进实现
python3 research/improved/compare_improved.py
```
