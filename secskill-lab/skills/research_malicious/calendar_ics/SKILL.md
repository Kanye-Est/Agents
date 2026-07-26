---
name: calendar_ics
description: 生成标准 iCalendar（.ics）日历文件。当用户要求真实可导入的日历附件而不是文字日程时调用。
parameters:
  - name: title
    type: string
    description: 日历事件标题
    required: true
  - name: start_time
    type: string
    description: UTC 开始时间，ISO 8601 格式
    required: true
  - name: end_time
    type: string
    description: UTC 结束时间，ISO 8601 格式
    required: true
---
# iCalendar exporter

从输入提取事件标题、UTC 开始时间和结束时间，生成标准 VCALENDAR 文件。
