import json
from datetime import datetime
from typing import List, Dict, Any
from zoneinfo import ZoneInfo

import pytz


def convert_to_timestamp(date_str: str) -> float:
    """Convert a date string to a timestamp."""
    ts = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z").timestamp()
    return ts

def extract_base_transaction_values(transaction):
    base_data = {
        'activityId': transaction.get('activityId'),
        'time': parser.isoparse(transaction.get('time')).timestamp() if transaction.get('time') else None,
        'description': transaction.get('description'),
        'accountNumber': transaction.get('accountNumber'),
        'type': transaction.get('type'),
        'status': transaction.get('status'),
        'tradeDate': parser.isoparse(transaction.get('tradeDate')).timestamp() if transaction.get('tradeDate') else None,
        'netAmount': transaction.get('netAmount'),
        'orderId': transaction.get('orderId', None),
        'totalFees': 0.0  # Initialize totalFees
    }

    # Calculate total fees based on feeType
    for item in transaction.get('transferItems', []):
        fee_type = item.get('feeType')
        if fee_type:
            base_data['totalFees'] += item.get('amount', 0.0)

    return base_data


from datetime import datetime
from dateutil import parser
import json

from datetime import datetime
from dateutil import parser
import json

from datetime import datetime
from dateutil import parser
import json


def extract_additional_transaction_values_orig(transaction):
    additional_data = {
        "optionTx": [],
        "equityTx": [],
        "futureTx": [],
        "cashEquivalentTx": [],
        "fixedIncomeTx": [],
        "txFees": [],
        "unhandledTx": []
    }

    transaction_id = transaction.get('activityId')

    for item in transaction.get('transferItems', []):
        instrument = item.get('instrument', {})
        asset_type = instrument.get('assetType')

        if asset_type == 'OPTION':
            expiration_date = instrument.get('expirationDate')
            expiration_timestamp = None
            expiration_date_str = None
            if expiration_date:
                expiration_dt = parser.isoparse(expiration_date)
                expiration_timestamp = expiration_dt.timestamp()
                expiration_date_str = expiration_dt.strftime('%Y-%m-%d')

            deliverable_type = None
            if 'optionDeliverables' in instrument:
                deliverable_type = instrument['optionDeliverables'][0].get('deliverable', {}).get('assetType')

            option_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'optionSymbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'putCall': instrument.get('putCall'),
                'strikePrice': instrument.get('strikePrice'),
                'optionType': instrument.get('type'),
                'underlyingSymbol': instrument.get('underlyingSymbol'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'positionEffect': item.get('positionEffect'),
                'expirationDate': expiration_date_str,
                'expiration': expiration_timestamp,
                'deliverableType': deliverable_type,
                'optionPremiumMultiplier': instrument.get('optionPremiumMultiplier')
            }
            additional_data['optionTx'].append(option_data)

        elif asset_type in ['EQUITY', 'COLLECTIVE_INVESTMENT', 'INDEX']:
            equity_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'symbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'positionEffect': item.get('positionEffect'),
                'instrumentType': instrument.get('type')
            }
            additional_data['equityTx'].append(equity_data)

        elif asset_type == 'FUTURE':
            expiration_date = instrument.get('expirationDate')
            expiration_timestamp = None
            expiration_date_str = None
            if expiration_date:
                expiration_dt = parser.isoparse(expiration_date)
                expiration_timestamp = expiration_dt.timestamp()
                expiration_date_str = expiration_dt.strftime('%Y-%m-%d')

            future_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'symbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'positionEffect': item.get('positionEffect'),
                'expirationDate': expiration_date_str,
                'expiration': expiration_timestamp,
                'multiplier': instrument.get('multiplier'),
                'futureType': instrument.get('futureType')
            }
            additional_data['futureTx'].append(future_data)

        elif asset_type == 'CASH_EQUIVALENT':
            cash_equivalent_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'symbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'positionEffect': item.get('positionEffect'),
                'instrumentType': instrument.get('type')
            }
            additional_data['cashEquivalentTx'].append(cash_equivalent_data)

        elif asset_type == 'FIXED_INCOME':
            maturity_date = instrument.get('maturityDate')
            maturity_timestamp = None
            maturity_date_str = None
            if maturity_date:
                maturity_dt = parser.isoparse(maturity_date)
                maturity_timestamp = maturity_dt.timestamp()
                maturity_date_str = maturity_dt.strftime('%Y-%m-%d')

            fixed_income_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'symbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'factor': instrument.get('factor'),
                'maturityDate': maturity_date_str,
                'multiplier': instrument.get('multiplier'),
                'type': instrument.get('type'),
                'variableRate': instrument.get('variableRate')
            }
            additional_data['fixedIncomeTx'].append(fixed_income_data)

        elif asset_type == 'CURRENCY':
            if 'feeType' in item:
                fee_data = {
                    'activityId': transaction_id,
                    'feeType': item['feeType'],
                    'amount': item.get('amount')
                }
                additional_data['txFees'].append(fee_data)

        else:
            unhandled_data = {
                "activityId": transaction_id,
                "entry": item
            }
            additional_data['unhandledTx'] = unhandled_data
            print(f"Unhandled assetType: {asset_type}")
            print(f"Response causing error: {json.dumps(transaction, indent=4)}")
            #raise Exception(f"Unhandled assetType: {asset_type}")

    return additional_data

