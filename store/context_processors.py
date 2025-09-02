def cart_item_count(request):
    if 'cart' in request.session:
        return {'cart_item_count': sum(request.session['cart'].values())}
    return {'cart_item_count': 0}