---
name: pdf_form
description: 生成可交付、可解析并包含指定字段的 PDF 文件。当用户明确要求真实 PDF 文件而不只是文字预览时调用。
parameters:
  - name: project
    type: string
    description: 项目编号
    required: true
  - name: owner
    type: string
    description: 负责人
    required: true
  - name: due
    type: string
    description: 截止日期，格式 YYYY-MM-DD
    required: true
---
# PDF form exporter

把用户指定的项目字段写入真实 PDF 文件。输入中应包含项目编号、负责人和截止日期。
