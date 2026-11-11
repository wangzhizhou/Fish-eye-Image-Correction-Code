# research/ — Fish-eye Image Correction 源码研究与 Python 复现

本目录独立于原工程（`program/` 未做任何修改）。完整报告见 [`REPORT.md`](REPORT.md)，简明结论见 [`results/REPORT.md`](results/REPORT.md)。论文修订建议见 [`PAPER_REVISION.md`](PAPER_REVISION.md)。

## 环境

```bash
cd research
python3 -m pip install -r requirements.txt     # numpy scipy opencv-python matplotlib sympy mpmath pytest
```

在 Python 3.10 与 3.13 上运行过；第二阶段在 Python 3.14.6（numpy 2.5.4、opencv-python 5.0.0、sympy 1.14.0）上重新运行。

## 运行

```bash
python3 run_all.py            # 全部实验 + 符号验证 + pytest（约 3 分钟）
python3 run_all.py --quick    # VALS 实验减少蒙特卡洛次数
python3 -m pytest -q tests    # 只跑测试（约 3 秒；未装 sympy 时符号测试自动跳过）
python3 experiments/verify_symbolic.py   # SymPy + 50 位 mpmath 验证全部闭式解
```

实验从仓库读取真实图像（`ImagesForTest/`、`resources/`）。若 `research/` 不在仓库根目录下，设置 `FISHEYE_REPO=/path/to/Fish-eye-Image-Correction-Code`。

| 脚本 | 内容 | 输出 |
|---|---|---|
| `experiments/experiment_projection.py` | 实验 A：四种投影模型 | `results/*/projection_A_*` |
| `experiments/experiment_lccp.py` | 实验 B/C：LCCP 曲线、二分精度、static 缓存、采样网格 | `results/*/lccp_*` |
| `experiments/experiment_roundtrip.py` | 实验 D：Correction4 ↔ Correction5 往返误差、正向映射空洞 | `results/*/roundtrip_D*` |
| `experiments/experiment_real.py` | 实验 E：与原程序输出 `resources/corrected0.jpg` 对比；真实图像；**合成**棋盘格 | `results/*/real_E*`, `synthetic_E3*` |
| `experiments/experiment_vals.py` | VALS / Kasa：合成边缘点、合成图像参数扫描、真实图像稳定性 | `results/*/vals_E*` |
| `experiments/verify_symbolic.py` | 符号/高精度验证 | `results/metrics/symbolic_verification.json` |

## C++ 实测（原始 program/，不修改）

需要 OpenCV 4.x（源码用了 OpenCV 5 已删除的 C 头文件）。默认使用 Homebrew `opencv@4`，其他安装路径用 `OPENCV_PREFIX` 指定：

```bash
brew install opencv@4
bash research/cpp_harness/build.sh          # 生成 harness、harness_asan_ndebug、navigator、navigator_asan
python3 research/cpp_harness/compare.py     # C++ 与 Python 逐项对比 -> results/metrics/cpp_harness.json
```

harness 构建好以后，`run_all.py` 会自动运行 compare.py，`tests/test_cpp_harness.py` 的 5 个测试也会启用（未构建时跳过）。

## 改进实现（第三阶段）

见 [`improved/README.md`](improved/README.md) 和 REPORT §16。需要 OpenCV 4 和（可选）OpenCV 5：

```bash
brew install opencv@4 opencv
bash research/improved/cpp/build.sh
python3 research/improved/compare_improved.py    # -> results/metrics/improved.json, results/figures/improved_*
```

两个 build.sh 都执行过以后，`run_all.py` 会自动运行这个对比；`tests/test_improved.py` 的 C++ 部分在未构建时跳过。

## 目录

```
src/
  kasa.py                 Kasa（含源码 int 截断版）、Pratt、Taubin、几何、Huber、RANSAC
  vals.py                 VALS 逐行移植 vals_source + 改进版 vals_improved + 合成数据
  fisheye_models.py       四种镜头模型、焦距、反函数
  lccp.py                 func/getPhi/func1/getPhi1/auxFunc 源码移植 + 闭式解
  coordinate_transform.py 像素/中心化/极坐标/球面/经纬坐标；OpenCV fastAtan2 复刻
  correction.py           Correction2/3/4（反向）/5（正向），source_like 与精确两种模式
experiments/              实验脚本（见上表），_common.py 为公共路径与绘图样式
tests/                    pytest：kasa、projection、lccp、roundtrip、vals、symbolic
results/figures/          全部图
results/metrics/          全部数值结果（json / csv）
tools/remove_orzcalibration_submodule.sh   清理不存在的 OrzCalibration 子模块
improved/                 改进方案：C++ 库/CLI、圆检测、球面拼接、投影度量、对比脚本（见 improved/README.md）
cpp_harness/              harness.cpp（原始源码 unity build 的测试驱动）、build.sh、compare.py；build/ 不入库
```

## 如何独立验证关键结论

| 结论 | 验证 |
|---|---|
| auxFunc 闭式解、h(w)=√2 sin w/sin(3π/4−w)、w∈(0,3π/4) | `verify_symbolic.py`；`tests/test_lccp.py` |
| getPhi 在赤道附近误差 0.0123 rad | `tests/test_lccp.py::test_getphi_bisection_error_peaks_at_equator`；`lccp_B2_bisection_accuracy.png` |
| 该误差存在于原 C++ 输出中 | `experiment_real.py` → `metrics/real_E.json`（赤道行 MAE 1.12 vs 8.28）；C++ 逐字节复现见 `cpp_harness.json` |
| C3 与 C4 默认参数下不等价 | `lccp_C_sampling_grids.png`；`correction.c3_latlon` vs `c4_latlon` |
| C4/C5 仅在 EQUIDISTANCE 下互逆 | `tests/test_roundtrip.py`；`metrics/roundtrip_D.json` |
| static 缓存 bug | `tests/test_lccp.py::test_static_cache_bug` |
| C++ 行为与移植逐位一致、仓库输出逐字节复现、`cv::Point` 截断 | `tests/test_cpp_harness.py`；`metrics/cpp_harness.json` |

## 清理 OrzCalibration 子模块

该子模块指向的仓库已不存在。在仓库根目录执行（第二阶段已执行并暂存）：

```bash
bash research/tools/remove_orzcalibration_submodule.sh   # 只暂存不提交，可重复执行
git status                                                # 确认后自行 git commit
```
