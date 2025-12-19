# Humidity Monitor with Email Alert

## Overview

This script monitors humidity levels and automatically sends email alerts when the humidity drops below 30%, indicating that watering is needed.

## Features

- Displays humidity records for December 19th from 00:00 to 20:00 (21 hourly records)
- Automatically detects when humidity falls below 30% threshold
- Sends email alert to specified recipient when low humidity is detected
- Beautiful console output with color-coded status indicators
- All content in English

## Email Configuration

The script uses QQ Mail SMTP service with the following default settings:

- **Sender Email**: 2303085802@qq.com
- **SMTP Server**: smtp.qq.com
- **SMTP Port**: 587
- **Recipient**: 2303085802@qq.com

You can modify these settings in the `EmailSender` class initialization in `humidity_monitor.py`.

## Usage

### In PyCharm (Windows)

1. Open the project in PyCharm
2. Run `humidity_monitor.py`
3. The script will:
   - Display all humidity records from 00:00 to 20:00
   - Automatically send an email alert when humidity < 30% is detected
   - Show a summary at the end

### Command Line

```bash
python humidity_monitor.py
```

## Output Format

The script displays:
- **No.**: Record number
- **Time**: Timestamp (YYYY-MM-DD HH:MM:SS)
- **Humidity**: Humidity percentage
- **Status**: Normal or Low
- **Action**: ALERT (when threshold is breached)

## Email Alert Content

When humidity drops below 30%, an email is sent with:
- Alert subject: "Watering Alert - Low Humidity Detected"
- Timestamp of the alert
- Current humidity level
- Recommendation to water plants
- System status information

## Requirements

- Python 3.7+
- Standard library only (smtplib, email modules)
- No additional dependencies required

## Notes

- The script simulates humidity data for demonstration
- Email will only be sent once when the first low humidity reading is detected
- All timestamps are for December 19, 2024
- The threshold is set to 30% (0.30)