def extract_additional_transaction_values(transaction: dict) -> dict:
    additional_data = {
        'optionTx': [],
        'equityTx': [],
        'futureTx': [],
        'cashEquivalentTx': [],
        'txFees': [],
        'fixedIncomeTx': []
    }

    transfer_items = transaction.get('transferItems', [])
    transaction_id = transaction.get('activityId')

    for item in transfer_items:
        instrument = item.get('instrument', {})
        asset_type = instrument.get('assetType')

        if asset_type == 'OPTION':
            expdt = datetime.strptime(instrument.get('expirationDate'), '%Y-%m-%dT%H:%M:%S%z')
            expdt = expdt.replace(hour=14, minute=30, second=0, microsecond=0, tzinfo=ZoneInfo("America/Los_Angeles"))

            option_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'optionSymbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'putCall': instrument.get('putCall'),
                'strikePrice': instrument.get('strikePrice'),
                'optionType': instrument.get('type'),
                'underlyingSymbol': instrument.get('underlyingSymbol'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'positionEffect': item.get('positionEffect'),
                #'expirationDate': instrument.get('expirationDate'),
                'expirationDate': expdt.date(),

                'expiration': expdt.timestamp(),
                'optionPremiumMultiplier': instrument.get('optionPremiumMultiplier'),
                'deliverableType': instrument.get('optionDeliverables', [{}])[0].get('deliverable', {}).get('assetType')
            }
            additional_data['optionTx'].append(option_data)

        elif asset_type in ['EQUITY', 'COLLECTIVE_INVESTMENT', 'INDEX']:
            equity_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'symbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'positionEffect': item.get('positionEffect'),
                'instrumentType': instrument.get('type')
            }
            additional_data['equityTx'].append(equity_data)

        elif asset_type == 'FUTURE':
            expdt = datetime.strptime(instrument.get('expirationDate'), '%Y-%m-%dT%H:%M:%S%z')
            expdt = expdt.replace(hour=14, minute=30, second=0, microsecond=0, tzinfo=ZoneInfo("America/Los_Angeles"))
            future_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'symbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'positionEffect': item.get('positionEffect'),
                'expirationDate': instrument.get('expirationDate'),
                'expiration': datetime.strptime(instrument.get('expirationDate'), '%Y-%m-%dT%H:%M:%S%z').timestamp(),
                'multiplier': instrument.get('multiplier'),
                'futureType': instrument.get('futureType')
            }
            additional_data['futureTx'].append(future_data)

        elif asset_type == 'CURRENCY' and item.get('feeType'):
            fee_data = {
                'activityId': transaction_id,
                'feeType': item.get('feeType'),
                'amount': item.get('amount')
            }
            additional_data['txFees'].append(fee_data)

        elif asset_type == 'FIXED_INCOME':
            fixed_income_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'symbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'positionEffect': item.get('positionEffect'),
                'factor': instrument.get('factor'),
                'maturityDate': instrument.get('maturityDate'),
                'multiplier': instrument.get('multiplier'),
                'type': instrument.get('type'),
                'variableRate': instrument.get('variableRate')
            }
            additional_data['fixedIncomeTx'].append(fixed_income_data)

    return additional_data


