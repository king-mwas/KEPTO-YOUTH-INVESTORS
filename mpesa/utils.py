import requests
import json
from base64 import b64encode
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils import timezone
import logging

from .models import MpesaCredentials, StkPushRequest, MpesaTransaction, MpesaCallback

logger = logging.getLogger(__name__)


class MpesaAPIClient:
    def __init__(self):
        try:
            self.credentials = MpesaCredentials.objects.filter(is_active=True).first()
            if not self.credentials:
                raise ValueError("No active M-Pesa credentials found")
        except MpesaCredentials.DoesNotExist:
            raise ValueError("M-Pesa credentials not configured")

    def get_access_token(self):
        cache_key = 'mpesa_access_token'
        token = cache.get(cache_key)

        if token:
            return token

        try:
            auth_string = f"{self.credentials.consumer_key}:{self.credentials.consumer_secret}"
            auth_bytes = b64encode(auth_string.encode()).decode()

            headers = {
                'Authorization': f'Basic {auth_bytes}',
                'Content-Type': 'application/json',
            }

            response = requests.get(
                self.credentials.access_token_url,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            token = data.get('access_token')

            if token:
                cache.set(cache_key, token, timeout=3600)

            return token

        except requests.RequestException as e:
            logger.error(f"Failed to get access token: {str(e)}")
            raise

    def initiate_stk_push(self, member, amount, phone_number, deposit=None):
        try:
            access_token = self.get_access_token()

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password_string = f"{self.credentials.business_shortcode}{self.credentials.pass_key}{timestamp}"
            password = b64encode(password_string.encode()).decode()

            payload = {
                'BusinessShortCode': self.credentials.business_shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(float(amount)),
                'PartyA': phone_number,
                'PartyB': self.credentials.business_shortcode,
                'PhoneNumber': phone_number,
                'CallBackURL': self.credentials.callback_url,
                'AccountReference': f"KEPTO-{member.member_id}",
                'TransactionDesc': 'Savings Deposit - KEPTO Youth Investors',
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }

            response = requests.post(
                self.credentials.api_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()

            stk_request = StkPushRequest.objects.create(
                member=member,
                deposit=deposit,
                amount=amount,
                phone_number=phone_number,
                status=StkPushRequest.SENT,
                checkout_request_id=result.get('CheckoutRequestID'),
                response_code=result.get('ResponseCode'),
                response_description=result.get('ResponseDescription'),
                expires_at=timezone.now() + timedelta(minutes=2),
            )

            logger.info(f"STK Push initiated for {member.member_id}: {stk_request.request_id}")
            return stk_request

        except requests.RequestException as e:
            logger.error(f"STK Push initiation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during STK Push: {str(e)}")
            raise

    def query_stk_status(self, stk_request):
        try:
            access_token = self.get_access_token()

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password_string = f"{self.credentials.business_shortcode}{self.credentials.pass_key}{timestamp}"
            password = b64encode(password_string.encode()).decode()

            payload = {
                'BusinessShortCode': self.credentials.business_shortcode,
                'Password': password,
                'Timestamp': timestamp,
                'CheckoutRequestID': stk_request.checkout_request_id,
            }

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
            }

            query_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query' if self.credentials.is_sandbox else \
                        'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'

            response = requests.post(
                query_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"STK Status queried for {stk_request.member.member_id}: {result}")
            return result

        except requests.RequestException as e:
            logger.error(f"STK Status query failed: {str(e)}")
            raise

    @staticmethod
    def process_callback(callback_data):
        try:
            body = callback_data.get('Body', {})
            stk_callback = body.get('stkCallback', {})

            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_code = stk_callback.get('ResultCode')
            result_description = stk_callback.get('ResultDesc')
            merchant_request_id = stk_callback.get('MerchantRequestID')
            callback_metadata = stk_callback.get('CallbackMetadata', {})

            stk_request = StkPushRequest.objects.get(checkout_request_id=checkout_request_id)

            transaction = MpesaTransaction.objects.create(
                transaction_id=merchant_request_id,
                stk_push_request=stk_request,
                member=stk_request.member,
                phone_number=stk_request.phone_number,
                amount=stk_request.amount,
                result_code=result_code,
                result_description=result_description,
                merchant_request_id=merchant_request_id,
                checkout_request_id=checkout_request_id,
                raw_response=callback_data,
            )

            if result_code == '0':
                transaction.status = MpesaTransaction.SUCCESS
                stk_request.status = StkPushRequest.COMPLETED

                items = callback_metadata.get('Item', [])
                for item in items:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        transaction.mpesa_receipt_number = item.get('Value')
                    elif item.get('Name') == 'TransactionDate':
                        try:
                            dt = datetime.strptime(str(item.get('Value')), '%Y%m%d%H%M%S')
                            transaction.completed_at = timezone.make_aware(dt)
                        except:
                            pass

                if stk_request.deposit:
                    stk_request.deposit.transaction_code = transaction.mpesa_receipt_number
                    stk_request.deposit.status = 'approved'
                    stk_request.deposit.save()

            else:
                transaction.status = MpesaTransaction.FAILED
                stk_request.status = StkPushRequest.CANCELLED

            transaction.save()
            stk_request.save()

            logger.info(f"Callback processed for {stk_request.member.member_id}: {result_code}")
            return transaction

        except StkPushRequest.DoesNotExist:
            logger.error(f"STK Request not found for checkout_request_id: {checkout_request_id}")
            raise
        except Exception as e:
            logger.error(f"Error processing callback: {str(e)}")
            raise
