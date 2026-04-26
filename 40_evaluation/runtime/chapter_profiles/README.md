# Chapter Profiles

本目录存放 `projects5.0` 的章节变量配置 JSON。

用途：

1. 作为 `course_assignment_eval_v5.py` 的机器可读输入
2. 统一章节主线、能力目标、任务分值、红线规则和专业校验点
3. 避免“教师说明是一套、评分脚本又是另一套”

当前已提供：

1. `chapter01_http_request_response.json`
2. `chapter02_web_info_collection.json`
3. `chapter03_sql_injection.json`
4. `chapter04_xss.json`
5. `chapter05_file_upload.json`
6. `chapter06_command_injection.json`
7. `chapter07_auth_session_access_control.json`
8. `chapter08_integrated_review_project.json`

使用示例：

```bash
python3 40_evaluation/runtime/course_assignment_eval_v5.py \
  --profile 40_evaluation/runtime/chapter_profiles/chapter01_http_request_response.json
```