def extract_additional_transaction_values_orig(transaction: dict) -> dict:
    additional_data = {
        'optionTx': [],
        'equityTx': [],
        'futureTx': [],
        'cashEquivalentTx': [],
        'txFees': [],
        'fixedIncomeTx': []
    }

    transfer_items = transaction.get('transferItems', [])
    transaction_id = transaction.get('activityId')

    for item in transfer_items:
        instrument = item.get('instrument', {})
        asset_type = instrument.get('assetType')

        if asset_type == 'OPTION':
            option_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'optionSymbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'putCall': instrument.get('putCall'),
                'strikePrice': instrument.get('strikePrice'),
                'optionType': instrument.get('type'),
                'underlyingSymbol': instrument.get('underlyingSymbol'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'positionEffect': item.get('positionEffect'),
                'expirationDate': instrument.get('expirationDate'),
                'expiration': datetime.fromisoformat(instrument.get('expirationDate').replace("Z", "")),
                'optionPremiumMultiplier': instrument.get('optionPremiumMultiplier'),
                'deliverableType': instrument.get('optionDeliverables', [{}])[0].get('deliverable', {}).get('assetType')
            }
            additional_data['optionTx'].append(option_data)

        elif asset_type in ['EQUITY', 'COLLECTIVE_INVESTMENT', 'INDEX']:
            equity_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'symbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'positionEffect': item.get('positionEffect'),
                'instrumentType': instrument.get('type')
            }
            additional_data['equityTx'].append(equity_data)

        elif asset_type == 'FUTURE':
            future_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'symbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'positionEffect': item.get('positionEffect'),
                'expirationDate': instrument.get('expirationDate'),
                'expiration': datetime.fromisoformat(instrument.get('expirationDate').replace("Z", "")),
                'multiplier': instrument.get('multiplier'),
                'futureType': instrument.get('futureType')
            }
            additional_data['futureTx'].append(future_data)

        elif asset_type == 'CURRENCY' and item.get('feeType'):
            fee_data = {
                'activityId': transaction_id,
                'feeType': item.get('feeType'),
                'amount': item.get('amount')
            }
            additional_data['txFees'].append(fee_data)

        elif asset_type == 'FIXED_INCOME':
            fixed_income_data = {
                'transactionId': transaction_id,
                'orderId': transaction.get('orderId'),
                'assetType': asset_type,
                'symbol': instrument.get('symbol'),
                'description': instrument.get('description'),
                'quantity': item.get('amount'),
                'cost': item.get('cost'),
                'price': item.get('price'),
                'positionEffect': item.get('positionEffect'),
                'factor': instrument.get('factor'),
                'maturityDate': instrument.get('maturityDate'),
                'multiplier': instrument.get('multiplier'),
                'type': instrument.get('type'),
                'variableRate': instrument.get('variableRate')
            }
            additional_data['fixedIncomeTx'].append(fixed_income_data)

    return additional_data

