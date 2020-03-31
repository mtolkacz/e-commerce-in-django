/*price range*/

$('#sl2').slider();

var RGBChange = function() {
    $('#RGB').css('background', 'rgb('+r.getValue()+','+g.getValue()+','+b.getValue()+')')
};

/*scroll to top*/

$(document).ready(function(){
    $(function () {
        $.scrollUp({
            scrollName: 'scrollUp', // Element ID
            scrollDistance: 300, // Distance from top/bottom before showing element (px)
            scrollFrom: 'top', // 'top' or 'bottom'
            scrollSpeed: 300, // Speed back to top (ms)
            easingType: 'linear', // Scroll to top easing (see http://easings.net/)
            animation: 'fade', // Fade, slide, none
            animationSpeed: 200, // Animation in speed (ms)
            scrollTrigger: false, // Set a custom triggering element. Can be an HTML string or jQuery object
                    //scrollTarget: false, // Set a custom target element for scrolling to the top
            scrollText: '<i class="fa fa-angle-up"></i>', // Text for element, can contain HTML
            scrollTitle: false, // Set a custom <a> title if required.
            scrollImg: false, // Set true to use image
            activeOverlay: false, // Set CSS color to display scrollUp active point, e.g '#00FFFF'
            zIndex: 2147483647 // Z-Index for the overlay
        });
    });
});

/* cart checkout calculations */

setTimeout(function() {
    $('#cart_messages').fadeOut(3000);
}, 5000);

var max_items_in_cart = 30

function increaseValue(item_id) {
    var cart_value = parseInt(document.getElementById('item'+item_id).value, 10);
    cart_value = isNaN(cart_value) ? 0 : cart_value;
    cart_value > max_items_in_cart-1 ? cart_value = max_items_in_cart : cart_value++;
    if (document.getElementById('item'+item_id).value == cart_value){
        return
    }
    if (cart_value == 2){
        if(document.getElementById('apiece_value'+item_id).innerText == ''){
                document.getElementById('apiece_value'+item_id).innerText = document.getElementById('item_total_value'+item_id).innerText + ' apiece'
        }
    }
    document.getElementById('item'+item_id).value = cart_value;
    console.log(cart_value);
    calculate_cart(cart_value, item_id);
}

$('#increase_cart').click(function(){
    var item_id = $(this).closest('div').attr('id');
    increaseValue(item_id);
    return false; }
);

$('#decrease_cart').click(function(){
    var item_id = $(this).closest('div').attr('id');
    decreaseValue(item_id);
    return false;
});


function decreaseValue(item_id) {
    var cart_value = parseInt(document.getElementById('item'+item_id).value, 10);
    cart_value = isNaN(cart_value) ? 1 : cart_value;
    cart_value <= 2 ? cart_value = 1 : cart_value--;
    if (document.getElementById('item'+item_id).value == cart_value){
        return
    }
    if (cart_value == 1){
        if(document.getElementById('apiece_value'+item_id).innerText != ''){
                document.getElementById('apiece_value'+item_id).innerText = ''
        }
    }
    document.getElementById('item'+item_id).value = cart_value;
    calculate_cart(cart_value, item_id);
}

function updateValue(item_id) {
    var cart_value = parseInt(document.getElementById('item'+item_id).value, 10);
    cart_value = isNaN(cart_value) ? 1 : cart_value;
    cart_value < 1 ? cart_value = 1 : '';
    cart_value > max_items_in_cart ? cart_value = max_items_in_cart : '';

    if (cart_value == 1){
        document.getElementById('apiece_value'+item_id).innerText = ''
    }
    else {
        if(document.getElementById('apiece_value'+item_id).innerText == ''){
                document.getElementById('apiece_value'+item_id).innerText = document.getElementById('item_total_value'+item_id).innerText + ' apiece'
        }
    }
    document.getElementById('item'+item_id).value = cart_value;
    calculate_cart(cart_value, item_id);
}

function removeItem(item_id)
{
    var elem = document.getElementById("row"+item_id);
    elem.parentNode.removeChild(elem);
    delete_from_cart(item_id);
}

function calculate_cart(cart_value, item_id)
{
    $.ajax({
        url: '/cart/calculate/',
        data: {
            'cart_value': cart_value,
            'item_id': item_id
        },
        dataType: 'json',
        success: function (data) {
            if(data.success){
                if(data.item_total_value) {
                    document.getElementById("item_total_value"+item_id).innerText = data.item_total_value
                }
                if(data.cart_total_value) {
                    document.getElementById("cart_total_value").innerText = data.cart_total_value
                }
            }
            else if (data.remove_cart){
                console.log("No success");
                //window.location.replace("/cart/");
            }
        }
    });
}

function add_to_cart(item_id)
{
    $.ajax({
        url: '/cart/add_item/',
        data: {
            'item_id': item_id,
            'ajax': True
        },
        dataType: 'json',
        success: function (data) {
            if(data.success){
                console.log("Success");
            }
            else {
                console.log("Failed");
            }
        }
    });
}

function delete_from_cart(item_id)
{
    $.ajax({
        url: '/cart/delete_item/',
        data: {
            'item_id': item_id
        },
        dataType: 'json',
        success: function (data) {
            if(data.success){
                console.log("Success");
            }
            else if (data.remove_cart){
                location.reload();
                console.log("Removed cart");
            }
        }
    });
}
