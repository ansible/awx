from decimal import Decimal


def ResponseFactory(action):
    class FPSResponse(Response):
        _action = action
        _Result = globals().get(action + 'Result', ResponseElement)

        # due to nodes receiving their closing tags
        def endElement(self, name, value, connection):
            if name != action + 'Response':
                super(FPSResponse, self).endElement(name, value, connection)
    return FPSResponse


class ResponseElement(object):
    def __init__(self, connection=None, name=None):
        if connection is not None:
            self._connection = connection
        self._name = name or self.__class__.__name__

    @property
    def connection(self):
        return self._connection

    def __repr__(self):
        render = lambda pair: '{!s}: {!r}'.format(*pair)
        do_show = lambda pair: not pair[0].startswith('_')
        attrs = filter(do_show, self.__dict__.items())
        return '{0}({1})'.format(self.__class__.__name__,
                               ', '.join(map(render, attrs)))

    def startElement(self, name, attrs, connection):
        return None

    # due to nodes receiving their closing tags
    def endElement(self, name, value, connection):
        if name != self._name:
            setattr(self, name, value)


class Response(ResponseElement):
    _action = 'Undefined'

    def startElement(self, name, attrs, connection):
        if name == 'ResponseMetadata':
            setattr(self, name, ResponseElement(name=name))
        elif name == self._action + 'Result':
            setattr(self, name, self._Result(name=name))
        else:
            return super(Response, self).startElement(name, attrs, connection)
        return getattr(self, name)


class ComplexAmount(ResponseElement):
    def __repr__(self):
        return '{0} {1}'.format(self.CurrencyCode, self.Value)

    def __float__(self):
        return float(self.Value)

    def __str__(self):
        return str(self.Value)

    def startElement(self, name, attrs, connection):
        if name not in ('CurrencyCode', 'Value'):
            message = 'Unrecognized tag {0} in ComplexAmount'.format(name)
            raise AssertionError(message)
        return super(ComplexAmount, self).startElement(name, attrs, connection)

    def endElement(self, name, value, connection):
        if name == 'Value':
            value = Decimal(value)
        super(ComplexAmount, self).endElement(name, value, connection)


class AmountCollection(ResponseElement):
    def startElement(self, name, attrs, connection):
        setattr(self, name, ComplexAmount(name=name))
        return getattr(self, name)


class AccountBalance(AmountCollection):
    def startElement(self, name, attrs, connection):
        if name == 'AvailableBalances':
            setattr(self, name, AmountCollection(name=name))
            return getattr(self, name)
        return super(AccountBalance, self).startElement(name, attrs, connection)


class GetAccountBalanceResult(ResponseElement):
    def startElement(self, name, attrs, connection):
        if name == 'AccountBalance':
            setattr(self, name, AccountBalance(name=name))
            return getattr(self, name)
        return super(GetAccountBalanceResult, self).startElement(name, attrs,
            connection)


class GetTotalPrepaidLiabilityResult(ResponseElement):
    def startElement(self, name, attrs, connection):
        if name == 'OutstandingPrepaidLiability':
            setattr(self, name, AmountCollection(name=name))
            return getattr(self, name)
        return super(GetTotalPrepaidLiabilityResult, self).startElement(name,
            attrs, connection)


class GetPrepaidBalanceResult(ResponseElement):
    def startElement(self, name, attrs, connection):
        if name == 'PrepaidBalance':
            setattr(self, name, AmountCollection(name=name))
            return getattr(self, name)
        return super(GetPrepaidBalanceResult, self).startElement(name, attrs,
            connection)


class GetOutstandingDebtBalanceResult(ResponseElement):
    def startElement(self, name, attrs, connection):
        if name == 'OutstandingDebt':
            setattr(self, name, AmountCollection(name=name))
            return getattr(self, name)
        return super(GetOutstandingDebtBalanceResult, self).startElement(name,
            attrs, connection)


class TransactionPart(ResponseElement):
    def startElement(self, name, attrs, connection):
        if name == 'FeesPaid':
            setattr(self, name, ComplexAmount(name=name))
            return getattr(self, name)
        return super(TransactionPart, self).startElement(name, attrs,
            connection)


class Transaction(ResponseElement):
    def __init__(self, *args, **kw):
        self.TransactionPart = []
        super(Transaction, self).__init__(*args, **kw)

    def startElement(self, name, attrs, connection):
        if name == 'TransactionPart':
            getattr(self, name).append(TransactionPart(name=name))
            return getattr(self, name)[-1]
        if name in ('TransactionAmount', 'FPSFees', 'Balance'):
            setattr(self, name, ComplexAmount(name=name))
            return getattr(self, name)
        return super(Transaction, self).startElement(name, attrs, connection)


class GetAccountActivityResult(ResponseElement):
    def __init__(self, *args, **kw):
        self.Transaction = []
        super(GetAccountActivityResult, self).__init__(*args, **kw)

    def startElement(self, name, attrs, connection):
        if name == 'Transaction':
            getattr(self, name).append(Transaction(name=name))
            return getattr(self, name)[-1]
        return super(GetAccountActivityResult, self).startElement(name, attrs,
            connection)


class GetTransactionResult(ResponseElement):
    def startElement(self, name, attrs, connection):
        if name == 'Transaction':
            setattr(self, name, Transaction(name=name))
            return getattr(self, name)
        return super(GetTransactionResult, self).startElement(name, attrs,
            connection)


class GetTokensResult(ResponseElement):
    def __init__(self, *args, **kw):
        self.Token = []
        super(GetTokensResult, self).__init__(*args, **kw)

    def startElement(self, name, attrs, connection):
        if name == 'Token':
            getattr(self, name).append(ResponseElement(name=name))
            return getattr(self, name)[-1]
        return super(GetTokensResult, self).startElement(name, attrs,
            connection)
