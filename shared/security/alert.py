# shared/security/alert.py
# 역할: 보안 이벤트 알림 (Slack Webhook)
# 관련 챕터: Chapter 10

import logging
import httpx

logger = logging.getLogger(__name__)


class SecurityAlertService:

    def __init__(self, slack_webhook_url: str = ""):
        self.slack_webhook_url = slack_webhook_url

    async def send(self, level: str, event: str, detail: dict, user_id: str = None) -> None:
        message = self._format_message(level, event, detail, user_id)
        logger.warning("security alert | level=%s event=%s user=%s", level, event, user_id)

        if self.slack_webhook_url:
            await self._send_slack(message, level)

    def _format_message(self, level: str, event: str, detail: dict, user_id: str) -> str:
        emoji = {"HIGH": "🚨", "MEDIUM": "⚠️", "LOW": "ℹ️"}.get(level, "🔔")
        return (
            f"{emoji} *MCP 보안 알림* [{level}]\n"
            f"이벤트: `{event}`\n"
            f"사용자: `{user_id or 'unknown'}`\n"
            f"상세: {detail}"
        )

    async def _send_slack(self, message: str, level: str) -> None:
        color = {"HIGH": "#e74c3c", "MEDIUM": "#f39c12", "LOW": "#3498db"}.get(level, "#95a5a6")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    self.slack_webhook_url,
                    json={
                        "attachments": [{
                            "color": color,
                            "text": message,
                            "mrkdwn_in": ["text"],
                        }]
                    },
                )
        except Exception as e:
            logger.error("slack alert failed: %s", e)
