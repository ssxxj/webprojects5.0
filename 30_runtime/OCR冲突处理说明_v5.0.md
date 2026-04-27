# OCR 可选依赖改动冲突处理说明（给非程序员）

## 一、检测结果（你看到的冲突是什么）
GitHub 提示“这个分支有必须解决的冲突”，说明：
- 你当前的 PR 分支和目标分支，都改了同一个文件的同一段代码；
- GitHub 不能自动判断该保留哪一版，所以需要人工选择。

本次冲突文件是评估引擎主文件（截图里显示为中文路径名），本质上就是 OCR 相关逻辑与主评分流程的重叠修改。

## 二、这个问题可能带来的风险
如果不正确处理冲突，可能出现：
1. **评分中断风险**：把旧代码覆盖回来后，缺少降级保护，OCR 异常会中断评分。
2. **结果不可解释风险**：丢失 `ocr_status` 字段后，老师无法判断是否已降级到“仅文本模式”。
3. **隐性回归风险**：测试代码未同步冲突解决结果，线上行为和本地验证不一致。

## 三、建议修复方案（非技术同学也能执行）
### 方案 A：GitHub 网页“解决冲突”
1. 打开 PR，点击“解决冲突”。
2. 找到冲突标记：
   - `<<<<<<<` 到 `=======` 是“当前分支版本”；
   - `=======` 到 `>>>>>>>` 是“目标分支版本”。
3. 以“保留 OCR 降级能力”为准，确保最终代码保留以下能力：
   - OCR 缺失时不崩溃；
   - OCR 运行出错时自动回退文本抽取；
   - 输出中包含 `ocr_status`。
4. 标记冲突已解决并提交。

### 方案 B：命令行解决（给开发同学）
```bash
git fetch origin
git merge origin/main
# 手工编辑冲突文件，删除 <<<<<<< ======= >>>>>>> 标记
git add <冲突文件>
git commit
```

## 四、验收清单（合并前必须确认）
- `ocr_status` 字段仍存在（单文件评分与目录评分都应有）。
- OCR 初始化失败时不会中断。
- OCR 运行时异常时会自动降级继续。
- 单元测试通过。

## 五、一句话结论
这不是“系统坏了”，而是“两个分支都改了同一块代码”。按上面流程保留 OCR 的降级与状态输出能力，就能安全合并。

## 六、你截图这个冲突应当怎么点
你图里冲突发生在 `build_rapidocr_instance()` 和 `OCRExtractor` 初始化段，建议直接点 **“接受两种更改”**，然后把冲突块手动整理成下面这版（删除所有 `<<<<<<< ======= >>>>>>>` 标记）：

```python
def build_rapidocr_instance() -> tuple[Any | None, str]:
    try:
        rapidocr_module = importlib.import_module("rapidocr_onnxruntime")
        rapidocr_cls = getattr(rapidocr_module, "RapidOCR", None)
        if rapidocr_cls is None:
            return None, "rapidocr_onnxruntime 中未找到 RapidOCR。"
        return rapidocr_cls(), ""
    except Exception as exc:
        return None, f"RapidOCR 初始化失败：{exc}"


class OCRExtractor:
    def __init__(self) -> None:
        self.ocr, self.ocr_error = build_rapidocr_instance()
        self.ocr_available = self.ocr is not None
        self.ocr_runtime_error = ""
```

原因：这版同时保留了“可选依赖不崩溃”和“更清晰错误信息/运行期状态追踪”两方面能力。

### 点完后的 3 个快速自检
1. 文件内不再有 `<<<<<<<`、`=======`、`>>>>>>>`。
2. `OCRExtractor.__init__` 里有 `self.ocr_runtime_error = ""`。
3. `build_rapidocr_instance()` 的 `except` 返回的是 `RapidOCR 初始化失败：...`。
