# Copyright (c) 2012 Andy Davidoff http://www.disruptek.com/
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
from decimal import Decimal


class ComplexType(dict):
    _value = 'Value'

    def __repr__(self):
        return '{0}{1}'.format(getattr(self, self._value, None), self.copy())

    def __str__(self):
        return str(getattr(self, self._value, ''))


class DeclarativeType(object):
    def __init__(self, _hint=None, **kw):
        if _hint is not None:
            self._hint = _hint
        else:
            class JITResponse(ResponseElement):
                pass
            self._hint = JITResponse
            for name, value in kw.items():
                setattr(self._hint, name, value)
        self._value = None

    def setup(self, parent, name, *args, **kw):
        self._parent = parent
        self._name = name
        self._clone = self.__class__(self._hint)
        self._clone._parent = parent
        self._clone._name = name
        setattr(self._parent, self._name, self._clone)

    def start(self, *args, **kw):
        raise NotImplemented

    def end(self, *args, **kw):
        raise NotImplemented

    def teardown(self, *args, **kw):
        if self._value is None:
            delattr(self._parent, self._name)
        else:
            setattr(self._parent, self._name, self._value)


class Element(DeclarativeType):
    def start(self, *args, **kw):
        self._value = self._hint(parent=self._parent, **kw)
        return self._value

    def end(self, *args, **kw):
        pass


class SimpleList(DeclarativeType):
    def __init__(self, *args, **kw):
        DeclarativeType.__init__(self, *args, **kw)
        self._value = []

    def teardown(self, *args, **kw):
        if self._value == []:
            self._value = None
        DeclarativeType.teardown(self, *args, **kw)

    def start(self, *args, **kw):
        return None

    def end(self, name, value, *args, **kw):
        self._value.append(value)


class ElementList(SimpleList):
    def start(self, *args, **kw):
        value = self._hint(parent=self._parent, **kw)
        self._value += [value]
        return self._value[-1]

    def end(self, *args, **kw):
        pass


class MemberList(ElementList):
    def __init__(self, *args, **kw):
        self._this = kw.get('this')
        ElementList.__init__(self, *args, **kw)

    def start(self, attrs={}, **kw):
        Class = self._this or self._parent._type_for(self._name, attrs)
        if issubclass(self._hint, ResponseElement):
            ListClass = ElementList
        else:
            ListClass = SimpleList
        setattr(Class, Class._member, ListClass(self._hint))
        self._value = Class(attrs=attrs, parent=self._parent, **kw)
        return self._value

    def end(self, *args, **kw):
        self._value = getattr(self._value, self._value._member)
        ElementList.end(self, *args, **kw)


def ResponseFactory(action):
    result = globals().get(action + 'Result', ResponseElement)

    class MWSResponse(Response):
        _name = action + 'Response'

    setattr(MWSResponse, action + 'Result', Element(result))
    return MWSResponse


def strip_namespace(func):
    def wrapper(self, name, *args, **kw):
        if self._namespace is not None:
            if name.startswith(self._namespace + ':'):
                name = name[len(self._namespace + ':'):]
        return func(self, name, *args, **kw)
    return wrapper


class ResponseElement(dict):
    _override = {}
    _member = 'member'
    _name = None
    _namespace = None

    def __init__(self, connection=None, name=None, parent=None, attrs={}):
        if parent is not None and self._namespace is None:
            self._namespace = parent._namespace
        if connection is not None:
            self._connection = connection
        self._name = name or self._name or self.__class__.__name__
        self._declared('setup', attrs=attrs)
        dict.__init__(self, attrs.copy())

    def _declared(self, op, **kw):
        def inherit(obj):
            result = {}
            for cls in getattr(obj, '__bases__', ()):
                result.update(inherit(cls))
            result.update(obj.__dict__)
            return result

        scope = inherit(self.__class__)
        scope.update(self.__dict__)
        declared = lambda attr: isinstance(attr[1], DeclarativeType)
        for name, node in filter(declared, scope.items()):
            getattr(node, op)(self, name, parentname=self._name, **kw)

    @property
    def connection(self):
        return self._connection

    def __repr__(self):
        render = lambda pair: '{0!s}: {1!r}'.format(*pair)
        do_show = lambda pair: not pair[0].startswith('_')
        attrs = filter(do_show, self.__dict__.items())
        name = self.__class__.__name__
        if name == 'JITResponse':
            name = '^{0}^'.format(self._name or '')
        elif name == 'MWSResponse':
            name = '^{0}^'.format(self._name or name)
        return '{0}{1!r}({2})'.format(
            name, self.copy(), ', '.join(map(render, attrs)))

    def _type_for(self, name, attrs):
        return self._override.get(name, globals().get(name, ResponseElement))

    @strip_namespace
    def startElement(self, name, attrs, connection):
        attribute = getattr(self, name, None)
        if isinstance(attribute, DeclarativeType):
            return attribute.start(name=name, attrs=attrs,
                                              connection=connection)
        elif attrs.getLength():
            setattr(self, name, ComplexType(attrs.copy()))
        else:
            return None

    @strip_namespace
    def endElement(self, name, value, connection):
        attribute = getattr(self, name, None)
        if name == self._name:
            self._declared('teardown')
        elif isinstance(attribute, DeclarativeType):
            attribute.end(name=name, value=value, connection=connection)
        elif isinstance(attribute, ComplexType):
            setattr(attribute, attribute._value, value)
        else:
            setattr(self, name, value)