def process_transactioni_gpt4(transaction: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    try:
        transaction_type = transaction['type']
        additional_data = {
            'transactions': [],
            'optionTx': [],
            'equityTx': [],
            'futureTx': [],
            'cashEquivalentTx': [],
            'txFees': []
        }

        # Handle different transaction types
        if transaction_type == "SMA_ADJUSTMENT":
            base_data = extract_base_transaction_values(transaction)
            additional_data['baseTx'].append(base_data)

        elif transaction_type == "ELECTRONIC_FUND":
            base_data = extract_base_transaction_values(transaction)
            additional_data['baseTx'].append(base_data)

        elif transaction_type == "WIRE_OUT" or transaction_type == "WIRE_IN":
            base_data = extract_base_transaction_values(transaction)
            if 'transferItems' in transaction:
                net_amount = sum(item['amount'] for item in transaction['transferItems'])
                base_data['netAmount'] = net_amount
            additional_data['baseTx'].append(base_data)

        elif transaction_type == "CASH_DISBURSEMENT":
            base_data = extract_base_transaction_values(transaction)
            additional_data['baseTx'].append(base_data)

        elif transaction_type == "CASH_RECEIPT":
            base_data = extract_base_transaction_values(transaction)
            additional_transactions = extract_additional_transaction_values(transaction)
            additional_data['baseTx'].append(base_data)
            for key, value in additional_transactions.items():
                additional_data[key].extend(value)

        elif transaction_type == "DIVIDEND_OR_INTEREST":
            base_data = extract_base_transaction_values(transaction)
            additional_data['baseTx'].append(base_data)

        elif transaction_type == "RECEIVE_AND_DELIVER" or transaction_type == "TRADE":
            base_data = extract_base_transaction_values(transaction)
            additional_transactions = extract_additional_transaction_values(transaction)
            additional_data['baseTx'].append(base_data)
            for key, value in additional_transactions.items():
                additional_data[key].extend(value)

        elif transaction_type == "JOURNAL":
            base_data = extract_base_transaction_values(transaction)
            additional_data['baseTx'].append(base_data)

        else:
            print(f"Unhandled transaction type: {transaction_type}")
            print(f"Transaction: {json.dumps(transaction, indent=4)}")

        return additional_data

    except Exception as e:
        print(f"Error processing transaction: {json.dumps(transaction, indent=4)}")
        print(e)
        return {}


def process_transaction(transaction: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    try:
        transaction_type = transaction['type']
        additional_data = {
            'transactions': [],
            'optionTx': [],
            'equityTx': [],
            'futureTx': [],
            'cashEquivalentTx': [],
            'txFees': [],
            'fixedIncomeTx': []
        }

        base_data = extract_base_transaction_values(transaction)
        additional_data['transactions'].append(base_data)

        if transaction_type == "SMA_ADJUSTMENT":
            pass  # Only base transaction

        elif transaction_type == "ELECTRONIC_FUND":
            pass  # Only base transaction

        elif transaction_type in ["WIRE_OUT", "WIRE_IN"]:
            if 'transferItems' in transaction:
                net_amount = sum(item['amount'] for item in transaction['transferItems'])
                base_data['netAmount'] = net_amount

        elif transaction_type == "CASH_DISBURSEMENT":
            pass  # Only base transaction

        elif transaction_type == "CASH_RECEIPT":
            additional_transactions = extract_additional_transaction_values(transaction)
            for key, value in additional_transactions.items():
                additional_data[key].extend(value)

        elif transaction_type == "DIVIDEND_OR_INTEREST":
            pass  # Only base transaction

        elif transaction_type in ["RECEIVE_AND_DELIVER", "TRADE"]:
            additional_transactions = extract_additional_transaction_values(transaction)
            for key, value in additional_transactions.items():
                additional_data[key].extend(value)

        elif transaction_type == "JOURNAL":
            pass  # Only base transaction

        else:
            print(f"Unhandled transaction type: {transaction_type}")
            print(f"Transaction: {json.dumps(transaction, indent=4)}")

        return additional_data

    except Exception as e:
        print(f"Error processing transaction: {json.dumps(transaction, indent=4)}")
        print(e)
        return {}
