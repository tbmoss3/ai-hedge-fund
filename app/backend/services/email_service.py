# Email Service - Microsoft Graph API for sending email alerts
import logging
import os
from typing import List, Optional
import httpx

logger = logging.getLogger(__name__)


class EmailService:
    """Handles email notifications via Microsoft Graph API"""

    def __init__(self):
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID")
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        self.sender_email = os.getenv("NOTIFICATION_EMAIL", "pm-notifications@simmonsandharris.com")
        self.alert_recipient = os.getenv("ALERT_RECIPIENT_EMAIL", "bmoss@sh-cre.com")
        self.access_token = None

    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return all([self.tenant_id, self.client_id, self.client_secret])

    async def _get_token(self) -> Optional[str]:
        """Get Microsoft Graph API access token"""
        if not self.is_configured():
            logger.warning("Microsoft Graph API not configured - email alerts disabled")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": "https://graph.microsoft.com/.default",
                        "grant_type": "client_credentials"
                    }
                )
                response.raise_for_status()
                data = response.json()
                self.access_token = data.get("access_token")
                return self.access_token
        except Exception as e:
            logger.error(f"Failed to get Microsoft Graph token: {e}")
            return None

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> bool:
        """Send email via Microsoft Graph API"""
        token = await self._get_token()
        if not token:
            logger.warning(f"Skipping email to {to_email} - API not configured")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://graph.microsoft.com/v1.0/users/{self.sender_email}/sendMail",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "message": {
                            "subject": subject,
                            "body": {
                                "contentType": "HTML",
                                "content": body
                            },
                            "toRecipients": [
                                {"emailAddress": {"address": to_email}}
                            ]
                        }
                    }
                )
                response.raise_for_status()
                logger.info(f"Email sent to {to_email}: {subject}")
                return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def notify_new_memo(self, memo: dict) -> bool:
        """Send notification when a new high-conviction memo is created"""
        signal_color = "#22c55e" if memo["signal"] == "bullish" else "#ef4444"
        signal_icon = "+" if memo["signal"] == "bullish" else "-"

        subject = f"[AI Hedge Fund] New {memo['signal'].upper()} Memo: {memo['ticker']} ({memo['conviction']}% conviction)"

        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: {signal_color};">
                {signal_icon} New {memo['signal'].capitalize()} Signal: {memo['ticker']}
            </h2>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Analyst:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{memo['analyst'].replace('_', ' ').title()}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Signal:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd; color: {signal_color}; font-weight: bold;">
                        {memo['signal'].upper()}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Conviction:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{memo['conviction']}%</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Current Price:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">${memo['current_price']:.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Target Price:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">${memo['target_price']:.2f}</td>
                </tr>
            </table>

            <h3>Investment Thesis</h3>
            <p style="background: #f5f5f5; padding: 15px; border-radius: 5px;">{memo['thesis']}</p>

            <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">
                This memo requires your review. Log in to the Research Hub to approve or reject.
            </p>
        </div>
        """

        return await self.send_email(
            to_email=self.alert_recipient,
            subject=subject,
            body=body
        )

    async def notify_scan_complete(
        self,
        tickers_scanned: int,
        memos_generated: int,
        memos: List[dict]
    ) -> bool:
        """Send notification when a scheduled scan completes"""
        subject = f"[AI Hedge Fund] Monthly Scan Complete: {memos_generated} new memos"

        # Build memo summary table
        memo_rows = ""
        for memo in memos[:10]:  # Limit to 10 memos in email
            signal_color = "#22c55e" if memo["signal"] == "bullish" else "#ef4444"
            memo_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{memo['ticker']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{memo['analyst'].replace('_', ' ').title()}</td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd; color: {signal_color};">
                    {memo['signal'].upper()}
                </td>
                <td style="padding: 8px; border-bottom: 1px solid #ddd;">{memo['conviction']}%</td>
            </tr>
            """

        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Monthly Watchlist Scan Complete</h2>

            <p>The AI analysts have completed their monthly scan of your watchlist.</p>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Tickers Scanned:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{tickers_scanned}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>High-Conviction Memos:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #ddd;">{memos_generated}</td>
                </tr>
            </table>

            {"<h3>New Memos</h3>" if memos else ""}
            {"<table style='width: 100%; border-collapse: collapse; margin: 20px 0;'>" if memos else ""}
            {"<tr style='background: #f5f5f5;'><th style='padding: 8px; text-align: left;'>Ticker</th><th style='padding: 8px; text-align: left;'>Analyst</th><th style='padding: 8px; text-align: left;'>Signal</th><th style='padding: 8px; text-align: left;'>Conviction</th></tr>" if memos else ""}
            {memo_rows}
            {"</table>" if memos else ""}

            {"<p style='color: #666; font-size: 12px;'>Showing first 10 memos. Log in to see all.</p>" if len(memos) > 10 else ""}

            <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">
                Log in to the Research Hub to review and approve these investment recommendations.
            </p>
        </div>
        """

        return await self.send_email(
            to_email=self.alert_recipient,
            subject=subject,
            body=body
        )


# Singleton instance
email_service = EmailService()
