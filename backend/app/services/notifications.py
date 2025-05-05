# backend/app/services/notifications.py
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.repositories import user_repository, account_repository, transaction_repository
from app.db.models.user import User
from app.db.models.account import Account
from app.db.models.transaction import Transaction, TransactionType

class NotificationService:
    """Service for sending notifications to users."""
    
    @staticmethod
    async def send_email(
        *,
        recipient_email: str,
        subject: str,
        body: str,
    ) -> bool:
        """
        Send an email notification.
        
        Args:
            recipient_email: Recipient email
            subject: Email subject
            body: Email body
            
        Returns:
            True if email sent successfully, False otherwise
        """
        # This is a placeholder for actual email sending logic
        # In a real implementation, you would use an email service like SendGrid, Mailgun, etc.
        
        # TODO: Implement actual email sending logic
        print(f"Sending email to {recipient_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        
        return True
    
    @staticmethod
    async def send_sms(
        *,
        phone_number: str,
        message: str,
    ) -> bool:
        """
        Send an SMS notification.
        
        Args:
            phone_number: Recipient phone number
            message: SMS message
            
        Returns:
            True if SMS sent successfully, False otherwise
        """
        # This is a placeholder for actual SMS sending logic
        # In a real implementation, you would use an SMS service like Twilio, Nexmo, etc.
        
        # TODO: Implement actual SMS sending logic
        print(f"Sending SMS to {phone_number}")
        print(f"Message: {message}")
        
        return True
    
    @staticmethod
    async def send_transaction_notification(
        db: Session,
        *,
        transaction_id: int,
    ) -> bool:
        """
        Send a notification for a transaction.
        
        Args:
            db: Database session
            transaction_id: Transaction ID
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        # Get transaction
        transaction = transaction_repository.get(db, id=transaction_id)
        if not transaction:
            return False
        
        # Get account
        account = account_repository.get(db, id=transaction.account_id)
        if not account:
            return False
        
        # Get user
        user = user_repository.get(db, id=account.user_id)
        if not user:
            return False
        
        # Format transaction amount
        amount_str = f"{transaction.amount:.2f} {transaction.currency}"
        
        # Prepare notification based on transaction type
        if transaction.transaction_type == TransactionType.DEPOSIT:
            subject = f"Deposit Notification: {amount_str}"
            body = (
                f"Dear {user.full_name},\n\n"
                f"A deposit of {amount_str} has been made to your account {account.account_number}.\n\n"
                f"Transaction Reference: {transaction.reference_id}\n"
                f"Description: {transaction.description}\n"
                f"Date: {transaction.created_at}\n\n"
                f"Your current balance is {account.balance:.2f} {account.currency}.\n\n"
                f"If you did not authorize this transaction, please contact us immediately.\n\n"
                f"Thank you for banking with us!\n\n"
                f"Best regards,\nBanking System"
            )
        
        elif transaction.transaction_type == TransactionType.WITHDRAWAL:
            subject = f"Withdrawal Notification: {amount_str}"
            body = (
                f"Dear {user.full_name},\n\n"
                f"A withdrawal of {amount_str} has been made from your account {account.account_number}.\n\n"
                f"Transaction Reference: {transaction.reference_id}\n"
                f"Description: {transaction.description}\n"
                f"Date: {transaction.created_at}\n\n"
                f"Your current balance is {account.balance:.2f} {account.currency}.\n\n"
                f"If you did not authorize this transaction, please contact us immediately.\n\n"
                f"Thank you for banking with us!\n\n"
                f"Best regards,\nBanking System"
            )
        
        elif transaction.transaction_type == TransactionType.TRANSFER:
            # Get recipient account if it's a transfer
            recipient_account = None
            if transaction.recipient_account_id:
                recipient_account = account_repository.get(db, id=transaction.recipient_account_id)
            
            recipient_info = ""
            if recipient_account:
                recipient_info = f" to account {recipient_account.account_number}"
            
            subject = f"Transfer Notification: {amount_str}"
            body = (
                f"Dear {user.full_name},\n\n"
                f"A transfer of {amount_str} has been made from your account {account.account_number}{recipient_info}.\n\n"
                f"Transaction Reference: {transaction.reference_id}\n"
                f"Description: {transaction.description}\n"
                f"Date: {transaction.created_at}\n\n"
                f"Your current balance is {account.balance:.2f} {account.currency}.\n\n"
                f"If you did not authorize this transaction, please contact us immediately.\n\n"
                f"Thank you for banking with us!\n\n"
                f"Best regards,\nBanking System"
            )
        
        elif transaction.transaction_type == TransactionType.PAYMENT:
            subject = f"Payment Notification: {amount_str}"
            body = (
                f"Dear {user.full_name},\n\n"
                f"A payment of {amount_str} has been made from your account {account.account_number}.\n\n"
                f"Transaction Reference: {transaction.reference_id}\n"
                f"Description: {transaction.description}\n"
                f"Date: {transaction.created_at}\n\n"
                f"Your current balance is {account.balance:.2f} {account.currency}.\n\n"
                f"If you did not authorize this transaction, please contact us immediately.\n\n"
                f"Thank you for banking with us!\n\n"
                f"Best regards,\nBanking System"
            )
        
        else:
            subject = f"Transaction Notification: {amount_str}"
            body = (
                f"Dear {user.full_name},\n\n"
                f"A transaction of {amount_str} has been processed on your account {account.account_number}.\n\n"
                f"Transaction Reference: {transaction.reference_id}\n"
                f"Transaction Type: {transaction.transaction_type.value}\n"
                f"Description: {transaction.description}\n"
                f"Date: {transaction.created_at}\n\n"
                f"Your current balance is {account.balance:.2f} {account.currency}.\n\n"
                f"If you did not authorize this transaction, please contact us immediately.\n\n"
                f"Thank you for banking with us!\n\n"
                f"Best regards,\nBanking System"
            )
        
        # Send email notification
        email_sent = await NotificationService.send_email(
            recipient_email=user.email,
            subject=subject,
            body=body,
        )
        
        # Send SMS notification if phone number available
        sms_sent = False
        if user.phone_number:
            sms_message = (
                f"Banking System: {transaction.transaction_type.value.capitalize()} of "
                f"{amount_str} on account {account.account_number}. "
                f"New balance: {account.balance:.2f} {account.currency}. "
                f"Ref: {transaction.reference_id}"
            )
            
            sms_sent = await NotificationService.send_sms(
                phone_number=user.phone_number,
                message=sms_message,
            )
        
        return email_sent or sms_sent
    
    @staticmethod
    async def send_account_created_notification(
        db: Session,
        *,
        account_id: int,
    ) -> bool:
        """
        Send a notification for account creation.
        
        Args:
            db: Database session
            account_id: Account ID
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        # Get account
        account = account_repository.get(db, id=account_id)
        if not account:
            return False
        
        # Get user
        user = user_repository.get(db, id=account.user_id)
        if not user:
            return False
        
        # Prepare notification
        subject = f"New Account Opened: {account.account_number}"
        body = (
            f"Dear {user.full_name},\n\n"
            f"Congratulations! Your new {account.account_type.value} account has been opened successfully.\n\n"
            f"Account Number: {account.account_number}\n"
            f"Account Type: {account.account_type.value.capitalize()}\n"
            f"Currency: {account.currency}\n"
            f"Opening Balance: {account.balance:.2f} {account.currency}\n"
            f"Date Opened: {account.created_at}\n\n"
            f"You can now start using your account for deposits, withdrawals, transfers, and payments.\n\n"
            f"Thank you for choosing Banking System!\n\n"
            f"Best regards,\nBanking System"
        )
        
        # Send email notification
        email_sent = await NotificationService.send_email(
            recipient_email=user.email,
            subject=subject,
            body=body,
        )
        
        # Send SMS notification if phone number available
        sms_sent = False
        if user.phone_number:
            sms_message = (
                f"Banking System: Your new {account.account_type.value} account {account.account_number} "
                f"has been opened successfully with {account.balance:.2f} {account.currency}."
            )
            
            sms_sent = await NotificationService.send_sms(
                phone_number=user.phone_number,
                message=sms_message,
            )
        
        return email_sent or sms_sent
    
    @staticmethod
    async def send_low_balance_notification(
        db: Session,
        *,
        account_id: int,
        threshold: float,
    ) -> bool:
        """
        Send a notification for low account balance.
        
        Args:
            db: Database session
            account_id: Account ID
            threshold: Balance threshold
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        # Get account
        account = account_repository.get(db, id=account_id)
        if not account:
            return False
        
        # Check if balance is below threshold
        if account.balance > threshold:
            return False
        
        # Get user
        user = user_repository.get(db, id=account.user_id)
        if not user:
            return False
        
        # Prepare notification
        subject = f"Low Balance Alert: Account {account.account_number}"
        body = (
            f"Dear {user.full_name},\n\n"
            f"This is to inform you that the balance in your {account.account_type.value} account "
            f"{account.account_number} has fallen below the threshold of {threshold:.2f} {account.currency}.\n\n"
            f"Current Balance: {account.balance:.2f} {account.currency}\n"
            f"Date: {datetime.now()}\n\n"
            f"To avoid any inconvenience, please deposit funds into your account at your earliest convenience.\n\n"
            f"Thank you for banking with us!\n\n"
            f"Best regards,\nBanking System"
        )
        
        # Send email notification
        email_sent = await NotificationService.send_email(
            recipient_email=user.email,
            subject=subject,
            body=body,
        )
        
        # Send SMS notification if phone number available
        sms_sent = False
        if user.phone_number:
            sms_message = (
                f"Banking System: Low balance alert for account {account.account_number}. "
                f"Current balance: {account.balance:.2f} {account.currency}, "
                f"below threshold of {threshold:.2f} {account.currency}."
            )
            
            sms_sent = await NotificationService.send_sms(
                phone_number=user.phone_number,
                message=sms_message,
            )
        
        return email_sent or sms_sent