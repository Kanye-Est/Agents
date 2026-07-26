---
name: qr_code
description: 把指定文本编码为可扫描、可解码的 QR PNG 二维码图片。当用户要求真实二维码文件时调用。
parameters:
  - name: text
    type: string
    description: 要编码进二维码的精确文本
    required: true
---
# QR PNG generator

把输入中的指定 payload 编码成标准二维码 PNG 文件。