class Response(ResponseElement):
    ResponseMetadata = Element()

    @strip_namespace
    def startElement(self, name, attrs, connection):
        if name == self._name:
            self.update(attrs)
        else:
            return ResponseElement.startElement(self, name, attrs, connection)

    @property
    def _result(self):
        return getattr(self, self._action + 'Result', None)

    @property
    def _action(self):
        return (self._name or self.__class__.__name__)[:-len('Response')]


class ResponseResultList(Response):
    _ResultClass = ResponseElement

    def __init__(self, *args, **kw):
        setattr(self, self._action + 'Result', ElementList(self._ResultClass))
        Response.__init__(self, *args, **kw)


class FeedSubmissionInfo(ResponseElement):
    pass


class SubmitFeedResult(ResponseElement):
    FeedSubmissionInfo = Element(FeedSubmissionInfo)


class GetFeedSubmissionListResult(ResponseElement):
    FeedSubmissionInfo = ElementList(FeedSubmissionInfo)


class GetFeedSubmissionListByNextTokenResult(GetFeedSubmissionListResult):
    pass


class GetFeedSubmissionCountResult(ResponseElement):
    pass


class CancelFeedSubmissionsResult(GetFeedSubmissionListResult):
    pass


class GetServiceStatusResult(ResponseElement):
    Messages = Element(Messages=ElementList())


class ReportRequestInfo(ResponseElement):
    pass


class RequestReportResult(ResponseElement):
    ReportRequestInfo = Element()


class GetReportRequestListResult(RequestReportResult):
    ReportRequestInfo = ElementList()


class GetReportRequestListByNextTokenResult(GetReportRequestListResult):
    pass


class CancelReportRequestsResult(RequestReportResult):
    pass


class GetReportListResult(ResponseElement):
    ReportInfo = ElementList()


class GetReportListByNextTokenResult(GetReportListResult):
    pass


class ManageReportScheduleResult(ResponseElement):
    ReportSchedule = Element()


class GetReportScheduleListResult(ManageReportScheduleResult):
    pass


class GetReportScheduleListByNextTokenResult(GetReportScheduleListResult):
    pass


class UpdateReportAcknowledgementsResult(GetReportListResult):
    pass


class CreateInboundShipmentPlanResult(ResponseElement):
    InboundShipmentPlans = MemberList(ShipToAddress=Element(),
                                      Items=MemberList())


class ListInboundShipmentsResult(ResponseElement):
    ShipmentData = MemberList(Element(ShipFromAddress=Element()))


class ListInboundShipmentsByNextTokenResult(ListInboundShipmentsResult):
    pass


class ListInboundShipmentItemsResult(ResponseElement):
    ItemData = MemberList()


class ListInboundShipmentItemsByNextTokenResult(ListInboundShipmentItemsResult):
    pass


class ListInventorySupplyResult(ResponseElement):
    InventorySupplyList = MemberList(
        EarliestAvailability=Element(),
        SupplyDetail=MemberList(\
            EarliestAvailabileToPick=Element(),
            LatestAvailableToPick=Element(),
        )
    )


class ListInventorySupplyByNextTokenResult(ListInventorySupplyResult):
    pass


