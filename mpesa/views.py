import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .utils import MpesaAPIClient
from .models import StkPushRequest, MpesaTransaction, MpesaCallback
from savings.models import Deposit
from accounts.models import Member

logger = logging.getLogger(__name__)


@login_required
def initiate_deposit_payment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        amount = data.get('amount')
        phone_number = request.user.member.phone_number

        if not amount or float(amount) <= 0:
            return JsonResponse({'error': 'Invalid amount'}, status=400)

        deposit = Deposit.objects.create(
            member=request.user.member,
            amount=amount,
            status=Deposit.PENDING,
        )

        client = MpesaAPIClient()
        stk_request = client.initiate_stk_push(
            member=request.user.member,
            amount=amount,
            phone_number=phone_number,
            deposit=deposit,
        )

        return JsonResponse({
            'success': True,
            'message': 'STK Push initiated. Please enter your M-Pesa PIN.',
            'request_id': str(stk_request.request_id),
            'checkout_request_id': stk_request.checkout_request_id,
        })

    except Exception as e:
        logger.error(f"Error initiating STK Push: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@csrf_exempt
def mpesa_callback(request):
    try:
        callback_data = json.loads(request.body)

        callback = MpesaCallback.objects.create(
            callback_type='stk_push',
            raw_body=callback_data,
        )

        transaction = MpesaAPIClient.process_callback(callback_data)
        callback.transaction = transaction
        callback.processed = True
        callback.save()

        logger.info(f"M-Pesa callback processed: {callback.callback_id}")

        return JsonResponse({
            'ResultCode': 0,
            'ResultDesc': 'Callback processed successfully'
        })

    except Exception as e:
        logger.error(f"Error processing callback: {str(e)}")
        return JsonResponse({
            'ResultCode': 1,
            'ResultDesc': f'Error: {str(e)}'
        }, status=500)


@login_required
def query_transaction_status(request, request_id):
    try:
        stk_request = StkPushRequest.objects.get(request_id=request_id, member=request.user.member)

        client = MpesaAPIClient()
        status_result = client.query_stk_status(stk_request)

        return JsonResponse({
            'success': True,
            'status': status_result,
        })

    except StkPushRequest.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)
    except Exception as e:
        logger.error(f"Error querying transaction status: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