class ComplexAmount(ResponseElement):
    _amount = 'Value'

    def __repr__(self):
        return '{0} {1}'.format(self.CurrencyCode, getattr(self, self._amount))

    def __float__(self):
        return float(getattr(self, self._amount))

    def __str__(self):
        return str(getattr(self, self._amount))

    @strip_namespace
    def startElement(self, name, attrs, connection):
        if name not in ('CurrencyCode', self._amount):
            message = 'Unrecognized tag {0} in ComplexAmount'.format(name)
            raise AssertionError(message)
        return ResponseElement.startElement(self, name, attrs, connection)

    @strip_namespace
    def endElement(self, name, value, connection):
        if name == self._amount:
            value = Decimal(value)
        ResponseElement.endElement(self, name, value, connection)


class ComplexMoney(ComplexAmount):
    _amount = 'Amount'


class ComplexWeight(ResponseElement):
    def __repr__(self):
        return '{0} {1}'.format(self.Value, self.Unit)

    def __float__(self):
        return float(self.Value)

    def __str__(self):
        return str(self.Value)

    @strip_namespace
    def startElement(self, name, attrs, connection):
        if name not in ('Unit', 'Value'):
            message = 'Unrecognized tag {0} in ComplexWeight'.format(name)
            raise AssertionError(message)
        return ResponseElement.startElement(self, name, attrs, connection)

    @strip_namespace
    def endElement(self, name, value, connection):
        if name == 'Value':
            value = Decimal(value)
        ResponseElement.endElement(self, name, value, connection)


class Dimension(ComplexType):
    _value = 'Value'


class ComplexDimensions(ResponseElement):
    _dimensions = ('Height', 'Length', 'Width', 'Weight')

    def __repr__(self):
        values = [getattr(self, key, None) for key in self._dimensions]
        values = filter(None, values)
        return 'x'.join(map('{0.Value:0.2f}{0[Units]}'.format, values))

    @strip_namespace
    def startElement(self, name, attrs, connection):
        if name not in self._dimensions:
            message = 'Unrecognized tag {0} in ComplexDimensions'.format(name)
            raise AssertionError(message)
        setattr(self, name, Dimension(attrs.copy()))

    @strip_namespace
    def endElement(self, name, value, connection):
        if name in self._dimensions:
            value = Decimal(value or '0')
        ResponseElement.endElement(self, name, value, connection)


class FulfillmentPreviewItem(ResponseElement):
    EstimatedShippingWeight = Element(ComplexWeight)


class FulfillmentPreview(ResponseElement):
    EstimatedShippingWeight = Element(ComplexWeight)
    EstimatedFees = MemberList(\
        Element(\
            Amount=Element(ComplexAmount),
        ),
    )
    UnfulfillablePreviewItems = MemberList(FulfillmentPreviewItem)
    FulfillmentPreviewShipments = MemberList(\
        FulfillmentPreviewItems=MemberList(FulfillmentPreviewItem),
    )


class GetFulfillmentPreviewResult(ResponseElement):
    FulfillmentPreviews = MemberList(FulfillmentPreview)


class FulfillmentOrder(ResponseElement):
    DestinationAddress = Element()
    NotificationEmailList = MemberList(str)


class GetFulfillmentOrderResult(ResponseElement):
    FulfillmentOrder = Element(FulfillmentOrder)
    FulfillmentShipment = MemberList(Element(\
            FulfillmentShipmentItem=MemberList(),
            FulfillmentShipmentPackage=MemberList(),
        )
    )
    FulfillmentOrderItem = MemberList()


class ListAllFulfillmentOrdersResult(ResponseElement):
    FulfillmentOrders = MemberList(FulfillmentOrder)


class ListAllFulfillmentOrdersByNextTokenResult(ListAllFulfillmentOrdersResult):
    pass


class Image(ResponseElement):
    pass


class AttributeSet(ResponseElement):
    ItemDimensions = Element(ComplexDimensions)
    ListPrice = Element(ComplexMoney)
    PackageDimensions = Element(ComplexDimensions)
    SmallImage = Element(Image)


class ItemAttributes(AttributeSet):
    Languages = Element(Language=ElementList())

    def __init__(self, *args, **kw):
        names = ('Actor', 'Artist', 'Author', 'Creator', 'Director',
                 'Feature', 'Format', 'GemType', 'MaterialType',
                 'MediaType', 'OperatingSystem', 'Platform')
        for name in names:
            setattr(self, name, SimpleList())
        AttributeSet.__init__(self, *args, **kw)


class VariationRelationship(ResponseElement):
    Identifiers = Element(MarketplaceASIN=Element(),
                          SKUIdentifier=Element())
    GemType = SimpleList()
    MaterialType = SimpleList()
    OperatingSystem = SimpleList()


class Price(ResponseElement):
    LandedPrice = Element(ComplexMoney)
    ListingPrice = Element(ComplexMoney)
    Shipping = Element(ComplexMoney)


class CompetitivePrice(ResponseElement):
    Price = Element(Price)


class CompetitivePriceList(ResponseElement):
    CompetitivePrice = ElementList(CompetitivePrice)


class CompetitivePricing(ResponseElement):
    CompetitivePrices = Element(CompetitivePriceList)
    NumberOfOfferListings = SimpleList()
    TradeInValue = Element(ComplexMoney)


class SalesRank(ResponseElement):
    pass


class LowestOfferListing(ResponseElement):
    Qualifiers = Element(ShippingTime=Element())
    Price = Element(Price)


class Product(ResponseElement):
    _namespace = 'ns2'
    Identifiers = Element(MarketplaceASIN=Element(),
                          SKUIdentifier=Element())
    AttributeSets = Element(\
        ItemAttributes=ElementList(ItemAttributes),
    )
    Relationships = Element(\
        VariationParent=ElementList(VariationRelationship),
    )
    CompetitivePricing = ElementList(CompetitivePricing)
    SalesRankings = Element(\
        SalesRank=ElementList(SalesRank),
    )
    LowestOfferListings = Element(\
        LowestOfferListing=ElementList(LowestOfferListing),
    )


class ListMatchingProductsResult(ResponseElement):
    Products = Element(Product=ElementList(Product))


class ProductsBulkOperationResult(ResponseElement):
    Product = Element(Product)
    Error = Element()


class ProductsBulkOperationResponse(ResponseResultList):
    _ResultClass = ProductsBulkOperationResult


class GetMatchingProductResponse(ProductsBulkOperationResponse):
    pass


class GetMatchingProductForIdResult(ListMatchingProductsResult):
    pass


class GetCompetitivePricingForSKUResponse(ProductsBulkOperationResponse):
    pass


class GetCompetitivePricingForASINResponse(ProductsBulkOperationResponse):
    pass


class GetLowestOfferListingsForSKUResponse(ProductsBulkOperationResponse):
    pass


class GetLowestOfferListingsForASINResponse(ProductsBulkOperationResponse):
    pass


class ProductCategory(ResponseElement):

    def __init__(self, *args, **kw):
        setattr(self, 'Parent', Element(ProductCategory))
        ResponseElement.__init__(self, *args, **kw)


class GetProductCategoriesResult(ResponseElement):
    Self = Element(ProductCategory)


class GetProductCategoriesForSKUResult(GetProductCategoriesResult):
    pass


class GetProductCategoriesForASINResult(GetProductCategoriesResult):
    pass


class Order(ResponseElement):
    OrderTotal = Element(ComplexMoney)
    ShippingAddress = Element()
    PaymentExecutionDetail = Element(\
        PaymentExecutionDetailItem=ElementList(\
            PaymentExecutionDetailItem=Element(\
                Payment=Element(ComplexMoney)
            )
        )
    )


class ListOrdersResult(ResponseElement):
    Orders = Element(Order=ElementList(Order))


class ListOrdersByNextTokenResult(ListOrdersResult):
    pass


class GetOrderResult(ListOrdersResult):
    pass


class OrderItem(ResponseElement):
    ItemPrice = Element(ComplexMoney)
    ShippingPrice = Element(ComplexMoney)
    GiftWrapPrice = Element(ComplexMoney)
    ItemTax = Element(ComplexMoney)
    ShippingTax = Element(ComplexMoney)
    GiftWrapTax = Element(ComplexMoney)
    ShippingDiscount = Element(ComplexMoney)
    PromotionDiscount = Element(ComplexMoney)
    PromotionIds = SimpleList()
    CODFee = Element(ComplexMoney)
    CODFeeDiscount = Element(ComplexMoney)


class ListOrderItemsResult(ResponseElement):
    OrderItems = Element(OrderItem=ElementList(OrderItem))


class ListMarketplaceParticipationsResult(ResponseElement):
    ListParticipations = Element(Participation=ElementList())
    ListMarketplaces = Element(Marketplace=ElementList())


class ListMarketplaceParticipationsByNextTokenResult(ListMarketplaceParticipationsResult):
    pass
